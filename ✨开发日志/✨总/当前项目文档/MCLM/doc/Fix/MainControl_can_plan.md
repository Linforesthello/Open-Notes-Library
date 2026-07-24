# MainControl CAN 增强计划

> 目标：让末端节点（电机控制器）主动向主控上报必要信息，满足移动机器人底盘需求

---

## 变更清单

### 1. Motor_t 结构体 — [`App/config/app_globals.h`](../App/config/app_globals.h)

- 增加 `uint8_t flags` 字段，包含位定义：
  - `MOTOR_FLAG_STALL` (bit0)：堵转标志
  - `MOTOR_FLAG_SATURATED` (bit1)：PID 饱和标志
- 增加 `uint8_t stall_counter` 字段：连续堵转计数

### 2. 堵转/饱和检测 — [`App/tasks/tb6612_DC_task.c`](../App/tasks/tb6612_DC_task.c)

在 PID 计算循环中追加检测逻辑：

- **堵转检测**：`setpoint != 0` 且 `current_logic_speed ≈ 0` 连续超过 5 个周期（>50ms）→ 置 `MOTOR_FLAG_STALL`
- **饱和检测**：`PWM >= (PWM_MAX - 10)` 且 `|current - setpoint| > 5` → 置 `MOTOR_FLAG_SATURATED`
- 正常运行时清除对应标志

### 3. CAN 状态帧格式变更 — [`App/tasks/command_task.c`](../App/tasks/command_task.c)

| byte | 旧格式 | 新格式 |
|------|--------|--------|
| [0-1] | `target_logic_speed` (int16) | `current_logic_speed` (int16) ← **实际速度放首位** |
| [2-3] | `current_logic_speed` (int16) | `accumulated_ticks` (uint16) ← **里程计低16位** |
| [4-5] | `pwm_output` (int16) | `pwm_output` (int16) |
| [6] | reserved (0x00) | `target_logic_speed` (int8) ← **-100~100 够用** |
| [7] | reserved (0x00) | `flags` (uint8) ← **堵转/饱和/故障** |

### 4. 主动上报（心跳替代） — [`App/tasks/command_task.c`](../App/tasks/command_task.c)

- `osMessageQueueGet` 从 `osWaitForever` 改为 `50ms` 超时
- **超时路径**：主动发送 motor0 + motor1 两帧状态（~20Hz 心跳）
- **命令路径**：保持原有处理逻辑，CMD_QUERY_STATUS 也使用新格式响应
- 主控端：如果超过 100ms 未收到状态帧，可判定节点离线

---

## 改动文件一览

| 文件 | 变更类型 |
|---|---|
| `App/config/app_globals.h` | 修改结构体 + 宏定义 |
| `App/tasks/tb6612_DC_task.c` | 增加检测逻辑 |
| `App/tasks/command_task.c` | 增加主动上报 + 状态帧格式变更 |
| `doc/deepseek_can.md` | 更新 TX 帧格式文档 |
| `doc/all_motor.md` | 更新 Motor_t 结构体文档 |

---

## 向后兼容

- RX 命令协议 **不变**（白名单、命令字节格式不改）
- TX 状态帧格式变更，主控侧需同步更新解析逻辑
- 主控若仍按旧格式解析，会导致 `current` / `target` 读反、`accumulated_ticks` 被当作速度
