# ChassisController_t1：网关 → 下层主控演进计划

## Context

**当前状态：** `ChassisController_t1` 是纯 UART↔CAN 透明网关，无本地状态、无控制语义。`3_MCLM_t2` 是双电机 PID 闭环控制器板，已定义完整的 CAN 命令协议（0x123/0x124 控制、0x323/0x324 状态反馈、0x101 全车停止）。

**目标：** 将底盘控制器从"数据转发系统"升级为"分布式控制节点"，保留网关功能的同时新增 SystemState 管理、IMU（MPU6050 + Mahony 9 轴融合）、本地控制决策能力。

**工作区已有可复用资产：**
- `6_Mpu6050/6_Mpu6050_t1/App/` — 生产级 MPU6050 + AK09911 驱动 + Mahony 9 轴 AHRS 融合，ROS 标准单位输出
- `6_BMP280/` — 已验证可工作的气压/高度传感器驱动
- `vofa/` — 数据可视化工具生态

---

## Phase 0：准备工作（分析对齐）

**目的：** 确保 CAN 协议两侧完全对齐，避免集成后不匹配。

| 步骤 | 动作 | 涉及文件 |
|------|------|----------|
| 0.1 | 确认 ChassisController 当前 CAN ID_GROUP 与 MCLM_t2 一致（当前都默认 group=2，即 0x123/0x124 系） | `ChassisController:App/app_config.h`（当前无此配置，需新增） |
| 0.2 | 记录 MCLM_t2 完整 CAN 协议到 ChassisController 文档：控制 ID、状态 ID、命令字节含义、状态帧编码格式 | 新增 `doc/can_protocol.md` |
| 0.3 | 确认 MPU6050 的 I2C 引脚分配与 ChassisController 硬件不冲突（Chassis 当前 I2C 未用，需分配 PB6/PB7 或其它） | `ChassisController:Core/Inc/main.h` + `Core/Src/main.c` |

---

## Phase 1：基础架构升级（SystemState + 任务重构）

**核心变更：** 从"数据管道"变"状态驱动"架构。

### 1.1 新增 `App/app_system_state.h`

新建系统状态结构体，作为所有任务的数据中枢：

```c
typedef struct {
    // IMU 状态
    float roll, pitch, yaw;           // 欧拉角 (deg)
    float quat[4];                    // 四元数 (w,x,y,z)
    float gyro[3];                    // 角速度 (rad/s)
    float accel[3];                   // 线加速度 (m/s^2)
    uint32_t imu_timestamp;
} IMU_State_t;

typedef struct {
    int16_t current_speed;            // 当前逻辑速度 (-100..100)
    int16_t target_speed;             // 目标逻辑速度
    int16_t pwm_output;               // PWM 输出值
    uint8_t flags;                    // 状态标志 (stall, saturated 等)
    uint32_t last_update_tick;        // 最后更新时刻
} Motor_State_t;

typedef struct {
    uint8_t mode;                     // 系统模式
    uint8_t estop;                    // 紧急停止标志
    uint32_t uptime_ms;               // 系统运行时间
} System_Flag_t;

typedef struct {
    IMU_State_t    imu;
    Motor_State_t  motor[8];          // 最多 8 个电机
    System_Flag_t  flag;
} System_State_t;

extern System_State_t g_system_state;
```

**为什么：** 现有架构没有统一状态，每个任务各自为政。SystemState 是后续所有控制算法的基础。

### 1.2 新增 `App/app_command.h`

命令消息结构体（从 MCLM_t2 的 `command.h` 借鉴，适配 ChassisController）：

```c
typedef enum {
    CMD_NONE = 0,
    CMD_SET_SPEED = 1,
    CMD_STOP = 3,
    CMD_ESTOP = 4,
    CMD_QUERY_STATUS = 6,
    // ... 可扩展
} App_CommandType_t;

typedef struct {
    App_CommandType_t type;
    int16_t value;
    uint8_t motor_id;
    uint32_t can_id;                  // 原始 CAN ID，用于回传
} App_CommandMsg_t;
```

### 1.3 重构 `CanRxProcess_Task_Run()` → `CanRxProcess_Task_Run()`

**变更要点：** CAN RX 不再无脑打印到 UART，而是根据 CAN ID 解析并更新 `g_system_state`：

| CAN ID | 动作 |
|--------|------|
| 0x323 (转向状态) | 解析 8 字节状态帧 → 更新 `g_system_state.motor[0]` |
| 0x324 (动力状态) | 解析 8 字节状态帧 → 更新 `g_system_state.motor[1]` |
| 其他 | 可选：通过 UART 打印（保留原有调试能力） |

状态帧编码（来自 MCLM_t2 `command_task.c`）：
```
[0-1] current_logic_speed (int16)
[2-3] accumulated_ticks   (uint16)
[4-5] pwm_output          (int16)
[6]   target_logic_speed  (int8)
[7]   flags               (uint8)
```

### 1.4 新增 `CommandProcess_Task_Run()`（高优先级）

新任务替代原有直接 `UartToCan` 透传逻辑：

```
ProtocolParser → uartToCanQueue → CommandProcess_Task
                                      │
                                      ├── CMD_SET_SPEED → 更新 g_system_state.motor[x].target
                                      ├── CMD_ESTOP     → g_system_state.flag.estop = 1
                                      ├── CMD_QUERY_STATUS → 发送状态回 UART
                                      └── 其他 CAN 命令 → 转发到 CAN 总线（保留透传）
```

### 1.5 保留 `UartToCan_Task_Run()` 但简化为"纯 CAN 发送器"

拆分为二：
- `CommandProcess_Task`：解析语义、更新状态、决策
- `UartToCan_Task`：仅做 "从队列取消息 → HAL_CAN_AddTxMessage" 的机械发送

### 1.6 更新 `freertos.c`（CubeMX 守护区域）

- 新增 `CommandQueueHandle` 消息队列（深度 16，元素 `App_CommandMsg_t`）
- 新增 `CommandProcess_Ta` 任务（优先级 `osPriorityNormal1`，栈 256 字）
- 调整 `CanRxProcess_Ta` 优先级从 NORMAL 提升到 NORMAL1（状态更新应优先于调试输出）

### 1.7 修改 `app_config.h`

- 新增 CAN_ID_GROUP 宏定义，与 MCLM_t2 对齐
- 新增 CAN 协议常量（CAN_MOTOR_TURN_STATUS_STDID 等）

### 涉及文件

| 文件 | 变更类型 |
|------|----------|
| `App/app_system_state.h` | **新建** |
| `App/app_command.h` | **新建** |
| `App/app_config.h` | 修改：新增 CAN 协议宏、状态类型 |
| `App/app_globals.h` | 修改：新增 SystemState 和 CommandQueue 的 extern |
| `App/app_task.h` | 修改：新增 CommandProcess_Task_Run 声明 |
| `App/app_task.c` | 重构：CanRxProcess（状态更新），新增 CommandProcess 任务，修改 UartToCan |
| `Core/Src/freertos.c` | 修改：新增队列和任务创建 |
| `Core/Src/stm32f1xx_it.c` | 若有新队列 drop 统计变量则添加 |

---

## Phase 2：CAN 协议完整集成

**目的：** ChassisController 理解 MCLM_t2 的 CAN 协议，实现智能转发和双向状态同步。

### 2.1 修改 CAN 硬件过滤器

当前 ChassisController 的 CAN 过滤器接收所有帧。改为"接收所需 ID + 全部通配"的双滤波器方案：

| 滤波器组 | 模式 | 用途 |
|----------|------|------|
| Bank 0 | ID_Mask: 接收 0x323, 0x324（电机状态）| 下行：电机状态←MCLM |
| Bank 1 | ID_Mask: 接收全部（0x000 mask）| 保持原有全收能力 |

或保留全收，依赖软件过滤（更简单，当前项目规模足够）。

### 2.2 新增 `services/can_protocol.h` & `can_protocol.c`

参照 MCLM_t2 的 `can_filter.c` 设计，新增软件层：

```c
// CAN 帧编码
void CAN_Encode_MotorCmd(uint8_t motor_id, int16_t speed, CAN_TxHeaderTypeDef *header, uint8_t *data);

// CAN 帧解码（状态反馈）
void CAN_Decode_StatusFrame(uint32_t std_id, const uint8_t *data, Motor_State_t *out_state);

// 全车命令
void CAN_Build_StopFrame(CAN_TxHeaderTypeDef *header, uint8_t *data);
void CAN_Build_TurnFrame(int16_t angle, CAN_TxHeaderTypeDef *header, uint8_t *data);
```

### 2.3 CAN TX 封装

基于 `UartToCan_Task` 已有能力，增加：
- 支持发送 MCLM_t2 协议的命令帧（正确填充 data[0] = 0x11 命令字节）
- 支持全车停止（CAN ID 0x101）
- 支持转向和动力命令（CAN ID 0x102/0x103）

### 涉及文件

| 文件 | 变更类型 |
|------|----------|
| `App/services/can_protocol.h` | **新建** |
| `App/services/can_protocol.c` | **新建** |
| `App/app_config.h` | 修改：补充 CAN 协议常量 |
| `App/app_task.c` | 修改：UartToCan 使用新协议编码 |

---

## Phase 3：IMU（MPU6050 + Mahony）集成

**目的：** 添加姿态感知能力，为控制闭环提供反馈。

### 3.1 从 `6_Mpu6050_t1/App/` 复用文件

直接复制以下文件到 ChassisController 的 `App/` 目录：

| 源文件 | 目标 | 说明 |
|--------|------|------|
| `App/Inc/mpu6050.h` | `App/imu/mpu6050.h` | I2C 驱动 |
| `App/Src/mpu6050.c` | `App/imu/mpu6050.c` | I2C 驱动 |
| `App/Inc/ak09911.h` | `App/imu/ak09911.h` | 磁力计驱动 |
| `App/Src/ak09911.c` | `App/imu/ak09911.c` | 磁力计驱动 |
| `App/Inc/imu_process.h` | `App/imu/imu_process.h` | Mahony 融合 |
| `App/Src/imu_process.c` | `App/imu/imu_process.c` | Mahony 融合 |

### 3.2 适配 IMU 代码

- 移除原有的 `main.c` 调用上下文，封装为纯驱动函数
- 将 `I2C_HandleTypeDef` 句柄改为 extern 引用

### 3.3 新增 `IMU_Task_Run()`（高优先级独立任务）

```c
void IMU_Task_Run(void *argument)
{
    IMU_Process_Init();   // 含 500 样本静态校准
    for(;;) {
        IMU_Process_Update();
        // 更新系统状态
        g_system_state.imu.roll  = imu_output.attitude[0];
        g_system_state.imu.pitch = imu_output.attitude[1];
        g_system_state.imu.yaw   = imu_output.attitude[2];
        g_system_state.imu.imu_timestamp = HAL_GetTick();
        osDelay(2);  // ~500Hz
    }
}
```

### 3.4 CubeMX 配置
- 使能 I2C1（PB6-SCL, PB7-SDA）
- 确认引脚不与其他外设冲突

### 涉及文件

| 文件 | 变更类型 |
|------|----------|
| `App/imu/mpu6050.c/h` | **新增**（从 6_Mpu6050 移植） |
| `App/imu/ak09911.c/h` | **新增**（从 6_Mpu6050 移植） |
| `App/imu/imu_process.c/h` | **新增**（从 6_Mpu6050 移植） |
| `App/app_task.c` | 修改：新增 IMU_Task_Run 实现 |
| `App/app_task.h` | 修改：新增声明 |
| `App/app_system_state.h` | 修改：IMU 状态已在 Phase1 定义 |
| `Core/Src/freertos.c` | 修改：新增 IMU_Ta 任务创建 |
| `Core/Src/main.c` | 修改：添加 MX_I2C1_Init() 调用 |
| `Core/Inc/main.h` | 修改：I2C 句柄声明 |
| `Core/Src/i2c.c` | **新增**（或从 CubeMX 生成） |
| `Core/Inc/i2c.h` | **新增** |
| `CMakeLists.txt` | 修改：添加新源文件和新目录 |

---

## Phase 4：控制任务

**目的：** 基于 SystemState 执行本地控制逻辑，实现闭环控制。

### 4.1 新增 `Control_Task_Run()`（高优先级，100Hz）

```
每个周期：
  1. 检查 estop → 若置位，发送 CAN 全车停止
  2. 遍历 motor[]：
     - 读取 target_speed（来自 UART 命令或 IMU 决策）
     - 计算 PID（可选）
     - 通过 CAN 发送控制命令到 MCLM_t2
  3. 可选：IMU 姿态辅助控制（如保持平衡）
```

### 4.2 保留 UART 调试透传

控制任务同时负责：
- 定期（如 100ms）打印系统状态到 UART（调试用）
- 保留 UART→CAN 转发能力

### 涉及文件

| 文件 | 变更类型 |
|------|----------|
| `App/app_task.c` | 修改：新增 Control_Task_Run |
| `App/app_task.h` | 修改：新增声明 |
| `Core/Src/freertos.c` | 修改：新增 Control_Ta 任务 |
| `App/modules/pid.c/h` | **可选新增**（参考 MCLM_t2 的 pid.c） |

---

## Phase 5：调试与诊断

**目的：** 分离调试输出与主数据路径。

### 5.1 新增 `Debug_Task_Run()`（低优先级，10Hz）

```
每个周期：
  1. 格式化 SystemState 摘要
  2. 通过 UART1 发送（复用 uart1_send）
```

### 5.2 看门狗（IWDG）

- 使能独立看门狗，超时约 4 秒
- Heartbeat_Task 同步喂狗

### 涉及文件

| 文件 | 变更类型 |
|------|----------|
| `App/app_task.c` | 修改：新增 Debug_Task_Run |
| `Core/Src/main.c` | 修改：MX_IWDG_Init 配置 |

---

## 最终任务拓扑

| 任务 | 优先级 | 频率 | 职责 |
|------|--------|------|------|
| ProtocolParser_Ta | HIGH | 事件驱动 | UART 协议解析 → CommandQueue |
| CommandProcess_Ta | HIGH | 事件驱动 | 命令语义解析，状态更新，决策 |
| IMU_Ta | HIGH | ~500Hz | MPU6050 读取 + Mahony 融合 |
| Control_Ta | HIGH | 100Hz | 控制输出到 CAN |
| CanRxProcess_Ta | NORMAL | 事件驱动 | CAN 状态帧 → SystemState |
| Debug_Ta | LOW | 10Hz | 系统状态 UART 输出 |
| Heartbeat_Ta | LOW | 3Hz | LED 闪烁 + IWDG 喂狗 |

**数据流：**
```
UART → ProtocolParser → CommandQueue → CommandProcess_Task
                                            ├── UART 命令 → 本地状态更新
                                            ├── CAN 命令 → UartToCan_Task → CAN 总线
                                            └── 本地控制 → Control_Task → CAN 总线
CAN → CanRxProcess_Task → SystemState (motor[], flags)
IMU → IMU_Task → SystemState (imu)
Debug_Task → SystemState → UART 输出
```

---

## 实现顺序建议

| 优级 | Phase | 工作量估计 | 风险 | 价值 |
|------|-------|-----------|------|------|
| P0 | Phase 1: SystemState + 任务重构 | 中 (~2天) | 中（影响现有功能） | 基础架构，后续所有依赖 |
| P0 | Phase 3: IMU 集成 | 中 (~2天) | 低（独立模块） | 姿态感知核心能力 |
| P1 | Phase 2: CAN 协议集成 | 小 (~1天) | 低（封装已有协议） | 与 MCLM 双向对齐 |
| P2 | Phase 4: 控制任务 | 中 (~2天) | 中（控制逻辑调优） | 闭环控制核心 |
| P3 | Phase 5: 调试诊断 | 小 (~1天) | 低 | 可观测性提升 |

**建议从 Phase 1 开始**（基础设施），与 Phase 3（IMU）并行开发——两者独立，IMU 可先在原 6_Mpu6050 项目中验证新架构适配。

---

## 验证方案

### Phase 1 验证
1. 编译通过，烧录后心跳 LED 正常闪烁
2. UART 发送 `AA 01 01 01 00 00 02 11 64` → CAN 总线正确发出 0x123 data=[0x11,0x64]
3. MCLM_t2 的 0x323/0x324 状态帧 → CanRxProcess 正确更新 `g_system_state.motor[]`

### Phase 2 验证
4. `CMD_ESTOP`（0x04）→ 总线出现 CAN ID 0x101 全车停止帧
5. 状态查询命令 → UART 输出当前电机状态

### Phase 3 验证
6. `IMU_Task` 运行后，UART 可打印 `roll/pitch/yaw`
7. 静置时角度稳定不漂移

### Phase 4 验证
8. UART 发速度命令 → CAN 发 0x123 速度帧 → MCLM 电机响应
9. Control_Task 100Hz 稳定运行，不丢帧

### 端到端验证
10. PC → UART（速度命令）→ ChassisController（解析+状态更新）→ CAN → MCLM_t2（电机控制）→ CAN（状态反馈）→ ChassisController（SystemState 更新）→ UART（调试输出）完整链路确认
