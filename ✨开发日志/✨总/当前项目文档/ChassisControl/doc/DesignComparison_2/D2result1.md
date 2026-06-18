# 反馈设计修复结果

## 原始问题

来自 [Q2_comparison_t1.md](Q2_comparison_t1.md) 的分析：

| 等级 | 问题 | 表现 |
|---|---|---|
| P0 | PC 端无行缓冲，不定长读取 | `ID: 0x102` 被拆成 `0x10` + `2, DLC: 2` 两行 |
| P1 | "Sending..." 在 `HAL_CAN_AddTxMessage` 之前打印 | 发送失败时用户仍看到 Sending，误导调试 |
| P2 | 无 CAN TX 完成确认 | 不知道报文是否在总线发送成功 |
| P3 | 诊断日志与 CAN RX 反馈共享 UART1 TX | 高负载下可能丢反馈（暂不处理） |

---

## 修复总览

```
涉及文件:
  PC 端 Python 脚本           — P0: 行缓冲读取（用户自行完成）
  App/app_task.c              — P1: 打印顺序 + 语义修正
  App/app_globals.h           — P2: can_tx_done_cnt 外部声明
  Core/Src/can.c              — P2: 开启 CAN 外设 TX 中断
  Core/Src/stm32f1xx_it.c     — P2: CAN TX 完成回调
```

---

## 测试验证（Done 正常递增）

```
TX: AA 01 02 01 00 00 02 11 00
RX: CAN_TX OK | ID=0x102 DLC=2 Done=1      ← 首次发送，已完成 1 帧
TX: AA 01 03 01 00 00 02 11 4B
RX: CAN_TX OK | ID=0x103 DLC=2 Done=2
TX: AA 01 03 01 00 00 02 11 00
RX: CAN_TX OK | ID=0x103 DLC=2 Done=3
TX: AA 01 01 01 00 00 02 11 00
RX: CAN_TX OK | ID=0x101 DLC=2 Done=4
...
TX: AA 01 26 02 00 00 01 01
RX: CAN_TX OK | ID=0x226 DLC=1 Done=10
RX: CAN RX | ID: 0x326 | DLC: 8 | Data: ...  ← 下行反馈也正常
...
TX: AA 01 01 01 00 00 02 11 00
RX: CAN_TX OK | ID=0x101 DLC=2 Done=12
```

- ID 不再错位 ✓
- OK/FAIL 语义清晰 ✓
- Done 从 1 连续递增到 12 ✓
- 下行 CAN RX 反馈正常共存 ✓

---

## P0 — PC 端行缓冲读取（用户自行完成）

**文件**: Python 脚本 `rx_reader`

**问题**: `ser.read(ser.in_waiting)` 不定长读取，可能落在 `\r\n` 之间的任意位置。

**修复**: 用 `io.BytesIO` 做行缓冲，按 `\n` 切分，不完整行暂存回 buffer，完整行才输出到日志。

---

## P1 — 网关端修正打印顺序

**文件**: `App/app_task.c`，`UartToCan_Task_Run()` 函数

**原代码问题**:

```c
// 先打印 "Sending..."（此时还没调用 AddTxMessage）
sprintf(dbg_buffer, "UART->CAN | RX_MSG | ID: 0x%lX, DLC: %d. Sending...\r\n");
uart1_send(dbg_buffer, offset);

// 再调用 AddTxMessage
HAL_StatusTypeDef tx_status = HAL_CAN_AddTxMessage(...);

// 失败才报告，成功无反馈
if (tx_status != HAL_OK) { /* TX_FAIL */ }
```

**修复**: 删除 AddTxMessage 之前的打印，统一在调用后输出：

```c
HAL_StatusTypeDef tx_status = HAL_CAN_AddTxMessage(&hcan, &tx_header, uart_msg.data, &tx_mailbox);

int offset;
if (tx_status == HAL_OK) {
    offset = sprintf(dbg_buffer, "CAN_TX OK | ID=0x%lX DLC=%d Done=%lu\r\n",
                     uart_msg.id, uart_msg.len, can_tx_done_cnt);
} else {
    offset = sprintf(dbg_buffer, "CAN_TX FAIL | ID=0x%lX DLC=%d Status=%d\r\n",
                     uart_msg.id, uart_msg.len, tx_status);
}
uart1_send(dbg_buffer, offset);
```

**反馈格式变化**:
```
# 之前
UART->CAN | RX_MSG | ID: 0x102, DLC: 2. Sending...   ← 发送前就打印
UART->CAN | TX_FAIL | Status: 3                        ← 失败才出

# 之后
CAN_TX OK | ID=0x102 DLC=2 Done=15     ← 发送后统一打印，Done 累计
CAN_TX FAIL | ID=0x102 DLC=2 Status=3  ← 失败时一目了然
```

---

## P2 — CAN TX 完成中断确认

### 目标

每次 CAN 报文成功从总线发出后，`Done` 计数器递增，`CAN_TX OK` 日志中显示累计完成数。

### 涉及改动

**`App/app_globals.h`**: 新增外部声明
```c
extern volatile uint32_t can_tx_done_cnt;
```

**`Core/Src/can.c`**: `MX_CAN_Init` 末尾开启 CAN 外设 TX 空中断
```c
__HAL_CAN_ENABLE_IT(&hcan, CAN_IT_TX_MAILBOX_EMPTY);
```

### 错路 #1：写错回调名

**错误做法** → 实现 `HAL_CAN_TxCpltCallback`:

```c
// ❌ STM32F1 HAL 不会调用这个函数
void HAL_CAN_TxCpltCallback(CAN_HandleTypeDef *hcan)
{
    can_tx_done_cnt++;
}
```

**为什么错**: 查看 HAL 源码 `stm32f1xx_hal_can.c:1719-1724`，`HAL_CAN_IRQHandler` 在 TX 完成时调用的是**按邮箱的三个回调**：

```c
// stm32f1xx_hal_can.c 实际代码:
if ((tsrflags & CAN_TSR_TXOK0) != 0U) {
    HAL_CAN_TxMailbox0CompleteCallback(hcan);   // ← 这个
}
if ((tsrflags & CAN_TSR_TXOK1) != 0U) {
    HAL_CAN_TxMailbox1CompleteCallback(hcan);   // ← 这个
}
if ((tsrflags & CAN_TSR_TXOK2) != 0U) {
    HAL_CAN_TxMailbox2CompleteCallback(hcan);   // ← 这个
}
```

而非通用 `HAL_CAN_TxCpltCallback`（那是 F4/H7 的 API）。

**结果**: 中断确实触发了，但弱定义的三个回调是空函数，`Done` 始终为零。

### 错路 #2：怀疑 CubeMX 未开中断

由于 `Done` 为零，怀疑 CubeMX `.ioc` 中 CAN TX 中断未配置。检查后确认 NVIC `USB_HP_CAN1_TX_IRQn=true` 已开启。`__HAL_CAN_ENABLE_IT` 的添加也是必要的（`HAL_CAN_AddTxMessage` 不自动开外设中断），但只加它不足以让 `Done` 工作 —— 因为回调名仍然不对。

### 正确路线

**文件**: `Core/Src/stm32f1xx_it.c`

```c
void HAL_CAN_TxMailbox0CompleteCallback(CAN_HandleTypeDef *hcan)
{
    can_tx_done_cnt++;
}

void HAL_CAN_TxMailbox1CompleteCallback(CAN_HandleTypeDef *hcan)
{
    can_tx_done_cnt++;
}

void HAL_CAN_TxMailbox2CompleteCallback(CAN_HandleTypeDef *hcan)
{
    can_tx_done_cnt++;
}
```

三个回调分别对应 CAN 控制器的三个发送邮箱。任一个完成都递增同一计数器。

### 完整数据流

```
HAL_CAN_AddTxMessage()         ← Task 上下文，写邮箱，启动发送
        │
        ▼
CAN 总线传输完成 (ACK 到达)
        │
        ▼
CAN 硬件: TSR.RQCPx=1, TXOKx=1
        │
        ▼
CAN 外设 → NVIC → CPU: USB_HP_CAN1_TX_IRQHandler
        │
        ▼
HAL_CAN_IRQHandler(&hcan)     ← 读 IER/TSR，检查 TMEIE
        │
        ├─ RQCP0+TXOK0 → HAL_CAN_TxMailbox0CompleteCallback → can_tx_done_cnt++
        ├─ RQCP1+TXOK1 → HAL_CAN_TxMailbox1CompleteCallback → can_tx_done_cnt++
        └─ RQCP2+TXOK2 → HAL_CAN_TxMailbox2CompleteCallback → can_tx_done_cnt++
        │
        ▼
UartToCan_Task: 下次 AddTxMessage 后读取 can_tx_done_cnt
        │
        ▼
PC 端: "CAN_TX OK | ID=0x102 DLC=2 Done=15"
```

---

## 关键教训

1. **HAL 回调名因芯片系列而异**：F1 用 `HAL_CAN_TxMailboxNCompleteCallback`，F4/H7 用 `HAL_CAN_TxCpltCallback`。写回调前先读 HAL 驱动源码中 `HAL_CAN_IRQHandler` 的实际调用，不要凭经验猜测。

2. **NVIC 使能 ≠ 外设中断使能**：NVIC 只是 CPU 级的中断门，CAN 外设自身的 IER 寄存器也需要相应位被置位。`HAL_CAN_AddTxMessage` 是轮询 API，不自动开外设中断，需手动 `__HAL_CAN_ENABLE_IT`。

3. **`__HAL_CAN_ENABLE_IT` 不依赖 HAL 内部状态**：即使 `HAL_CAN_AddTxMessage` 不设 `pTxMailbox`，只要 TMEIE 开了，RQCP+TXOK 满足时回调就会被调用。HAL 的 IRQ Handler 判断条件全是硬件寄存器值，不检查软件状态。


4. 原始问题 — P0/P1/P2 三级问题
5. 测试验证 — Done 从 1 连续递增到 12，ID 不再错位
6. P0/P1 修复 — 行缓冲 + 打印顺序修正
7. P2 完整记录 — 两条错路（HAL_CAN_TxCpltCallback 回调名错误、怀疑 CubeMX 未开中断）→ 查 HAL 源
定位真因 → 改为三个 HAL_CAN_TxMailboxNCompleteCallback → 成功
8. 完整数据流图 — 从 AddTxMessage 到 PC 端显示的全链路
9. 三条关键教训 — 不同芯片 HAL 回调名不同、NVIC ≠ 外设中断、HAL IRQ Handler 靠硬件寄存器判断不靠软件状态

## 所以“__HAL_CAN_ENABLE_IT(&hcan, CAN_IT_TX_MAILBOX_EMPTY)”这条语句有用么？
经实际测的，确实有用

有用，而且必须要有。

原因分两层：

中断链路需要两道门同时开

CAN 外设 IER.TMEIE  ──→  CAN NVIC  ──→  CPU
      (第一道门)          (第二道门)
NVIC（HAL_NVIC_EnableIRQ(USB_HP_CAN1_TX_IRQn)）— CubeMX 已生成，管 CPU 是否响应
CAN_IER.TMEIE（__HAL_CAN_ENABLE_IT）— 管 CAN 外设是否产生中断信号
两道门缺一不可。HAL_CAN_AddTxMessage 是轮询 API，不碰 IER，所以 TMEIE 初始为 0。不加这一行，CAN 外设永远不会因为 TX 完成而拉中断线，USB_HP_CAN1_TX_IRQHandler 根本不会进。

之前 Done 为零时的两处缺失
缺失	后果
回调名错误（HAL_CAN_TxCpltCallback）	中断进了，但跑了空函数
如果没有 __HAL_CAN_ENABLE_IT	中断根本不会进
第一条是"进了门但找错人"，第二条是"门都没开"。后来两处都修了，链路才通。所以这行寄存器操作是必要条件，不是多余的。