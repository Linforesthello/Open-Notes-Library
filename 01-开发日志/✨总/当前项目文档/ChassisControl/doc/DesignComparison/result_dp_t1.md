# Phase 1 — P0 阻塞性缺陷修复 Plan

> 基线：commit `19c25f4` / 当前 `fix_base` 分支
> 依据：[deepseek_t1.md](deepseek_t1.md) 审查结论

---

## 总览：3 项修复

| # | 缺陷 | 风险等级 | 涉及文件 | 改动量 |
|---|------|---------|---------|--------|
| 1 | `cmd` 字段未透传 CAN 总线 | **高** | `app_task.c` | ~10 行 |
| 2 | `osMessageQueuePut` 返回值未检查 | **中** | `app_task.c`、`app_config.h` | ~15 行 |
| 3 | DMA 发送信号量超时导致死锁 | **中** | `app_task.c` | ~8 行 |

---

## Fix 1：cmd 字段透传 CAN

### 问题

`UartToCan_Task_Run` 调用 `HAL_CAN_AddTxMessage(&hcan, &tx_header, uart_msg.data, &tx_mailbox)` 时，只发送了 `data[8]` 部分。`cmd` 字节（指令类型）从未出现在 CAN data payload 中，CAN 接收端无法区分 `CMD_SET_SPEED(0x01)` 和 `CMD_GET_STATE(0x02)`。

### 修改方案

在 `UartToCan_Task_Run` 中，发送前将 `cmd` 填入 `data[0]`，原有数据右移 1 字节，DLC +1：

```c
// app_task.c — UartToCan_Task_Run, 在 HAL_CAN_AddTxMessage 之前插入
uint8_t can_data[8];
can_data[0] = uart_msg.cmd;                         // cmd → data[0]
memcpy(&can_data[1], uart_msg.data, uart_msg.len);  // 原有数据 → data[1..]
tx_header.DLC = uart_msg.len + 1;                   // DLC = len + 1 (cmd 占 1 字节)

HAL_CAN_AddTxMessage(&hcan, &tx_header, can_data, &tx_mailbox);
```

### 影响

- **协议升级**：CAN payload 格式变为 `[CMD][DATA0..DATA7]`，DLC 比原来多 1
- **兼容性**：所有 CAN 接收节点需同步更新解析逻辑
- **边界**：`len == 8` 时 `can_data` 填满 9 字节 → **不合法**（CAN 最大 8 字节）
  - 需在解析时限制：`uart_msg.len > 7` 时报错/截断
  - 实际 `data[8]` 最大 8 字节，cmd 占 1 字节 → 实际负载最大 7 字节

### 协议约束更新

| 字段 | UART 帧 | CAN 帧 |
|------|---------|--------|
| cmd | 协议帧第 2 字节 | CAN data[0] |
| data[0..7] | 协议帧 data 段 | CAN data[1..8] |
| DLC | len (0-8) | len+1 (1-8) |

---

## Fix 2：osMessageQueuePut 返回值检查

### 问题

`ProtocolParser_Task_Run` 中两处 `osMessageQueuePut`（STATE_WAIT_LEN 和 STATE_WAIT_DATA 分支）使用 `timeout=0` 且返回值未检查。队列满（16 条）时消息静默丢弃，无反馈。

### 修改方案

#### 2a. 定义错误统计变量

在 `app_config.h` 或 `app_task.c` 文件作用域添加：

```c
// app_task.c — 文件作用域
static volatile uint32_t parser_queue_drop_count = 0;
```

#### 2b. 替换两处 osMessageQueuePut

两处原代码：
```c
osMessageQueuePut(uartToCanQueueHandle, &current_msg, 0, 0);
```

改为：
```c
if (osMessageQueuePut(uartToCanQueueHandle, &current_msg, 0, 0) != osOK) {
    parser_queue_drop_count++;
}
```

#### 2c. （可选）增加诊断接口

可通过心跳任务或专用诊断命令查询 `parser_queue_drop_count`，辅助调试。

---

## Fix 3：DMA 发送信号量超时保护

### 问题

`uart1_send()` 中 `osSemaphoreAcquire(uart1_tx_semHandle, osWaitForever)` 若因 DMA 回调未触发/信号量被消耗而长期不返回，将永久持有 `uart1_tx_mutexHandle`，导致所有 UART TX 死锁。

### 修改方案

改用有限超时（如 100ms），超时后释放互斥锁并返回错误：

```c
// app_task.c — uart1_send()
osMutexAcquire(uart1_tx_mutexHandle, osWaitForever);

memcpy(uart1_tx_dma_buf, buf, len);
HAL_UART_Transmit_DMA(&huart1, uart1_tx_dma_buf, len);

// 改用有限超时：等待 100ms，超时则释放互斥锁
if (osSemaphoreAcquire(uart1_tx_semHandle, 100) != osOK) {
    osMutexRelease(uart1_tx_mutexHandle);
    return;  // 发送失败，调用方需感知
}

osMutexRelease(uart1_tx_mutexHandle);
```

### 超时值选择依据

| 因素 | 值 |
|------|-----|
| UART 115200bps 最慢发送 (8字节+start+stop=10bit) | ~0.7ms |
| UART 115200bps 最慢发送 (128字节) | ~11ms |
| **选定时长** | **100ms** |
| 裕量 | ~9-140x |

100ms 远超正常 DMA 传输时间，同时远小于心跳周期（300ms），可在死锁后 1-2 个心跳周期内恢复。

---

## 文件改动汇总

| 文件 | 改动内容 | 行数 |
|------|---------|------|
| `App/app_task.c` | Fix1: UartToCan_Task_Run 中 cmd 填入 data[0] | ~10 |
| `App/app_task.c` | Fix2: 两处 osMessageQueuePut 加返回值检查 + 错误计数 | ~8 |
| `App/app_task.c` | Fix3: uart1_send 信号量超时 + 失败释放 | ~8 |
| `App/app_config.h` | (可选) 队列满丢弃计数 extern 声明 | - |

**总改动量：约 25 行，不涉及架构变更。**

---

## 实施顺序与验证

```
Fix1 (cmd透传)
  → 验证：CAN 接收端确认 data[0] == cmd 字节
  ↓
Fix2 (队列检查)
  → 验证：压力发送时 drop_count 不异常增长
  ↓
Fix3 (死锁保护)
  → 验证：人为制造 DMA 失败，确认互斥锁释放 + 任务恢复
```

### 回滚方案

三项修改互不依赖，均可独立回滚。修改前后 git diff 清晰可辨。
