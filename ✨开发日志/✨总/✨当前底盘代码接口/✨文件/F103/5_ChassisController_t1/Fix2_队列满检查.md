
> [!NOTE]
> # Fix2: 队列满检查
> 
> 
> ## 问题
> 
>   
> 
> `osMessageQueuePut` 在所有调用点均未检查返回值。当队列满时，消息会被静默丢弃，无法感知丢帧。
> 
>   
> 
> ## 改动范围
> 
>   
> 
> 共 3 处 `osMessageQueuePut` 调用，分布在 2 个文件中。
> 
>   
> 
> ## 改动内容
> 
>   
> 
> 每个调用点增加返回值检查 + 丢帧计数器递增：
> 
>   
> 
> ```c
> 
> if (osMessageQueuePut(...) != osOK) {
> 
> xxx_drop_cnt++;
> 
> }
> 
> ```
> 
>   
> 
> ### 文件清单
> 
>   
> 
> | 文件 | 位置 | 调用队列 | 计数器名 |
> 
> |------|------|---------|---------|
> 
> | `App/app_task.c` | `STATE_WAIT_LEN` (len==0) | uartToCanQueue | `uartToCanQueue_drop_cnt` |
> 
> | `App/app_task.c` | `STATE_WAIT_DATA` (收完data) | uartToCanQueue | `uartToCanQueue_drop_cnt` |
> 
> | `Core/Src/stm32f1xx_it.c` | ISR `HAL_CAN_RxFifo0MsgPendingCallback` | canRxQueue | `canRxQueue_drop_cnt` (volatile) |
> 
>   
> 
> ### 计数器说明
> 
>   
> 
> - `uartToCanQueue_drop_cnt` — `static uint32_t`，在 `app_task.c` 文件作用域内
> 
> - `canRxQueue_drop_cnt` — `static volatile uint32_t`，在 ISR 中递增，`volatile` 防止编译器优化
> 
>   
> 
> 两个计数器当前仅供诊断观察，可后续接入日志/错误报告接口。
> 
>   
> 
> ## 设计要点
> 
>   
> 
> - ISR 中不可阻塞，因此 timeout 保持 0，只检查返回值并计数
> 
> - 不在 ISR 中做复杂处理（如重试），最小化中断服务时间
> 
> - 计数器不重置，溢出归零——对于 uint32_t 约 43 亿次后才溢出，实际使用中不会发生

