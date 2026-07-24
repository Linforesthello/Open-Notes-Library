# CAN 数据流文档

## 架构说明

**现状：** 软件过滤从 `can.c` 回调中抽取为独立模块，职责分离通过文件目录体现：

| 层 | 文件 | 职责 |
|---|---|---|
| HAL 层 | `Core/Src/can.c` | 收帧、调过滤模块、推队列 |
| 服务层 | `App/services/can_filter.h/.c` | 表格驱动 ID 白名单 + 命令字节校验 + 映射 |
| 服务层 | `App/services/command.h` | 定义 `CommandMsg_t`/`AckMsg_t` 结构体 |
| 任务层 | `App/tasks/command_task.c` | 命令路由、CAN TX 响应 |

---

## CAN ID 定义

定义于 `App/config/app_config.h`（当前 `CAN_ID_GROUP=1`）：

| 宏定义 | ID (Group 1) | ID (Group 2) | 方向 | 用途 |
|---|---|---|---|---|
| `CAN_MOTOR_TURN_CMD_STDID` | **`0x125`** | `0x123` | RX | **转向**电机控制指令 |
| `CAN_MOTOR_POWER_CMD_STDID` | **`0x126`** | `0x124` | RX | **动力**电机控制指令 |
| `CAN_MOTOR_TURN_CMD_STATUS_STDID` | **`0x225`** | `0x223` | RX | **转向**电机状态查询 / 日志控制 |
| `CAN_MOTOR_POWER_CMD_STATUS_STDID` | **`0x226`** | `0x224` | RX | **动力**电机状态查询 / 日志控制 |
| `CAN_MOTOR_TURN_STATUS_STDID` | **`0x325`** | `0x323` | TX | **转向**电机状态反馈 |
| `CAN_MOTOR_POWER_STATUS_STDID` | **`0x326`** | `0x324` | TX | **动力**电机状态反馈 |
| `CAN_CMD_STOP_STDID` | `0x101` | `0x101` | RX | 全车停止 |
| `CAN_CMD_TURN_STDID` | `0x102` | `0x102` | RX | 全车转向命令 |
| `CAN_CMD_POWER_STDID` | `0x103` | `0x103` | RX | 全车动力命令 |

> 切换 Group：修改 `app_config.h:52` 的 `CAN_ID_GROUP` 值。Group 1（0x125/0x126 系列）为当前默认，Group 2（0x123/0x124 系列）为备选。

---

## CAN 总线硬件配置

定义于 `App/config/app_config.h`，初始化于 `Core/Src/can.c:MX_CAN_Init()`：

- 实例：`CAN1`，引脚 PA11 (RX) / PA12 (TX)
- 波特率：500 kbps（Prescaler=4, BS1=13TQ, BS2=4TQ）
- 过滤器：Bank 0，掩码全 0（接收所有 ID），FIFO0
- 中断：`USB_LP_CAN1_RX0_IRQn`，优先级 5
- 自动重传：ENABLE（硬件重传直到收到 ACK）

---

## RX 数据流（接收路径）

```
CAN 总线
    │  硬件帧（StdId + DLC + Data[8]）
    ▼
[Core/Src/can.c]
HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
    │  调用 HAL_CAN_GetRxMessage() → rxHeader, rxData[8]
    │  CAN_Filter_Accept(id, rxData[0]) 查白名单表 ← can_filter.c
    │     └─ REJECT → return（丢弃）
    │  CAN_Filter_GetMotorId(id)        查表 → motor_id
    │  CAN_Filter_CmdByteToType(id, rxData[0]) → CommandType_t
    │  CAN_Filter_GetValue(id, rxData[0], rxData) → 速度值
    │  若 cmdMsg.type != CMD_NONE → osMessageQueuePut(CommandQueueHandle, &cmd, 0, 0)
    ▼
[FreeRTOS Queue]
CommandQueueHandle  (CommandMsg_t)
    ▼
[App/tasks/command_task.c]
Command_Task(void *argument)
    │  osMessageQueueGet(CommandQueueHandle, &cmd, NULL, 50)  // 50ms 超时实现主动上报
    │
    ├─ cmd.type == CMD_LOG_START/STOP
    │       → 设置 g_logger_enabled = 1/0
    │       → 发送 CAN 回传帧（见 LOG 命令 CAN 回传）
    │       → osMessageQueuePut(AckQueueHandle, &ack, ...)
    │
    ├─ cmd.type == CMD_LIST_STATUS / CMD_QUERY_STATUS
    │       → 读 g_motors[mid]（mutex 保护）
    │       → CMD_QUERY_STATUS: 按 motor_id 选 CAN ID 发送 TX 帧
    │       → osMessageQueuePut(AckQueueHandle, &ack, ...)
    │
    └─ is_motor_cmd(cmd.type) == true  (控制命令)
            → osMessageQueuePut(AckQueueHandle, &ack, ...)
            → 按 motor_id 路由：
                motor_id=0   → MotorQueueHandle
                motor_id=1   → MotorQueue1Handle
                motor_id=0xFF → 同时投递两个队列（广播）
```

---

## 协议解析：`can_filter.c` 表格驱动

文件：`App/services/can_filter.c`

输入：
- `stdId`：CAN 帧 ID
- `cmdByte`：命令字节（`rxData[0]`）
- `rxData`：完整数据帧（提取速度值时用到）

### 白名单表

以表格形式（而非 if-else）定义 7 个 ID 的合法命令字节组合：

| StdId | motor_id | 允许的命令字节 |
|---|---|---|
| `CAN_MOTOR_TURN_CMD_STDID` (0x125) | 0 | `0x11` 调速, `0x07` 调速, `0x08` 停止, `0x02` 倒转 |
| `CAN_MOTOR_POWER_CMD_STDID` (0x126) | 1 | `0x11` 调速, `0x07` 调速, `0x08` 停止, `0x02` 倒转 |
| `CAN_MOTOR_TURN_CMD_STATUS_STDID` (0x225) | 0 | `0x01` 查询, `0x04` 日志开始, `0x05` 日志停止 |
| `CAN_MOTOR_POWER_CMD_STATUS_STDID` (0x226) | 1 | `0x01` 查询, `0x04` 日志开始, `0x05` 日志停止 |
| `CAN_CMD_STOP_STDID` (`0x101`) | 广播 | `0x08` 停止, `0x11` 调速 |
| `CAN_CMD_TURN_STDID` (`0x102`) | 0 | `0x07` 调速, `0x08` 停止, `0x02` 倒转, `0x11` 调速 |
| `CAN_CMD_POWER_STDID` (`0x103`) | 1 | `0x07` 调速, `0x08` 停止, `0x02` 倒转, `0x11` 调速 |

### 命令字节 → CommandType_t 映射

| rxData[0] | 输出 type | 输出 value | 约束 |
|---|---|---|---|
| `0x11` | `CAN_CMD_SET_SPEED` | `(int8_t)rxData[1]` | — |
| `0x07` | `CAN_CMD_SET_SPEED` | `(int8_t)rxData[1]` | — |
| `0x08` | `CAN_CMD_STOP` | 0 | — |
| `0x02` | `CMD_REVERSE` | 0（任务侧用 `-MOTOR_CMD_DEFAULT_SPEED`） | — |
| `0x01` | `CMD_QUERY_STATUS` | 0 | 仅当 StdId == STATUS ID |
| `0x04` | `CMD_LOG_START` | 0 | 仅当 StdId == STATUS ID |
| `0x05` | `CMD_LOG_STOP` | 0 | 仅当 StdId == STATUS ID |

> 注意：相比原内联代码，新过滤表对 ID 与命令字节的合法组合做了明确约束。原代码中 `0x11`/`0x07`/`0x08`/`0x02` 在 switch 中不检查 ID，任意白名单 ID 上发送这些字节都会被接受。新过滤表按 ID 限制了允许的命令字节（例如 STATUS ID 不再接受调速命令）。

### 公共 API

函数定义于 `App/services/can_filter.h`：

```c
CAN_FilterResult_t CAN_Filter_Accept(uint32_t stdId, uint8_t cmdByte);
uint8_t           CAN_Filter_GetMotorId(uint32_t stdId);
CommandType_t     CAN_Filter_CmdByteToType(uint32_t stdId, uint8_t cmdByte);
int16_t           CAN_Filter_GetValue(uint32_t stdId, uint8_t cmdByte, const uint8_t rxData[8]);
```

---

## LOG 命令 CAN 回传

当 `command_task.c` 处理 `CMD_LOG_START` 或 `CMD_LOG_STOP` 时，除了设置 `g_logger_enabled`，还会发送一帧 CAN 消息作为确认：

```
txHeader.StdId = CAN_MOTOR_TURN_CMD_STATUS_STDID (0x225)
txData[0] = 0xCF           // 标识魔术字
txData[1] = cmd.type       // 4=LOG_START, 5=LOG_STOP
txData[2] = g_logger_enabled  // 1=开启, 0=关闭
txData[3..7] = 0x00        // 保留
```

---

## TX 数据流（发送路径）

触发条件：每 50ms 主动上报，或 `command_task.c` 收到 `CMD_QUERY_STATUS`

`send_motor_status()` 函数定义于 `App/tasks/command_task.c`，发送新格式状态帧：

```
[App/tasks/command_task.c]
Command_Task
    │  定时触发: last_status_tick 每 50ms 到期
    │  或命令触发: 收到 CMD_QUERY_STATUS
    │
    │  调用 send_motor_status(mid)
    │  读 g_motors[mid]（mutex 保护）
    │  构造 CAN_TxHeaderTypeDef txHeader:
    │      .StdId = (mid == 0) ? CAN_MOTOR_TURN_STATUS_STDID (0x325)
    │                           : CAN_MOTOR_POWER_STATUS_STDID (0x326)
    │      .DLC   = 8
    │      .IDE   = CAN_ID_STD
    │      .RTR   = CAN_RTR_DATA
    │  构造 txData[8]:
    │      [0..1] = current_logic_speed    (int16_t, little-endian) ← 实际速度
    │      [2..3] = accumulated_ticks      (uint16_t, little-endian) ← 里程计低16位
    │      [4..5] = pwm_output             (int16_t, little-endian)
    │      [6]    = target_logic_speed     (int8_t,  -100..100)
    │      [7]    = flags                  (uint8_t) → MOTOR_FLAG_*
    │  HAL_CAN_AddTxMessage(&hcan, &txHeader, txData, &txMailbox)
    ▼
CAN 总线  →  主控

注：主控若超过 100ms 未收到任何状态帧，可判定节点离线。
```

### 状态帧格式验证

经 `doc/Can_MainControl_t1.csv`（23974 帧总线录制）验证确认：

| 验证项 | 结果 | 说明 |
|--------|------|------|
| 上报周期 | ✅ 50ms±2ms | 20Hz 稳定，连续 5 分钟无丢帧 |
| 字节序 | ✅ Little-Endian | `(D2<<8)\|D1` = current, `(D4<<8)\|D3` = ticks |
| `accumulated_ticks` 方向 | ✅ 正转递增，反转递减 | 与编码器实际运动一致 |
| `flags` 堵转检测 | ✅ 真实堵转上报 `0x03` | STALL\|SATURATED，正常运行时 `0x00` |
| `target` (int8) 范围 | ✅ -50~80 | int8 (-128~127) 完全够用 |

详见 [`ai_session/can_data_analyze.md`](ai_session/can_data_analyze.md)。

### 状态帧 flags 定义

定义于 `App/config/app_globals.h`：

| bit | 宏 | 含义 |
|---|---|---|
| 0 | `MOTOR_FLAG_STALL` | 堵转：有目标速度但电机不转 |
| 1 | `MOTOR_FLAG_SATURATED` | PWM 饱和：已满功率输出但仍未达到目标 |

---

## ACK 旁路流

所有命令（CAN + UART）处理后均生成 ACK，通过 `Logger_Print` 输出到 UART 调试口。

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

支持的命令类型（即 `ack.type` 的 switch-case）：
`CMD_SET_SPEED`, `CMD_STOP`, `CMD_FORWARD`, `CMD_REVERSE`, `CMD_LIST_STATUS`,
`CMD_LOG_START`, `CMD_LOG_STOP`, `CAN_CMD_SET_SPEED`, `CAN_CMD_STOP`

---

## `is_motor_cmd()` 路由函数

`command_task.c` 中的静态内联函数，决定命令是否投递到电机控制队列：

```c
static inline int is_motor_cmd(CommandType_t type)
{
    return type == CMD_FORWARD    || type == CMD_REVERSE  ||
           type == CMD_STOP       || type == CMD_SET_SPEED ||
           type == CAN_CMD_SET_SPEED || type == CAN_CMD_STOP;
}
```

- 返回 `true`：控制命令 → 投递到 `MotorQueueHandle`/`MotorQueue1Handle`
- 返回 `false`：查询/日志命令 → 已在前面分支处理，不会再走到路由

---

## 关键数据结构

定义于 `App/services/command.h`：

```c
typedef enum {
    CMD_NONE = 0,
    CMD_FORWARD = 1,  CMD_REVERSE = 2,  CMD_STOP = 3,
    CMD_SET_SPEED = 4,  CMD_LIST_STATUS = 5,  CMD_QUERY_STATUS = 6,
    CAN_CMD_SET_SPEED = 7,  CAN_CMD_STOP = 8,
    CMD_LOG_START = 9,  CMD_LOG_STOP = 10,
} CommandType_t;

typedef struct {
    CommandType_t type;
    int16_t value;      // 速度值（控制命令时有效）
    uint8_t motor_id;   // 目标电机：0=转向, 1=动力, 0xFF=广播
} CommandMsg_t;

typedef struct {
    CommandType_t type;
    int16_t value;
    uint8_t ok;         // 1=成功, 0=失败
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
| `MotorQueueHandle` | `CommandMsg_t` | `command_task.c` | 转向电机控制任务（电机 0） |
| `MotorQueue1Handle` | `CommandMsg_t` | `command_task.c` | 动力电机控制任务（电机 1） |
| `AckQueueHandle` | `AckMsg_t` | `command_task.c` | `Ack_task.c` |
| `LogQueueHandle` | `LogMotorData_t` | logger 模块 | UART 发送任务 |