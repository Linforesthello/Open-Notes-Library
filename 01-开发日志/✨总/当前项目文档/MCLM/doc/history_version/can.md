# CAN 数据流文档

## 架构改动说明

**改动前：** `can.c` 的中断回调直接内嵌协议解析逻辑（60+ 行 switch），业务代码混入 HAL 层。

**改动后：** 协议解析逻辑被直接内联在 `HAL_CAN_RxFifo0MsgPendingCallback` 中，但职责分离的思想仍然存在：

| 层 | 文件 | 职责 |
|---|---|---|
| HAL 层 | `Core/Src/can.c` | 收帧、**内联解析**、推队列 |
| 服务层 | `App/services/command.h` | 定义 `CommandMsg_t` 结构体 |
| 任务层 | `App/tasks/command_task.c` | 命令路由、CAN TX 响应 |

---

## CAN ID 定义

定义于 `App/config/app_config.h`：

| 宏定义 | ID | 方向 | 用途 |
|---|---|---|---|
| `CAN_MOTOR_TURN_CMD_STDID` | `0x125` | RX | **转向**电机控制指令 |
| `CAN_MOTOR_POWER_CMD_STDID` | `0x126` | RX | **动力**电机控制指令 |
| `CAN_MOTOR_TURN_CMD_STATUS_STDID` | `0x225` | RX | **转向**电机状态查询 / 日志控制 |
| `CAN_MOTOR_POWER_CMD_STATUS_STDID`| `0x226` | RX | **动力**电机状态查询 / 日志控制 |
| `CAN_MOTOR_TURN_STATUS_STDID` | `0x325` | TX | **转向**电机状态反馈 |
| `CAN_MOTOR_POWER_STATUS_STDID` | `0x326` | TX | **动力**电机状态反馈 |
| `CAN_CMD_STOP_STDID` | `0x101` | RX | 全车停止 |
| `CAN_CMD_TURN_STDID` | `0x102` | RX | 全车转向命令 |
| `CAN_CMD_POWER_STDID` | `0x103` | RX | 全车动力命令 |

---

## CAN 总线硬件配置

定义于 `App/config/app_config.h`，初始化于 `Core/Src/can.c:MX_CAN_Init()`：

- 实例：`CAN1`，引脚 PA11 (RX) / PA12 (TX)
- 波特率：500 kbps（Prescaler=4, BS1=13TQ, BS2=4TQ）
- 过滤器：Bank 0，掩码全 0（接收所有 ID），FIFO0
- 中断：`USB_LP_CAN1_RX0_IRQn`，优先级 5

---

## RX 数据流（接收路径）

```
CAN 总线
    │  硬件帧（StdId + DLC + Data[8]）
    ▼
[Core/Src/can.c]
HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
    │  调用 HAL_CAN_GetRxMessage() → rxHeader, rxData[8]
    │  **内联解析 (switch-case)** → CommandMsg_t cmd
    │  若 cmd.type == CMD_NONE → 丢弃返回
    │  否则 osMessageQueuePut(CommandQueueHandle, &cmd, 0, 0)
    ▼
[FreeRTOS Queue]
CommandQueueHandle  (CommandMsg_t)
    ▼
[App/tasks/command_task.c]
Command_Task(void *argument)
    │  osMessageQueueGet(CommandQueueHandle, &cmd, ...)
    │
    ├─ cmd.type == CMD_LOG_START/STOP
    │       → 设置 g_logger_enabled = 1/0
    │
    ├─ cmd.type == CMD_QUERY_STATUS
    │       → 读 g_motor_status（加 motor0_mutexHandle 锁）
    │       → HAL_CAN_AddTxMessage(&hcan, txHeader, txData, &txMailbox)
    │         （见 TX 数据流）
    │       → osMessageQueuePut(AckQueueHandle, &ack, ...)
    │
    └─ is_motor_cmd(cmd.type) == true
            → osMessageQueuePut(AckQueueHandle, &ack, ...)
            → osMessageQueuePut(MotorQueueHandle, &cmd, ...)
```

---

## 协议解析：内联于 `can.c`

文件：`Core/Src/can.c`（中断回调函数 `HAL_CAN_RxFifo0MsgPendingCallback`）

**输入：**
- `rxHeader->StdId`：CAN 帧 ID
- `rxData[0]`：命令字节（CMD byte）
- `rxData[1]`：参数字节（速度值等）

**ID 过滤（白名单）：**

| StdId | 允许的命令字节 |
|---|---|
| `0x125` / `0x126` | `CAN_CMD_SET_SPEED_T2`, `CAN_CMD_SET_SPEED`, `CAN_CMD_STOP`, **`CAN_CMD_REVERSE_BYTE`** |
| `0x225` / `0x226` | `CAN_CMD_QUERY_STATUS`, `CAN_CMD_LOG_START`, `CAN_CMD_LOG_STOP` |
| `0x101` | `CAN_CMD_STOP` |
| `0x102` | `CAN_CMD_SET_SPEED` |
| `0x103` | `CAN_CMD_SET_SPEED` |

**命令字节映射：**

| rxData[0] | 条件 | 输出 CommandMsg_t.type | 输出 .value |
|---|---|---|---|
| `CAN_CMD_SET_SPEED_T2` (`0x11`) | 任意 ID | `CAN_CMD_SET_SPEED` | ~~`(int16_t)rxData[1]`~~ → **`(int8_t)rxData[1]`**（Bug fix） |
| `CAN_CMD_SET_SPEED` (`0x07`) | 任意 ID | `CAN_CMD_SET_SPEED` | `(int8_t)rxData[CAN_DATA_INDEX_SPEED]` |
| `CAN_CMD_STOP` (`0x08`) | 任意 ID | `CAN_CMD_STOP` | 0 |
| **`CAN_CMD_REVERSE_BYTE`** (`0x02`) | `0x125`/`0x126` | **`CMD_REVERSE`** | 0（任务侧用 `-MOTOR_CMD_DEFAULT_SPEED`） |
| `CAN_CMD_QUERY_STATUS` | StdId == `0x225` 或 `0x226` | `CMD_QUERY_STATUS` | 0 |
| `CAN_CMD_LOG_START` | StdId == `0x225` 或 `0x226` | `CMD_LOG_START` | 0 |
| `CAN_CMD_LOG_STOP` | StdId == `0x225` 或 `0x226` | `CMD_LOG_STOP` | 0 |
| 其他 | — | `CMD_NONE`（丢弃） | — |

---

## TX 数据流（发送路径）

触发条件：`command_task.c` 收到 `CMD_QUERY_STATUS`

```
[App/tasks/command_task.c]
Command_Task
    │  读 g_motors[mid]（mutex 保护）
    │  构造 CAN_TxHeaderTypeDef txHeader:
    │      .StdId = (mid == 0) ? CAN_MOTOR_TURN_STATUS_STDID : CAN_MOTOR_POWER_STATUS_STDID
    │      .DLC   = 8
    │      .IDE   = CAN_ID_STD
    │      .RTR   = CAN_RTR_DATA
    │  构造 txData[8]:
    │      [0..1] = target_logic_speed  (int16_t, little-endian)
    │      [2..3] = current_logic_speed (int16_t, little-endian)
    │      [4..5] = pwm_output          (int16_t, little-endian)
    │      [6..7] = 0x0000 (reserved)
    │  HAL_CAN_AddTxMessage(&hcan, &txHeader, txData, &txMailbox)
    ▼
CAN 总线  →  上位机 / 主控
```

---

## ACK 旁路流

每条命令（含 CAN 命令）在 `command_task.c` 处理后都会生成 ACK。
此外，`CMD_LOG_START` 和 `CMD_LOG_STOP` 还会触发 CAN 消息发送。

```
Command_Task
    │  构造 AckMsg_t ack { .type, .value, .ok, .current_logic_speed, .pwm_output }
    │  osMessageQueuePut(AckQueueHandle, &ack, ...)
    ▼
[App/tasks/Ack_task.c]
Ack_Task
    │  osMessageQueueGet(AckQueueHandle, &ack, ...)
    │  snprintf(buf, ACK_MSG_BUF_SIZE, "ACK: ...")
    │  Logger_Print(buf)
    ▼
UART 输出（调试用）
```

---

## 关键数据结构

定义于 `App/services/command.h`：

```c
typedef enum {
    CMD_NONE = 0,
    CMD_FORWARD, CMD_REVERSE, CMD_STOP, CMD_SET_SPEED,
    CMD_LIST_STATUS, CMD_QUERY_STATUS,
    CAN_CMD_SET_SPEED, CAN_CMD_STOP,
    CMD_LOG_START, CMD_LOG_STOP,
} CommandType_t;

typedef struct {
    CommandType_t type;
    int16_t value;      // 速度值（CAN_CMD_SET_SPEED 时有效）
    uint8_t motor_id;   // 目标电机：0=转向, 1=动力, 0xFF=广播
} CommandMsg_t;

typedef struct {
    CommandType_t type;
    int16_t value;
    uint8_t ok;
    int16_t current_logic_speed;
    int16_t pwm_output;
} AckMsg_t;
```

---

## 全局队列

定义于 `freertos.c`（CMSIS-OS 句柄）：

| 队列 | 类型 | 生产者 | 消费者 |
|---|---|---|---|
| `CommandQueueHandle` | `CommandMsg_t` | `can.c` 中断回调 / UART 命令解析 | `command_task.c` |
| `MotorQueueHandle` | `CommandMsg_t` | `command_task.c` | 转向电机控制任务 |
| `MotorQueue1Handle` | `CommandMsg_t` | `command_task.c` | 动力电机控制任务 |
| `AckQueueHandle` | `AckMsg_t` | `command_task.c` | `Ack_task.c` |