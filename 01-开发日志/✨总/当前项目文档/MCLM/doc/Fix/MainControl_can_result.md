# MainControl CAN 增强 — 会话总结

> 项目：3_MCLM_t2（电机控制器末端节点）
> 日期：2026-05-18
> 分支：fix_base

---

## 1. 会话背景与问题

### 上下文

开发者有两份文档：

- [all_motor.md](all_motor.md) — 电机参数清单，定义 `Motor_t` 结构体、PID 参数、CAN ID 等
- [deepseek_can.md](deepseek_can.md) — CAN 数据流文档，描述 ID 定义、RX/TX 协议、过滤模块

项目是 STM32F103C8T6 上的电机控制器，作为**末端节点**通过 CAN 总线与**下层主控**对接，控制两路直流电机（转向 + 动力），构成移动机器人底盘的执行层。

### 提出的问题

> "作为末端节点与下层主控对接的，主控需要什么信息？作为移动机器人底盘"

即：从主控的角度看，这个末端节点应该**主动提供**哪些信息，才能满足移动机器人底盘的控制需求？

### 现状分析

通过阅读约 15 个源文件，梳理出当前主控能获取的信息：

| 方向 | 当前能力 | 方式 |
|---|---|---|
| 主控 → 节点 | 调速、停止、状态查询、全局命令 | CAN RX：0x123/0x124/0x101 等 |
| 节点 → 主控 | target, current, pwm（6 字节，2 字节保留） | CAN TX：0x323/0x324，收到查询才回复 |

### 发现的核心缺口

| 缺失信息 | 严重性 | 说明 |
|---|---|---|
| **里程计累计值** | 🔴 高 | 编码器已有 `accumulated_ticks`，UART 日志也有输出，但 CAN 状态帧中 bytes[6-7] 是保留 0x00，没有利用 |
| **主动上报** | 🔴 高 | 节点仅在收到查询命令时才回复，主控必须不断轮询，且无法判断节点是否存活 |
| **堵转/饱和检测** | 🟡 中 | 无软件故障检测，主控不知道电机是否卡住或过载 |
| **电源电压** | 🟢 低 | 需额外 ADC 硬件，暂不纳入本次范围 |

---

## 2. 思考过程与方案设计

### 2.1 状态帧格式设计

原有 8 字节 TX 帧布局：

```
旧格式:
  [0-1] target_logic_speed    (int16)
  [2-3] current_logic_speed   (int16)
  [4-5] pwm_output            (int16)
  [6-7] 0x0000 (reserved)     ← 2字节浪费
```

需要塞入 `accumulated_ticks` + `flags` + 保留已有字段。

**关键考量：**

- `target_logic_speed` 范围 `-100..100`（LOGIC_SPEED_MAX=100）→ **int8_t 完全够用**，降宽度腾空间
- `current_logic_speed` 需要小数精度，保留 int16
- `accumulated_ticks` 是 int32，CAN 帧只有 8 字节 → 发低 16 位，主控端跟踪翻转
  - 翻转周期：满速 6600 ticks/s，16 位 = 65536 ticks，约 **10 秒翻转**
  - 主控 50ms 一次接收，最多收 330 个 delta ticks，远低于 16 位范围 → **可可靠跟踪**

**最终格式：**

```
新格式:
  [0-1] current_logic_speed    (int16)    ← 实际速度放首位，最有价值
  [2-3] accumulated_ticks      (uint16)   ← 里程计低16位
  [4-5] pwm_output             (int16)    ← 电机出力
  [6]   target_logic_speed     (int8)     ← -100..100，int8够用
  [7]   flags                  (uint8)    ← 故障标志位
```

### 2.2 主动上报策略

原 `Command_Task` 阻塞模式：

```c
osMessageQueueGet(..., osWaitForever)  // 阻塞等待，无命令就挂起
```

改后：

```c
osMessageQueueGet(..., 50)             // 50ms 超时
                                       // 超时 → 发两电机状态帧
```

- 收到命令：正常处理 + 路由
- 超时（空闲）：主动发两电机状态帧（~20Hz）
- 主控端：若 100ms 无帧到达，判定节点离线

### 2.3 堵转/饱和检测

在 `TB6612_DC_Task` 的 10ms PID 循环中嵌入：

| 检测项 | 条件 | 置位时机 |
|---|---|---|
| 堵转 | setpoint != 0 && speed < 1.0 | 连续 > 50ms（5 周期） |
| 饱和 | pwm >= PWM_MAX-10 && \|speed - setpoint\| > 10.0 | 任一周期满足 |
| 清除 | 停止/恢复正常 | 立即清零 |

---

## 3. 改动前后对比

### 3.1 `App/config/app_globals.h`

```diff
+#define MOTOR_FLAG_STALL      0x01U
+#define MOTOR_FLAG_SATURATED  0x02U

 typedef struct {
     ...
     int16_t  pwm_output;
+    uint8_t  flags;            // 新增：状态标志
+    uint8_t  stall_counter;    // 新增：堵转周期计数
 } Motor_t;
```

### 3.2 `App/tasks/tb6612_DC_task.c`

```diff
  float current_speed = motor->current_logic_speed;

+ /* Stall Detection */
+ if (fabsf(current_speed) < 1.0f) {
+     if (motor->stall_counter < 255) motor->stall_counter++;
+     if (motor->stall_counter > 5) motor->flags |= MOTOR_FLAG_STALL;
+ } else {
+     motor->stall_counter = 0;
+     motor->flags &= ~MOTOR_FLAG_STALL;
+ }
+
  float output = PID_Compute(...);
  TB6612_Motor_SetSpeed(...);
  motor->pwm_output = motor->hardware.pwm_output;

+ /* Saturation Detection */
+ if (motor->pwm_output >= (PWM_MAX - 10) &&
+     fabsf(current_speed - motor->pid.setpoint) > 10.0f)
+     motor->flags |= MOTOR_FLAG_SATURATED;
+ else
+     motor->flags &= ~MOTOR_FLAG_SATURATED;
```

停止分支也增强了：

```diff
  } else {
      TB6612_Motor_Stop(&(motor->hardware));
      motor->pwm_output = 0;
+     motor->stall_counter = 0;    // 停止时清零
+     motor->flags = 0;             // 停止时清零
  }
```

### 3.3 `App/tasks/command_task.c` — 核心重构

**新增函数：`send_motor_status(uint8_t mid)`**

封装了：取互斥锁 → 读 `g_motors[mid]` → 组装新格式帧 → `HAL_CAN_AddTxMessage`

```
static void send_motor_status(uint8_t mid)
{
    // 按 mid 选互斥锁和 CAN ID
    // osMutexAcquire → 读字段 → memcpy 组包 → HAL_CAN_AddTxMessage
}
```

**重构 `Command_Task` 主循环**

```diff
-    osMessageQueueGet(..., osWaitForever)  // 阻塞
+    osStatus_t q_status = osMessageQueueGet(..., 50);  // 50ms 超时

-    // 命令处理（全部在 for 循环体）
+    // 命令处理（仅当 q_status == osOK）
+    if (q_status == osOK && cmd.type != CMD_NONE) {
+        ...原有命令处理逻辑...
+    }

+    // 主动状态上报
+    uint32_t now = HAL_GetTick();
+    if (now - last_status_tick >= 50) {
+        send_motor_status(0);     // 转向电机
+        send_motor_status(1);     // 动力电机
+        last_status_tick = now;
+    }
```

**CAN 帧格式变化：**

| byte | 旧 | 新 |
|------|----|----|
| [0-1] | target_speed (int16) | **current_speed** (int16) |
| [2-3] | current_speed (int16) | **accumulated_ticks** (uint16) |
| [4-5] | pwm_output (int16) | pwm_output (int16) |
| [6-7] | reserved (0x0000) | **target_speed** (int8) + **flags** (uint8) |

**CMD_QUERY_STATUS 处理简化：**

```diff
-// 原来：内联组包，旧格式
-uint32_t replyId = ...;
-CAN_TxHeaderTypeDef txHeader = {...};
-uint8_t txData[8] = {0};
-int16_t target = ..., current = ..., pwm = ...;
-memcpy(&txData[0], &target, 2);
-memcpy(&txData[2], &current, 2);
-memcpy(&txData[4], &pwm, 2);
-HAL_CAN_AddTxMessage(...);

+// 现在：调用统一函数，新格式
+send_motor_status(mid);
```

### 3.4 文档更新

| 文件 | 变更 |
|---|---|
| `doc/all_motor.md` | Motor_t 新增 `accumulated_ticks`、`flags`、`stall_counter` 说明；flags 位定义表；行号更新 16→27 |
| `doc/deepseek_can.md` | TX 数据流改为新格式 + 主动上报说明；新增 flags 位定义表 |
| `doc/MainControl_can_plan.md` | **新增**：实施计划文档 |
| `doc/MainControl_can_result.md` | **新增**：本总结文档 |

---

## 4. 涉及文件清单

| # | 文件路径 | 操作 | 行数变化 |
|---|----------|------|----------|
| 1 | `App/config/app_globals.h` | 修改 | +8/-0 |
| 2 | `App/tasks/tb6612_DC_task.c` | 修改 | +29/-0 |
| 3 | `App/tasks/command_task.c` | 重构 | 大幅调整 |
| 4 | `doc/all_motor.md` | 修改 | +14/-2 |
| 5 | `doc/deepseek_can.md` | 修改 | +18/-4 |
| 6 | `doc/MainControl_can_plan.md` | 新增 | 全部 |
| 7 | `doc/MainControl_can_result.md` | 新增 | 全部（本文件） |

---

## 5. 主控侧注意事项

1. **CAN 状态帧解析需更新**，新格式不兼容旧格式
2. **不再需要轮询** — 节点每 50ms 主动上报，超过 100ms 无帧可判定离线
3. **里程计处理**：主控方需在接收端累加翻转计数，或对 `accumulated_ticks` 做差分得到当前 delta
4. **故障处理**：flags 的 bit0（堵转）/bit1（饱和）是非破坏性预警，不清零时会持续置位直到恢复正常

---

## 6. 待解决问题

- 此环境无 ARM 交叉编译器，未做编译验证。改动均复用现有 API，需在真正开发机上 `make` 确认
- AT8236 驱动场景（当前未启用）未同步添加堵转检测，后续如需切换驱动需补上
- `accumulated_ticks` 低 16 位翻转跟踪全部在主控侧完成，如果主控丢帧超过 10 秒会导致里程计漂移
