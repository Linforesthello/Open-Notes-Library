# 项目目标与展望

本文档记录 `UartToCan_test` 项目的目标完成状态及后续演进方向。
已完成状态包含**初始实现**与**代码审查阶段优化**两个阶段的成果（详见 `claude.md`）。

---

## 1. 已完成目标

### 1.1 基础功能

- **[✔] 稳定的多任务架构**
  基于 FreeRTOS 建立清晰的四任务系统（`ProtocolParser_` / `UartToCan_Ta` / `CanRxProcess_Ta` / `Heartbeat_Ta`），任务间通过消息队列解耦通信，职责单一，结构清晰。

- **[✔] 自定义 UART 协议解析**
  基于状态机的 `ProtocolParser_Ta` 任务，稳定解析自定义帧格式：
  `SOF(1B)` + `CMD(1B)` + `CAN_ID(4B)` + `DLC(1B)` + `Data(0~8B)`。

- **[✔] UART → CAN 可靠转换**
  `UartToCan_Ta` 任务正确将解析后的指令转换为 CAN 报文，并实现对**标准帧（11-bit ID）**与**扩展帧（29-bit ID）**的自动识别与切换，增强网关通用性。

- **[✔] CAN → UART 透明传输**
  `CanRxProcess_Ta` 任务监听 CAN 总线，将接收报文格式化后实时经 UART 输出，为总线提供透明监控窗口。

- **[✔] 健壮的错误处理与诊断**
  环形缓冲区 + 消息队列安全隔离中断与任务；关键任务内置串口日志；`Heartbeat_Ta` LED 指示系统存活状态。

### 1.2 代码审查阶段优化（新增）

- **[✔] ring_buffer 原子性保障（P0）**
  `head`/`tail` 改为 `volatile uint8_t`，利用 256 字节自然溢出回绕，消除 Cortex-M3 上 16-bit 读写的撕裂风险，无需临界区。

- **[✔] UART 多任务互斥（P0）**
  引入 `uart1_tx_mutex`，封装 `uart1_send()` 统一管理发送路径，彻底消除多任务并发输出乱码问题。

- **[✔] ProtocolParser 事件驱动（P1）**
  以 `uart1_rx_event` 事件标志替代 `osDelay(1)` 轮询，中断置位后任务零延迟唤醒，CPU 空载时任务完全挂起。

- **[✔] 代码规范整理（P2）**
  `ParserState_t` 移至文件级作用域（调试器可见枚举符号）；补充 `cmd` 字段注释；清理残留开发注释。


> 后续演进方向已移至 `goal.md` 统一管理。
