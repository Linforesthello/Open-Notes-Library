# 项目架构与数据流分析

本文档详细分析了 `UartToCan_test` 项目的软件架构、核心任务以及关键数据流。
文档内容已同步反映 **代码审查阶段** 完成的全部优化修改（详见 `claude.md`）。

---

## 1. 整体架构

项目基于 **STM32F103C8T6** 微控制器和 **FreeRTOS** 实时操作系统，采用模块化的多任务设计。
核心功能是实现 **UART（串口）** 与 **CAN（控制器局域网）** 总线之间的双向数据转换。

架构分为以下三层：

| 层次 | 组件 | 职责 |
| ---- | ---- | ---- |
| **硬件抽象层 (HAL)** | `STM32F1xx_HAL_Driver` | 驱动 UART、CAN、GPIO 等底层外设 |
| **操作系统层 (OS)** | `FreeRTOS` | 任务调度、消息队列、互斥锁、事件标志 |
| **应用逻辑层 (App)** | `App/` 目录下各模块 | 核心业务逻辑，任务通过队列/事件解耦通信 |

---

## 2. 核心任务 (FreeRTOS Tasks)

系统共创建四个核心任务，各司其职：

| 任务名称 | 优先级 | 核心功能 |
| -------- | ------ | -------- |
| `ProtocolParser_Ta` | High | **（关键）** 从环形缓冲区读取字节，通过状态机解析自定义协议帧，将解析结果放入 `uartToCanQueue` |
| `UartToCan_Ta` | Normal | 从 `uartToCanQueue` 取出解析后的 UART 消息，打包为 CAN 报文并发送 |
| `CanRxProcess_Ta` | Normal | 从 `canRxQueue` 取出 CAN 报文，格式化为可读字符串后经 UART 输出 |
| `Heartbeat_Ta` | Low | 周期性翻转板载 LED（PC13），直观指示系统运行状态 |

---

## 3. 关键数据结构与同步组件

### 3.1 环形缓冲区 `ring_buffer`

- **文件**: `App/ring_buffer.h` / `App/ring_buffer.c`
- **用途**: UART 接收中断（ISR）与 `ProtocolParser_Ta` 任务之间的数据缓冲，实现"中断写、任务读"的异步模型。
- **实现要点**（已优化）:
  - `head` / `tail` 声明为 `volatile uint8_t`，单字节读写在 Cortex-M3 上天然原子，无需临界区。
  - 缓冲区容量固定为 256 字节，利用 `uint8_t` 自然溢出回绕代替 `% 256` 取模，节省指令周期。

### 3.2 消息队列 `canRxQueue`

- **元素类型**: `App_CAN_Message_t`
- **用途**: CAN 接收中断 → `CanRxProcess_Ta` 任务的数据通道。中断将报文快速入队，任务异步出队处理。

### 3.3 消息队列 `uartToCanQueue`

- **元素类型**: `App_UART_Message_t`
- **用途**: `ProtocolParser_Ta` → `UartToCan_Ta` 任务的数据通道。协议解析完成后入队，等待转换发送。

### 3.4 互斥锁 `uart1_tx_mutex`

- **句柄**: `uart1_tx_mutexHandle`（CubeMX 创建）
- **用途**: 保护 `USART1` 发送通道。`UartToCan_Ta` 和 `CanRxProcess_Ta` 均通过 `uart1_send()` 封装函数加锁后再调用 `HAL_UART_Transmit`，防止多任务并发导致输出乱码。

### 3.5 事件标志组 `uart1_rx_event`

- **句柄**: `uart1_rx_eventHandle`（CubeMX 创建）
- **标志位**: `UART1_RX_FLAG (0x01U)`
- **用途**: 替代轮询延迟。`HAL_UART_RxCpltCallback` 在写入环形缓冲区后立即置位此标志，`ProtocolParser_Ta` 在缓冲区为空时挂起等待，有数据到来时零延迟唤醒，消除最坏 1 ms 的 `osDelay(1)` 轮询延迟。

---

## 4. 数据流分析

### 4.1 上行数据流（UART → CAN）

将通过串口发送的自定义协议数据转换为标准 CAN 报文。

```
USART1 外设接收字节
    │
    ▼
USART1_IRQHandler (stm32f1xx_it.c)
    │  写入 uart1_rx_buffer (ring_buffer)
    │  osEventFlagsSet(uart1_rx_eventHandle, UART1_RX_FLAG)  ← 触发事件
    ▼
ProtocolParser_Ta（状态机解析）
    │  缓冲区空时：osEventFlagsWait(..., 10ms 超时) 挂起等待
    │  收到事件立即唤醒，继续读取字节
    │
    │  自定义协议格式：
    │    SOF(1B) | CMD(1B) | CAN_ID(4B) | DLC(1B) | Data(0~8B)
    │
    │  解析成功 → 封装 App_UART_Message_t
    │  osMessageQueuePut → uartToCanQueue
    ▼
UartToCan_Ta
    │  osMessageQueueGet ← uartToCanQueue
    │
    │  智能帧类型判断：
    │    CAN_ID > 0x7FF → 扩展帧 (29-bit)
    │    CAN_ID ≤ 0x7FF → 标准帧 (11-bit)
    │
    │  HAL_CAN_AddTxMessage → CAN 总线发送
    │  uart1_send() 打印发送日志（加锁）
    ▼
CAN 总线
```

### 4.2 下行数据流（CAN → UART）

监听 CAN 总线，将接收到的报文格式化后由串口输出。

```
CAN 控制器接收报文（符合过滤器）
    │
    ▼
USB_LP_CAN1_RX0_IRQHandler (stm32f1xx_it.c)
    │  封装 App_CAN_Message_t
    │  osMessageQueuePut → canRxQueue
    ▼
CanRxProcess_Ta
    │  osMessageQueueGet ← canRxQueue
    │  格式化字符串：ID | DLC | Data[0..N]
    │  uart1_send() 输出（加锁）
    ▼
USART1 发送，PC 串口工具可读
```

---

## 5. 自定义 UART 协议格式

| 字段 | 长度 | 说明 |
| ---- | ---- | ---- |
| `SOF` | 1 字节 | 帧起始标志，固定值 |
| `CMD` | 1 字节 | 指令类型，透传至 CAN 总线，由接收端根据 `Command_ID_t` 解释执行 |
| `CAN_ID` | 4 字节 | CAN 报文标识符（支持 11-bit 标准帧 / 29-bit 扩展帧自动识别）|
| `DLC` | 1 字节 | 数据长度，范围 0~8 |
| `Data` | 0~8 字节 | CAN 报文有效载荷 |

---

## 6. 诊断与调试

| 机制 | 实现 | 作用 |
| ---- | ---- | ---- |
| 心跳 LED | `Heartbeat_Ta` 周期翻转 PC13 | 直观判断系统是否"存活" |
| UART 发送日志 | `uart1_send()`（互斥保护） | 打印 UART→CAN 指令内容、发送失败错误码、CAN→UART 报文内容 |
| 状态机枚举符号 | `ParserState_t` 定义在 `app_config.h` | 调试器可直接显示枚举名，便于状态跟踪 |
