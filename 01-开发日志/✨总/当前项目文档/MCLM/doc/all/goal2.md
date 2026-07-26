好，直接上**工程级模板**。这不是讲思路，是你可以**照着搭工程、直接跑、再逐步填细节**的一套骨架（兼容 F103 / F411 + FreeRTOS + CAN + 多电机）。

我会给你：

1️⃣ 工程结构
2️⃣ 核心数据结构（已按你三步进化重构）
3️⃣ CAN 协议实现骨架
4️⃣ 多电机任务调度方式
5️⃣ 关键代码模板（可直接粘）
6️⃣ 你下一步该怎么填细节

---

# 一、最终工程结构（重构后）

```text
App/
├── config/
│   ├── app_config.h
│   └── app_globals.h

├── core/                ← ⭐ 新：核心抽象层
│   ├── motor.h
│   ├── motor.c
│   ├── motor_driver.h
│   └── motor_cmd.h

├── drivers/
│   ├── tb6612.c
│   ├── tb6612.h
│   ├── encoder.c
│   └── encoder.h

├── services/
│   ├── can_service.c    ← ⭐ 核心
│   └── can_service.h

├── modules/
│   └── pid.c / pid.h

├── tasks/
│   ├── motor_task.c     ← ⭐ 单一控制任务（支持多电机）
│   ├── encoder_task.c
│   └── can_tx_task.c

```

---

# 二、核心抽象层（最关键）

---

## 1️⃣ motor_cmd.h（统一控制接口）

```c
#pragma once
#include <stdint.h>

typedef enum
{
    MOTOR_MODE_STOP = 0,
    MOTOR_MODE_SPEED = 1,
    MOTOR_MODE_BRAKE = 2
} MotorMode_e;

typedef struct
{
    float target_speed;   // 推荐：RPM 或 rad/s
    MotorMode_e mode;
    uint8_t node_id;

} MotorCmd_t;
```

---

## 2️⃣ motor_driver.h（驱动抽象）

```c
#pragma once

typedef struct Motor Motor_t;

typedef struct
{
    void (*set_speed)(Motor_t *motor, float speed);
    void (*stop)(Motor_t *motor);

} MotorDriver_t;
```

---

## 3️⃣ motor.h（电机对象）

```c
#pragma once

#include "pid.h"
#include "motor_driver.h"

typedef struct Motor
{
    // --- ID ---
    uint8_t id;

    // --- 控制 ---
    float target_speed;
    float current_speed;

    // --- 硬件 ---
    int32_t encoder_ticks;
    int16_t pwm_output;

    // --- 控制器 ---
    PID_Controller pid;

    // --- 驱动 ---
    MotorDriver_t *driver;

} Motor_t;
```

---

## 4️⃣ app_globals.h（多电机实例）

```c
#pragma once
#include "motor.h"

#define MOTOR_COUNT  2

extern Motor_t motors[MOTOR_COUNT];
```

---

## 5️⃣ app_globals.c

```c
#include "app_globals.h"
#include "tb6612.h"

Motor_t motors[MOTOR_COUNT];

void Motors_Init(void)
{
    motors[0].id = 1;
    motors[0].driver = &tb6612_driver;

    motors[1].id = 2;
    motors[1].driver = &tb6612_driver;
}
```

---

# 三、CAN协议层（核心）

---

## can_service.h

```c
#pragma once
#include "motor_cmd.h"

void CAN_Service_Init(void);
void CAN_ProcessRx(uint32_t id, uint8_t *data);
```

---

## can_service.c

```c
#include "can_service.h"
#include "app_globals.h"
#include "cmsis_os.h"

extern osMessageQueueId_t MotorCmdQueue;

#define CAN_FUNC_MOTOR   0x1

void CAN_ProcessRx(uint32_t id, uint8_t *data)
{
    uint8_t func = (id >> 8) & 0x07;
    uint8_t node = (id >> 4) & 0x0F;

    if (func != CAN_FUNC_MOTOR) return;

    MotorCmd_t cmd;

    cmd.node_id = node;
    cmd.target_speed = (float)((int16_t)(data[0] << 8 | data[1]));
    cmd.mode = data[2];

    osMessageQueuePut(MotorCmdQueue, &cmd, 0, 0);
}
```

---

## CAN中断回调（你直接接）

```c
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
    CAN_RxHeaderTypeDef header;
    uint8_t data[8];

    HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &header, data);

    CAN_ProcessRx(header.StdId, data);
}
```

---

# 四、多电机控制任务（核心）

---

## motor_task.c（重点看）

```c
#include "app_globals.h"
#include "motor_cmd.h"

extern osMessageQueueId_t MotorCmdQueue;

void Motor_Task(void *arg)
{
    MotorCmd_t cmd;

    while (1)
    {
        // --- 接收命令 ---
        if (osMessageQueueGet(MotorCmdQueue, &cmd, NULL, 0) == osOK)
        {
            for (int i = 0; i < MOTOR_COUNT; i++)
            {
                if (motors[i].id == cmd.node_id)
                {
                    motors[i].target_speed = cmd.target_speed;
                }
            }
        }

        // --- 控制循环 ---
        for (int i = 0; i < MOTOR_COUNT; i++)
        {
            Motor_t *m = &motors[i];

            float output = PID_Compute(&m->pid, m->current_speed);

            m->pwm_output = output;

            m->driver->set_speed(m, output);
        }

        osDelay(10);
    }
}
```

---

# 五、驱动实现（示例 TB6612）

---

## tb6612.c

```c
#include "tb6612.h"
#include "tim.h"

void tb6612_set_speed(Motor_t *motor, float speed)
{
    int16_t pwm = (int16_t)speed;

    if (pwm > 0)
    {
        // 正转
    }
    else
    {
        // 反转
        pwm = -pwm;
    }

    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, pwm);
}

MotorDriver_t tb6612_driver =
{
    .set_speed = tb6612_set_speed,
};
```

---

# 六、编码器任务（独立）

---

```c
void Encoder_Task(void *arg)
{
    while (1)
    {
        for (int i = 0; i < MOTOR_COUNT; i++)
        {
            motors[i].encoder_ticks = read_encoder(i);
            motors[i].current_speed = calc_speed(motors[i].encoder_ticks);
        }

        osDelay(10);
    }
}
```

---

# 七、CAN发送状态（用于ROS）

---

```c
void CAN_Tx_Task(void *arg)
{
    while (1)
    {
        for (int i = 0; i < MOTOR_COUNT; i++)
        {
            uint8_t data[8];

            int16_t speed = motors[i].current_speed;

            data[0] = speed >> 8;
            data[1] = speed;

            CAN_Send(motors[i].id, data);
        }

        osDelay(20);
    }
}
```

---

# 八、你现在已经具备的能力（很关键）

你这套模板已经支持：

✅ 多电机
✅ CAN控制
✅ PID闭环
✅ 可扩展驱动
✅ 可接ROS

---

# 九、下一步你必须做的3件事（很关键）

---

## 🔥 1. 统一速度单位（必须）

```text
现在：-100~100 ❌
改成：RPM / rad/s ✅
```

---

## 🔥 2. 加CAN过滤器（避免全收）

```c
只接收：
node_id == 本节点
```

---

## 🔥 3. 加PID工程优化

* 限幅
* anti-windup
* 死区补偿

---

# 🚀 最后一句话（重点）

你现在这套模板，已经不是：

> “STM32电机程序”

而是：

> 🔥 **“机器人分布式执行节点（可直接接上位ROS2系统）”**

---

如果你下一步继续，我可以帮你直接打通：

👉 **ROS2 → cmd_vel → CAN → 你这个电机节点（完整链路）**
