# UART1 TX 阻塞发送 → DMA 发送改造记录

## 背景

原 `uart1_send()` 使用 `HAL_UART_Transmit`（阻塞模式），任务在发送期间独占 CPU
直到最后一个字节从移位寄存器移出，期间无法处理任何其他逻辑。
目标：改为 DMA + 完成回调模式，让 CPU 在硬件搬运数据时可以被调度出去。

---

## 设计方案

### 同步机制选择

| 机制 | 原方案 | 新方案 |
|------|--------|--------|
| 独占发送通道 | `osMutex` | `osMutex`（保留） |
| 等待发送完成 | 阻塞在 `HAL_UART_Transmit` 内部 | `osSemaphore`（Binary，初始=0） |

**为什么不能继续用 Mutex 等待完成？**
CMSIS-OS2 的 Mutex 不能在 ISR / 回调中释放（`osMutexRelease` 内部断言上下文），
而 DMA 完成通知必须从 `HAL_UART_TxCpltCallback`（ISR 上下文）发出。
Binary Semaphore 的 `osSemaphoreRelease` 对 ISR 安全，因此用信号量承担"完成通知"职责，
Mutex 仅保留其"互斥"语义。

### 完整发送流程

```
Task (uart1_send)                   DMA / ISR
─────────────────────────────────   ──────────────────────────────
osMutexAcquire(mutex)               
memcpy(data → 静态 dma_buf)         
HAL_UART_Transmit_DMA() ──────────► DMA 开始搬运，CPU 立即返回
osSemaphoreAcquire(sem) ← 挂起等待
                                    ... DMA 传输中 ...
                                    DMA TC 中断触发
                                    HAL_DMA_IRQHandler
                                      └─ HAL_UART_TxCpltCallback
                                           └─ osSemaphoreRelease(sem)
osSemaphoreAcquire 返回 ✓           
osMutexRelease(mutex)               
```

### 信号量初始计数必须为 0

- **初始 = 1（Available）**：第一次 `osSemaphoreAcquire` 立即返回，
  Mutex 在 DMA 完成前就被释放，第二帧 `memcpy` 可能覆盖仍在传输中的 `dma_buf`，
  产生数据损坏。
- **初始 = 0（Not Available）**：每次发送都必须等到 `TxCpltCallback` 释放信号量，
  保证 `dma_buf` 在 DMA 结束前不被写入。

---

## 改动清单

### 1. CubeMX（`.ioc`）

在 FreeRTOS → Semaphores 中新增：

| 字段 | 值 |
|------|----|
| Semaphore Name | `uart1_tx_sem` |
| Allocation | Static |
| Control Block Name | `uart1_tx_semControlBlock` |
| Initial State | **Not Available**（初始令牌 = 0） |

重新生成后 `freertos.c` 自动产生：
```c
uart1_tx_semHandle = osSemaphoreNew(1, 0, &uart1_tx_sem_attributes);
```

---

### 2. `App/app_globals.h`

新增信号量句柄的全局 `extern` 声明，使各翻译单元均可访问：

```c
// 新增
extern osSemaphoreId_t uart1_tx_semHandle; // DMA TX 完成信号量（ISR → Task）
```

---

### 3. `App/app_task.c`

#### 新增头文件

```c
#include <string.h>   // memcpy
```

#### 新增静态 DMA 缓冲区

```c
#define UART1_TX_DMA_BUF_SIZE  128u
static uint8_t uart1_tx_dma_buf[UART1_TX_DMA_BUF_SIZE];
```

> `HAL_UART_Transmit_DMA` 要求缓冲区在传输期间持续有效，栈变量会在函数返回后失效，
> 因此必须使用静态（全局生命周期）数组。

#### 重写 `uart1_send()`

```c
// 旧版（阻塞）
static void uart1_send(const char *buf, uint16_t len)
{
    osMutexAcquire(uart1_tx_mutexHandle, osWaitForever);
    HAL_UART_Transmit(&huart1, (const uint8_t *)buf, len, 0xFFFF);
    osMutexRelease(uart1_tx_mutexHandle);
}

// 新版（DMA）
static void uart1_send(const char *buf, uint16_t len)
{
    if (len == 0 || len > UART1_TX_DMA_BUF_SIZE) { return; }

    osMutexAcquire(uart1_tx_mutexHandle, osWaitForever);

    memcpy(uart1_tx_dma_buf, buf, len);
    HAL_UART_Transmit_DMA(&huart1, uart1_tx_dma_buf, len);

    /* 挂起等待 HAL_UART_TxCpltCallback 释放信号量 */
    osSemaphoreAcquire(uart1_tx_semHandle, osWaitForever);

    osMutexRelease(uart1_tx_mutexHandle);
}
```

---

### 4. `Core/Src/stm32f1xx_it.c`

新增 `HAL_UART_TxCpltCallback`，在 DMA 传输完成后从 ISR 侧释放信号量：

```c
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        osSemaphoreRelease(uart1_tx_semHandle);
    }
}
```

**回调触发链路**（CubeMX 已生成，无需手动添加）：
```
DMA1_Channel4_IRQHandler
  └─ HAL_DMA_IRQHandler(&hdma_usart1_tx)
       └─ HAL_UART_TxCpltCallback  ← 此处释放信号量
```

---

## 验证要点

| 项目 | 方法 | 通过标准 |
|------|------|----------|
| 基本功能 | 发送任意长度（≤128字节）字符串 | 串口助手收到内容完整、无乱码 |
| 并发安全 | 同时触发 UART→CAN 和 CAN→UART 双向转发 | 输出无交错乱码 |
| 边界保护 | 发送长度 = 0 或 > 128 | 函数静默返回，不崩溃 |
| CPU 释放 | 逻辑分析仪观察发送期间心跳 LED | LED 不卡顿，任务调度正常 |
