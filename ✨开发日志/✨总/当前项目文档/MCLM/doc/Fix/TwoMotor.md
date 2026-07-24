# 双电机扩展计划

> 工程：`3_MCLM_t2`  日期：2026-04-19  
> 目标：在现有单电机闭环控制基础上，加入第二个电机（动力电机）的完整控制链路

---

## 一、现有代码现状评估

### 已经天然支持多实例（✅ 无需改动）

| 文件 | 原因 |
|---|---|
| `pid.h / pid.c` | PID_Controller 是值结构体，Init/Compute 全靠参数传入，无全局状态 |
| `motor_DC_tb6612.h / .c` | TB6612_Motor_t 是值结构体，Init/SetSpeed 全靠指针参数 |
| `app_globals.h` → `Motor_t` | 聚合体结构设计正确，硬件句柄+PID+状态全部内嵌，天然独立 |
| `tb6612_DC_task.c` | 已通过 `argument` 传入 `Motor_t*`，`argument != NULL` 分支已写好 |

### 需要改动（⚠️ 当前硬编码单电机）

| 文件 | 问题 | 改动量 |
|---|---|---|
| `app_globals.h` | `MOTOR_COUNT 1` 硬编码 | 小 |
| `app_config.h` | 无 MOTOR2_* 参数组 | 中（纯增加） |
| `app_task.c` | `Motor_PID_Init` 只用 MOTOR1_* 参数 | 小 |
| `encoder_task.c` | 硬编码 `&htim2` 和 `g_motors[0]` | 小 |
| `command.h` | `CommandMsg_t` 无 `motor_id` 字段 | 小（+1字节） |
| `command_task.c` | 路由硬编码 `MotorQueueHandle` 和 `g_motors[0]` | 中 |
| `can.c` | RX 回调不填 `motor_id` | 小 |
| `freertos.c` | 无第二电机任务、无第二电机队列 | 中 |
| `app_globals.h` | 无 MotorQueue0/1、Encoder2、MotorControl2 句柄声明 | 小 |

---

## 二、改动清单（按执行顺序）

### Step 1 — `app_config.h`：增加电机2参数组

在 `#if (ACTIVE_MOTOR_DRIVER == MOTOR_DRIVER_TB6612)` 块内，紧接 MOTOR1 末尾追加：

```c
/* ── 电机2 (动力电机) TB6612 配置 ── */
#define MOTOR2_TIM_HANDLE           &htim1          // PWM统一使用TIM1
#define MOTOR2_TIM_CHANNEL          TIM_CHANNEL_2   // TIM1_CH2（确认 CubeMX 已使能）
#define MOTOR2_IN1_PORT             GPIOA
#define MOTOR2_IN1_PIN              GPIO_PIN_0
#define MOTOR2_IN2_PORT             GPIOA
#define MOTOR2_IN2_PIN              GPIO_PIN_1
#define MOTOR2_EN_PORT              NULL            // 无独立使能引脚时填 NULL
#define MOTOR2_EN_PIN               0
#define MOTOR2_MAX_PWM_OUTPUT       PWM_MAX
#define MOTOR2_MAX_SPEED_LOGIC      SPEED_LOGIC_MAX
#define MOTOR2_DEAD_ZONE            10

/* 电机2 PID参数（初始与电机1相同，后续独立整定） */
#define MOTOR2_PID_KP               0.4584f
#define MOTOR2_PID_KI               17.66f
#define MOTOR2_PID_KD               0.0025f
#define MOTOR2_PID_INTEGRAL_LIMIT   5.66f
#define MOTOR2_PID_OUTPUT_LIMIT     100.0f
#define MOTOR2_PID_TS               0.01f
#define MOTOR2_PID_DERIVATIVE_FILTER_ALPHA 0.3f

/* 编码器定时器（CubeMX 需同步配置 TIM3 为 Encoder 模式） */
#define MOTOR1_ENCODER_TIM          &htim2
#define MOTOR2_ENCODER_TIM          &htim3
```

> **⚠️ 硬件确认前提**：引脚、TIM 通道需根据实际 PCB 接线修改，上面是占位示例。

---

### Step 2 — `app_globals.h`：MOTOR_COUNT 改为 2，增加新句柄声明

```c
// 修改前
#define MOTOR_COUNT 1

// 修改后
#define MOTOR_COUNT 2
```

同文件追加：

```c
/* ===================== 新增：第二电机任务/队列句柄 ===================== */
extern osThreadId_t MotorControl2_TaHandle;
extern osThreadId_t Encoder2_TaHandle;
extern osMessageQueueId_t MotorQueue0Handle;   // 替代原 MotorQueueHandle
extern osMessageQueueId_t MotorQueue1Handle;
```

> `MotorQueueHandle` 原声明保留以便向后兼容，后续重构时移除。

---

### Step 3 — `command.h`：CommandMsg_t 增加 motor_id

```c
// 修改前
typedef struct {
    CommandType_t type;
    int16_t value;
} CommandMsg_t;

// 修改后
typedef struct {
    CommandType_t type;
    int16_t value;
    uint8_t motor_id;   // 0=电机0(转向), 1=电机1(动力), 0xFF=广播(两路都执行)
} CommandMsg_t;
```

> 结构体增加 1 字节，编译器对齐后实际大小不变（仍4字节对齐），队列深度/消息大小无需修改。

---

### Step 4 — `app_task.c`：Motor_PID_Init 按索引区分参数

```c
// 修改前（只用 MOTOR1_* 参数）
void Motor_PID_Init(Motor_t *motor) {
    PID_Init(&(motor->pid), MOTOR1_PID_KP, MOTOR1_PID_KI, ...);
}

// 修改后
void Motor_PID_Init(Motor_t *motor) {
    uint8_t idx = (uint8_t)(motor - &g_motors[0]);
    if (idx == 0) {
        PID_Init(&(motor->pid),
                 MOTOR1_PID_KP, MOTOR1_PID_KI, MOTOR1_PID_KD,
                 MOTOR1_PID_INTEGRAL_LIMIT, MOTOR1_PID_OUTPUT_LIMIT,
                 MOTOR1_PID_TS, MOTOR1_PID_DERIVATIVE_FILTER_ALPHA);
    } else {
        PID_Init(&(motor->pid),
                 MOTOR2_PID_KP, MOTOR2_PID_KI, MOTOR2_PID_KD,
                 MOTOR2_PID_INTEGRAL_LIMIT, MOTOR2_PID_OUTPUT_LIMIT,
                 MOTOR2_PID_TS, MOTOR2_PID_DERIVATIVE_FILTER_ALPHA);
    }
}
```

---

### Step 5 — `tb6612_DC_task.c`：按 idx 选硬件配置 + 按 idx 选队列

当前 `TB6612_DC_Task` 已支持 `argument` 传入，只需修改两处：

**① 初始化部分（Motor_Init 参数按 idx 分支）**

```c
void TB6612_DC_Task(void *argument)
{
    Motor_t *motor = (argument != NULL) ? (Motor_t *)argument : &g_motors[0];
    uint8_t idx = (uint8_t)(motor - &g_motors[0]);   // ← 新增

    Motor_PID_Init(motor);

    if (idx == 0) {
        TB6612_Motor_Init(&(motor->hardware),
            MOTOR1_TIM_HANDLE, MOTOR1_TIM_CHANNEL,
            MOTOR1_IN1_PORT, MOTOR1_IN1_PIN,
            MOTOR1_IN2_PORT, MOTOR1_IN2_PIN,
            MOTOR1_EN_PORT,  MOTOR1_EN_PIN,
            MOTOR1_MAX_PWM_OUTPUT, MOTOR1_MAX_SPEED_LOGIC,
            MOTOR1_DEAD_ZONE, 1,                // Polarity=1：此电机硬件接线需要反转
            TB6612_MOTOR_STOP_BRAKE);
    } else {
        TB6612_Motor_Init(&(motor->hardware),
            MOTOR2_TIM_HANDLE, MOTOR2_TIM_CHANNEL,
            MOTOR2_IN1_PORT, MOTOR2_IN1_PIN,
            MOTOR2_IN2_PORT, MOTOR2_IN2_PIN,
            MOTOR2_EN_PORT,  MOTOR2_EN_PIN,
            MOTOR2_MAX_PWM_OUTPUT, MOTOR2_MAX_SPEED_LOGIC,
            MOTOR2_DEAD_ZONE, 0,                // Polarity 根据实际接线确认
            TB6612_MOTOR_STOP_BRAKE);
    }
```

**② 主循环队列选择**

```c
    // 按电机索引选专属队列（替代原来的 MotorQueueHandle）
    osMessageQueueId_t myQueue = (idx == 0) ? MotorQueue0Handle : MotorQueue1Handle;

    for(;;) {
        status = osMessageQueueGet(myQueue, &cmdMsg, NULL, 0);  // ← 从 MotorQueueHandle 改为 myQueue
        // ... 以下逻辑不变 ...
    }
```

---

### Step 6 — `encoder_task.c`：参数化 htim，支持两个实例

```c
// 修改前（硬编码 htim2 和 g_motors[0]）
void Encoder_Task(void *argument)
{
    HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);
    ...
    g_motors[0].current_ticks = diff;
    g_motors[0].current_logic_speed = ticks_to_logic(diff);

// 修改后（通过 argument 传入 Motor_t*，idx 推断编码器 TIM）
void Encoder_Task(void *argument)
{
    Motor_t *motor = (argument != NULL) ? (Motor_t *)argument : &g_motors[0];
    uint8_t idx = (uint8_t)(motor - &g_motors[0]);

    TIM_HandleTypeDef *htim_enc = (idx == 0) ? MOTOR1_ENCODER_TIM : MOTOR2_ENCODER_TIM;
    HAL_TIM_Encoder_Start(htim_enc, TIM_CHANNEL_ALL);

    int16_t last_cnt = 0;
    for(;;)
    {
        int16_t now  = (int16_t)__HAL_TIM_GET_COUNTER(htim_enc);
        int16_t diff = (int16_t)(now - last_cnt);
        last_cnt = now;

        if (osMutexAcquire(motor_mutexHandle, osWaitForever) == osOK)
        {
            motor->current_ticks = diff;
            motor->current_logic_speed = ticks_to_logic(diff);
            osMutexRelease(motor_mutexHandle);

            // 只让电机0的编码器唤醒 Logger（避免双重唤醒）
            if (idx == 0 && Logger_TaHandle != NULL)
                osThreadFlagsSet(Logger_TaHandle, 0x01);
        }
        osDelay(10);
    }
}
```

---

### Step 7 — `can.c`：RX 回调填写 motor_id

在 `HAL_CAN_RxFifo0MsgPendingCallback` 中，解析完 `cmdMsg.type` 后，增加 `motor_id` 赋值：

```c
// 根据 CAN ID 决定目标电机
if (rxHeader.StdId == CAN_MOTOR_TURN_CMD_STDID ||
    rxHeader.StdId == CAN_MOTOR_TURN_CMD_STATUS_STDID) {
    cmdMsg.motor_id = 0;          // 转向电机（电机0）
}
else if (rxHeader.StdId == CAN_MOTOR_POWER_CMD_STDID ||
         rxHeader.StdId == CAN_MOTOR_POWER_CMD_STATUS_STDID) {
    cmdMsg.motor_id = 1;          // 动力电机（电机1）
}
else if (rxHeader.StdId == CAN_CMD_STOP_STDID  ||
         rxHeader.StdId == CAN_CMD_TURN_STDID  ||
         rxHeader.StdId == CAN_CMD_POWER_STDID) {
    cmdMsg.motor_id = 0xFF;       // 广播：两个电机都执行
}
```

> CAN ID 已在 `app_config.h` 中预留（`0x126/0x226/0x326`），协议层无需新增定义。

---

### Step 8 — `command_task.c`：按 motor_id 路由队列 + 按 motor_id 读状态

**① 路由到专属队列（替代原 `MotorQueueHandle`）**

```c
// 修改前
if (is_motor_cmd(cmd.type))
    osMessageQueuePut(MotorQueueHandle, &cmd, 0, 0);

// 修改后
if (is_motor_cmd(cmd.type)) {
    if (cmd.motor_id == 0xFF) {
        // 广播：同时投递两个队列
        osMessageQueuePut(MotorQueue0Handle, &cmd, 0, 0);
        osMessageQueuePut(MotorQueue1Handle, &cmd, 0, 0);
    } else {
        osMessageQueueId_t q = (cmd.motor_id == 1) ? MotorQueue1Handle : MotorQueue0Handle;
        osMessageQueuePut(q, &cmd, 0, 0);
    }
}
```

**② 读状态按 motor_id 区分（CMD_QUERY_STATUS 路径）**

```c
// 修改前（始终读 g_motors[0]）
status = g_motors[0];

// 修改后
uint8_t mid = (cmd.motor_id < MOTOR_COUNT) ? cmd.motor_id : 0;
status = g_motors[mid];
```

> CAN TX 回复帧 StdId 也需按 mid 选择（`CAN_MOTOR_TURN_STATUS_STDID` vs `CAN_MOTOR_POWER_STATUS_STDID`）。

---

### Step 9 — `freertos.c`：新增第二电机任务 + 拆分队列

**① 新增队列定义（在现有 MotorQueue 之后）**

```c
/* Definitions for MotorQueue0 */
osMessageQueueId_t MotorQueue0Handle;
const osMessageQueueAttr_t MotorQueue0_attributes = { .name = "MotorQueue0" };

/* Definitions for MotorQueue1 */
osMessageQueueId_t MotorQueue1Handle;
const osMessageQueueAttr_t MotorQueue1_attributes = { .name = "MotorQueue1" };
```

**② 新增第二电机任务 + 第二编码器任务的静态定义**

```c
/* Definitions for MotorControl2_Ta */
osThreadId_t MotorControl2_TaHandle;
uint32_t MotorControl2_TaBuffer[128];
osStaticThreadDef_t MotorControl2_TaControlBlock;
const osThreadAttr_t MotorControl2_Ta_attributes = {
    .name = "MotorCtrl2",
    .cb_mem = &MotorControl2_TaControlBlock,
    .cb_size = sizeof(MotorControl2_TaControlBlock),
    .stack_mem = &MotorControl2_TaBuffer[0],
    .stack_size = sizeof(MotorControl2_TaBuffer),
    .priority = (osPriority_t) osPriorityAboveNormal1,
};

/* Definitions for Encoder2_Ta */
osThreadId_t Encoder2_TaHandle;
uint32_t Encoder2_TaBuffer[128];
osStaticThreadDef_t Encoder2_TaControlBlock;
const osThreadAttr_t Encoder2_Ta_attributes = {
    .name = "Encoder2_Ta",
    .cb_mem = &Encoder2_TaControlBlock,
    .cb_size = sizeof(Encoder2_TaControlBlock),
    .stack_mem = &Encoder2_TaBuffer[0],
    .stack_size = sizeof(Encoder2_TaBuffer),
    .priority = (osPriority_t) osPriorityAboveNormal2,
};
```

**③ MX_FREERTOS_Init() 中创建新队列 + 新任务**

```c
// 队列
MotorQueue0Handle = osMessageQueueNew(72, sizeof(CommandMsg_t), &MotorQueue0_attributes);
MotorQueue1Handle = osMessageQueueNew(72, sizeof(CommandMsg_t), &MotorQueue1_attributes);

// 任务（传入各自的 Motor_t 指针, 注意 Start_MotorControl 和 Start_Encoder 两个函数是复用的）
MotorControl_TaHandle  = osThreadNew(TB6612_DC_Task, &g_motors[0], &MotorControl_Ta_attributes);
MotorControl2_TaHandle = osThreadNew(TB6612_DC_Task, &g_motors[1], &MotorControl2_Ta_attributes);
Encoder_TaHandle       = osThreadNew(Encoder_Task,   &g_motors[0], &Encoder_Ta_attributes);
Encoder2_TaHandle      = osThreadNew(Encoder_Task,   &g_motors[1], &Encoder2_Ta_attributes);
```

新增两个 wrapper 函数：

```c
void Start_MotorControl2(void *argument) { TB6612_DC_Task(argument); }
void Start_Encoder2(void *argument)      { Encoder_Task(argument); }
```

---

## 三、CubeMX 硬件配置要求

在代码修改之前，需要先在 CubeMX 中完成以下配置并重新生成：

| 配置项 | 目标状态 | 说明 |
|---|---|---|
| TIM1 CH1 | PWM Generation CH1 | 电机1 PWM 输出 |
| TIM1 CH2 | PWM Generation CH2 | 电机2 PWM 输出 |
| TIM2 | Encoder Mode TI1/TI2 | 电机1 编码器输入 (保持不变) |
| TIM3 | Encoder Mode TI1/TI2 | 电机2 编码器输入 (从TIM4改来) |
| TIM4 | Systick | 保持不变, 不再用于编码器 |
| 电机2方向引脚 | Output Push-Pull | 根据实际引脚填写 |

> **核心改动**：PWM统一由TIM1提供，编码器由TIM2和TIM3负责，TIM4不再参与业务。

---

## 四、数据流图（扩展后）

```
CAN 0x125 (转向)        CAN 0x126 (动力)        CAN 0x101/0x102 (广播)
     │                       │                           │
     │ motor_id=0            │ motor_id=1                │ motor_id=0xFF
     └───────────────────────┴───────────────────────────┘
                                     │
                          [CommandQueueHandle]
                                     │
                             Command_Task()
                             ├─ motor_id=0   → [MotorQueue0Handle]
                             ├─ motor_id=1   → [MotorQueue1Handle]
                             └─ motor_id=0xFF→ [MotorQueue0] + [MotorQueue1]

[MotorQueue0Handle]                     [MotorQueue1Handle]
       │                                        │
TB6612_DC_Task(&g_motors[0])       TB6612_DC_Task(&g_motors[1])
  PID + htim1_CH1 PWM               PID + htim1_CH2 PWM
       ↑                                        ↑
Encoder_Task(&g_motors[0])         Encoder_Task(&g_motors[1])
  htim2 (TI1+TI2, Filter=8)          htim3 (TI1+TI2, Filter=8)
```

---

## 五、互斥锁策略说明

当前使用**单个 `motor_mutex` 保护整个 `g_motors[]` 数组**。

双电机扩展后，电机0任务和电机1任务都会竞争同一把锁，产生不必要的阻塞。

**当前方案（保持单锁，够用）：**
- 每个任务持锁时间极短（仅读写几个 float/int16），约 < 5 μs
- 10 ms 周期内锁竞争概率极低
- 保持现状，实现简单

**可选升级（后期如有性能需求）：**
```c
// app_globals.h
extern osMutexId_t motor_mutex[MOTOR_COUNT];   // 每电机独立锁

// 用法
osMutexAcquire(motor_mutex[idx], osWaitForever);
```

---

## 六、影响范围汇总

### 需要修改

| # | 文件 | 改动性质 | 改动量 |
|---|---|---|---|
| 1 | `App/config/app_config.h` | 纯增加 MOTOR2_* 宏 | 小 |
| 2 | `App/config/app_globals.h` | MOTOR_COUNT 2，新增句柄 extern | 小 |
| 3 | `App/config/app_task.c` | Motor_PID_Init 加 idx 分支 | 小 |
| 4 | `App/services/command.h` | CommandMsg_t +1 字段 | 小 |
| 5 | `App/tasks/tb6612_DC_task.c` | Init 加 idx 分支，队列换名 | 小 |
| 6 | `App/tasks/encoder_task.c` | 参数化 htim，argument 接收 Motor_t* | 小 |
| 7 | `App/tasks/command_task.c` | 路由逻辑按 motor_id 分发 | 中 |
| 8 | `Core/Src/can.c` | RX 回调填 motor_id | 小 |
| 9 | `Core/Src/freertos.c` | 新增任务/队列定义 + Init 调用 | 中 |

### 无需修改

| 文件 | 原因 |
|---|---|
| `pid.h / pid.c` | 无全局状态，天然多实例 |
| `motor_DC_tb6612.h / .c` | 无全局状态，天然多实例 |
| `App/tasks/Ack_task.c` | 通过 AckQueue 解耦，不感知电机数量 |
| `App/tasks/logger_task.c` | 当前只显示 g_motors[0]，保持不变 |
| `App/services/command.c` | UART 命令解析，motor_id 可默认填 0 |

---

## 七、RAM 资源评估（STM32F103C8T6，20 KB SRAM）

```
现有静态栈占用：
  Heartbeat  64×4  =  256 B
  MotorCtrl 128×4  =  512 B
  Encoder   128×4  =  512 B
  Logger    256×4  = 1024 B
  Command   128×4  =  512 B
  Ack       256×4  = 1024 B
  小计                3840 B

新增：
  MotorCtrl2  128×4 =  512 B
  Encoder2    128×4 =  512 B
  MotorQueue1  72×4 =  288 B   (CommandMsg_t 大约 4 B)
  g_motors[1] 额外一份 Motor_t ≈ 200 B

新增合计 ≈ 1.5 KB
总计 ≈ 5.3 KB  （20 KB 的 26%，完全可行）
```

---

## 八、实施顺序建议

```
阶段1（纯配置/接口）：Step 1 → Step 2 → Step 3
  → 只改宏和结构体，不影响运行时，可先编译验证

阶段2（逻辑修改）：Step 4 → Step 5 → Step 6
  → Motor_PID_Init + Task 参数化，编译 + 单电机回归测试

阶段3（路由层）：Step 7 → Step 8
  → command_task / can.c 路由，此时 MotorQueue1 还未创建不会跑，安全

阶段4（OS 层）：Step 9 + CubeMX 配置
  → 创建队列任务，接入第二电机硬件，开始联调
```