# 双电机扩展实施结果

> 工程：`3_MCLM_t2`  日期：2026-04-20  
> 基于 `TwoMotor.md` 计划实施，硬件配置：TIM1(PWM CH1/CH2) + TIM2/TIM3(编码器) + TIM4(Systick)

---

## 一、硬件配置确认（与计划的差异）

| 资源 | 计划 | 实际 |
|---|---|---|
| 电机0 PWM | TIM1_CH1 | TIM1_CH1 ✅ |
| 电机1 PWM | TIM1_CH2 | TIM1_CH2 ✅ |
| 电机0 编码器 | TIM2 | TIM2 ✅ |
| 电机1 编码器 | TIM3 | TIM3 ✅ |
| Systick | TIM4 | TIM4 ✅（不参与业务） |
| 互斥锁策略 | 单锁 or 可选双锁 | CubeMX 直接生成双锁（`motor0_mutex` + `motor1_mutex`） |

---

## 二、FreeRTOS 对象命名（freertos.c 实际 vs 计划）

> CubeMX 生成的名称与计划文档有差异，以实际为准。

| 类型 | 计划名 | 实际名（freertos.c） |
|---|---|---|
| 电机1控制任务 | `MotorControl2_TaHandle` | `MotorControl1_THandle` |
| 电机1编码器任务 | `Encoder2_TaHandle` | `Encoder1_THandle` |
| 电机0队列 | `MotorQueue0Handle` | `MotorQueueHandle`（原名保留） |
| 电机1队列 | `MotorQueue1Handle` | `MotorQueue1Handle` ✅ |
| 互斥锁0 | `motor_mutexHandle` | `motor0_mutexHandle` ✅ |
| 互斥锁1 | 可选 | `motor1_mutexHandle` ✅ |

---

## 三、各文件改动明细

### `App/config/app_config.h` — 未改动（已预先完成）

- MOTOR2_* 硬件宏（TIM1_CH2、IN1/IN2 引脚）
- MOTOR2_* PID 参数宏
- `MOTOR1_ENCODER_TIM &htim2` / `MOTOR2_ENCODER_TIM &htim3`

---

### `App/config/app_globals.h` — Step 2

```diff
- #define MOTOR_COUNT 1
+ #define MOTOR_COUNT 2

+ extern osThreadId_t MotorControl1_THandle;   // 电机1控制任务
+ extern osThreadId_t Encoder1_THandle;         // 电机1编码器任务
+ extern osMessageQueueId_t MotorQueue1Handle;  // 电机1专属队列
+ extern osMutexId_t motor1_mutexHandle;        // 保护 g_motors[1]
+ extern osSemaphoreId_t uart_rx_semaphoreHandle;
+ extern osSemaphoreId_t can_rx_semaphoreHandle;
```

---

### `App/services/command.h` — Step 3

```diff
 typedef struct {
     CommandType_t type;
     int16_t value;
+    uint8_t motor_id;  // 0=电机0(转向), 1=电机1(动力), 0xFF=广播
 } CommandMsg_t;
```

> 结构体增加 1 字节，4 字节对齐后实际大小不变。

---

### `App/config/app_task.c` — Step 4

`Motor_PID_Init` 由硬编码 MOTOR1 参数改为按 `idx` 分支：

```c
void Motor_PID_Init(Motor_t *motor)
{
    uint8_t idx = (uint8_t)(motor - &g_motors[0]);
    if (idx == 0) {
        PID_Init(&(motor->pid), MOTOR1_PID_KP, ...);
    } else {
        PID_Init(&(motor->pid), MOTOR2_PID_KP, ...);
    }
}
```

---

### `App/tasks/tb6612_DC_task.c` — Step 5

三处改动：

1. 计算 `idx`
2. `TB6612_Motor_Init` 按 idx 选 MOTOR1/MOTOR2 硬件配置（Polarity：电机0=1反转，电机1=0）
3. `myQueue` / `myMutex` 按 idx 选取，替代原来硬编码的 `MotorQueueHandle` / `motor0_mutexHandle`

```c
uint8_t idx    = (uint8_t)(motor - &g_motors[0]);
osMessageQueueId_t myQueue = (idx == 0) ? MotorQueueHandle  : MotorQueue1Handle;
osMutexId_t        myMutex = (idx == 0) ? motor0_mutexHandle : motor1_mutexHandle;
```

---

### `App/tasks/encoder_task.c` — Step 6

由硬编码 `htim2` / `g_motors[0]` 改为全参数化：

```c
Motor_t *motor  = (argument != NULL) ? (Motor_t *)argument : &g_motors[0];
uint8_t  idx    = (uint8_t)(motor - &g_motors[0]);
TIM_HandleTypeDef *htim_enc = (idx == 0) ? MOTOR1_ENCODER_TIM : MOTOR2_ENCODER_TIM;
osMutexId_t        myMutex  = (idx == 0) ? motor0_mutexHandle  : motor1_mutexHandle;
```

> 只有 `idx == 0` 的编码器任务会唤醒 Logger，避免双重触发。

---

### `Core/Src/can.c` — Step 7

RX 回调增加动力电机 ID 识别，并按 ID 填写 `motor_id`：

| CAN StdId | `motor_id` | 含义 |
|---|---|---|
| `0x125` / `0x225` | `0` | 转向电机（电机0） |
| `0x126` / `0x226` | `1` | 动力电机（电机1） |
| 广播类 ID | `0xFF` | 两个电机都执行 |

同时清理了原来冗余的注释和重复逻辑。

---

### `App/tasks/command_task.c` — Step 8

三处改动：

1. 去掉顶部重复 `extern osMutexId_t motor0_mutexHandle`（已在 globals.h 统一声明）
2. 读状态按 `motor_id` 选对应锁和 `g_motors[mid]`
3. 路由逻辑：

```c
if (cmd.motor_id == 0xFF) {
    osMessageQueuePut(MotorQueueHandle,  &cmd, 0, 0);  // 广播
    osMessageQueuePut(MotorQueue1Handle, &cmd, 0, 0);
} else {
    osMessageQueueId_t q = (cmd.motor_id == 1) ? MotorQueue1Handle : MotorQueueHandle;
    osMessageQueuePut(q, &cmd, 0, 0);
}
```

4. `CMD_QUERY_STATUS` CAN 回复帧 StdId 按 `mid` 区分（`0x325` / `0x326`）

---

### `Core/Src/freertos.c` — Step 9

| 改动 | 内容 |
|---|---|
| `USER CODE BEGIN Includes` | 新增 `#include "app_globals.h"` |
| `osThreadNew(Start_MotorControl1_T, ...)` | `NULL` → `&g_motors[1]` |
| `osThreadNew(Start_Encoder1_T, ...)` | `NULL` → `&g_motors[1]` |
| `Start_MotorControl1_T` 函数体 | 空 `osDelay(1)` → `TB6612_DC_Task(argument)`（含驱动宏） |
| `Start_Encoder1_T` 函数体 | 空 `osDelay(1)` → `Encoder_Task(argument)` |
| 电机0任务传参 | 保留 `NULL`，Task 内部 fallback 到 `&g_motors[0]` |

---

## 四、数据流（实施后）

```
CAN 0x125/0x225 (转向)    CAN 0x126/0x226 (动力)    广播 ID
  motor_id=0                motor_id=1                motor_id=0xFF
        └──────────────────────┴──────────────────────────┘
                                    │
                         [CommandQueueHandle]
                                    │
                            Command_Task()
                     ┌──────────────┴──────────────┐
              motor_id=0                      motor_id=1 / 0xFF
                     │                              │
          [MotorQueueHandle]            [MotorQueue1Handle]
                     │                              │
      TB6612_DC_Task(&g_motors[0])  TB6612_DC_Task(&g_motors[1])
        PID + TIM1_CH1 PWM            PID + TIM1_CH2 PWM
        motor0_mutex                  motor1_mutex
               ↑                              ↑
      Encoder_Task(&g_motors[0])   Encoder_Task(&g_motors[1])
        TIM2 (htim2)                  TIM3 (htim3)
```

---

## 五、无需改动的文件

| 文件 | 原因 |
|---|---|
| `pid.h / pid.c` | 无全局状态，天然多实例 |
| `motor_DC_tb6612.h / .c` | 无全局状态，天然多实例 |
| `App/tasks/Ack_task.c` | 通过 AckQueue 解耦，不感知电机数量 |
| `App/tasks/logger_task.c` | 当前只显示 g_motors[0]，保持不变 |
| `App/services/command.c` | UART 命令解析，motor_id 默认 0 即可 |

---

## 六、待验证事项（下一步）

- [ ] `can.c` 中 `CAN_CMD_STOP_STDID` / `CAN_CMD_TURN_STDID` / `CAN_CMD_POWER_STDID` 广播 ID 是否在 `app_config.h` 中已定义
- [ ] CubeMX 中 TIM3 已配置为 Encoder Mode TI1/TI2（Filter=8），TIM4 仅作 Systick
- [ ] TIM1 CH1 / CH2 均已在 CubeMX 使能为 PWM Generation
- [ ] 电机1方向引脚（`MOTOR2_IN1/IN2`）根据实际 PCB 接线在 `app_config.h` 修正
- [ ] 编译通过后，先单独跑电机0回归测试，再接入电机1联调
- [ ] `MotorControl1_T` / `Encoder1_T` 栈大小当前为 64 word（256 B），如运行中出现栈溢出可扩至 128 word
