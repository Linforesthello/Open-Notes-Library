# 「UART1 DMA 发送信号量死锁」问题分析与修复

## 一句话总结

**潜在死锁风险**：`uart1_send()` 中等待 DMA 发送完成信号量时使用 `osWaitForever`，若 DMA 启动失败或中断丢失，信号量永远不被释放，导致 mutex 被永久持有，所有后续发送任务阻塞。

---

## 一、前因：问题分析

### 1.1 代码现场 (app_task.c)

`UartToCan_Task_Run` 和 `CanRxProcess_Task_Run` 都通过 `uart1_send()` 输出诊断信息：

```c
static void uart1_send(const char *buf, uint16_t len)
{
    if (len == 0 || len > UART1_TX_DMA_BUF_SIZE) { return; }

    osMutexAcquire(uart1_tx_mutexHandle, osWaitForever);  // (1)

    memcpy(uart1_tx_dma_buf, buf, len);
    HAL_UART_Transmit_DMA(&huart1, uart1_tx_dma_buf, len); // (2)

    /* 等待 HAL_UART_TxCpltCallback 释放信号量 */
    osSemaphoreAcquire(uart1_tx_semHandle, osWaitForever);  // (3)

    osMutexRelease(uart1_tx_mutexHandle);  // (4)
}
```

信号量在中断中释放：

```c
// stm32f1xx_it.c
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        osSemaphoreRelease(uart1_tx_semHandle);
    }
}
```

### 1.2 问题认定

| 审查项 | 结论 | 风险等级 |
|--------|------|:--------:|
| `osSemaphoreAcquire` 使用 `osWaitForever` | DMA 失败/异常时永久阻塞 | **P0** |
| `HAL_UART_Transmit_DMA` 返回值未检查 | 启动失败时无 fallback 路径 | **P0** |
| mutex 在异常路径未释放 | 死锁传导：阻塞所有其他发送任务 | **P0** |

### 1.3 风险场景

**场景 A：DMA 启动失败**
- `HAL_UART_Transmit_DMA()` 返回 `HAL_ERROR`
- TxCpltCallback **不会被触发**
- 信号量永远不释放，第(3)步永久阻塞
- mutex 被持有，**所有调用 `uart1_send()` 的任务死锁**

**场景 B：中断丢失（极端情况）**
- DMA 传输完成但中断未到达（NVIC 竞争、异常）
- 信号量永远不释放
- 同样导致死锁

**场景 C：高频率发送竞争**
- `uart1_send()` 被多任务调用（UartToCan + CanRxProcess 共用）
- 一次死锁 → 下一次 `osMutexAcquire` 也死锁 → 全系统诊断输出瘫痪

---

## 二、修复方案

### 2.1 修改要点

```
(1) 启动 DMA 后检查返回值
    ├── 成功 → 等待信号量（带超时）
    └── 失败 → 释放 mutex，直接返回

(2) 信号量等待从 osWaitForever 改为带超时
    ├── 成功 → 正常释放 mutex
    └── 超时 → 释放 mutex，返回（防中断丢失）
```

### 2.2 代码对比

| 项目 | 修改前 | 修改后 |
|------|--------|--------|
| DMA 返回值检查 | 无 | `if (HAL_UART_Transmit_DMA(...) != HAL_OK) { osMutexRelease; return; }` |
| 信号量等待 | `osWaitForever` | `UART1_TX_SEM_TIMEOUT_MS` (1000ms) |
| 超时处理 | 无 | `osSemaphoreAcquire(...) != osOK → osMutexRelease; return` |
| 新增宏 | 无 | `#define UART1_TX_SEM_TIMEOUT_MS 1000u` |

### 2.3 最终代码

```c
#define UART1_TX_SEM_TIMEOUT_MS  1000u

static void uart1_send(const char *buf, uint16_t len)
{
    if (len == 0 || len > UART1_TX_DMA_BUF_SIZE) { return; }

    osMutexAcquire(uart1_tx_mutexHandle, osWaitForever);

    memcpy(uart1_tx_dma_buf, buf, len);

    /* DMA 启动失败 → 不会触发 TxCpltCallback → 直接释放 mutex 返回 */
    if (HAL_UART_Transmit_DMA(&huart1, uart1_tx_dma_buf, len) != HAL_OK)
    {
        osMutexRelease(uart1_tx_mutexHandle);
        return;
    }

    /* 等待 TxCplt 信号量，超时说明中断丢失，释放 mutex 防止死锁 */
    if (osSemaphoreAcquire(uart1_tx_semHandle, UART1_TX_SEM_TIMEOUT_MS) != osOK)
    {
        osMutexRelease(uart1_tx_mutexHandle);
        return;
    }

    osMutexRelease(uart1_tx_mutexHandle);
}
```

---

## 三、超时值选择依据

- **UART 配置**：115200 bps，8N1
- **最大发送量**：128 字节
- **理论耗时**：`128 * 10 / 115200 ≈ 11.1ms`（1 起始 + 8 数据 + 1 停止）
- **选值**：`1000ms`

1000ms 远超实际传输时间（~11ms），正常场景不会误超时；同时足以覆盖 DMA/中断异常场景的判断窗口。

---

## 四、验证方法

### 4.1 正常路径验证

```bash
# 构建并烧录
cmake --build build
# 观察诊断输出，UART→CAN 和 CAN→UART 双向通信正常
# 不出现超时导致的丢数据
```

### 4.2 异常注入测试（可选）

在代码中临时注入 DMA 失败场景验证死锁解除：

```c
// 临时修改：模拟 DMA 启动失败
// if (HAL_UART_Transmit_DMA(&huart1, uart1_tx_dma_buf, len) != HAL_OK)
if (1)  // 强制失败路径
{
    osMutexRelease(uart1_tx_mutexHandle);
    return;
}
```

观察任务是否仍能正常运行（不应死锁）。

---

## 五、关联修改

本次 Fix3 与 Fix2（队列满检查）均为 P0 优先级，改动集中在 `app_task.c`：

| 文件 | 改动内容 | 
|------|---------|
| [app_task.c](../../App/app_task.c) | `uart1_send()` 加 DMA 返回值检查 + 信号量超时 |
| [fix3_信号量死锁.md](fix3_信号量死锁.md) | 本文档 |

**互斥锁 + 信号量 + DMA 回调的死锁三角是本项目最核心的并发风险，修复后应保持对此模式的审查意识。**
