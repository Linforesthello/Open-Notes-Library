# fix2: 双路电机 Logger DMA 冲突修复方案

## 问题描述

`logger_task.c` 使用全局 `tx_buf[64]` 作为 DMA 发送缓冲区，`HAL_UART_Transmit_DMA` 是异步的。
当前通过 `idx == 0` 限制只有 Motor0 的编码器任务唤醒 Logger（规避双唤醒），但这是**打补丁**而非根治。
一旦需要同时上报两路电机数据，冲突立刻复现。

```
根本矛盾：
  N 路电机数据  →  1 个全局 tx_buf  →  1 路 DMA（异步）
  ↓
  第 N+1 次 snprintf 覆盖 DMA 还在搬运的 tx_buf → 乱码
```

---

## 方案对比

### 方案 A：合并为单帧（当前临时方案）

```
Motor0 数据 + Motor1 数据 → 一次 snprintf → 一次 DMA
```

| 优点 | 缺点 |
|---|---|
| 改动最小，当天可用 | 帧变长（超 64 字节可能溢出），两路耦合 |
| 无需新增 RTOS 对象 | 扩展到 N 路时需要改帧格式和缓冲区大小 |
| | 丢失单路数据的独立性 |

**适合**：临时验证、只有固定两路且不再扩展。

---

### 方案 B：双缓冲（Ping-Pong Buffer）

```c
static uint8_t tx_buf[2][64];
static volatile uint8_t dma_buf_idx = 0;  // DMA 正在用哪个

// 发送时：写另一个 buf，DMA 发当前 buf
uint8_t write_idx = dma_buf_idx ^ 1;
snprintf((char *)tx_buf[write_idx], 64, "...");
dma_buf_idx = write_idx;
HAL_UART_Transmit_DMA(&huart1, tx_buf[write_idx], len);
```

```
tx_buf[0] ←── DMA 正在发
tx_buf[1] ←── snprintf 安全写入
下一帧翻转：
tx_buf[1] ←── DMA 发
tx_buf[0] ←── snprintf 写
```

| 优点 | 缺点 |
|---|---|
| 无 RTOS 开销，极低延迟 | 只能防止相邻两帧冲突，若 DMA 未完成仍会覆盖 |
| 实现简单 | 需配合 DMA 完成标志位才严格安全 |
| | 不能处理两路并发写（仍需序列化） |

**适合**：单一生产者，发送频率稳定，追求最低开销。

---

### 方案 C：Log 消息队列 + DMA 信号量驱动（推荐）★

**核心思路：** 把"谁有数据要发"和"何时可以发"彻底解耦。
编码器任务只负责把数据投递到队列，Logger 任务串行出队、格式化、发送，DMA 完成后释放信号量，Logger 才发下一帧。

#### 数据结构

```c
// App/services/logger.h 新增
typedef struct {
    uint8_t  motor_id;           // 0 or 1
    int32_t  current_ticks;
    float    target_logic_speed;
    int16_t  pwm_output;
    uint32_t timestamp_ms;
} LogMotorData_t;
```

#### 新增 RTOS 对象（freertos.c）

```c
// 队列：深度 4，存放两路电机数据（各2帧缓冲）
osMessageQueueId_t LogQueueHandle;       // LogMotorData_t, depth=4

// 二值信号量：DMA 完成时释放，Logger 拿到后才能发下一帧
osSemaphoreId_t    uart1_dma_semHandle;  // init count = 1
```

#### 数据流

```
Encoder_Task(Motor0)              Encoder_Task(Motor1)
      │                                  │
      │  osMutexAcquire(motor0_mutex)    │  osMutexAcquire(motor1_mutex)
      │  读取 g_motors[0]                │  读取 g_motors[1]
      │  osMutexRelease                  │  osMutexRelease
      │                                  │
      │  LogMotorData_t d0 = {...}       │  LogMotorData_t d1 = {...}
      │  osMessageQueuePut(LogQueue, d0) │  osMessageQueuePut(LogQueue, d1)
      │                                  │
      └──────────────┬───────────────────┘
                     │
                     ▼
              [LogQueueHandle]
              depth=4, 天然串行化
                     │
                     ▼
              Logger_Task
                     │
                     ├─ osMessageQueueGet(LogQueue, &d, osWaitForever)
                     │
                     ├─ osSemaphoreAcquire(uart1_dma_sem, osWaitForever)
                     │    ← 阻塞直到上一次 DMA 完成
                     │
                     ├─ snprintf(tx_buf, ..., d.motor_id, d.current_ticks, ...)
                     │
                     └─ HAL_UART_Transmit_DMA(&huart1, tx_buf, len)
                              │
                              ▼ DMA TC 中断
                        HAL_UART_TxCpltCallback
                              │
                              └─ if USART1: osSemaphoreRelease(uart1_dma_sem)
```

#### 关键代码片段

**logger_task.c（改造后）**

```c
void Logger_Task(void *argument)
{
    Logger_Init();

    for (;;)
    {
        LogMotorData_t d;

        // 1. 等待任意一路电机的数据入队
        if (osMessageQueueGet(LogQueueHandle, &d, NULL, osWaitForever) != osOK)
            continue;

        if (!g_logger_enabled)
            continue;

        // 2. 等待上一帧 DMA 完成（初始信号量=1，第一帧直接通过）
        osSemaphoreAcquire(uart1_dma_semHandle, osWaitForever);

        // 3. 格式化（tx_buf 此时 DMA 已完成，安全写入）
        int32_t ti = (int32_t)d.target_logic_speed;
        int32_t td = (int32_t)(fabsf(d.target_logic_speed - (float)ti) * 10.0f);

        int len = snprintf((char *)tx_buf, sizeof(tx_buf),
                           "%lu,%u,%d,%ld.%ld,%d\r\n",
                           (unsigned long)d.timestamp_ms,
                           d.motor_id,
                           (int)d.current_ticks,
                           (long)ti, (long)td,
                           (int)d.pwm_output);

        // 4. 启动 DMA（信号量在 TxCpltCallback 里释放）
        HAL_UART_Transmit_DMA(&huart1, tx_buf, len);

        // 5. ORE 清理
        if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_ORE))
            __HAL_UART_CLEAR_OREFLAG(&huart1);
    }
}
```

**encoder_task.c（改造后，idx 限制移除）**

```c
// 在 osMutexRelease 之后（两路都可以投递）
LogMotorData_t log_d = {
    .motor_id           = idx,
    .current_ticks      = motor->current_ticks,
    .target_logic_speed = motor->target_logic_speed,
    .pwm_output         = motor->pwm_output,
    .timestamp_ms       = HAL_GetTick(),
};
if (LogQueueHandle != NULL)
    osMessageQueuePut(LogQueueHandle, &log_d, 0, 0);  // 不等待，满则丢弃
```

**logger.c（TxCpltCallback 新增 USART1 处理）**

```c
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2)
        uart2_tx_busy = 0;

    if (huart->Instance == USART1)              // 新增
        osSemaphoreRelease(uart1_dma_semHandle); // 释放，允许 Logger 发下一帧
}
```

**freertos.c（新增对象）**

```c
// 声明
osMessageQueueId_t LogQueueHandle;
osSemaphoreId_t    uart1_dma_semHandle;

// 创建
LogQueueHandle     = osMessageQueueNew(4, sizeof(LogMotorData_t), &LogQueue_attributes);
uart1_dma_semHandle = osSemaphoreNew(1, 1, &uart1_dma_sem_attributes); // init=1
```

| 优点 | 缺点 |
|---|---|
| tx_buf 永远不会在 DMA 期间被覆盖 | 新增 2 个 RTOS 对象（约 200 字节 RAM） |
| 编码器任务完全解耦，随时可加第 3 路 | LogMotorData_t 入队有拷贝开销（24 字节/次） |
| 队列满时自动丢帧，不阻塞编码器任务 | |
| 上位机可用 motor_id 字段区分两路曲线 | |

**适合**：扩展性要求高，N 路电机，长期维护的项目。

---

## 方案选择建议

| 场景 | 推荐 |
|---|---|
| 快速验证，只有2路不再扩展 | 方案 A（合并单帧）|
| 中期，追求零 RTOS 开销 | 方案 B（Ping-Pong）+ DMA busy flag |
| 长期，架构清晰，支持 N 路 | **方案 C（队列 + 信号量）** |

---

## 上位机协议变更（方案 C）

帧格式新增 `motor_id` 字段：

```
原格式：timestamp,cnt,speed,target,pwm\r\n
新格式：timestamp,motor_id,speed,target,pwm\r\n
```

上位机按 `motor_id` 分流到两条曲线即可，无需两条串口或两套解析器。

---

## 改动文件清单（方案 C）

| 文件 | 改动 |
|---|---|
| `App/services/logger.h` | 新增 `LogMotorData_t` 结构体 |
| `App/services/logger.c` | `TxCpltCallback` 加 USART1 信号量释放 |
| `App/tasks/logger_task.c` | 改为从队列获取数据 + 信号量保护 DMA |
| `App/tasks/encoder_task.c` | 移除 `idx==0` 限制，改为投队列 |
| `App/config/app_globals.h` | 新增 `extern LogQueueHandle`, `uart1_dma_semHandle` |
| `Core/Src/freertos.c` | 创建 `LogQueueHandle` 和 `uart1_dma_semHandle` |
