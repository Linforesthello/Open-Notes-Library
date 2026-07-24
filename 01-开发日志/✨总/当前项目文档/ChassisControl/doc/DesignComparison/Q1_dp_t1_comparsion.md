# CAN 数据流文档

## 架构说明

**现状：** `can.c` 的中断回调内联协议解析逻辑，职责分离通过文件目录体现：

| 层 | 文件 | 职责 |
|---|---|---|
| HAL 层 | `Core/Src/can.c` | 收帧、内联解析、推队列 |
| 服务层 | `App/services/command.h` | 定义 `CommandMsg_t`/`AckMsg_t` 结构体 |
| 任务层 | `App/tasks/command_task.c` | 命令路由、CAN TX 响应 |

---

## CAN ID 定义

定义于 `App/config/app_config.h`：

| 宏定义 | ID | 方向 | 用途 |
|---|---|---|---|
| `CAN_MOTOR_TURN_CMD_STDID` | **`0x123`** | RX | **转向**电机控制指令 |
| `CAN_MOTOR_POWER_CMD_STDID` | **`0x124`** | RX | **动力**电机控制指令 |
| `CAN_MOTOR_TURN_CMD_STATUS_STDID` | **`0x223`** | RX | **转向**电机状态查询 / 日志控制 |
| `CAN_MOTOR_POWER_CMD_STATUS_STDID` | **`0x224`** | RX | **动力**电机状态查询 / 日志控制 |
| `CAN_MOTOR_TURN_STATUS_STDID` | **`0x323`** | TX | **转向**电机状态反馈 |
| `CAN_MOTOR_POWER_STATUS_STDID` | **`0x324`** | TX | **动力**电机状态反馈 |
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
    │  ID 白名单过滤（7 个已知 ID，其余丢弃）
    │  switch(rxData[0]) 协议解析 → CommandMsg_t cmd
    │  若 cmd.type == CMD_NONE → 丢弃返回
    │  否则 osMessageQueuePut(CommandQueueHandle, &cmd, 0, 0)
    ▼
[FreeRTOS Queue]
CommandQueueHandle  (CommandMsg_t)
    ▼
[App/tasks/command_task.c]
Command_Task(void *argument)
    │  osMessageQueueGet(CommandQueueHandle, &cmd, NULL, osWaitForever)
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

## 协议解析：内联于 `can.c`

文件：`Core/Src/can.c`（中断回调函数 `HAL_CAN_RxFifo0MsgPendingCallback`）

**输入：**
- `rxHeader->StdId`：CAN 帧 ID
- `rxData[0]`：命令字节（CMD byte）
- `rxData[1]`：参数字节（速度值等）

**ID 白名单（代码中最外层 if 过滤）：**

| StdId | 用途 |
|---|---|
| `0x123` / `0x124` | 电机控制 |
| `0x223` / `0x224` | 状态查询 / 日志控制 |
| `0x101` | 全车停止 |
| `0x102` | 全车转向 |
| `0x103` | 全车动力 |

通过白名单后，按 ID 决定 `motor_id`：
- `0x123` / `0x223` / `0x102` → `motor_id = 0`（转向）
- `0x124` / `0x224` / `0x103` → `motor_id = 1`（动力）
- `0x101` → `motor_id = 0xFF`（广播）

**命令字节映射：**

| rxData[0] | 输出 type | 输出 value |
|---|---|---|
| `CAN_CMD_SET_SPEED_T2` (`0x11`) | `CAN_CMD_SET_SPEED` | **`(int8_t)rxData[1]`**（先转 int8_t 保留符号，再隐式扩展为 int16_t） |
| `CAN_CMD_SET_SPEED` (`0x07`) | `CAN_CMD_SET_SPEED` | `(int8_t)rxData[CAN_DATA_INDEX_SPEED]` |
| `CAN_CMD_STOP` (`0x08`) | `CAN_CMD_STOP` | 0 |
| `CAN_CMD_REVERSE_BYTE` (`0x02`) | **`CMD_REVERSE`** | 0（任务侧用 `-MOTOR_CMD_DEFAULT_SPEED`） |
| `CAN_CMD_QUERY_STATUS` (`0x01`) | `CMD_QUERY_STATUS` | 0（仅当 StdId == `0x223` 或 `0x224`） |
| `CAN_CMD_LOG_START` (`0x04`) | `CMD_LOG_START` | 0（仅当 StdId == `0x223` 或 `0x224`） |
| `CAN_CMD_LOG_STOP` (`0x05`) | `CMD_LOG_STOP` | 0（仅当 StdId == `0x223` 或 `0x224`） |
| 其他 | `CMD_NONE`（丢弃） | — |

> 注意：`CAN_CMD_REVERSE_BYTE` 在 switch 中 **不检查 ID**，只要通过最外层白名单即生效（即 0x123/0x124/0x223/0x224/0x101/0x102/0x103 均可触发）。`CAN_CMD_SET_SPEED`/`CAN_CMD_STOP` 同理。
>
> `CAN_CMD_SET_SPEED_T2` (`0x11`) 是旧版上位机使用的命令字节，解析后映射为与 `0x07` 相同的 `CAN_CMD_SET_SPEED` 类型。

---

## LOG 命令 CAN 回传

当 `command_task.c` 处理 `CMD_LOG_START` 或 `CMD_LOG_STOP` 时，除了设置 `g_logger_enabled`，还会发送一帧 CAN 消息作为确认：

```
txHeader.StdId = CAN_MOTOR_TURN_CMD_STATUS_STDID (0x223)
txData[0] = 0xCF           // 标识魔术字
txData[1] = cmd.type       // 4=LOG_START, 5=LOG_STOP
txData[2] = g_logger_enabled  // 1=开启, 0=关闭
txData[3..7] = 0x00        // 保留
```

---

## TX 数据流（发送路径）

触发条件：`command_task.c` 收到 `CMD_QUERY_STATUS`

```
[App/tasks/command_task.c]
Command_Task
    │  读 g_motors[mid]（mutex 保护）
    │  构造 CAN_TxHeaderTypeDef txHeader:
    │      .StdId = (mid == 0) ? CAN_MOTOR_TURN_STATUS_STDID (0x323)
    │                           : CAN_MOTOR_POWER_STATUS_STDID (0x324)
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


can.c
"/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    can.c
  * @brief   This file provides code for the configuration
  *          of the CAN instances.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "can.h"

/* USER CODE BEGIN 0 */

// #include "app_includes.h"
#include "cmsis_os.h" // 使用 CMSIS-OS API
#include "stm32f1xx_hal_gpio.h"
#include "string.h"
#include "stdint.h"
#include "command.h"
#include "app_config.h"

// 使用在 freertos.c 中定义的 CMSIS 句柄
extern osMessageQueueId_t CommandQueueHandle; 

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
    CAN_RxHeaderTypeDef rxHeader;
    uint8_t rxData[8];
    if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rxHeader, rxData) == HAL_OK)
    {
        uint32_t id = rxHeader.StdId;

        // 只处理已知 ID，其余丢弃
        if (id != CAN_MOTOR_TURN_CMD_STDID  && id != CAN_MOTOR_TURN_CMD_STATUS_STDID  &&
            id != CAN_MOTOR_POWER_CMD_STDID && id != CAN_MOTOR_POWER_CMD_STATUS_STDID &&
            id != CAN_CMD_STOP_STDID && id != CAN_CMD_TURN_STDID && id != CAN_CMD_POWER_STDID)
        {
            return;
        }

        CommandMsg_t cmdMsg;
        cmdMsg.type     = CMD_NONE;
        cmdMsg.value    = 0;

        // 根据 CAN ID 决定目标电机
        if (id == CAN_MOTOR_TURN_CMD_STDID || id == CAN_MOTOR_TURN_CMD_STATUS_STDID || id == CAN_CMD_TURN_STDID)
        {
            cmdMsg.motor_id = 0;          // 转向电机（电机0）
        }
        else if (id == CAN_MOTOR_POWER_CMD_STDID || id == CAN_MOTOR_POWER_CMD_STATUS_STDID || id == CAN_CMD_POWER_STDID)
        {
            cmdMsg.motor_id = 1;          // 动力电机（电机1）
        }
        else  // CAN_CMD_STOP_STDID / CAN_CMD_TURN_STDID / CAN_CMD_POWER_STDID
        {
            cmdMsg.motor_id = 0xFF;       // 广播：两个电机都执行
        }

        // 协议解析
        switch (rxData[0])
        {
            case CAN_CMD_SET_SPEED_T2:
                cmdMsg.type  = CAN_CMD_SET_SPEED;
                cmdMsg.value = (int8_t)rxData[1];   /* Fix: 先转 int8_t 保留符号位，再隐式扩展为 int16_t */
                break;

            case CAN_CMD_SET_SPEED:
                cmdMsg.type  = CAN_CMD_SET_SPEED;
                cmdMsg.value = (int8_t)rxData[CAN_DATA_INDEX_SPEED];
                break;

            case CAN_CMD_STOP:
                cmdMsg.type = CAN_CMD_STOP;
                break;

            case CAN_CMD_QUERY_STATUS:
                if (id == CAN_MOTOR_TURN_CMD_STATUS_STDID ||
                    id == CAN_MOTOR_POWER_CMD_STATUS_STDID)
                    cmdMsg.type = CMD_QUERY_STATUS;
                break;

            case CAN_CMD_LOG_START:
                if (id == CAN_MOTOR_TURN_CMD_STATUS_STDID ||
                    id == CAN_MOTOR_POWER_CMD_STATUS_STDID)
                    cmdMsg.type = CMD_LOG_START;
                break;

            case CAN_CMD_LOG_STOP:
                if (id == CAN_MOTOR_TURN_CMD_STATUS_STDID ||
                    id == CAN_MOTOR_POWER_CMD_STATUS_STDID)
                    cmdMsg.type = CMD_LOG_STOP;
                break;

            case CAN_CMD_REVERSE_BYTE:
                /* 独立倒转命令：设 type=CMD_REVERSE，value=0（速度由任务侧决定） */
                cmdMsg.type  = CMD_REVERSE;
                cmdMsg.value = 0;
                break;

            default:
                return;
        }

        if (cmdMsg.type != CMD_NONE)
        {
            osMessageQueuePut(CommandQueueHandle, &cmdMsg, 0U, 0U);
        }
    }
}

/* USER CODE END 0 */

CAN_HandleTypeDef hcan;

/* CAN init function */
void MX_CAN_Init(void)
{

  /* USER CODE BEGIN CAN_Init 0 */
  CAN_FilterTypeDef sFilterConfig;

  /* USER CODE END CAN_Init 0 */

  /* USER CODE BEGIN CAN_Init 1 */

  /* USER CODE END CAN_Init 1 */
  hcan.Instance = CAN1;
  hcan.Init.Prescaler = 4;
  hcan.Init.Mode = CAN_MODE_NORMAL;
  hcan.Init.SyncJumpWidth = CAN_SJW_1TQ;
  hcan.Init.TimeSeg1 = CAN_BS1_13TQ;
  hcan.Init.TimeSeg2 = CAN_BS2_4TQ;
  hcan.Init.TimeTriggeredMode = DISABLE;
  hcan.Init.AutoBusOff = ENABLE;
  hcan.Init.AutoWakeUp = DISABLE;
  hcan.Init.AutoRetransmission = ENABLE;
  hcan.Init.ReceiveFifoLocked = DISABLE;
  hcan.Init.TransmitFifoPriority = ENABLE;
  if (HAL_CAN_Init(&hcan) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN CAN_Init 2 */
    // 配置CAN过滤器，放行所有消息，由软件中断回调根据 ID 列表进行过滤
    sFilterConfig.FilterBank = CAN_FILTER_BANK;
    sFilterConfig.FilterMode = CAN_FILTER_MODE;
    sFilterConfig.FilterScale = CAN_FILTER_SCALE;
    sFilterConfig.FilterIdHigh = 0x0000;
    sFilterConfig.FilterIdLow = 0x0000;
    sFilterConfig.FilterMaskIdHigh = 0x0000; // 掩码设为0，接收所有 StdID
    sFilterConfig.FilterMaskIdLow = 0x0000;
    sFilterConfig.FilterFIFOAssignment = CAN_FILTER_FIFO;
    sFilterConfig.FilterActivation = CAN_FILTER_ACTIVATION;
    sFilterConfig.SlaveStartFilterBank = CAN_SLAVE_START_FILTER_BANK;

    if (HAL_CAN_ConfigFilter(&hcan, &sFilterConfig) != HAL_OK)
    {
        Error_Handler();
    }

    // 启动CAN
    if (HAL_CAN_Start(&hcan) != HAL_OK)
    {
        Error_Handler();
    }

    // 使能接收中断
    if (HAL_CAN_ActivateNotification(&hcan, CAN_IT_RX_FIFO0_MSG_PENDING) != HAL_OK)
    {
        Error_Handler();
    }

  /* USER CODE END CAN_Init 2 */

}

void HAL_CAN_MspInit(CAN_HandleTypeDef* canHandle)
{

  GPIO_InitTypeDef GPIO_InitStruct = {0};
  if(canHandle->Instance==CAN1)
  {
  /* USER CODE BEGIN CAN1_MspInit 0 */

  /* USER CODE END CAN1_MspInit 0 */
    /* CAN1 clock enable */
    __HAL_RCC_CAN1_CLK_ENABLE();

    __HAL_RCC_GPIOA_CLK_ENABLE();
    /**CAN GPIO Configuration
    PA11     ------> CAN_RX
    PA12     ------> CAN_TX
    */
    GPIO_InitStruct.Pin = GPIO_PIN_11;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_12;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    /* CAN1 interrupt Init */
    HAL_NVIC_SetPriority(USB_LP_CAN1_RX0_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(USB_LP_CAN1_RX0_IRQn);
  /* USER CODE BEGIN CAN1_MspInit 1 */

  /* USER CODE END CAN1_MspInit 1 */
  }
}

void HAL_CAN_MspDeInit(CAN_HandleTypeDef* canHandle)
{

  if(canHandle->Instance==CAN1)
  {
  /* USER CODE BEGIN CAN1_MspDeInit 0 */

  /* USER CODE END CAN1_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_CAN1_CLK_DISABLE();

    /**CAN GPIO Configuration
    PA11     ------> CAN_RX
    PA12     ------> CAN_TX
    */
    HAL_GPIO_DeInit(GPIOA, GPIO_PIN_11|GPIO_PIN_12);

    /* CAN1 interrupt Deinit */
    HAL_NVIC_DisableIRQ(USB_LP_CAN1_RX0_IRQn);
  /* USER CODE BEGIN CAN1_MspDeInit 1 */

  /* USER CODE END CAN1_MspDeInit 1 */
  }
}

/* USER CODE BEGIN 1 */

/* USER CODE END 1 */

"

command_task.c
"#include "app_includes.h"

extern CAN_HandleTypeDef hcan;

/* 判断是否为电机控制命令（需要投递到MotorQueue） */
static inline int is_motor_cmd(CommandType_t type)
{
    return type == CMD_FORWARD    || type == CMD_REVERSE  ||
           type == CMD_STOP       || type == CMD_SET_SPEED ||
           type == CAN_CMD_SET_SPEED || type == CAN_CMD_STOP;
}

void Command_Task(void *argument)
{
    CommandMsg_t cmd;

    for (;;)
    {
        if (osMessageQueueGet(CommandQueueHandle, &cmd, NULL, osWaitForever) != osOK)
            continue;

        // 过滤无效命令
        if (cmd.type == CMD_NONE)
            continue;

        // 读取目标电机状态
        uint8_t mid = (cmd.motor_id < MOTOR_COUNT) ? cmd.motor_id : 0;
        osMutexId_t myMutex = (mid == 0) ? motor0_mutexHandle : motor1_mutexHandle;

        Motor_t status = {0};
        if (osMutexAcquire(myMutex, osWaitForever) == osOK)
        {
            status = g_motors[mid];
            osMutexRelease(myMutex);
        }

        /* ===== 数据流控制命令 ===== */
        if (cmd.type == CMD_LOG_START || cmd.type == CMD_LOG_STOP)
        {
            g_logger_enabled = (cmd.type == CMD_LOG_START);

            CAN_TxHeaderTypeDef txHeader = {
                .StdId = CAN_MOTOR_TURN_CMD_STATUS_STDID,
                .DLC   = 8,
                .IDE   = CAN_ID_STD,
                .RTR   = CAN_RTR_DATA,
            };
            uint8_t txData[8] = {0};
            txData[0] = 0xCF;
            txData[1] = (uint8_t)cmd.type;
            txData[2] = (uint8_t)g_logger_enabled;

            uint32_t txMailbox;
            HAL_CAN_AddTxMessage(&hcan, &txHeader, txData, &txMailbox);

            AckMsg_t ack = {
                .type  = cmd.type,
                .value = g_logger_enabled,
                .ok    = 1,
                .current_logic_speed = (int16_t)status.current_logic_speed,
                .pwm_output          = (int16_t)status.pwm_output,
            };
            osMessageQueuePut(AckQueueHandle, &ack, 0, 0);
            continue;
        }

        /* ===== 查询命令 ===== */
        if (cmd.type == CMD_LIST_STATUS || cmd.type == CMD_QUERY_STATUS)
        {
            if (cmd.type == CMD_QUERY_STATUS)
            {
                // 按 motor_id 选回复 CAN ID
                uint32_t replyId = (mid == 0) ? CAN_MOTOR_TURN_STATUS_STDID
                                              : CAN_MOTOR_POWER_STATUS_STDID;
                CAN_TxHeaderTypeDef txHeader = {
                    .StdId = replyId,
                    .DLC   = 8,
                    .IDE   = CAN_ID_STD,
                    .RTR   = CAN_RTR_DATA,
                };
                uint8_t txData[8] = {0};
                int16_t target  = (int16_t)status.target_logic_speed;
                int16_t current = (int16_t)status.current_logic_speed;
                int16_t pwm     = (int16_t)status.pwm_output;
                memcpy(&txData[0], &target,  2);
                memcpy(&txData[2], &current, 2);
                memcpy(&txData[4], &pwm,     2);
                uint32_t txMailbox;
                HAL_CAN_AddTxMessage(&hcan, &txHeader, txData, &txMailbox);
            }

            AckMsg_t ack = {
                .type = cmd.type, .value = 0, .ok = 1,
                .current_logic_speed = status.current_logic_speed,
                .pwm_output          = status.pwm_output,
            };
            osMessageQueuePut(AckQueueHandle, &ack, 0, 0);
            continue;
        }

        /* ===== 控制命令：生成ACK + 按 motor_id 路由到专属队列 ===== */
        AckMsg_t ack = {
            .type  = cmd.type,
            .value = is_motor_cmd(cmd.type) ? cmd.value : 0,
            .ok    = is_motor_cmd(cmd.type) ? 1 : 0,
            .current_logic_speed = status.current_logic_speed,
            .pwm_output          = status.pwm_output,
        };
        osMessageQueuePut(AckQueueHandle, &ack, 0, 0);

        if (is_motor_cmd(cmd.type))
        {
            if (cmd.motor_id == 0xFF)
            {
                // 广播：同时投递两个队列
                osMessageQueuePut(MotorQueueHandle,  &cmd, 0, 0);
                osMessageQueuePut(MotorQueue1Handle, &cmd, 0, 0);
            }
            else
            {
                osMessageQueueId_t q = (cmd.motor_id == 1) ? MotorQueue1Handle : MotorQueueHandle;
                osMessageQueuePut(q, &cmd, 0, 0);
            }
        }
    }
}"


app_config.h节选
“/* ------------------- CAN总线配置 ------------------- */
/* CAN ID 组选择：改下面这个数字即可切换
 *   1 = 0x125/0x126 系列
 *   2 = 0x123/0x124 系列
 */
#define CAN_ID_GROUP  1

#if CAN_ID_GROUP == 1
    #define CAN_MOTOR_TURN_CMD_STDID             0x125   // 方向电机控制指令的CAN ID
    #define CAN_MOTOR_TURN_CMD_STATUS_STDID      0x225   // 方向上层控制电机状态的CAN ID
    #define CAN_MOTOR_TURN_STATUS_STDID          0x325   // 方向电机状态反馈的CAN ID
    #define CAN_MOTOR_POWER_CMD_STDID            0x126   // 动力电机控制指令的CAN ID
    #define CAN_MOTOR_POWER_CMD_STATUS_STDID     0x226   // 动力上层控制电机状态的CAN ID
    #define CAN_MOTOR_POWER_STATUS_STDID         0x326   // 动力电机状态反馈的CAN ID
#elif CAN_ID_GROUP == 2
    #define CAN_MOTOR_TURN_CMD_STDID             0x123   // 方向电机控制指令的CAN ID
    #define CAN_MOTOR_TURN_CMD_STATUS_STDID      0x223   // 方向上层控制电机状态的CAN ID
    #define CAN_MOTOR_TURN_STATUS_STDID          0x323   // 方向电机状态反馈的CAN ID
    #define CAN_MOTOR_POWER_CMD_STDID            0x124   // 动力电机控制指令的CAN ID
    #define CAN_MOTOR_POWER_CMD_STATUS_STDID     0x224   // 动力上层控制电机状态的CAN ID
    #define CAN_MOTOR_POWER_STATUS_STDID         0x324   // 动力电机状态反馈的CAN ID
#else
    #error "CAN_ID_GROUP must be 1 (0x125/0x126) or 2 (0x123/0x124)"
#endif

#define CAN_CMD_SET_SPEED_T2            0x11    // 新的设置速度命令 
#define CAN_CMD_REVERSE_BYTE            0x02    // 独立倒转命令字节（宏，避免与枚举 CMD_REVERSE=2 在 switch 中混用）
#define CAN_CMD_QUERY_STATUS            0x01    // 查询状态命令 (兼容旧协议)
#define CAN_CMD_LOG_START               0x04    // 开始发送实时电机数据
#define CAN_CMD_LOG_STOP                0x05    // 停止发送实时电机数据

// 全车停止
#define CAN_CMD_STOP_STDID              0x101   // 全车停止命令的CAN ID
// 全车转向命令
#define CAN_CMD_TURN_STDID              0x102   // 转向命令的CAN ID
// 全车动力命令
#define CAN_CMD_POWER_STDID             0x103   // 动力命令的CAN ID”