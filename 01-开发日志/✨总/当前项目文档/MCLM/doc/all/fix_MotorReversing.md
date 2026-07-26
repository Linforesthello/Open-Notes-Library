# Fix：CAN 倒车控制

**日期：** 2026-04-24
**状态：** ✅ 已完成

---

## 问题描述

通过 CAN 总线只能控制电机正转、设置速度和停车，无法实现倒转。
底层 TB6612 驱动已实现硬件倒转逻辑（负 PWM → IN1=LOW, IN2=HIGH），
但上层协议解析存在 Bug，且任务层缺少对倒转命令的处理分支。

---

## 根因分析

### Bug 1（主因）— `can.c` 符号位丢失

```c
// ❌ 原代码 — uint8_t 强转 int16_t：零扩展，0xCE → 206，永远为正数
case CAN_CMD_SET_SPEED_T2:          // rxData[0] == 0x11
    cmdMsg.value = (int16_t)rxData[1];

// ✅ 修复 — 先转 int8_t 做符号扩展，0xCE → -50
    cmdMsg.value = (int8_t)rxData[1];
```

上位机发送负速度（如 `0xCE` = -50）时，被零扩展为 +206，电机永远正转。

### Bug 2 — `tb6612_DC_task.c` 未处理 `CMD_REVERSE`

`command.h` 中 `CMD_REVERSE = 2` 枚举早已存在，
但任务的 if-else 链只处理 `CMD_SET_SPEED / CAN_CMD_SET_SPEED` 和 `CMD_STOP / CAN_CMD_STOP`，
`CMD_REVERSE` 和 `CMD_FORWARD` 到达后静默跳过，电机不动作。

### 缺失 — `can.c` 无独立倒转命令 case

`app_config.h` 已定义 `CAN_CMD_REVERSE_BYTE 0x02`，
但 `can.c` 的 switch-case 中没有该分支，
上位机无法用单字节命令触发倒转。

---

## 改动文件

### 1. `Core/Src/can.c`

**改动 A — 修复符号位（`CAN_CMD_SET_SPEED_T2` case）**

```c
// Before
cmdMsg.value = (int16_t)rxData[1];

// After
cmdMsg.value = (int8_t)rxData[1];   // 先做符号扩展（-128~+127），负值即倒转
```

**改动 B — 新增独立倒转 case**

```c
case CAN_CMD_REVERSE_BYTE:   // 0x02
    // 独立倒转命令：速度由任务侧 MOTOR_CMD_DEFAULT_SPEED 决定
    cmdMsg.type  = CMD_REVERSE;
    cmdMsg.value = 0;
    break;
```

---

### 2. `App/tasks/tb6612_DC_task.c`

在消息处理的 if-else 链中新增两个分支（插在 `CMD_STOP` 之前）：

```c
else if (cmdMsg.type == CMD_FORWARD)
{
    /* 正转默认速度：切换方向时清积分，防止积分残留导致超调 */
    if (motor->pid.setpoint < 0.0f)
        PID_Reset(&(motor->pid));
    motor->pid.setpoint = MOTOR_CMD_DEFAULT_SPEED;   // +50.0f
}
else if (cmdMsg.type == CMD_REVERSE)
{
    /* 倒转默认速度：切换方向时清积分 */
    if (motor->pid.setpoint > 0.0f)
        PID_Reset(&(motor->pid));
    motor->pid.setpoint = -MOTOR_CMD_DEFAULT_SPEED;  // -50.0f
}
```

---

### 3. `doc/can.md`

- 协议白名单表：各 CAN ID 行新增 `CAN_CMD_REVERSE_BYTE`
- 命令字节映射表：新增 `0x02` 行，修正 `CAN_CMD_SET_SPEED_T2` 的 value 说明
- 新增"倒转方式说明"注释块

---

## 未改动文件（原因）

| 文件 | 原因 |
|---|---|
| `App/config/app_config.h` | `CAN_CMD_REVERSE_BYTE 0x02` 和 `MOTOR_CMD_DEFAULT_SPEED 50.0f` 均已存在 |
| `App/services/command.h` | `CMD_REVERSE = 2` 枚举已存在 |
| `App/tasks/command_task.c` | `is_motor_cmd()` 已含 `CMD_REVERSE`，路由逻辑无需改动 |
| TB6612 驱动 / 编码器任务 | 负 PWM 倒转硬件逻辑已实现 |

---

## 修复后数据流

```
上位机 CAN 帧
    │
    ├─ [StdId=0x126, Data=[0x02]]        独立倒转命令
    │       ↓ can.c: case CAN_CMD_REVERSE_BYTE
    │       cmdMsg = { CMD_REVERSE, value=0, motor_id=1 }
    │
    └─ [StdId=0x126, Data=[0x11, 0xCE]]  带速度倒转（0xCE → int8 = -50）
            ↓ can.c: case CAN_CMD_SET_SPEED_T2
            cmdMsg = { CAN_CMD_SET_SPEED, value=-50, motor_id=1 }
    │
    ▼ CommandQueueHandle
    │
    ▼ command_task.c: is_motor_cmd() == true → MotorQueue1Handle
    │
    ▼ tb6612_DC_task.c
    │   CMD_REVERSE      → setpoint = -50.0f
    │   CAN_CMD_SET_SPEED → setpoint = -50.0f
    │
    ▼ PID_Compute() → output < 0
    │
    ▼ TB6612_Motor_SetSpeed(speed < 0) → IN1=LOW, IN2=HIGH → 电机倒转 ✅
```

---

## 测试验证

| 场景 | CAN 帧 | 预期现象 |
|---|---|---|
| 独立倒转（动力电机） | `StdId=0x126, DLC=1, Data=[0x02]` | 电机以 50% 额定速度倒转 |
| 独立倒转（转向电机） | `StdId=0x125, DLC=1, Data=[0x02]` | 电机以 50% 额定速度倒转 |
| 带速度倒转 | `StdId=0x126, DLC=2, Data=[0x11, 0xCE]` | 0xCE→-50，电机以 -50 逻辑速度倒转 |
| 正转仍正常 | `StdId=0x126, DLC=2, Data=[0x11, 0x32]` | 0x32→+50，电机正转，行为不变 |
| 正转→倒转切换 | 先发 `[0x11,0x32]`，再发 `[0x02]` | PID 积分清零，平滑切换，无超调 |
| 停车 | `StdId=0x126, DLC=1, Data=[0x08]` | 电机停止，行为不变 |

---

## 注意事项

- `CAN_CMD_REVERSE_BYTE = 0x02` 与枚举 `CMD_REVERSE = 2` 数值相同，
  但前者是宏、后者是枚举，语义不同，switch 中必须使用宏版本，避免混淆。
- 方向切换时 PID 积分清零（`PID_Reset`）已加入，可防止反向超调。
- 默认倒转速度 `MOTOR_CMD_DEFAULT_SPEED = 50.0f` 集中在 `app_config.h` 中定义，易于调整。
