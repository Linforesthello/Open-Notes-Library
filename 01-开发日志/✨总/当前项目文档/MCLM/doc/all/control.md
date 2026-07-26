# 电机控制数据流文档

## 系统概述

本系统运行于 STM32F103C8T6，使用 FreeRTOS 多任务架构。电机控制采用**闭环 PID**，编码器反馈，支持 CAN 和 UART 双路命令输入，通过条件编译在 TB6612 / AT8236 驱动器之间切换。

---

## 一、任务总览

| 任务名 | 实现文件 | 优先级 | 周期 | 职责 |
|---|---|---|---|---|
| `Encoder_Ta` | `encoder_task.c` | `High` | 10 ms | TIM2 正交编码器读取，更新 `g_motors[0]` 速度 |
| `MotorControl_Ta` | `tb6612_DC_task.c` | `High` | 10 ms | PID 计算，输出 TIM3 PWM |
| `Command_Ta` | `command_task.c` | `BelowNormal` | 阻塞 | 命令路由：日志控制 / 状态查询 / 转发电机命令 |
| `Ack_Ta` | `Ack_task.c` | `Low` | 阻塞 | 从 `AckQueueHandle` 取 ACK，UART 打印回复 |
| `Logger_Ta` | `logger_task.c` | `Low` | 事件驱动 | 编码器更新后打印实时数据流（DMA） |
| `Heartbeat_Ta` | `heartbeat_task.c` | `Low` | 200 ms | PC13 心跳灯翻转 |

---

## 二、队列与同步原语

| 名称 | 类型 | 深度 | 消息类型 | 生产者 → 消费者 |
|---|---|---|---|---|
| `CommandQueueHandle` | Queue | 72 | `CommandMsg_t` | CAN 中断 / UART 解析 → `Command_Task` |
| `MotorQueueHandle` | Queue | 72 | `CommandMsg_t` | `Command_Task` → `TB6612_DC_Task` |
| `AckQueueHandle` | Queue | 64 | `AckMsg_t` | `Command_Task` → `Ack_Task` |
| `motor_mutexHandle` | Mutex | — | — | 保护 `g_motors[]` 的并发读写 |
| `uart_rx_semaphoreHandle` | Binary Sem | — | — | UART 接收同步 |
| `can_rx_semaphoreHandle` | Binary Sem | — | — | CAN 接收同步 |

---

## 三、核心数据结构

定义于 `App/config/app_globals.h`：

```c
typedef struct {
    TB6612_Motor_t hardware;      // 硬件驱动句柄（引脚/定时器/限幅等）
    PID_Controller pid;           // PID 控制器实例（含 setpoint）

    float    target_logic_speed;  // 当前 PID 目标速度（-100 ~ 100）
    float    current_logic_speed; // 编码器测量值换算后的逻辑速度
    int32_t  current_ticks;       // 当前 10 ms 内编码器 tick 增量
    int16_t  pwm_output;          // 当前 PWM 输出值（0 ~ 99）
} Motor_t;

extern Motor_t          g_motors[MOTOR_COUNT];  // 电机数组，MOTOR_COUNT = 1
extern volatile uint8_t g_logger_enabled;       // 日志开关（CAN 命令控制）
extern uint8_t          tx_buf[64];             // UART DMA 发送缓冲区
```

---

## 四、电机控制完整数据流

```
════════════════════════════════ 外部输入 ════════════════════════════════

  UART1 (USART1)                               CAN 总线
  字符命令: "S50", "F", "R", "X"...             帧: StdId + Data[8]
       │                                              │
       │ UART RX 中断 → command.c                    │ CAN RX FIFO0 中断
       │ Command_ParseUART()                          │ can.c: HAL_CAN_RxFifo0MsgPendingCallback()
       │ → CommandMsg_t                               │ → Command_ParseCAN()
       │                                              │ → CommandMsg_t
       └────────────────────┬─────────────────────────┘
                            │
                            ▼
               ┌─────────────────────────┐
               │     CommandQueueHandle  │
               │    depth=72, 10ms 不阻塞│
               └────────────┬────────────┘
                            │ osWaitForever
                            ▼
               ┌────────────────────────────────┐
               │         Command_Task           │  BelowNormal
               │                                │
               │  ① CMD_LOG_START/STOP          │
               │     → g_logger_enabled = 1/0   │
               │     → CAN TX (0x325) + ACK     │
               │                                │
               │  ② CMD_QUERY_STATUS            │
               │     读 g_motors（加锁）         │
               │     → CAN TX (0x325) + ACK     │
               │                                │
               │  ③ CMD_LIST_STATUS             │
               │     → ACK (UART 打印)          │
               │                                │
               │  ④ is_motor_cmd() == true      │
               │     → AckQueueHandle           │
               │     → MotorQueueHandle         │
               └────────────┬───────────────────┘
                 ┌──────────┘
                 │
       ┌─────────▼──────────┐       ┌─────────────────────┐
       │    AckQueueHandle  │       │   MotorQueueHandle   │
       │   depth=64         │       │   depth=72           │
       └─────────┬──────────┘       └──────────┬───────────┘
                 │ osWaitForever                │ 非阻塞 (timeout=0)
                 ▼                              ▼
       ┌─────────────────┐     ┌────────────────────────────────────────┐
       │    Ack_Task     │     │           TB6612_DC_Task               │  High
       │    Low 优先级   │     │                                        │  10 ms 周期
       │ UART 打印 ACK   │     │  Step1: 取命令（非阻塞）               │
       └─────────────────┘     │    CMD_SET_SPEED / CAN_CMD_SET_SPEED  │
                               │      → 若方向翻转 → PID_Reset()       │
                               │      → pid.setpoint = (float)value    │
                               │    CMD_STOP / CAN_CMD_STOP            │
                               │      → pid.setpoint = 0              │
                               │      → PID_Reset()                   │
                               │                                        │
                               │  Step2: PID 计算（每 10 ms 必执行）   │
                               │    加锁读 g_motors[0].current_logic_speed
                               │    output = PID_Compute(&pid, speed)  │
                               │    TB6612_Motor_SetSpeed(output)      │
                               │    motor->pwm_output = hardware.pwm   │
                               └────────────────┬───────────────────────┘
                                                │
                         ┌──────────────────────▼──────────────────────┐
                         │         TB6612 驱动层（motor_DC_tb6612.c）   │
                         │                                              │
                         │  1. 限幅（-99 ~ 99）                        │
                         │  2. 极性修正（Polarity=1 → 取反）           │
                         │  3. 死区处理（|speed| < 10 → 钳到 10）      │
                         │  4. 线性映射 pwmVal = |speed| × 99 / 100   │
                         │  5. 方向引脚 PB0(IN1) / PB1(IN2)           │
                         │  6. TIM3 CH1 → __HAL_TIM_SET_COMPARE()     │
                         └──────────────────────┬──────────────────────┘
                                                │
                         ┌──────────────────────▼──────────────────────┐
                         │           硬件输出                           │
                         │   PA6  → TIM3 CH1 PWM（10 kHz）            │
                         │   PB0  → IN1 方向控制                       │
                         │   PB1  → IN2 方向控制                       │
                         │   PB10 → EN  使能                           │
                         └──────────────────────┬──────────────────────┘
                                                │
                                               电机
                                                │
                         ┌──────────────────────▼──────────────────────┐
                         │           Encoder_Task                       │  High
                         │   TIM2 正交编码器（PA0 CH1 / PA1 CH2）      │  10 ms 周期
                         │                                              │
                         │   diff = now_cnt - last_cnt                  │
                         │   加锁写 g_motors[0].current_ticks = diff   │
                         │   加锁写 current_logic_speed                 │
                         │            = ticks_to_logic(diff)           │
                         │            = diff × 100 / 80（线性映射）    │
                         │   osThreadFlagsSet(Logger_TaHandle, 0x01)   │
                         └──────────────────────┬──────────────────────┘
                                                │ 线程标志 0x01
                                                ▼
                         ┌──────────────────────────────────────────────┐
                         │           Logger_Task                        │  Low
                         │   osThreadFlagsWait(0x01, osWaitForever)    │
                         │   若 g_logger_enabled == 0 → 跳过           │
                         │   加锁读 g_motors[0]（timeout=10 ms）       │
                         │   snprintf → tx_buf                         │
                         │   HAL_UART_Transmit_DMA(&huart1, ...)       │
                         └──────────────────────────────────────────────┘
```

---

## 五、PID 控制器详解

文件：`App/modules/pid.c`

### 5.1 结构体

```c
typedef struct {
    float Kp, Ki, Kd;
    float setpoint;                   // 目标速度（-100 ~ 100）
    float integral;                   // 积分累计
    float prev_error;                 // 上次误差
    float prev_value;                 // 上次测量值
    float integral_limit;             // 积分限幅
    float output_limit;               // 输出限幅（100.0）
    float last_derivative;            // 滤波后的微分
    float Ts;                         // 采样周期（0.01 s）
    float derivative_filter_alpha;    // 微分低通滤波系数（0.3）
} PID_Controller;
```

### 5.2 计算流程

```
error = setpoint - current_logic_speed

── 条件积分 Anti-Windup ──────────────────────────────
pre_output = Kp × error + Ki × integral
若 pre_output 饱和 且 error 与饱和方向同向
    → 冻结积分（不更新 integral）
否则
    → integral += error × Ts
    → 积分硬限幅 ±integral_limit

── 微分项（低通滤波）────────────────────────────────
raw_d = (error - prev_error) / Ts
last_d = (1 - alpha) × last_d + alpha × raw_d    ← IIR 低通
d_term = Kd × last_d

── 合并输出并限幅 ─────────────────────────────────────
output = Kp × error + Ki × integral + d_term
output = clamp(output, -output_limit, +output_limit)
```

### 5.3 当前参数（TB6612 驱动）

| 参数 | 值 | 说明 |
|---|---|---|
| `Kp` | 0.4584 | 比例增益 |
| `Ki` | 17.66 | 积分增益（较大，靠积分消稳态误差） |
| `Kd` | 0.0025 | 微分增益 |
| `integral_limit` | 5.66 | Ki × 5.66 ≈ 100（精确匹配 output_limit） |
| `output_limit` | 100.0 | 对应逻辑速度满量程 |
| `Ts` | 0.01 s | 10 ms 控制周期 |
| `derivative_filter_alpha` | 0.3 | 微分低通系数 |

---

## 六、速度换算链路

```
编码器 tick（每 10 ms 增量）
    │  ticks_to_logic(diff)
    │  = diff × SPEED_LOGIC_MAX / SPEED_TICKS_MAX
    │  = diff × 100 / 80
    ▼
逻辑速度（-100 ~ +100）    ← PID 的输入和 setpoint 单位
    │  PID_Compute() 输出
    ▼
PID 输出（float，-100 ~ +100）
    │  TB6612_Motor_SetSpeed(int16_t output)
    │  → 限幅、极性修正、死区处理
    │  → pwmVal = |output| × PWM_MAX / MAX_SPEED_LOGIC
    │           = |output| × 99 / 100
    ▼
TIM3 CCR1（0 ~ 99）        ← __HAL_TIM_SET_COMPARE()
    ▼
PWM 占空比（0% ~ 99%，10 kHz）
```

**参数定义（`app_config.h`）：**

| 宏 | 值 | 含义 |
|---|---|---|
| `SPEED_TICKS_MAX` | 80 | 10 ms 内最大编码器计数（对应满速） |
| `SPEED_LOGIC_MAX` | 100 | 逻辑速度满量程 |
| `PWM_MAX` | 99 | TIM3 ARR = 99，对应 100% 占空比 |
| `MOTOR1_DEAD_ZONE` | 10 | 死区，低于此值不输出（防止低速抖动） |

---

## 七、硬件资源汇总

| 资源 | 配置 | 用途 |
|---|---|---|
| TIM2 | 正交编码器模式，PA0/PA1，Period=65535 | 速度反馈 |
| TIM3 CH1 | PWM，PA6，10 kHz，ARR=99 | 电机 PWM 输出 |
| PB0 / PB1 | GPIO 输出 | TB6612 IN1/IN2 方向控制 |
| PB10 | GPIO 输出 | TB6612 EN 使能 |
| USART1 | DMA 发送，中断接收 | 调试日志 + UART 命令 |
| CAN1 | 500 kbps（Prescaler=4），PA11/PA12 | 远程命令 + 状态反馈 |
| PC13 | GPIO 输出 | 心跳灯 |

---

## 八、关键设计说明

| 设计点 | 实现方式 |
|---|---|
| **多驱动支持** | `ACTIVE_MOTOR_DRIVER` 宏 + `#if/#elif` 条件编译，运行时零开销 |
| **任务解耦** | 命令 → `CommandQueue` → `Command_Task` → `MotorQueue` → `Motor_Task`，各层职责单一 |
| **共享状态保护** | `motor_mutexHandle` 保护 `g_motors[]`，编码器任务和控制任务均先获锁再读写 |
| **Anti-Windup** | 条件积分：输出饱和且误差同向时冻结积分，防止深度 windup |
| **换向清积分** | setpoint 符号变化时调用 `PID_Reset()`，防止方向切换时积分残留导致反向超调 |
| **事件驱动日志** | `osThreadFlagsSet` 由 Encoder_Task 在每次数据更新后触发，Logger_Task 零 CPU 占用等待 |
| **DMA 串口** | `HAL_UART_Transmit_DMA` + 仅检查 `gState`（非完整状态），避免 RX 浮空错误阻塞发送 |
| **非阻塞命令接收** | Motor_Task 用 `timeout=0` 取命令，保证每 10 ms PID 计算不被命令等待阻塞 |
