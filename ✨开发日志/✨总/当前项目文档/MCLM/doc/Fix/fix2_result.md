# fix2 实施结果：双路电机 Logger DMA 冲突修复（方案C）

> 实施时间：2026-04-27  
> 方案选择：**方案C — 消息队列 + 二值信号量**  
> 根治问题：N 路电机数据争抢全局 tx_buf 导致 DMA 乱码

---

## 一、问题回顾

```
N 路电机数据  →  1 个全局 tx_buf  →  1 路 DMA（异步）
↓
第 N+1 次 snprintf 覆盖 DMA 还在搬运的 tx_buf → 乱码
```

旧方案的补丁：`if (idx == 0)` 只让 Motor0 唤醒 Logger，Motor1 数据完全丢失。

---

## 二、新增 RTOS 对象（CubeMX 生成）

### `Core/Src/freertos.c`

| 对象 | 类型 | 参数 | 用途 |
|---|---|---|---|
| `LogQueueHandle` | `osMessageQueueId_t` | depth=24, item=`sizeof(LogMotorData_t)` | 两路编码器任务投递数据帧 |
| `uart1_dma_semHandle` | `osSemaphoreId_t` | max=1, init=**1** | 保护 USART1 DMA，防止覆盖 |

关键代码（CubeMX 自动生成）：
```c
LogQueueHandle      = osMessageQueueNew(24, sizeof(LogMotorData_t), &LogQueue_attributes);
uart1_dma_semHandle = osSemaphoreNew(1, 1, &uart1_dma_sem_attributes);
```

> `init=1`：第一帧无需等待，直接获取信号量发送。

---

## 三、新增类型定义

### `App/services/logger.h`

```c
typedef struct {
    uint8_t  motor_id;            // 0 = Motor0, 1 = Motor1
    int32_t  current_ticks;       // 编码器原始计数（差分值）
    float    target_logic_speed;  // 目标逻辑速度（-100 ~ 100）
    int16_t  pwm_output;          // 当前 PWM 输出
    uint32_t timestamp_ms;        // HAL_GetTick() 时间戳
} LogMotorData_t;
```

---

## 四、修改 `App/config/app_globals.h`

新增 extern 声明，供各任务引用：

```c
#include "logger.h"                                // 引入 LogMotorData_t

// Queues
extern osMessageQueueId_t LogQueueHandle;          // 新增

// Semaphores
extern osSemaphoreId_t uart1_dma_semHandle;        // 新增
```

---

## 五、修改 `App/tasks/encoder_task.c`

**删除**：`if (idx == 0)` 补丁 + `osThreadFlagsSet`  
**新增**：两路电机各自封包投递到 LogQueue

```c
// 旧（打补丁）
if (idx == 0 && Logger_TaHandle != NULL)
    osThreadFlagsSet(Logger_TaHandle, 0x01);

// 新（方案C）
LogMotorData_t log_data = {
    .motor_id           = idx,
    .current_ticks      = diff,
    .target_logic_speed = motor->target_logic_speed,
    .pwm_output         = motor->pwm_output,
    .timestamp_ms       = HAL_GetTick(),
};
osMessageQueuePut(LogQueueHandle, &log_data, 0, 0);
```

---

## 六、修改 `App/tasks/logger_task.c`

| 项目 | 旧逻辑 | 新逻辑 |
|---|---|---|
| 唤醒方式 | `osThreadFlagsWait(0x01, ...)` | `osMessageQueueGet(LogQueueHandle, &log_data, ...)` |
| 数据来源 | 加 mutex 读全局 `g_motors[0]` | 直接用队列帧（已复制，无需 mutex） |
| 发送缓冲区 | 全局 `tx_buf[64]`（DMA 异步仍搬） | `static uint8_t local_tx_buf[64]`（DMA 安全） |
| DMA 保护 | `huart1.gState == READY`（不可靠） | `osSemaphoreAcquire(uart1_dma_semHandle, osWaitForever)` |
| 双路支持 | ❌ 只有 Motor0 | ✅ 两路数据帧均可处理 |

核心代码：
```c
// 1. 阻塞取帧（队列空则挂起，不占 CPU）
LogMotorData_t log_data;
osMessageQueueGet(LogQueueHandle, &log_data, 0, osWaitForever);

if (!g_logger_enabled) continue;

// 2. 浮点转整数+小数（F103 无 %f 支持）
int32_t target_speed_int = (int32_t)log_data.target_logic_speed;
int32_t target_speed_dec = (int32_t)(fabsf(log_data.target_logic_speed
                           - (float)target_speed_int) * 10.0f);

int len = snprintf((char *)local_tx_buf, sizeof(local_tx_buf),
               "%lu,%u,%d,%ld.%ld,%d\r\n",
               (unsigned long)log_data.timestamp_ms,
               (unsigned int)log_data.motor_id,
               (int)log_data.current_ticks,
               (long int)target_speed_int,
               (long int)target_speed_dec,
               (int)log_data.pwm_output);

// 3. 等上一帧 DMA 完成后再发（信号量初值=1，第一帧直接通过）
osSemaphoreAcquire(uart1_dma_semHandle, osWaitForever);
HAL_UART_Transmit_DMA(&huart1, local_tx_buf, len);
```

---

## 七、修改 `App/services/logger.c`

`TxCpltCallback` 新增 USART1 分支，DMA 搬运完成后释放信号量：

```c
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    // USART1 DMA 完成 → 允许 Logger_Task 发下一帧
    if (huart->Instance == USART1) {
        osSemaphoreRelease(uart1_dma_semHandle);
        return;
    }
    if (huart->Instance == USART2)
        uart2_tx_busy = 0;
}
```

---

## 八、完整数据流

```
Encoder_Task(Motor0) ──┐
                       ├─► osMessageQueuePut(LogQueue)
Encoder_Task(Motor1) ──┘
                              │
                              ▼
                    Logger_Task: osMessageQueueGet (阻塞)
                              │
                    osSemaphoreAcquire(uart1_dma_sem)  ← 等上帧 DMA 完成
                              │
                    snprintf → local_tx_buf
                              │
                    HAL_UART_Transmit_DMA(&huart1, ...)
                              │
                    TxCpltCallback (ISR)
                              │
                    osSemaphoreRelease(uart1_dma_sem)  → Logger_Task 继续
```

---

## 九、输出帧格式

```
timestamp_ms, motor_id, current_ticks, target_speed, pwm_output\r\n
```

示例：
```
1234,0,120,50.5,800
1235,1,-88,-30.2,-600
```

---

## 十、注意事项

| 事项 | 说明 |
|---|---|
| `local_tx_buf` 必须是 `static` | 非 static 的栈变量在函数帧返回后可能被覆盖，DMA 会读到脏数据 |
| 信号量初值 = 1 | 第一帧无需等待 TxCplt，直接发送 |
| 队列深度 = 24 | 两路电机同频采样，队列不会积压；过小会 put 失败丢帧 |
| ORE 清除 | `HAL_UART_Transmit_DMA` 后检查并清除 ORE 标志，防止串口状态机卡死 |
| F103 无 `%f` | `snprintf` 浮点需手动拆分整数+小数，或链接时加 `-u _printf_float`（Flash 代价大） |
