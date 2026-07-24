# ChassisController_t1 工程架构与数据流分析（Phase 1）

---

## 一、工程文件职能总览

```
App/
├── app_config.h            ── 协议常量、数据结构类型定义（全局类型中枢）
├── app_globals.h           ── 跨模块共享句柄的 extern 声明
├── app_includes.h          ── 统一总头文件（单点包含入口）
├── ring_buffer.h/c         ── 无锁环形缓冲区（ISR↔Task 数据桥）
├── app_system_state.h      ── 全局系统状态结构体（Phase 1 新增）
├── app_command.h           ── 命令消息结构体（Phase 1 新增）
└── app_task.h/c            ── 五个 FreeRTOS 任务的全部实现（Phase 1 新增一个任务）

Core/Src/
├── main.c                  ── HAL 初始化、外设启动、内核调度入口
└── freertos.c              ── FreeRTOS 对象（队列/信号量/互斥锁/任务）创建 + 入口函数

doc/
├── trae.md                  ── 架构与数据流文档（主设计文档）
├── claude.md                ── 代码审查优化归档（P0/P1/P2 问题记录）
├── fix1_UartToDma.md        ── UART TX 阻塞→DMA 改造专题记录
├── result.md                ── 项目目标完成状态
├── goal.md                  ── 演进规划与验证要点
├── goal2_ToMaster.md             ── 网关→下位主控架构演进设计讨论
├── plan2_ToMaster.md             ── 演进实施规划
├── plan/plan_ToMaster.md         ── 网关→下层主控演进计划（详细实施步骤）
├── chassis_model_analysis.md     ── 底盘构型分析与网关抽象层设计（两种底盘构型的数据处理原则）
├── Now_all.md                    ── 当前状态汇总（本文件）
└── DesignComparison_2/           ── 反馈设计审查与修复
    ├── Q2_comparison_t1.md  ── 反馈问题分析
    ├── D2fix1_plan.md       ── 修复计划
    └── D2result1.md         ── 修复结果与教训
```

---

## 二、分层架构

```
┌──────────────────────────────────────────────────────────┐
│                    应用逻辑层 (App/)                        │
│   ProtocolParser  CommandProcess  UartToCan  CanRxProcess │
│   Heartbeat       (SystemState)                           │
├──────────────────────────────────────────────────────────┤
│                 操作系统层 (FreeRTOS)                      │
│   Queue  Mutex  Semaphore  EventFlags  osDelay            │
├──────────────────────────────────────────────────────────┤
│                硬件抽象层 (STM32 HAL)                      │
│   USART1(DMA)  CAN  GPIO(PC13)  DMA                      │
└──────────────────────────────────────────────────────────┘
```

**Phase 1 架构变更**：从「纯 UART↔CAN 透传网关」演进为「**命令解释型网关**」——新增 `CommandProcess_Task` 解释 UART 指令语义，维护全局系统状态，状态帧不再打印到 UART 而是解码存入 `SystemState`。

---

## 三、各文件职能详解

### 3.1 `app_config.h` — 配置与类型定义

| 元素 | 类型 | 作用 |
|---|---|---|
| `FRAME_SOF 0xAA` | 宏 | 自定义协议帧头标志字节 |
| `CAN_RX_QUEUE_SIZE 16` | 宏 | CAN 接收队列容量 |
| `UART_TO_CAN_QUEUE_SIZE 16` | 宏 | UART→CAN 转发队列容量 |
| `CAN_TX_QUEUE_SIZE 8` | 宏 | **Phase 1 新增**：待发送 CAN 帧队列容量 |
| `Command_ID_t` | enum | 指令集：`CMD_NONE / SET_SPEED / GET_STATE / SET_MODE / ESTOP / FORWARD / REVERSE / STOP` |
| `App_UART_Message_t` | struct | UART 解析结果（id + cmd + len + data[8]），入 `uartToCanQueue` |
| `App_CAN_Message_t` | struct | CAN 收发报文（id + len + data[8]），用于 `canRxQueue` 和 `canTxQueue` |
| `ParserState_t` | enum | 状态机五个状态：WAIT_SOF / WAIT_CMD / WAIT_ID / WAIT_LEN / WAIT_DATA |

> `Cmd_ID_t` 枚举 Phase 1 新增了 `CMD_NONE = 0x00`、`CMD_FORWARD = 0x05`、`CMD_REVERSE = 0x06`、`CMD_STOP = 0x07`。

#### Phase 1 新增：CAN 协议常量（与 MCLM_t2 电机控制器协议对齐）

**CAN ID 组选择**（`CAN_ID_GROUP` 宏切换）：

| 组 | 转向电机 | 动力电机 |
|---|---|---|
| 1 (`0x125/0x126`) | CMD=`0x125`, STATUS=`0x325` | CMD=`0x126`, STATUS=`0x326` |
| 2 (`0x123/0x124`) **默认** | CMD=`0x123`, STATUS=`0x323` | CMD=`0x124`, STATUS=`0x324` |

**CAN 命令字节**：

| 宏 | 值 | 说明 |
|---|---|---|
| `CAN_CMD_SET_SPEED_T2` | `0x11` | 设置速度 |
| `CAN_CMD_STOP` | `0x08` | 停止 |
| `CAN_CMD_REVERSE` | `0x02` | 倒转 |

**全车命令 CAN ID**：

| 宏 | 值 | 说明 |
|---|---|---|
| `CAN_CMD_STOP_STDID` | `0x101` | 全车停止 |
| `CAN_CMD_TURN_STDID` | `0x102` | 全车转向 |
| `CAN_CMD_POWER_STDID` | `0x103` | 全车动力 |

**CAN 状态帧数据索引**：

| 索引 | 字段 | 类型 |
|---|---|---|
| 0-1 | `current_logic_speed` | int16, LE |
| 2-3 | `accumulated_ticks` | uint16, LE |
| 4-5 | `pwm_output` | int16, LE |
| 6 | `target_logic_speed` | int8 |
| 7 | `flags` | uint8 |

---

### 3.2 `app_globals.h` — 全局句柄声明

| 变量 | 类型 | 作用 |
|---|---|---|
| `hcan` | `CAN_HandleTypeDef` | HAL CAN 外设句柄 |
| `huart1` | `UART_HandleTypeDef` | USART1（调试/协议口）句柄 |
| `huart2` | `UART_HandleTypeDef` | USART2（备用）句柄 |
| `canRxQueueHandle` | `osMessageQueueId_t` | CAN ISR → CanRxProcess 任务的消息队列 |
| `uartToCanQueueHandle` | `osMessageQueueId_t` | ProtocolParser → CommandProcess 任务的消息队列 |
| `canTxQueueHandle` | `osMessageQueueId_t` | **Phase 1 新增**：CommandProcess → UartToCan 任务的 CAN 发送队列 |
| `uart1_tx_mutexHandle` | `osMutexId_t` | 保护 UART1 TX 通道，防多任务并发乱码 |
| `uart1_tx_semHandle` | `osSemaphoreId_t` | DMA 传输完成信号量（ISR 释放，任务等待） |
| `uart1_rx_eventHandle` | `osEventFlagsId_t` | ISR 通知 ProtocolParser 有新数据到来 |
| `UART1_RX_FLAG 0x01U` | 宏 | 事件标志位掩码 |
| `can_tx_done_cnt` | `volatile uint32_t` | CAN TX 完成计数器（ISR 递增，Task 读取），用于 CAN_TX OK 反馈 |
| `g_system_state` | `System_State_t` | **Phase 1 新增**：全局系统状态实例 |

---

### 3.3 `ring_buffer.h / ring_buffer.c` — 无锁环形缓冲区

> 设计精髓：利用 `uint8_t` 自然溢出实现无锁 SPSC（单写单读）缓冲。

| 元素 | 说明 |
|---|---|
| `UART_RX_BUFFER_SIZE 256` | 固定 256，`uint8_t` 溢出回绕 ≡ `% 256`，无需取模运算 |
| `volatile uint8_t head` | ISR 写，`volatile` 防止编译器寄存器缓存 |
| `volatile uint8_t tail` | 任务读，单字节操作在 Cortex-M3 天然原子 |
| `ring_buffer_init()` | `head = tail = 0`，清空缓冲区 |
| `ring_buffer_put()` | ISR 调用：`next_head == tail` 则满，返回 `false` 丢弃 |
| `ring_buffer_get()` | 任务调用：`head == tail` 则空，返回 `false` |

```
buffer[0..255]:  [ ... data bytes ... ]
                    ↑tail(读)    ↑head(写)
  ISR  向 head 写入，head++（uint8_t 自动回绕）
  Task 从 tail 读取，tail++（uint8_t 自动回绕）
  满判断：(head + 1) == tail
  空判断：head == tail
```

---

### 3.4 `app_task.h` — 任务接口声明

纯声明五个任务函数，供 `freertos.c`（CubeMX 生成）在创建任务时注册：

| 函数 | 绑定任务 | 优先级 | Phase 1 变化 |
|---|---|---|---|
| `ProtocolParser_Task_Run()` | `ProtocolParser_` | Normal1 | 不变 |
| `CommandProcess_Task_Run()` | `CommandProcess_Ta` | Normal1 | **新增** |
| `UartToCan_Task_Run()` | `UartToCan_Ta` | Normal | **重构**：从消费 `uartToCanQueue` 改为消费 `canTxQueue` |
| `CanRxProcess_Task_Run()` | `CanRxProcess_Ta` | Normal | **重构**：解码状态帧 → SystemState，不再打印到 UART |
| `Heartbeat_Task_Run()` | `Heartbeat_Ta` | Low | 不变 |

> **优先级说明**：`ProtocolParser_` 和 `CommandProcess_Ta` 同为 Normal1（高于 Normal），确保 UART 帧解析和命令处理优先于 CAN 发送/接收反馈。

---

### 3.5 `app_task.c` — 核心任务实现

#### 静态辅助函数：`uart1_send(buf, len)` — DMA 发送封装（带超时保护）

```
调用方
  │  osMutexAcquire(uart1_tx_mutexHandle)     ← 独占 TX 通道
  │  memcpy → uart1_tx_dma_buf[128]            ← 拷贝到静态缓冲
  │  HAL_UART_Transmit_DMA()                   ← 启动 DMA
  │  └─ 失败 → osMutexRelease → return         ← 防永久阻塞
  │  osSemaphoreAcquire(timeout=1000ms)        ← 等待 TxCplt 回调
  │  └─ 超时 → osMutexRelease → return         ← 防中断丢失死锁
  ↓
  osMutexRelease(uart1_tx_mutexHandle)         ← 释放通道
```

关键变量：

| 变量 | 说明 |
|---|---|
| `uart1_tx_dma_buf[128]` | `static` 静态数组，生命周期贯穿整个 DMA 传输 |
| `UART1_TX_DMA_BUF_SIZE 128` | 最大单次发送长度限制 |
| `uartToCanQueue_drop_cnt` | `static uint32_t`，ProtocolParser 入队失败时递增 |
| `canTxQueue_drop_cnt` | **Phase 1 新增** `static uint32_t`，CommandProcess 入 `canTxQueue` 失败时递增 |
| `UART1_TX_SEM_TIMEOUT_MS 1000` | 宏，`osSemaphoreAcquire` 超时值 |

> **错误保护**：`HAL_UART_Transmit_DMA` 失败时立即释放 mutex 返回，避免永不触发 TxCplt 导致的死锁。`osSemaphoreAcquire` 带 1000ms 超时，超时后释放 mutex，防止中断丢失引发的永久阻塞。

---

#### 任务①：`ProtocolParser_Task_Run()` — 协议解析（最高优先级任务）

**Phase 1 状态：不变**。状态机逻辑与旧版相同，但输出队列改为 `uartToCanQueue`，由 `CommandProcess_Task` 消费。

状态机驱动，局部关键变量：

| 变量 | 类型 | 作用 |
|---|---|---|
| `state` | `ParserState_t` | 当前状态机状态 |
| `current_msg` | `App_UART_Message_t` | 正在组装中的帧 |
| `byte_received` | `uint8_t` | 从环形缓冲区取出的单字节 |
| `id_byte_count` | `uint8_t` | 已接收的 CAN_ID 字节数（累计到 4） |
| `data_idx` | `uint8_t` | 已接收的数据负载字节数 |

状态机逻辑（每次取出 1 字节驱动）：

```
STATE_WAIT_SOF  → 检测 0xAA          → STATE_WAIT_CMD
STATE_WAIT_CMD  → 存 cmd             → STATE_WAIT_ID
STATE_WAIT_ID   → 小端拼接 4 字节 id  → STATE_WAIT_LEN
STATE_WAIT_LEN  → 检查 len ≤ 8       → STATE_WAIT_DATA（len==0 直接入队）
STATE_WAIT_DATA → 填 data[]          → 满足 len 后 osMessageQueuePut（失败时递增 uartToCanQueue_drop_cnt）→ STATE_WAIT_SOF

任意状态收到 0xAA → 视为新帧开始，重置并跳回 STATE_WAIT_CMD（容错）
```

> **阻塞机制**：缓冲区为空时调用 `osEventFlagsWait`（10 ms 超时），ISR 写入后立即 `osEventFlagsSet` 唤醒，近零延迟。

---

#### 任务②：`CommandProcess_Task_Run()` — 命令处理（Phase 1 新增，Normal1 优先级）

**核心变更**：Phase 1 将命令解释逻辑从 `UartToCan_Task` 中分离出来，新增此任务作为架构中枢。

```
uartToCanQueue  ──→  CommandProcess_Task  ──→  canTxQueue  ──→  UartToCan_Task  ──→  CAN 总线
                          │
                          ↓
                    SystemState 更新
```

| 局部变量 | 作用 |
|---|---|
| `uart_msg`（`App_UART_Message_t`） | 从 `uartToCanQueueHandle` 取出的 UART 解析消息 |
| `can_tx`（`App_CAN_Message_t`） | 构建待发送 CAN 帧，入 `canTxQueue` |
| `dbg_buffer[128]` | `sprintf` 诊断字符串暂存 |

**命令解释逻辑**：

| UART 命令 `cmd` | 动作 | CAN 转发 |
|---|---|---|
| `CMD_SET_SPEED (0x01)` | 根据 `uart_msg.id` 映射到电机索引（转向/动力），更新 `SystemState.motor[midx].target_speed` | 构建 CAN 帧，`data[0]` 替换为 `CAN_CMD_SET_SPEED_T2 (0x11)`，入 `canTxQueue` |
| `CMD_ESTOP (0x04)` | 置位 `g_system_state.flag.estop = 1` | 发送三帧：全车停止 (`0x101`, `data[0]=0x08`) + 转向电机 + 动力电机，UART 打印 `ESTOP TRIGGERED` |
| `CMD_GET_STATE (0x02)` | 从 `SystemState` 读取电机状态 | **不转发 CAN**，UART 回传 `STATE_RSP \| Motor%d current=%d target=%d ...` |
| `CMD_SET_MODE (0x03)` | 更新 `g_system_state.flag.mode = data[0]` | 原样透传 |
| 其他（default） | — | 原样透传（保留网关兼容性） |

> **命令字节替换**：`CMD_SET_SPEED` 将 `data[0]` 替换为 `0x11`（`CAN_CMD_SET_SPEED_T2`），因为 UART 帧的 cmd 值与 CAN 命令码不兼容，不能在 CAN 总线上直接使用 UART 的 cmd 字节。

---

#### 任务③：`UartToCan_Task_Run()` — CAN 发送器（Phase 1 重构）

**Phase 1 重构**：不再直接消费 `uartToCanQueue`，改为从 `canTxQueue` 取帧并发送。从「协议转换器」变为「纯 CAN 发送器」。

| 局部变量 | 作用 |
|---|---|
| `can_msg`（`App_CAN_Message_t`） | 从 `canTxQueueHandle` 取出的待发送 CAN 帧 |
| `tx_header`（`CAN_TxHeaderTypeDef`） | HAL CAN 发送帧头（IDE / RTR / DLC / ID） |
| `tx_mailbox`（`uint32_t`） | HAL 分配的 CAN 发送邮箱编号 |
| `dbg_buffer[128]` | `sprintf` 诊断字符串暂存 |

帧类型自动判断：

```c
if (can_msg.id > 0x7FF)   // 扩展帧 29-bit
    tx_header.IDE = CAN_ID_EXT;  tx_header.ExtId = can_msg.id;
else                        // 标准帧 11-bit
    tx_header.IDE = CAN_ID_STD;  tx_header.StdId = (uint16_t)can_msg.id;
```

CAN 发送后通过 UART 反馈结果（**Phase 1 简化：仅打印成功路径**）：

```
CAN_TX OK | ID=0x102 DLC=2 Done=15    // 发送成功，Done 为历史累计完成数
```

`Done` 由 `stm32f1xx_it.c` 中的 `HAL_CAN_TxMailboxNCompleteCallback` 在 ISR 中递增，记录已从总线成功发出的帧数。

---

#### 任务④：`CanRxProcess_Task_Run()` — CAN 接收处理（Phase 1 重构）

**Phase 1 重构**：从「CAN→UART 透明输出」变为「**CAN 状态帧解码器 → SystemState 更新**」：

```
[CAN 总线]
    │  CAN RxISR → osMessageQueuePut(canRxQueue)
    ▼
canRxQueue [容量 16 × App_CAN_Message_t]
    │
    ▼  CanRxProcess_Task_Run（Normal 优先级）
    │  can_id_to_motor_idx() 判定帧来源
    │  ├─ 电机状态帧 (0x323 / 0x324)：
    │  │     decode_motor_status() 解码 8 字节状态帧
    │  │     → 更新 g_system_state.motor[midx]
    │  └─ 其他帧：忽略（UART 打印已关闭，防 MCLM 50ms 持续状态帧淹没 UART）
    ▼
SystemState 更新

[UART 打印 — 暂取消]
  原因：MCLM 每 50ms 持续发状态帧 → 不停调用 uart1_send
       → UART TX 互斥锁激烈竞争 → 阻塞 CommandProcess/UartToCan 的诊断打印
  恢复：取消 CanRxProcess_Task_Run 中注释代码即可
```

辅助函数：

| 函数 | 作用 |
|---|---|
| `can_id_to_motor_idx(stdId)` | CAN 状态反馈 ID → 电机索引（`0x323`→转向, `0x324`→动力, 未知→`0xFF`） |
| `decode_motor_status(data, out)` | 解码 8 字节 MCLM_t2 状态帧 → `Motor_State_t`（current_speed / pwm_output / target_speed / flags + timestamp） |

---

#### 任务⑤：`Heartbeat_Task_Run()` — 心跳

```c
HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);  // 翻转板载 LED
osDelay(300);                             // 300 ms 周期
```

> Phase 1 不变。系统存活指示：LED 停止闪烁 = 任务死锁或崩溃。

---

### 3.6 `app_system_state.h` — 系统状态结构体（Phase 1 新增）

```c
// 电机状态（每个电机一个）
typedef struct {
    int16_t  current_speed;      // 当前逻辑速度 (-100..100)
    int16_t  target_speed;       // 目标逻辑速度
    int16_t  pwm_output;         // PWM 输出值
    uint8_t  flags;              // MOTOR_FLAG_STALL / MOTOR_FLAG_SATURATED
    uint32_t last_update_tick;   // 最后更新时刻 (ms)
} Motor_State_t;

// 系统标志
typedef struct {
    uint8_t  mode;               // 系统模式
    uint8_t  estop;              // 紧急停止标志 (1=已触发)
    uint32_t uptime_ms;          // 系统运行时间 (ms)
} System_Flag_t;

// 全局系统状态（预留 IMU 扩展）
typedef struct {
    IMU_State_t    imu;          // IMU 状态（预留）
    Motor_State_t  motor[8];     // 最多 8 个电机
    System_Flag_t  flag;
} System_State_t;
```

---

### 3.7 `app_command.h` — 命令消息结构体（Phase 1 新增）

```c
typedef struct {
    Command_ID_t type;           // 命令类型（来自 app_config.h）
    int16_t  value;              // 参数值（如速度值）
    uint8_t  motor_id;           // 目标电机 ID，0xFF=广播
    uint32_t can_id;             // 关联的 CAN ID（用于回传/日志）
    uint8_t  raw_data[8];        // 原始数据（透传用）
    uint8_t  raw_len;            // 原始数据长度
} App_CommandMsg_t;
```

> 当前代码尚未使用 `App_CommandMsg_t`，为预留扩展结构。

---

### 3.8 `freertos.c` — 内核对象创建（Phase 1 更新）

**新增队列**：

| 队列 | 容量 | 元素类型 | 作用 |
|---|---|---|---|
| `canTxQueue` | 16 | `App_CAN_Message_t` | CommandProcess → UartToCan 待发送 CAN 帧 |

**新增任务**：

| 任务 | 优先级 | 栈大小 (words) | 入口 |
|---|---|---|---|
| `CommandProcess_Ta` | Normal1 | 256 | `Start_CommandProcess → CommandProcess_Task_Run` |

---

## 四、完整数据流图

### 4.1 上行：UART → CAN（Phase 1 重构）

```
[PC 串口工具]
    │  自定义帧: AA | CMD | ID(4B, LE) | DLC | Data
    ▼
USART1 外设（中断接收）
    │
    ▼  HAL_UART_RxCpltCallback（ISR 上下文）
    │  ├─ ring_buffer_put(&uart1_rx_buffer, byte)        写 head
    │  └─ osEventFlagsSet(uart1_rx_eventHandle, 0x01)    唤醒解析任务
    ▼
uart1_rx_buffer [RingBuffer_t, 256B]  ← ISR 写 head / 任务读 tail，无锁
    │
    ▼  ProtocolParser_Task_Run（osPriorityNormal1 优先级）
    │  ring_buffer_get() 逐字节取出
    │  状态机解析 → 组装 App_UART_Message_t
    │  osMessageQueuePut(uartToCanQueueHandle, &current_msg)
    ▼
uartToCanQueue [容量 16 × App_UART_Message_t]
    │
    ▼  CommandProcess_Task_Run（Normal1 优先级）  ★ Phase 1 新增
    │  根据 cmd 字段解释语义：
    │  ├─ CMD_SET_SPEED → 更新 SystemState.target_speed, data[0]=0x11
    │  ├─ CMD_ESTOP     → 置位 estop 标志，构建三帧停止帧
    │  ├─ CMD_GET_STATE → 读取 SystemState，UART 回传
    │  ├─ CMD_SET_MODE  → 更新 mode，透传
    │  └─ default       → 原样透传
    │  osMessageQueuePut(canTxQueueHandle, &can_tx)
    ▼
canTxQueue [容量 16 × App_CAN_Message_t]  ★ Phase 1 新增队列
    │
    ▼  UartToCan_Task_Run（Normal 优先级）  ★ 重构：消费 canTxQueue
    │  osMessageQueueGet() 阻塞等待
    │  判断帧类型（> 0x7FF → 扩展帧），填充 tx_header
    │  HAL_CAN_AddTxMessage(&hcan, &tx_header, can_msg.data, &tx_mailbox)
    │  └─ sprintf("CAN_TX OK | ID=... Done=%lu", can_tx_done_cnt)
    │  uart1_send() 打印到 PC
    ▼
[CAN 总线]
    │
    ▼  CAN TX 完成 → TSR.RQCPx=1, TXOKx=1 → 硬件中断
    │  USB_HP_CAN1_TX_IRQHandler → HAL_CAN_IRQHandler
    │  └─ HAL_CAN_TxMailboxNCompleteCallback → can_tx_done_cnt++
    ▼
 (Done 计数器递增，供下次 CAN_TX OK 打印)
```

### 4.2 下行：CAN → SystemState（Phase 1 重构）

```
[CAN 总线]
    │
    ▼  USB_LP_CAN1_RX0_IRQHandler（ISR 上下文）
    │  封装 App_CAN_Message_t（id / len / data）
    │  osMessageQueuePut(canRxQueueHandle, &msg)（失败时递增 canRxQueue_drop_cnt）
    ▼
canRxQueue [容量 16 × App_CAN_Message_t]
    │
    ▼  CanRxProcess_Task_Run（Normal 优先级）  ★ 重构：解码状态帧
    │  can_id_to_motor_idx() 判定帧来源
    │  ├─ 电机状态帧 (0x323/0x324) → decode_motor_status()
    │  │   → 更新 g_system_state.motor[midx]
    │  │      (current_speed, pwm_output, target_speed, flags, timestamp)
    │  └─ 其他帧 → 忽略（UART 打印已禁用，防淹没）
    ▼
  SystemState 更新
```

---

## 五、任务间通信与同步机制

### 5.1 同步对象总表

| 同步对象 | 方向 | 生产者 | 消费者 | 解决问题 |
|---|---|---|---|---|
| `uart1_rx_buffer`（RingBuffer） | ISR→Task | UART RxISR | ProtocolParser | 字节接收缓冲，无锁 SPSC |
| `uart1_rx_eventHandle`（EventFlag） | ISR→Task | UART RxISR | ProtocolParser | 事件驱动唤醒，零延迟 |
| `uartToCanQueue`（Queue×16） | Task→Task | ProtocolParser | CommandProcess | 帧级解耦，背压保护 |
| `canTxQueue`（Queue×16） | Task→Task | CommandProcess | UartToCan | **Phase 1 新增**：命令解释与 CAN 发送解耦 |
| `canRxQueue`（Queue×16） | ISR→Task | CAN RxISR | CanRxProcess | CAN 报文缓冲，ISR 快速返回 |
| `uart1_tx_mutexHandle`（Mutex） | 多→单 | — | `uart1_send()` | 防两个任务同时操作 UART1 TX |
| `uart1_tx_semHandle`（Semaphore） | ISR→Task | TxCplt 回调 | `uart1_send()` | DMA 完成通知，任务让出 CPU |
| `can_tx_done_cnt`（`volatile uint32_t`） | ISR→Task | CAN TX ISR | UartToCan_Task | CAN 总线发送完成确认 |

### 5.2 Phase 1 架构演进拓扑

```
                    ┌──────────────────┐
                    │  SystemState     │  ← 全局状态中枢
                    │  (g_system_state)│
                    └────────┬─────────┘
                             │ 读写
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│ ProtocolParser  │  │CommandProcess│  │ CanRxProcess │
│ (UART 解析)      │  │ (命令解释)    │  │ (状态解码)    │
└────────┬────────┘  └──────┬───────┘  └──────┬───────┘
         │  uartToCanQueue  │  canTxQueue     │  canRxQueue
         └──────────────────┴──────┬──────────┘
                                   ▼
                          ┌─────────────────┐
                          │   UartToCan     │
                          │  (CAN 发送器)    │
                          └────────┬────────┘
                                   │ CAN 总线
                                   ▼
```

---

## 六、CAN 命令层分析：从透传网关到命令解释

### 6.1 Phase 1 架构转变

| 维度 | 旧版（纯透传网关） | Phase 1（命令解释型网关） |
|---|---|---|
| 数据路径 | `UART → uartToCanQueue → UartToCan → CAN` | `UART → uartToCanQueue → CommandProcess → canTxQueue → UartToCan → CAN` |
| cmd 字段 | 仅存储后丢弃 | `CommandProcess` 根据 cmd 解释语义 |
| CAN 命令字节 | 原样透传（data[0] 为用户填入的值） | `CMD_SET_SPEED` 时替换 data[0] = `0x11` |
| CAN 接收 | 格式化打印到 UART | 解码状态帧 → SystemState（UART 打印暂关闭） |
| 系统状态 | 无 | `System_State_t` 全局实例，task 共享 |
| 命令集 | 4 个 cmd 枚举 | 8 个 cmd 枚举 + CAN 协议常量 |

### 6.2 当前代码中实际存在的命令

| UART 命令 | 值 | 处理位置 | 行为 |
|---|---|---|---|
| `CMD_NONE` | `0x00` | `CommandProcess` default 分支 | 透传到 CAN |
| `CMD_SET_SPEED` | `0x01` | `CommandProcess` 显式 case | 更新 `SystemState.target_speed`，替换 data[0]=0x11 后转发 CAN |
| `CMD_GET_STATE` | `0x02` | `CommandProcess` 显式 case | 读取 SystemState，UART 回传状态字符串 |
| `CMD_SET_MODE` | `0x03` | `CommandProcess` 显式 case | 更新 `flag.mode`，透传 CAN |
| `CMD_ESTOP` | `0x04` | `CommandProcess` 显式 case | 置位 `flag.estop=1`，发送三帧停止 CAN 帧 |
| `CMD_FORWARD` | `0x05` | `CommandProcess` default 分支 | 透传到 CAN |
| `CMD_REVERSE` | `0x06` | `CommandProcess` default 分支 | 透传到 CAN |
| `CMD_STOP` | `0x07` | `CommandProcess` default 分支 | 透传到 CAN |

### 6.3 CAN 协议常量（与 MCLM_t2 协议对齐）

| 符号 | 值 | 用途 |
|---|---|---|
| `CAN_CMD_SET_SPEED_T2` | `0x11` | CAN 调速命令字节（CommandProcess 在 SET_SPEED 时替换 data[0] 为此值） |
| `CAN_CMD_STOP` | `0x08` | CAN 停止命令字节（ESTOP 时使用） |
| `CAN_CMD_REVERSE` | `0x02` | CAN 倒转命令字节（预留） |
| `CAN_CMD_STOP_STDID` | `0x101` | 全车停止 CAN ID |
| `CAN_CMD_TURN_STDID` | `0x102` | 全车转向 CAN ID |
| `CAN_CMD_POWER_STDID` | `0x103` | 全车动力 CAN ID |

### 6.4 全车停止指令帧分析（举例）

用户查询的帧序列 `AA 01 01 01 00 00 02 11 00`，按协议拆解：

```
位置:    [0]   [1]   [2] [3] [4] [5]   [6]   [7]   [8]
值:     0xAA  0x01  0x01 0x01 0x00 0x00  0x02  0x11  0x00
字段:    SOF   cmd   ──── CAN ID (LE) ────  DLC   ── data ──
解析:          0x01  0x00000101          0x02  0x11  0x00
              (SET_SPEED)  (CAN ID)      (长度) (替换为0x11) (速度=0)
```

| 字段 | 值 | 含义 |
|---|---|---|
| SOF | `0xAA` | 帧头 |
| cmd | `0x01` | `CMD_SET_SPEED` → CommandProcess 会替换 `data[0]` 为 `0x11` |
| CAN ID | `0x00000101` | 目标电机 CAN ID（全车停止 ID `0x101`） |
| DLC | `0x02` | 2 字节数据 |
| data[0] | `0x11` | 被 CommandProcess 替换为 `CAN_CMD_SET_SPEED_T2`（调速命令） |
| data[1] | `0x00` | 速度值 = 0（停止） |

> **Phase 1 行为**：`CommandProcess_Task` 收到此帧后，根据 `cmd = CMD_SET_SPEED` 进入显式处理分支，将 `data[0]` 从用户值替换为 `0x11`，然后入 `canTxQueue` 发送到 CAN 总线。

### 6.5 命令解释关键代码

`CommandProcess_Task_Run`（[app_task.c:359-488](App/app_task.c#L359)）中的命令分发：

```c
switch (uart_msg.cmd)
{
    case CMD_SET_SPEED:
        // 映射电机索引 → 更新 SystemState → 替换 data[0]=0x11 → 入 canTxQueue
        break;
    case CMD_ESTOP:
        // flag.estop=1 → 三帧停止帧 → 入 canTxQueue
        break;
    case CMD_GET_STATE:
        // 读取 SystemState → sprintf → uart1_send（不回 CAN）
        break;
    case CMD_SET_MODE:
        // flag.mode = data[0] → 原样透传
        break;
    default:
        // 原样透传（保留网关兼容性）
        break;
}
```

---

## 七、关键设计决策

### 7.1 为什么新增 `canTxQueue` 而不是直接让 CommandProcess 调用 HAL？

- **解耦职责**：CommandProcess 负责命令解释和 SystemState 维护，UartToCan 负责 CAN 硬件操作
- **背压保护**：CAN 发送失败时（邮箱满），队列可缓冲待发送帧，不阻塞命令处理
- **可测试性**：队列内容可被诊断任务监控

### 7.2 为什么 CanRxProcess 关闭了 UART 打印？

MCLM 电机控制器每 50ms 发送一次状态帧，持续不断。如果 CanRxProcess 每收到一帧就调用 `uart1_send`，会导致：
- UART TX 互斥锁被 CanRxProcess 频繁持有，CommandProcess 和 UartToCan 的诊断打印被阻塞
- UART 输出被状态帧淹没，无法阅读有效信息

解决方案：状态帧解码存入 SystemState，UART 打印改为限频输出（恢复时每 950ms 打印一次）。

### 7.3 为什么 CMD_SET_SPEED 需要替换 data[0]？

UART 帧的 cmd 字段（取值 0x01~0x07）与 CAN 命令字节（取值 0x11、0x08 等）是两个不同的协议空间。将 UART 的 cmd 值直接透传到 CAN 总线会导致下游电机控制器无法识别，因此 CommandProcess 在 SET_SPEED 时将 data[0] 替换为 `CAN_CMD_SET_SPEED_T2 (0x11)`。

---

## 八、栈与资源使用

| 任务 | 栈大小 (words) | 优先级 | 备注 |
|---|---|---|---|
| `UartToCan_Ta` | 512 | Normal | CAN 发送 + sprintf 格式化，栈需求较大 |
| `CanRxProcess_Ta` | 512 | Normal | CAN 接收 + 状态解码 |
| `Heartbeat_Ta` | 64 | Low | 仅翻转 GPIO |
| `ProtocolParser_` | 256 | Normal1 | 状态机解析 |
| `CommandProcess_Ta` | 256 | Normal1 | 命令解释 + sprintf 格式化 |

---
