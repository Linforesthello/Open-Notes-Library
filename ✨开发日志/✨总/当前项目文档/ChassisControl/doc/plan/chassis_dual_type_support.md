# 底盘构型支持实现计划

> 本文档规划 ChassisController 如何从硬编码的 2 电机模型，演进为支持舵轮底盘和四全向轮底盘的数据处理中心。

---

## Context

ChassisController 当前硬编码假设**只有 2 个电机**（转向 Motor0=0x123，动力 Motor1=0x124），无法支持两种底盘构型：

- **构型 A（舵轮底盘）**：2~4 个动力单元 × 每单元 2 电机（驱动+转向）= **4~8 个电机**
- **构型 B（四全向轮底盘）**：4 个电机，轴向外射，延长线交于车体中心 = **4 个电机**

### 现有问题

1. CAN ID 映射在 `app_task.c` 中**重复两次**且硬编码
   - `can_id_to_motor_idx()` 只认 0x323/0x324
   - `CMD_SET_SPEED` handler 中又有另一套 if/else-if
2. 无运动学模块（正解/逆解）
3. 无底盘级状态上报
4. `App/` 目录扁平，未遵循工作区规范

### 设计原则

| 原则 | 含义 |
|------|------|
| **上层不感知构型** | 上层只发 vx/vy/omega，收 vx/vy/omega，不关心下面有几个电机 |
| **编译时选型** | 底盘构型是硬件属性，用宏选择，零运行时开销 |
| **表驱动映射** | CAN ID 映射改为查表，不再硬编码 if/else |
| **模块化** | 运动学作为独立 module，两种构型编译时切换 |
| **向后兼容** | 每一步保持现有功能不变 |

---

## 实现阶段

### Phase A：基础设施（只加不删，无功能变化）

**目标**：创建新文件，建立架构骨架。此时所有代码都不被现有逻辑引用，系统行为零变化。

#### A1. 底盘选型配置

**文件**：`App/config/app_chassis_config.h`（新建）

```c
#define CHASSIS_TYPE_STEERING_WHEEL  1
#define CHASSIS_TYPE_OMNI            2

#ifndef CHASSIS_TYPE
#define CHASSIS_TYPE  CHASSIS_TYPE_STEERING_WHEEL   // 默认舵轮，向后兼容
#endif

#if CHASSIS_TYPE == CHASSIS_TYPE_STEERING_WHEEL
    #ifndef STEERING_UNIT_COUNT
    #define STEERING_UNIT_COUNT  2                    // 默认 2 个动力单元
    #endif
    #define CHASSIS_MOTOR_COUNT  (STEERING_UNIT_COUNT * 2)  // 每单元 2 电机
#elif CHASSIS_TYPE == CHASSIS_TYPE_OMNI
    #define CHASSIS_MOTOR_COUNT  4
#else
    #error "CHASSIS_TYPE 必须为 1（舵轮）或 2（全向轮）"
#endif

#if CHASSIS_MOTOR_COUNT > MOTOR_MAX_COUNT
    #error "CHASSIS_MOTOR_COUNT 超过 MOTOR_MAX_COUNT (8)"
#endif
```

**核心决策**：
- `STEERING_UNIT_COUNT` 是动力单元数量，每个单元 = 2 个电机（转向 + 驱动）= 1 块 MCLM_t2 板
- 2 单元舵轮 = 4 电机 = 2 块 MCLM_t2 板
- 4 单元舵轮 = 8 电机 = 4 块 MCLM_t2 板（填满 MOTOR_MAX_COUNT 上限）

---

#### A2. 通用化 CAN ID 映射表

**目的**：替代硬编码的 `CAN_MOTOR_TURN_CMD_STDID` / `CAN_MOTOR_POWER_CMD_STDID` 等宏。

**文件**：`App/config/app_can_map.h`（新建）

```c
/* 每个电机的 CAN ID 三元组 */
typedef struct {
    uint16_t cmd_id;         /* 发送速度指令的 CAN ID */
    uint16_t cmd_status_id;  /* 状态查询的 CAN ID  */
    uint16_t status_id;      /* 自动状态帧的 CAN ID（MCLM_t2 每 50ms 上报） */
} CAN_Motor_Map_t;

extern const CAN_Motor_Map_t g_can_motor_map[];  // 按 motor_idx 索引
extern const uint8_t         g_can_motor_count;   // = CHASSIS_MOTOR_COUNT

/* CAN 状态 ID → motor_idx 查找，未找到返回 0xFF */
uint8_t CAN_Map_StatusIdToMotorIdx(uint32_t status_id);
```

**文件**：`App/config/app_can_map.c`（新建）

CAN ID 编码规则（每块 MCLM_t2 板控制 2 个电机）：

```
Board B, Motor 0 → base = 0x123 + B*2
Board B, Motor 1 → base = 0x124 + B*2

各功能 ID = base + 偏移：
  CMD        = base + 0x000
  CMD_STATUS = base + 0x100
  STATUS     = base + 0x200

所以 Board 0（当前 CAN_ID_GROUP=2）：
  Motor 0: cmd=0x123, status=0x323
  Motor 1: cmd=0x124, status=0x324

Board 1（CAN_ID_GROUP=1）：
  Motor 2: cmd=0x125, status=0x325
  Motor 3: cmd=0x126, status=0x326
```

**舵轮底盘的映射**：

```
motor[0] = Unit0 转向电机   (Board 0, Motor 0)
motor[1] = Unit0 驱动电机   (Board 0, Motor 1)
motor[2] = Unit1 转向电机   (Board 1, Motor 0)
motor[3] = Unit1 驱动电机   (Board 1, Motor 1)
...（Unit2、Unit3 类推）
```

**全向轮底盘的映射**（无"转向"概念，全部是驱动电机）：

```
motor[0] = 左前轮 FL  (Board 0, Motor 0)
motor[1] = 右前轮 FR  (Board 0, Motor 1)
motor[2] = 左后轮 RL  (Board 1, Motor 0)
motor[3] = 右后轮 RR  (Board 1, Motor 1)
```

---

#### A3. 运动学模块

**目的**：将各电机速度 ↔ 车体速度 vx/vy/omega 的换算封装为独立模块。

**文件**：`App/modules/kinematics.h`（新建）

```c
void Kinematics_Init(float wheelbase_mm, float track_mm, float wheel_radius_mm);

/* 逆解：车体速度 vx/vy/omega → 各电机目标速度 */
void Kinematics_Inverse(float vx_mms, float vy_mms, float omega_rads,
                        int16_t motor_speeds[]);

/* 正解：各电机当前速度 → 车体速度估计 */
void Kinematics_Forward(const int16_t motor_speeds[],
                        float *vx_mms, float *vy_mms, float *omega_rads);
```

**文件**：`App/modules/kinematics.c`（新建，`#if CHASSIS_TYPE` 内联两种实现）

**舵轮底盘（构型 A）逆解**：

```
对所有动力单元 u：
  转向电机 speed[u*2+0] = clamp(omega * K_steer, -100, 100)
  驱动电机 speed[u*2+1] = clamp(vx * K_drive, -100, 100)
```

**四全向轮（构型 B）逆解**：

```
ω₁ =  vx - vy - omega·(L+W)/2    // FL
ω₂ =  vx + vy + omega·(L+W)/2    // FR
ω₃ =  vx + vy - omega·(L+W)/2    // RL
ω₄ =  vx - vy + omega·(L+W)/2    // RR

归一化到 [-100, 100] 逻辑速度
```

**四全向轮（构型 B）正解**（逆矩阵）：

```
vx    = (ω₁ + ω₂ + ω₃ + ω₄) / 4
vy    = (-ω₁ + ω₂ + ω₃ - ω₄) / 4
omega = (-ω₁ + ω₂ - ω₃ + ω₄) / [4·(L+W)/2]
```

---

#### A4. 构建系统更新

**修改 `CMakeLists.txt`**：
- 添加 `App/config/app_can_map.c` 和 `App/modules/kinematics.c` 到 `target_sources()`
- `target_include_directories()` 添加 `App/config` 和 `App/modules`

**修改 `app_includes.h`**：
- include `app_chassis_config.h`
- include `app_can_map.h`
- include `kinematics.h`

---

### Phase B：重构现有任务用查表（行为不变）

**目标**：用新 CAN ID 映射表替换现有硬编码逻辑。**行为不变。**

#### B1. 替换 `can_id_to_motor_idx()`

```c
// 旧（app_task.c:88-93）
static uint8_t can_id_to_motor_idx(uint32_t stdId)
{
    if (stdId == CAN_MOTOR_TURN_STATUS_STDID)   return 0;
    if (stdId == CAN_MOTOR_POWER_STATUS_STDID)  return 1;
    return 0xFF;
}

// 新
// 删除上述函数，改为调用：
uint8_t midx = CAN_Map_StatusIdToMotorIdx(rx_can_msg.id);
```

#### B2. 替换 CMD_SET_SPEED 中的 ID 匹配

```c
// 旧：四行 if/else-if 硬编码 0x123/0x124/0x102/0x103
if (uart_msg.id == CAN_MOTOR_TURN_CMD_STDID)       midx = 0;
else if (uart_msg.id == CAN_MOTOR_POWER_CMD_STDID)  midx = 1;
else if (uart_msg.id == CAN_CMD_TURN_STDID)         midx = 0;
else if (uart_msg.id == CAN_CMD_POWER_STDID)        midx = 1;

// 新：查表匹配
uint8_t midx = 0xFF;
for (uint8_t i = 0; i < g_can_motor_count; i++) {
    if (g_can_motor_map[i].cmd_id == (uint16_t)uart_msg.id) {
        midx = i; break;
    }
}
```

#### B3. 替换 CMD_ESTOP 的固定三帧

```c
// 旧：只发 0x101 + 0x123 + 0x124 三帧
// 新：for 循环遍历所有电机 + 广播 0x101
for (uint8_t i = 0; i < g_can_motor_count; i++) {
    can.id = g_can_motor_map[i].cmd_id;
    osMessageQueuePut(canTxQueueHandle, &can, 0, 0);
}
// + 广播 0x101
can.id = CAN_CMD_STOP_STDID;
```

---

### Phase C：添加底盘级命令和状态

#### C1. 新命令枚举

**修改 `app_command.h`**，新增：

```c
CMD_CHASSIS_SPEED = 0x08,   // 车体速度指令：发 vx/vy/omega
CMD_REPORT_STATE  = 0x09,   // 请求底盘状态报告
```

#### C2. SystemState 新增字段

**修改 `app_system_state.h`**，新增：

```c
/* 上层下发的车体速度指令 */
typedef struct {
    float vx_cmd;            // 目标前进速度 (mm/s)
    float vy_cmd;            // 目标侧向速度 (mm/s)
    float omega_cmd;         // 目标旋转角速度 (rad/s)
    uint32_t last_cmd_tick;  // 最后收到命令的时间戳
} Chassis_Command_t;

/* 网关推算的车体速度估计 */
typedef struct {
    float vx_est;            // 估计前进速度 (mm/s)
    float vy_est;            // 估计侧向速度 (mm/s)
    float omega_est;         // 估计旋转角速度 (rad/s)
    uint32_t last_update_tick;
} Chassis_State_Estimate_t;

/* 加入 System_State_t */
typedef struct {
    IMU_State_t               imu;
    Motor_State_t             motor[MOTOR_MAX_COUNT];
    System_Flag_t             flag;
    Chassis_Command_t         chassis_cmd;        // ★ 新增
    Chassis_State_Estimate_t  chassis_state;      // ★ 新增
} System_State_t;
```

**RAM 影响**：约 48 字节（10 个 float + 2 个 uint32），相对于 20KB 可忽略。

#### C3. CMD_CHASSIS_SPEED 命令处理

**修改 `app_task.c` `CommandProcess_Task_Run()`**：

```c
case CMD_CHASSIS_SPEED:
{
    // 帧格式: AA 08 [CAN_ID] 06 vx_L vx_H vy_L vy_H om_L om_H
    // CAN_ID 可设为 0x000（未使用），len=6
    int16_t vx_raw = uart_msg.data[0] | (uart_msg.data[1] << 8);
    int16_t vy_raw = uart_msg.data[2] | (uart_msg.data[3] << 8);
    int16_t om_raw = uart_msg.data[4] | (uart_msg.data[5] << 8);

    g_system_state.chassis_cmd.vx_cmd    = (float)vx_raw;
    g_system_state.chassis_cmd.vy_cmd    = (float)vy_raw;
    g_system_state.chassis_cmd.omega_cmd = (float)om_raw / 1000.0f;
    g_system_state.chassis_cmd.last_cmd_tick = HAL_GetTick();

    // 逆解：车体速度 → 各电机目标
    int16_t motor_targets[CHASSIS_MOTOR_COUNT];
    Kinematics_Inverse(vx_raw, vy_raw, om_raw / 1000.0f, motor_targets);

    // 逐电机构建 CAN 帧 → canTxQueue
    for (uint8_t i = 0; i < g_can_motor_count; i++) {
        g_system_state.motor[i].target_speed = motor_targets[i];
        can.id = g_can_motor_map[i].cmd_id;
        can.len = 2;
        can.data[0] = CAN_CMD_SET_SPEED_T2;
        can.data[1] = (uint8_t)motor_targets[i];
        osMessageQueuePut(canTxQueueHandle, &can, 0, 0);
    }

    // ACK 回复
    sprintf(dbg_buffer, "CHASSIS_CMD_ACK | vx=%d vy=%d omega=%d\r\n",
            vx_raw, vy_raw, om_raw);
    uart1_send(dbg_buffer, offset);
    break;
}
```

#### C4. CanRxProcess_Task 正解

**修改 `app_task.c` `CanRxProcess_Task_Run()`**：

每次解码完一个电机的状态帧后，**对所有电机做一次正解** → 更新 chassis_state：

```c
// 在 decode_motor_status() 之后：
int16_t speeds[CHASSIS_MOTOR_COUNT];
for (uint8_t i = 0; i < CHASSIS_MOTOR_COUNT; i++) {
    speeds[i] = g_system_state.motor[i].current_speed;
}
Kinematics_Forward(speeds,
                   &g_system_state.chassis_state.vx_est,
                   &g_system_state.chassis_state.vy_est,
                   &g_system_state.chassis_state.omega_est);
g_system_state.chassis_state.last_update_tick = HAL_GetTick();
```

#### C5. 主动上报 CHASSIS_STATE（周期 5Hz）

**在 Heartbeat_Task 中增加**（简单有效，不需要新增任务）：

```c
static uint32_t last_report = 0;
uint32_t now = HAL_GetTick();
if (now - last_report >= 200) {  // 5Hz，不会淹没 UART
    last_report = now;
    char buf[80];
    int n = sprintf(buf,
        "CHASSIS_STATE | vx=%.1f vy=%.1f omega=%.2f estop=%d\r\n",
        g_system_state.chassis_state.vx_est,
        g_system_state.chassis_state.vy_est,
        g_system_state.chassis_state.omega_est,
        g_system_state.flag.estop);
    uart1_send(buf, n);
}
```

#### C6. CMD_REPORT_STATE 命令处理

```c
case CMD_REPORT_STATE:
{
    sprintf(dbg_buffer,
        "CHASSIS_STATE | vx=%.1f vy=%.1f omega=%.2f estop=%d uptime=%lu\r\n",
        g_system_state.chassis_state.vx_est,
        g_system_state.chassis_state.vy_est,
        g_system_state.chassis_state.omega_est,
        g_system_state.flag.estop,
        g_system_state.flag.uptime_ms);
    uart1_send(dbg_buffer, offset);
    break;
}
```

---

### Phase D：切换构型

**方法一：直接改宏**

```c
// app_chassis_config.h
#define CHASSIS_TYPE  CHASSIS_TYPE_OMNI   // ← 改为全向轮
```

重新编译即可。CAN ID 表和运动学算法自动切换。

**方法二：CMake 编译定义（推荐）**

```cmake
# CMakeLists.txt 或 CMakePresets.json
target_compile_definitions(... PRIVATE CHASSIS_TYPE=2)
```

只需改一个数字，重新 cmake + ninja，就得到全向轮固件。

---

## 文件变更清单

### 新建文件

| 文件 | 位置 |
|------|------|
| `app_chassis_config.h` | `App/config/` |
| `app_can_map.h` | `App/config/` |
| `app_can_map.c` | `App/config/` |
| `kinematics.h` | `App/modules/` |
| `kinematics.c` | `App/modules/` |

### 修改文件

| 文件 | 变更 |
|------|------|
| `app_config.h` | 移除 `CAN_MOTOR_TURN_*` / `CAN_MOTOR_POWER_*` 宏（或标记 deprecated），保留命令字节宏 |
| `app_system_state.h` | 新增 `Chassis_Command_t`、`Chassis_State_Estimate_t` |
| `app_command.h` | 新增 `CMD_CHASSIS_SPEED (0x08)`、`CMD_REPORT_STATE (0x09)` |
| `app_includes.h` | include 三个新头文件 |
| `app_task.c` | Phase B 替换映射逻辑，Phase C 加新命令处理、正解调用、周期上报 |
| `CMakeLists.txt` | 加新源文件，加 include 路径 |

---

## 内存影响预估

| 项目 | Flash | RAM |
|------|-------|-----|
| CAN 映射表（4 电机） | ~32 bytes (rodata) | 0 |
| 运动学代码（两种构型） | ~400 bytes (text) | 0 |
| 新 SystemState 字段 | 0 | ~48 bytes |
| **合计** | **~500 bytes / 64KB (<1%)** | **~48 bytes / 20KB (<1%)** |

---

## 验证方案

| # | 验证内容 | 方法 |
|---|---------|------|
| 1 | Phase B 后编译通过 | `cmake --build .` |
| 2 | 舵轮构型下 SET_SPEED 正常工作 | UART 发 `AA 01 01 01 00 00 02 11 32` → CAN 总线出现 `0x123 data=[0x11,0x32]` |
| 3 | 舵轮构型下 ESTOP 遍历所有电机 | ESTOP 后 CAN 总线上出现所有电机的停止帧（不再只有 3 帧） |
| 4 | CMD_CHASSIS_SPEED 发送 vx/vy/omega | UART 发新命令 → CAN 总线出现各电机对应的速度帧 |
| 5 | CHASSIS_STATE 主动上报 | UART 周期性收到 `CHASSIS_STATE \| vx=...`（5Hz） |
| 6 | 切换 OMNI 后重建 | 改 `CHASSIS_TYPE=2` → 重新 cmake → CAN ID 表自动变 4 电机 → 运动学变全向轮公式 |
| 7 | 全向轮正解精度 | 手动构造各电机速度 → 检查 `chassis_state.vx/vy/omega` 是否符合公式预期 |

---

## 附录：关键决策记录

| 决策 | 选项 | 选择理由 |
|------|------|---------|
| 构型选型时机 | 编译时 / 运行时 | 编译时。底盘构型是硬件属性，不会在运行中改变。零开销。 |
| CAN ID 组扩展 | 表驱动 / 宏展开 | 表驱动。避免宏爆炸，支持任意数量电机。查表 loop 在几十个电机内性能可忽略。 |
| 运动学实现 | `#if` 编译选择 / 函数指针运行时选择 | `#if` 编译选择。节省 Flash，简化代码。函数指针在 Cortex-M3 上有间接调用开销。 |
| CHASSIS_STATE 上报 | Heartbeat_Task 内 / 独立 Report_Task | 先用 Heartbeat_Task（减少任务切换），若后来 UART 竞争严重再考虑独立任务。 |
