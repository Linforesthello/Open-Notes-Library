# 反馈设计修复计划

## 问题回顾

| 等级 | 问题 | 位置 | 影响 |
|---|---|---|---|
| P0 | PC 端无行缓冲，不定长读取导致 ID 显示错位 (`0x102` → `0x10` + `2, DLC: 2`) | Python `rx_reader` | 日志不可读 |
| P1 | "Sending..." 在 `HAL_CAN_AddTxMessage` 之前打印，失败时用户看不到错误 | `app_task.c:99-123` | 误导调试 |
| P2 | 无 CAN TX 完成回调，不知道报文是否真正在总线上发送成功 | `stm32f1xx_it.c` / `app_task.c` | 无通信完整性确认 |
| P3 | 诊断日志与 CAN RX 反馈共享 UART1 TX 通道 | `app_task.c` | 高负载下可能丢反馈 |

---

## 修复方案

### Fix1 — P0: PC 端行缓冲读取

**文件**: Python 脚本 `rx_reader` 函数

**改动**: 用 `io.BytesIO` 做行缓冲，每次 `ser.read()` 后按 `\n` 切分，不完整的行暂存回 buffer，只输出完整行。

```python
def rx_reader(log_lines, log_win, lock, stop_event):
    buf = io.BytesIO()
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buf.write(data)
                buf.seek(0)
                content = buf.read()
                lines = content.split(b'\n')
                buf.seek(0)
                buf.truncate()
                buf.write(lines[-1])   # 不完整行存回
                for line in lines[:-1]:
                    text = line.decode('ascii', errors='replace').strip()
                    if text:
                        timestamp = time.strftime('%H:%M:%S')
                        log_lines.append(f"[{timestamp}] RX: {text}")
                        refresh_log(log_lines, log_win, lock)
        except serial.SerialException:
            break
        time.sleep(0.05)
```

**影响范围**: 仅 Python 主机脚本，不涉及固件。

---

### Fix2 — P1: 网关端修正打印顺序 + 语义

**文件**: `App/app_task.c`，`UartToCan_Task_Run()` 函数

**改动**:
1. 删除 `HAL_CAN_AddTxMessage` 之前的 `"Sending..."` 打印
2. 改为在 `HAL_CAN_AddTxMessage` 之后统一打印结果：
   - 成功：`"CAN_TX OK | ID=0x%lX DLC=%d"`
   - 失败：`"CAN_TX FAIL | ID=0x%lX DLC=%d Status=%d"`

```c
// 旧（删除这两行）:
// offset = sprintf(dbg_buffer, "UART->CAN | RX_MSG | ID: 0x%lX, DLC: %d. Sending...\r\n", ...);
// uart1_send(dbg_buffer, offset);

HAL_StatusTypeDef tx_status = HAL_CAN_AddTxMessage(&hcan, &tx_header, uart_msg.data, &tx_mailbox);

// 新:
if (tx_status == HAL_OK) {
    offset = sprintf(dbg_buffer, "CAN_TX OK | ID=0x%lX DLC=%d\r\n", uart_msg.id, uart_msg.len);
} else {
    offset = sprintf(dbg_buffer, "CAN_TX FAIL | ID=0x%lX DLC=%d Status=%d\r\n", uart_msg.id, uart_msg.len, tx_status);
}
uart1_send(dbg_buffer, offset);
```

**影响范围**: 固件 `UartToCan_Task_Run`，约 4 行删 + 7 行增。

---

### Fix3 — P2: 增加 CAN TX 完成回调

**说明**: CAN TX 完成回调 (`HAL_CAN_TxCpltCallback`) 可在报文真正从总线发送后提供确认（是否被 ACK）。
但对于 STM32F103 的 bxCAN，TX 完成回调中无法直接获取 ACK 状态——ACK 错误需要从 `CAN_ESR` 寄存器的 `LEC` 位获取，在错误中断中处理。
故此阶段改为**轻量实现**：仅用回调确认帧已由硬件发出（不阻塞后续）。

**文件**: `Core/Src/stm32f1xx_it.c`

**改动**: 在 `USB_HP_CAN1_TX_IRQHandler` 的 USER CODE 区域添加回调实现：

```c
void HAL_CAN_TxCpltCallback(CAN_HandleTypeDef *hcan)
{
    // CAN frame successfully transmitted on bus
    static uint32_t tx_ok_cnt = 0;
    tx_ok_cnt++;
    // 不在此处通过 uart1_send 打印（ISR 上下文，不可使用 mutex/semaphore）
}
```

**设计决策**:
- ISR 上下文中不能调用 `uart1_send()`（会阻塞 mutex），因此仅累计计数
- 后续考虑用一个轻量队列，在 `UartToCan_Task` 的空闲循环中检查并输出确认信息
- 暂不引入错误中断处理（ACK 错误需额外调试，STM32F103 bxCAN 错误处理机制有限）

**影响范围**: `stm32f1xx_it.c` 新增回调，`app_task.c`（可选）在 UartToCan_Task 中轮询并打印 TX 确认。

---

### Fix4 — 可选（P3）: 降低诊断打印频率

**说明**: 当前每个 CAN 帧都有一次 UART TX 打印，在高频场景下可能阻塞。可通过计数采样降低：每 N 帧打印一次，其余帧静默。

**改动**: 在 `UartToCan_Task_Run` 中增加 `static uint32_t tx_log_mod_N = 0`，仅在 `tx_log_mod_N % 10 == 0` 时打印（10 帧采样一次）。

此项留作可选，待实际负载测试后决定是否引入。

---

## 实施顺序

1. **Fix1** (P0) — 不涉及固件，立即可改
2. **Fix2** (P1) — 固件单文件小改，与 Fix1 无依赖
3. **Fix3** (P2) — 固件改动，可与 Fix2 同批提交
4. **Fix4** (P3) — 暂不实施，待评估
