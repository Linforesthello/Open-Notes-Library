# Func1: 舵向电机角度闭环控制 — 实施计划

> 基于 MT6701 SSI(SPI) 绝对角度传感器实现舵向位置闭环
> 日期: 2026-06-03
> 状态: 计划（已更新：
>   - 角度数据统一改用 int32_t x10 定标，避免新增 float（参考 logger_task.c 做法）
>   - 新增 Step 2.5: 传动比映射函数，支持 1:1/2:1/4:1 等非直连场景）
> SPI1 重映射至 PB3(SCK)/PB4(MISO)，已在 CubeMX IOC 中配置且代码已生成，无需改 .ioc
>
> **先验参考**: `6_mt6701_spi` 项目已完成 SPI 通信验证（见[实测数据](../../../../../6_MT6701/6_mt6701_spi/csv/test_csv.csv)）
> 本文档的驱动层参数和注意事项全部来自该实测验证，见 [build_config_260602.md](../../../../../6_MT6701/6_mt6701_spi/doc/build_config_260602.md)

---

## 目录

1. [资源确认](#一资源确认)
2. [修改文件清单](#二修改文件清单)
3. [硬件接线变化](#三硬件接线变化)
4. [控制架构](#四控制架构)
5. [Step 1: PA4 CS 引脚初始化](#五step-1-pa4-cs-引脚初始化)
6. [Step 2: MT6701 驱动层](#六step-2-mt6701-驱动层)
7. [Step 2.5: 传动比映射函数](#六点五step-25-传动比映射函数)
8. [Step 3: Motor_t 结构体扩展](#七step-3-motor_t-结构体扩展)
9. [Step 4: 角度 PID 参数配置](#八step-4-角度-pid-参数配置)
10. [Step 5: 编码器任务接入角度读取 + 位置外环](#九step-5-编码器任务接入角度读取--位置外环)
11. [Step 6: 舵向任务改为速度内环模式](#十step-6-舵向任务改为速度内环模式)
12. [Step 7: CAN 协议扩展](#十一step-7-can-协议扩展)
13. [Step 8: CMakeLists 添加新文件](#十二step-8-cmakelists-添加新文件)
14. [磁铁检测确认](#十三磁铁检测确认)
15. [编译与验证计划](#十四编译与验证计划)
16. [附录](#十五附录)

---

## 一、资源确认

### SPI1 状态（已验证）

| 检查项 | 状态 | 位置 |
|--------|:----:|------|
| `spi.h` include | ✅ | `main.c:24` |
| `MX_SPI1_Init()` 调用 | ✅ | `main.c:103` |
| `hspi1` 全局句柄 | ✅ | `spi.c:27` |
| AFIO 时钟使能 | ✅ | `stm32f1xx_hal_msp.c:69` |
| JTAG 关闭 (释放 PB3/PB4) | ✅ | `stm32f1xx_hal_msp.c:78` — `SWJ_NOJTAG` |
| SPI1 重映射使能 | ✅ | `spi.c:90` — `AFIO_REMAP_SPI1_ENABLE` |
| SPI 参数 (CPOL/CPHA/Prescaler) | ✅ 与 MT6701 完全匹配 | `spi.c:43-47` |
| HAL 驱动在编译中 | ✅ | `cmake/stm32cubemx` 子目录 |

```c
// spi.c 实际代码 — 与 MT6701 需求完全一致
hspi1.Init.Mode              = SPI_MODE_MASTER;         // ✅
hspi1.Init.Direction         = SPI_DIRECTION_2LINES;    // ✅ 发空字节收数据
hspi1.Init.DataSize          = SPI_DATASIZE_8BIT;       // ✅
hspi1.Init.CLKPolarity       = SPI_POLARITY_LOW;        // ✅ CPOL=Low
hspi1.Init.CLKPhase          = SPI_PHASE_2EDGE;         // ✅ CPHA=2Edge (Mode 1)
hspi1.Init.NSS               = SPI_NSS_SOFT;            // ✅ 软件 CS
hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_64;// ✅ 1.125MHz (72MHz/64)
hspi1.Init.FirstBit          = SPI_FIRSTBIT_MSB;        // ✅
```

> **⚠ SPI Mode 确认**: `6_mt6701_spi` 实测验证：**Mode 1 (CPOL=Low, CPHA=2Edge) 正确**，Mode 0 会导致 180~360° 范围异常。本文档的 SPI 参数已与实测一致，无需修改。

### 引脚占用

| 引脚 | 用途 | 能否用于 MT6701 |
|:----:|------|:--------------:|
| PA0,PA1 | TIM2 编码器 (舵向) | ❌ |
| PA2,PA3 | USART2 | ❌ |
| PA6,PA7 | TIM3 编码器 (动力) | ❌ |
| PA8 | TIM1_CH1 (舵向PWM) | ❌ |
| PA9,PA10 | TIM1_CH2/3 (动力PWM) | ❌ |
| PA11,PA12 | CAN | ❌ |
| PA13,PA14 | SWD 调试 | ❌ |
| PB0,PB1 | 舵向 IN1/IN2 | ❌ |
| PB6,PB7 | USART1 | ❌ |
| PB10,PB11 | USART3 | ❌ |
| PB12,PB13 | GPIO 输出 | ❌ |
| PC13 | LED | ❌ |
| PD0,PD1 | 晶振 | ❌ |
| **PA4** | ANALOG (空闲) | **→ CS** ✅ |
| **PB3** | SPI1_SCK (remap) | **→ SCLK** ✅ |
| **PB4** | SPI1_MISO (remap) | **→ MISO** ✅ |
| PB5 | SPI1_MOSI (remap) | 不接，发空字节 |

**结论：无需改 CubeMX `.ioc`，无需动任何 HAL 初始化，直接使用已有 SPI1。**

---

## 二、修改文件清单

### 新增文件（2 个）

| 文件 | 说明 |
|------|------|
| `App/drivers/mt6701.h` | MT6701 驱动头文件（含传动比配置类型、映射函数声明） |
| `App/drivers/mt6701.c` | MT6701 SPI 读取 + 传动比映射实现 |

### 修改文件（8 个）

| 文件 | 改动内容 |
|------|---------|
| `Core/Src/main.c` | ① PA4 CS 的 GPIO 初始化代码 |
| `App/config/app_globals.h` | ② Motor_t 增加角度控制字段 |
| `App/config/app_motor_cfg_new.h` | ③ 增加角度 PID 参数宏 |
| `App/tasks/encoder_task.c` | ④ 接入 MT6701 角度读取（自动传动比映射）+ 位置外环 PID |
| `App/tasks/tb6612_DC_task.c` | ⑤ 添加角度模式分支（仅运行速度内环） |
| `App/services/command.h` | ⑥ 新增角度控制命令类型 |
| `App/tasks/command_task.c` | ⑦ CAN 角度命令路由 + 状态帧扩展 |
| `CMakeLists.txt` | ⑧ 添加 `mt6701.c` 到编译 |

---

## 三、硬件接线变化

### 与独立测试 `6_mt6701_spi` 的差异

```
6_mt6701_spi (测试板 — 已验证通过)   3_MCLM_t2 (实际接线)
PA5 → SCLK                          PB3 → SCLK    (SPI1_REMAP)
PA6 → MISO                          PB4 → MISO    (SPI1_REMAP)
PA4 → CS                            PA4 → CS      (不变)
```

> PA6 已被 TIM3_CH1（动力电机编码器）占用，**不能**接 MT6701。

### 接线表

| MT6701 | STM32 | 备注 |
|:------:|:-----:|------|
| SCLK/B | **PB3** | SPI1_SCK (remap) |
| MISO/A | **PB4** | SPI1_MISO (remap) |
| NCS/Z  | **PA4** | CS, GPIO Output Push-Pull, 默认高电平 |
| VCC    | 3.3V | 不要接 5V |
| GND    | GND | |
| MOSI   | 不接 | PB5(SPI1_MOSI) 在 remap 后自动分配但硬件不接 |

---

## 四、控制架构

### 级联 PID 控制

```
  CAN 命令(目标角度°)
         │
         ▼
  ┌─────────────────────┐   50ms 周期 (20Hz，encoder_task 中运行)
  │  位置 PID 外环       │   setpoint = 角度误差 (归一化到 [-180,180])
  │                      │   output_limit = ±50  (最大速度 50%)
  │  输出: 目标速度      │
  └────────┬────────────┘
           │  motor->pid.setpoint = speed_setpoint
           ▼
  ┌─────────────────────┐   10ms 周期 (100Hz，tb6612_DC_task 中运行)
  │  速度 PID 内环       │   setpoint 来自外环
  │  输入: 编码器速度    │   feedback = motor->current_logic_speed
  │  输出: PWM           │
  └────────┬────────────┘
           │
     ┌──────────┐
     │ TB6612   │──→ 舵向直流电机 ──→ 机械转向
     └──────────┘
                    ▲
              ┌─────┴──────┐
              │   MT6701   │  14-bit 绝对角度 (SPI)
              └────────────┘
```

### 两种控制模式

| 模式 | `angle_ctrl_enabled` | 行为 | 触发条件 |
|:----:|:---------------------|------|---------|
| 速度模式 | 0 | 现有速度 PID 控制 | 收到 `CMD_SET_SPEED` |
| 角度模式 | 1 | 级联位置→速度 PID | 收到 `CAN_CMD_SET_ANGLE_MODE=1` |

### 频率规划

| 环 | 频率 | 位置 | 说明 |
|:--:|:----:|------|------|
| 位置外环 | 20Hz (50ms) | encoder_task | 读 MT6701 + 位置 PID 计算 |
| 速度内环 | 100Hz (10ms) | tb6612_DC_task | 保持现有频率不变 |

---

## 五、Step 1: PA4 CS 引脚初始化

### 文件: `Core/Src/main.c`

在 `USER CODE BEGIN 2` 区域（`MX_SPI1_Init()` 之后、`osKernelInitialize()` 之前）添加：

```c
/* USER CODE BEGIN 2 */
// ---- MT6701 CS 引脚初始化 (PA4) ----
// PA4 在 gpio.c 中被配置为 ANALOG，这里重新配置为 Output Push-Pull
__HAL_RCC_GPIOA_CLK_ENABLE();
GPIO_InitTypeDef gpio_mt6701 = {
    .Pin   = GPIO_PIN_4,
    .Mode  = GPIO_MODE_OUTPUT_PP,
    .Pull  = GPIO_PULLUP,
    .Speed = GPIO_SPEED_FREQ_LOW,
};
HAL_GPIO_Init(GPIOA, &gpio_mt6701);
HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);  // CS 默认高（非选通）
/* USER CODE END 2 */
```

> 注：`__HAL_RCC_GPIOA_CLK_ENABLE()` 可能已被之前的 MX_GPIO_Init() 开启，重复调用无副作用，保留以确保独立。

---

## 六、Step 2: MT6701 驱动层

### 新建 `App/drivers/mt6701.h`

```c
#ifndef __MT6701_H__
#define __MT6701_H__

#include <stdint.h>

/* MT6701 分辨率: 14-bit → 16384 步/圈 */
#define MT6701_RESOLUTION  16384

/* CS 引脚控制 (PA4) */
#define MT6701_CS_LOW()   HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET)
#define MT6701_CS_HIGH()  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET)

/**
 * @brief  角度误差归一化宏: 将误差限制在 [-1800, 1800] (x10 精度, int32_t)
 *         解决 0/360 过零问题，例如 target=10°, current=350°:
 *         error = 100-3500 = -3400 → -3400+3600 = 200 → 20.0°  (正确)
 *         使用 int32_t 避免引入浮点数
 */
#define ANGLE_NORMALIZE_ERROR_X10(err)                                     \
    ({ int32_t __e = (err);                                              \
       while (__e > 1800)  __e -= 3600;                                  \
       while (__e < -1800) __e += 3600;                                  \
       __e; })

/**
 * @brief  角度归一化宏: 将角度限制在 [0, 3600) (x10 精度, int32_t)
 */
#define ANGLE_NORMALIZE_X10(a)                                             \
    ({ int32_t __a = (a);                                                \
       while (__a >= 3600) __a -= 3600;                                  \
       while (__a < 0)     __a += 3600;                                  \
       __a; })

/* ==================== 函数声明 ==================== */

/**
 * @brief  读取 MT6701 原始 14-bit 角度值
 * @return 0~16383
 */
uint16_t MT6701_ReadRaw(void);

/**
 * @brief  获取 MT6701 角度 (x10, 0.1° 精度)
 * @return 0~3599 (对应 0.0° ~ 359.9°)
 *         使用 int32_t 整数存储，避免浮点数
 */
int32_t MT6701_GetAngle(void);

#endif /* __MT6701_H__ */
```

### 新建 `App/drivers/mt6701.c`

```c
#include "mt6701.h"
#include "spi.h"        // hspi1

/* ================================================================
 * MT6701 SSI (SPI) 读取
 *
 * 时序:
 *   1. CS↓ (拉低片选)
 *   2. SPI 接收 2 字节 (同时 MOSI 发 0xFF)
 *   3. CS↑ (拉高片选)
 *   4. 从接收数据中提取低 14-bit 角度值
 *
 * SPI 配置 (来自 spi.c):
 *   Master, 8bit, MSB, CPOL=Low, CPHA=2Edge (Mode 1), Prescaler=64 → 1.125MHz
 *
 * ⚠ 重要 — 先验实测确认 (见 build_config_260602.md):
 *
 *   [1] MOSI 数据敏感性: 该模块会读 MOSI。
 *       必须用 HAL_SPI_Receive (内部送 0xFF) 或 HAL_SPI_TransmitReceive 送
 *       {0xFF, 0xFF}。如果送 0x00 → 输出偏移到 8800~16383，范围错误。
 *
 *   [2] SPI Mode: 实测 Mode 1 (CPOL=Low, CPHA=2Edge) 是正确的。
 *       Mode 0 会导致 180~360° 范围异常。当前配置已采用 Mode 1。
 *
 *   [3] 帧格式: 本模块是 [Angle(14) | Extra(2)] 变体:
 *       角度占 bits 15:2 (MSB 先发)，附加位占 bits 1:0。
 *       非标准 Datasheet 排列 [ERR(1)|PAR(1)|Angle(14)]。
 *       提取方式: data >>= 2; return data & 0x3FFF;
 *
 *   [4] 分辨率: 14-bit → 0 ~ 16383 → 0.00° ~ 359.98°
 *       静止稳定性: ±1 LSB (已验证)
 *
 *   [5] 波特率 1.125MHz 通信稳定无丢帧 (72MHz / 64)
 * ================================================================ */
uint16_t MT6701_ReadRaw(void)
{
    uint8_t rx[2] = {0, 0};

    MT6701_CS_LOW();

    /*
     * 注意: 该模块会读 MOSI，HAL_SPI_Receive 内部送 0xFF 才能正确工作
     * 不要改为 HAL_SPI_TransmitReceive 送 0x00 —— 会导致输出偏移到 8800~16383
     */
    HAL_SPI_Receive(&hspi1, rx, 2, 10);

    MT6701_CS_HIGH();

    /*
     * SSI帧: [Angle(14) | Extra(2)]
     *        bit 15          bit 0
     * 角度在 bits 15:2, 需 >>2 提取
     */
    uint16_t data = ((uint16_t)rx[0] << 8) | rx[1];
    data >>= 2;
    return data & 0x3FFF;   // 14-bit 有效角度数据
}

int32_t MT6701_GetAngle(void)
{
    uint16_t raw = MT6701_ReadRaw();
    /* 角度 = raw × 360.0° / 16384
     * x10 整数: raw × 3600 / 16384，避免浮点数 */
    return ((int32_t)raw * 3600) / MT6701_RESOLUTION;
}
```

### 与 `6_mt6701_spi` 测试代码的差异说明

| 要点 | 测试项目 (已验证) | 本生产项目 |
|:----|:-----------------|:----------|
| SPI 引脚 | PA5(SCK), PA6(MISO) | PB3(SCK), PB4(MISO) — SPI1_REMAP |
| 读取函数 | `HAL_SPI_Receive` | 同左 |
| MOSI 数据 | 内部送 0xFF | 同左 |
| 输出方式 | printf → USART1 | CAN 状态帧 0x325 |
| CS 宏定义 | `MT6701_CS_GPIO_Port` (CubeMX 命名) | GPIOA, GPIO_PIN_4 (手动定义) |

---

## 六点五、Step 2.5: 传动比映射函数

### 背景

当前测试阶段 MT6701 磁编码器直接安装在电机轴上（1:1），但在实际部署场景中，
编码器可能安装在**从动轮侧**，通过皮带或齿轮与电机轴连接，此时存在传动比：

| 传动比 (电机:从动轮) | 含义 | 典型场景 |
|:--------------------:|:----:|---------|
| 1:1 | 电机轴与编码器 1:1 转动 | 测试/直驱 |
| 2:1 | 电机转 2 圈，从动轮转 1 圈 | 皮带减速 |
| 4:1 | 电机转 4 圈，从动轮转 1 圈 | 大减速比 |

电机轴角度与编码器角度的关系：

```
电机轴角度 = (编码器角度 × 传动比) 归一化到 0~360°
```

### 新增: `App/drivers/mt6701.h`

```c
/* ====== 传动比配置 ====== */
typedef struct {
    uint16_t numerator;      // 分子（电机侧）
    uint16_t denominator;    // 分母（从动轮侧）
} TransmissionRatio_t;

/* 预定义传动比 */
#define RATIO_1_1  ((TransmissionRatio_t){1, 1})   // 1:1，直连
#define RATIO_2_1  ((TransmissionRatio_t){2, 1})   // 2:1
#define RATIO_4_1  ((TransmissionRatio_t){4, 1})   // 4:1

/* 默认传动比 */
#define MT6701_RATIO_DEFAULT  RATIO_1_1

/**
 * @brief  设置传动比
 * @param  ratio  传动比结构体
 */
void MT6701_SetRatio(TransmissionRatio_t ratio);

/**
 * @brief  获取电机轴角度 (x10, 0.1°精度)
 *         自动应用传动比映射，对调用方透明
 * @return 0~3599 (电机轴 0.0°~359.9°)
 */
int32_t MT6701_GetMotorAngle(void);
```

### 新增: `App/drivers/mt6701.c`

```c
/* ====== 传动比静态变量 ====== */
static TransmissionRatio_t g_ratio = MT6701_RATIO_DEFAULT;

void MT6701_SetRatio(TransmissionRatio_t ratio)
{
    g_ratio = ratio;
}

int32_t MT6701_GetMotorAngle(void)
{
    uint16_t raw = MT6701_ReadRaw();

    /* 1. 编码器原始值 → 角度 x10 */
    int32_t encoder_angle_x10 = ((int32_t)raw * 3600) / MT6701_RESOLUTION;

    /* 2. 应用传动比: 先乘后除保持精度
     *    motor_angle = encoder_angle × (numerator / denominator)
     *    例如 2:1 时，从动轮 180° → 电机轴 180×2 = 360° → 归一化为 0° */
    int32_t motor_angle_x10 = encoder_angle_x10 * (int32_t)g_ratio.numerator
                            / (int32_t)g_ratio.denominator;

    /* 3. 归一化到 0~3599 */
    return ANGLE_NORMALIZE_X10(motor_angle_x10);
}
```

### 在 Encoder_Task 中的使用

将原来 `MT6701_GetAngle()` 替换为 `MT6701_GetMotorAngle()`：

```c
// Before: float angle = MT6701_GetAngle();
// After:  角度已自动应用传动比映射
int32_t angle_x10 = MT6701_GetMotorAngle();
```

### 传动比配置

在初始化阶段配置：

```c
// 配置为 2:1 传动比（电机轴转 2 圈，从动轮编码器转 1 圈）
MT6701_SetRatio(RATIO_2_1);

// 自定义传动比，如 3:1
MT6701_SetRatio((TransmissionRatio_t){3, 1});

// 恢复直连（默认 1:1）
MT6701_SetRatio(RATIO_1_1);
```

### 设计要点

| 要点 | 说明 |
|:----|------|
| **透明性** | 位置闭环始终以电机轴角度为目标，映射函数对上层控制完全透明 |
| **精度** | 14-bit 编码器 × 传动比后中间精度保持（先乘后除） |
| 1:1 | 0.022° / LSB |
| 2:1 | 0.044° / LSB（等效分辨率降低一半） |
| 4:1 | 0.088° / LSB（等效分辨率降低至 1/4） |
| **过零处理** | `ANGLE_NORMALIZE_X10` 确保映射后角度在 0/3600 边界正确 |
| **动态修改** | 运行中可通过 CAN 命令修改，复位后恢复默认 1:1 |
| **线程安全** | 当前未加锁（仅 encoder_task 读取 + init 阶段写入）；如需运行时动态修改，需考虑原子操作或互斥锁 |

---

## 七、Step 3: Motor_t 结构体扩展

### 文件: `App/config/app_globals.h`

在 `Motor_t` 结构体中增加角度控制字段：

```c
typedef struct {
    TB6612_Motor_t hardware;       // 硬件驱动句柄
    PID_Controller pid;            // PID 控制器实例（速度环）

    // 统一的状态反馈与控制量
    float    target_logic_speed;    // 目标逻辑速度 (-100 to 100)
    float    current_logic_speed;   // 实际测量速度
    int32_t  current_ticks;         // 编码器原始计数值（每周期差值）
    int32_t  accumulated_ticks;     // 编码器累计计数值（绝对位置）
    int16_t  pwm_output;            // 当前输出的 PWM 值

    // ====== MT6701 角度控制 (x10 整数, 0.1°精度) ======
    int32_t  target_angle_x10;       // 目标角度 0~3600 (0.0°~360.0°)
    int32_t  current_angle_x10;      // MT6701 当前角度 0~3599
    uint8_t  angle_ctrl_enabled;     // 0=速度模式(默认), 1=角度模式
    // ==================================================

    // 状态检测
    uint8_t  flags;                // 电机状态标志 (MOTOR_FLAG_*)
    uint8_t  stall_counter;        // 连续堵转周期计数
} Motor_t;
```

> `g_motors` 是全局 `.bss` 段变量，启动时自动清零，所以 `angle_ctrl_enabled=0` 是默认值，无需额外初始化代码。`target_angle_x10` 和 `current_angle_x10` 也同理为 0。

### 在 `app_task.c` 的 `Motor_PID_Init` 中（可选，仅作显式文档）

```c
void Motor_PID_Init(Motor_t *motor)
{
    uint8_t idx = (uint8_t)(motor - &g_motors[0]);
    // ... 原有 PID 初始化 ...

    // 角度控制字段显式初始化（bss 已清零，此代码仅为文档）
    motor->target_angle_x10   = 0;
    motor->current_angle_x10  = 0;
    motor->angle_ctrl_enabled = 0;
}
```

---

## 八、Step 4: 角度 PID 参数配置

### 文件: `App/config/app_motor_cfg_new.h`

在 MOTOR1（转向电机）配置区末尾追加：

```c
/* =================================================================================
 *   4. MT6701 角度控制参数（位置外环 PID，仅电机1转向用）
 *      输出为速度 setpoint，喂给速度内环
 * ================================================================================= */
#define MOTOR1_ANGLE_PID_KP                2.0f    // 比例: 10°误差→速度20
#define MOTOR1_ANGLE_PID_KI                0.1f    // 积分: 消除稳态静差
#define MOTOR1_ANGLE_PID_KD                0.005f  // 微分: 抑制过冲
#define MOTOR1_ANGLE_PID_INTEGRAL_LIMIT    10.0f   // 积分限幅
#define MOTOR1_ANGLE_PID_OUTPUT_LIMIT      50.0f   // 最大输出速度 (±50%)
#define MOTOR1_ANGLE_PID_TS                0.05f   // 采样周期 50ms (20Hz)
#define MOTOR1_ANGLE_PID_DERIVATIVE_FILTER_ALPHA 0.3f
```

> 初版参数安全整定：output_limit=50 限制最大转向速度 50%，防止机械冲击。后续根据实测调整。

---

## 九、Step 5: 编码器任务接入角度读取 + 位置外环

### 文件: `App/tasks/encoder_task.c`

在文件头部增加 include：

```c
#include "mt6701.h"
```

### 修改后的 `Encoder_Task` 完整逻辑

```c
void Encoder_Task(void *argument)
{
    Motor_t *motor = (argument != NULL) ? (Motor_t *)argument : &g_motors[0];
    uint8_t  idx   = (uint8_t)(motor - &g_motors[0]);

    TIM_HandleTypeDef *htim_enc = (idx == 0) ? MOTOR1_ENCODER_TIM : MOTOR2_ENCODER_TIM;
    osMutexId_t        myMutex  = (idx == 0) ? motor0_mutexHandle : motor1_mutexHandle;

    HAL_TIM_Encoder_Start(htim_enc, TIM_CHANNEL_ALL);

    /* ====== 位置外环 PID 实例（仅转向电机 idx==0） ====== */
    PID_Controller angle_pid;
    if (idx == 0) {
        PID_Init(&angle_pid,
                 MOTOR1_ANGLE_PID_KP, MOTOR1_ANGLE_PID_KI, MOTOR1_ANGLE_PID_KD,
                 MOTOR1_ANGLE_PID_INTEGRAL_LIMIT, MOTOR1_ANGLE_PID_OUTPUT_LIMIT,
                 MOTOR1_ANGLE_PID_TS, MOTOR1_ANGLE_PID_DERIVATIVE_FILTER_ALPHA);
    }

    int16_t  last_cnt = 0;
    uint32_t last_angle_tick = 0;

    for(;;)
    {
        /* ====== 编码器速度读取 (10ms/100Hz，所有电机) ====== */
        int16_t now  = (int16_t)__HAL_TIM_GET_COUNTER(htim_enc);
        int16_t diff = (int16_t)(now - last_cnt);
        last_cnt = now;

        if (osMutexAcquire(myMutex, osWaitForever) == osOK)
        {
            motor->current_ticks       = -diff;
            motor->accumulated_ticks  += -diff;
            motor->current_logic_speed = ticks_to_logic(-diff);
            osMutexRelease(myMutex);
        }

        /* ====== MT6701 角度读取 + 位置外环 (50ms/20Hz，仅转向电机) ====== */
        uint32_t now_tick = HAL_GetTick();
        if (idx == 0 && (now_tick - last_angle_tick >= 50)) {
            last_angle_tick = now_tick;

            int32_t angle_x10 = MT6701_GetMotorAngle();

            if (osMutexAcquire(myMutex, osWaitForever) == osOK)
            {
                motor->current_angle_x10 = angle_x10;

                if (motor->angle_ctrl_enabled) {
                    /* 角度误差计算（x10 整数，含过零处理） */
                    int32_t angle_error_x10 = motor->target_angle_x10 - angle_x10;
                    angle_error_x10 = ANGLE_NORMALIZE_ERROR_X10(angle_error_x10);

                    /* 死区: <1° (x10=10) 认为到位，停止输出 */
                    if (angle_error_x10 > -10 && angle_error_x10 < 10) {
                        motor->pid.setpoint = 0.0f;
                        PID_Reset(&angle_pid);
                        motor->flags &= ~(MOTOR_FLAG_STALL | MOTOR_FLAG_SATURATED);
                    } else {
                        /* 位置 PID 计算: 将 int32_t 误差转为 float 喂给 PID
                         * setpoint=angle_error, feedback=0
                         * 这样 error = angle_error - 0 = angle_error
                         * 避免了角度过零引起的 setpoint 跳变问题 */
                        float angle_error = (float)angle_error_x10 * 0.1f;
                        PID_SetSetpoint(&angle_pid, angle_error);
                        float speed_setpoint = PID_Compute(&angle_pid, 0.0f);
                        motor->pid.setpoint = speed_setpoint;   // 喂给速度内环
                    }
                }
                osMutexRelease(myMutex);
            }
        }

        /* ====== 日志投递（同现有） ====== */
        LogMotorData_t log_data = {
            .motor_id           = idx,
            .current_ticks      = motor->current_ticks,
            .accumulated_ticks  = motor->accumulated_ticks,
            .target_logic_speed = motor->target_logic_speed,
            .pwm_output         = motor->pwm_output,
            .timestamp_ms       = HAL_GetTick(),
        };
        osMessageQueuePut(LogQueueHandle, &log_data, 0, 0);

        osDelay(10);
    }
}
```

### 关于位置外环 PID 的计算方式

角度存储和传递使用 **int32_t x10 整数定标**（仿照 `logger_task.c` 对 speed 数据的处理），
仅在 PID 计算边界处转换为 float（PID 内核已使用 float，不新增 float 存储）。

使用**误差驱动法**，将角度误差直接作为 PID 的 setpoint，feedback=0：

```
error = setpoint - feedback = angle_error - 0 = angle_error
P = Kp × angle_error     (角度误差 10° × Kp=2.0 → P=20)
I = Ki × ∫(angle_error)  (消除静差)
D = Kd × d(angle_error)  (抑制过冲)
```

对比传统 setpoint=target, feedback=current 方式：
- 传统方式在目标角度跨过 0/360 边界时，setpoint 从 359→0 跳变，微分项会剧烈冲击
- 误差驱动法始终以误差为输入，误差从 -1° 平滑变化到 +1°，无跳变

> **数据流转示意**：
> ```
> MT6701 (raw 14-bit) → int32_t x10 → ANGLE_NORMALIZE_ERROR_X10 → float (PID边界) → speed setpoint
>                              ↑ 存储: Motor_t.current_angle_x10          ↑ 仅在此转 float
>                              ↑ CAN 通信、日志输出全部用 int32_t x10

---

## 十、Step 6: 舵向任务改为速度内环模式

### 文件: `App/tasks/tb6612_DC_task.c`

核心改动：在角度模式下，**不再直接设置 `pid.setpoint`**（由外环写入），仅执行速度内环 PID。

### 关键修改点

#### ① 命令处理分支：CMD_SET_SPEED 时退出角度模式

```c
if (cmdMsg.type == CMD_SET_SPEED || cmdMsg.type == CAN_CMD_SET_SPEED)
{
    motor->angle_ctrl_enabled = 0;           // ← 自动切回速度模式
    float new_setpoint = (float)cmdMsg.value;
    // ... 原有 setpoint 处理 ...
}
```

#### ② 新增 CAN_CMD_SET_ANGLE / CAN_CMD_SET_ANGLE_MODE 处理

```c
else if (cmdMsg.type == CAN_CMD_SET_ANGLE)
{
    // 设置目标角度 (x10 整数, 0.1°精度)，保持当前模式不变
    int32_t new_angle = ANGLE_NORMALIZE_X10(cmdMsg.value);
    motor->target_angle_x10 = new_angle;
}
else if (cmdMsg.type == CAN_CMD_SET_ANGLE_MODE)
{
    motor->angle_ctrl_enabled = (cmdMsg.value != 0) ? 1 : 0;
    if (!motor->angle_ctrl_enabled) {
        PID_Reset(&(motor->pid));            // 退出角度模式时重置速度 PID
        motor->pid.setpoint = 0.0f;
    }
}
```

#### ③ 控制循环增加角度模式分支

```c
if (osMutexAcquire(myMutex, osWaitForever) == osOK)
{
    motor->target_logic_speed = motor->pid.setpoint;

    if (motor->angle_ctrl_enabled) {
        /* ====== 角度模式：仅执行速度内环 ======
         * setpoint 已由 encoder_task 中的位置外环写入
         */
        float current_speed = motor->current_logic_speed;

        if (fabsf(motor->pid.setpoint) > FLT_EPSILON) {
            // 堵转检测（同现有）
            if (fabsf(current_speed) < 1.0f) {
                if (motor->stall_counter < 255) motor->stall_counter++;
                if (motor->stall_counter > 5)
                    motor->flags |= MOTOR_FLAG_STALL;
            } else {
                motor->stall_counter = 0;
                motor->flags &= ~MOTOR_FLAG_STALL;
            }

            float output = PID_Compute(&(motor->pid), current_speed);
            TB6612_Motor_SetSpeed(&(motor->hardware), (int16_t)output);
            motor->pwm_output = motor->hardware.pwm_output;

            // 饱和检测
            if (motor->pwm_output >= (PWM_MAX - 10) &&
                fabsf(current_speed - motor->pid.setpoint) > 10.0f)
            {
                motor->flags |= MOTOR_FLAG_SATURATED;
            } else {
                motor->flags &= ~MOTOR_FLAG_SATURATED;
            }
        } else {
            TB6612_Motor_Stop(&(motor->hardware));
            motor->pwm_output = 0;
            motor->stall_counter = 0;
            motor->flags = 0;
        }
    } else {
        /* ====== 速度模式（同现有完整逻辑） ====== */
        // ... 现有代码保持不变 ...
    }
    osMutexRelease(myMutex);
}
```

### 状态帧数据扩展

在 `command_task.c` 的 `send_motor_status` 中，为转向电机 (mid==0) 增加角度上报：

```c
// 原帧格式 (mid==1 动力电机保持):
// [0-1] current_logic_speed    (int16)
// [2-3] accumulated_ticks      (uint16)
// [4-5] pwm_output             (int16)
// [6]   target_logic_speed     (int8)
// [7]   flags                  (uint8)

// 转向电机 (mid==0) 新帧格式:
// [0-1] current_logic_speed    (int16)
// [2-3] current_angle          (uint16, 乘以10: 0~3599)
// [4-5] pwm_output             (int16)
// [6]   target_angle           (uint8, 1°, 0~255, >255则=0)
// [7]   flags | (angle_ctrl_enabled << 7)   (bit7=角度模式)
```

---

## 十一、Step 7: CAN 协议扩展

### 7.1 命令类型枚举

#### 文件: `App/services/command.h`

```c
typedef enum {
    CMD_NONE = 0,
    CMD_FORWARD = 1,
    CMD_REVERSE = 2,
    CMD_STOP = 3,
    CMD_SET_SPEED = 4,
    CMD_LIST_STATUS = 5,
    CMD_QUERY_STATUS = 6,
    CAN_CMD_SET_SPEED = 7,
    CAN_CMD_STOP = 8,
    CMD_LOG_START = 9,
    CMD_LOG_STOP = 10,
    // ===== MT6701 角度控制 =====
    CAN_CMD_SET_ANGLE = 11,         // 设置目标角度
    CAN_CMD_SET_ANGLE_MODE = 12,    // 切换速度/角度模式
} CommandType_t;
```

### 7.2 CAN 协议宏

#### 文件: `App/config/app_config.h`

```c
// 新增 CAN 命令字节 (沿用 0x11 风格)
#define CAN_CMD_SET_ANGLE                   0x12    // 设置目标角度
#define CAN_CMD_SET_ANGLE_MODE              0x13    // 切换控制模式

// CAN 数据帧索引 (已在底部)
#define CAN_DATA_INDEX_CMD      0   // 命令类型
#define CAN_DATA_INDEX_SPEED    1   // 速度值
#define CAN_DATA_INDEX_ANGLE_LOW  2   // 角度低字节 (新增)
#define CAN_DATA_INDEX_ANGLE_HIGH 3   // 角度高字节 (新增)
#define CAN_DATA_INDEX_MODE      4   // 模式 (新增)
```

### 7.3 CAN 命令路由

#### 文件: `App/tasks/command_task.c`

在 `is_motor_cmd()` 中增加角度命令：

```c
static inline int is_motor_cmd(CommandType_t type)
{
    return type == CMD_FORWARD     || type == CMD_REVERSE      ||
           type == CMD_STOP        || type == CMD_SET_SPEED    ||
           type == CAN_CMD_SET_SPEED|| type == CAN_CMD_STOP    ||
           type == CAN_CMD_SET_ANGLE|| type == CAN_CMD_SET_ANGLE_MODE;
}
```

在与 CAN 中断解包的接口处，增加角度命令的解析（`CAN_CMD_SET_ANGLE` 从 data[2]/data[3] 提取角度值）：

```c
// 在 CAN 接收解析处，假定收到标准 CAN 帧:
// data[0] = 命令类型
// data[1] = motor_id 或速度值
// data[2-3] = 角度值 (int16, 0.1°精度)
// data[4] = 模式

CommandMsg_t cmd = {0};

switch (data[0]) {
    case CAN_CMD_SET_ANGLE:
        cmd.type = CAN_CMD_SET_ANGLE;
        cmd.motor_id = data[1];
        // angle_x10 = (data[2] | data[3]<<8)  // 已为 0.1° 精度 int16
        cmd.value = (int16_t)((data[2]) | (data[3] << 8));  // 0.1°精度
        break;

    case CAN_CMD_SET_ANGLE_MODE:
        cmd.type = CAN_CMD_SET_ANGLE_MODE;
        cmd.motor_id = data[1];
        cmd.value = data[4];   // 0=速度, 1=角度
        break;
    // ... 其他命令 ...
}
```

### 7.4 CAN 数据帧格式

| CAN 命令 | data[0] | data[1] | data[2] | data[3] | data[4] |
|----------|:-------:|:-------:|:-------:|:-------:|:-------:|
| 设置角度 0x12 | `0x12` | motor_id | angle_L | angle_H | - |
| 切换模式 0x13 | `0x13` | motor_id | - | - | mode |

- 角度编码: `angle_x10 = data[3]<<8 | data[2]`，精度 0.1°，范围 0~3600 (0~360.0°)，直接作为 int16 解析
- mode: 0=速度模式, 1=角度模式

### 7.5 状态帧扩展

转向电机 (mid==0) 状态帧 `0x325`：

```
[0-1] current_logic_speed    (int16)  速度反馈
[2-3] current_angle          (uint16, 0.1°精度, 0~3599)
[4-5] pwm_output             (int16)
[6]   target_angle           (uint8,  1°精度, 0~255)
[7]   flags | (angle_ctrl_enabled << 7)
```

动力电机 (mid==1) 状态帧 `0x326`：**不变**

---

## 十二、Step 8: CMakeLists 添加新文件

### 文件: `CMakeLists.txt`

在 `App/drivers` 段下添加 `mt6701.c`：

```cmake
# ===== Drivers (no RTOS dependency) =====
App/drivers/motor_DC_tb6612.c
App/drivers/motor_DC_IBT4.c
App/drivers/mt6701.c                # ← 新增
```

---

## 十三、磁铁检测确认

> **先验重点**：`6_mt6701_spi` 项目实测发现，MT6701 读取正确性高度依赖磁铁的选择和安装。
> 在进入角度集成之前，必须先确认磁铁符合以下要求。

### 13.1 磁铁极对数确认

MT6701 设计配 **1 对极（2 极）径向充磁磁铁**：

| 磁铁参数 | 要求 | 验证方法 |
|---------|------|---------|
| 充磁方向 | **径向** (diametral) | 磁铁标签标注 "diametral" 或 "径向" |
| 极对数 | **1 对极（2 极）** | 手动转一圈，串口看 raw 0→16383→0 **恰好 1 次** |
| 极对数验证 | 如果出 2 次周期 | 说明磁铁是 2 对极（4 极），需更换 |

**确认步骤**：
1. 临时在 main.c 或调试入口中加入 `printf("raw=%u angle_x10=%ld\r\n", raw, (long)angle_x10)`（约 10Hz 输出）
2. 手动匀速旋转磁铁**一整圈（360°）**
3. 观察输出：`raw` 应从 `0→16383→0` 恰好一次
4. 如果出现 2 次完整周期 → 磁铁是 2 对极，需要更换

> **实测参考**：`6_mt6701_spi/csv/test_csv.csv` 确认 360° 内 1 次周期 ✅

### 13.2 磁铁安装检查

| 检查项 | 要求 | 异常现象 |
|-------|------|---------|
| **同轴度** | 磁铁中心与芯片中心对齐 (±0.3mm) | 数值跳变、非均匀步长 |
| **气隙** | 芯片表面到磁铁表面 0.5~2.0mm | 超出范围 → 读数不稳定或为 0 |
| **固定** | 磁铁无松动 | 静止时 raw 跳动 > 2 LSB |
| **干扰** | 附近无强磁场 (电机线圈、大电流) | 角度偏移或抖动 |

**快速测试**: 磁铁静止不动时，角度输出应稳定在 ±1 LSB 以内：

```
raw=2309 angle_x10=507   ← 50.7° (int32_t, 静止稳定)
raw=2309 angle_x10=507
raw=2309 angle_x10=507   ← 静止状态，数值稳定
raw=2309 angle_x10=507
```

如果静止晃动 > 2 LSB，检查安装同轴度或外部磁场干扰。

### 13.3 磁铁类型快速判断

| 肉眼特征 | 极对数 | 是否适配 | 处理方法 |
|---------|-------|---------|---------|
| 标 1 个点 (N 极标记) | 1 对极 | ✅ 适配 | 直接使用 |
| 标 2 个点或无标记 | 可能 2 对极 | ❌ 不适配 | 更换为 1 对极径向磁铁 |
| 条形/矩形磁铁 | 不规则 | ❌ 不适配 | 更换为圆柱形径向磁铁 |

---

## 十四、编译与验证计划

### Phase 0: 磁铁与 SPI 通信验证（在 main.c 中添加临时 printf）

> 在集成到 encoder_task 之前，先在 main.c 中做裸机 SPI 通信验证，确认驱动代码和磁铁正常。

准备工作：
- 角度值使用 int32_t x10 (0~3599) 输出，无需 printf 浮点支持
- 在 main.c 中临时加入角度读取和 printf 输出

```
[ ] 0.1 编译: cmake --build build/Debug
[ ] 0.2 烧录: cmake --build build/Debug --target flash
[ ] 0.3 串口查看 raw 和 angle_x10 输出 (115200-8N1)
[ ] 0.4 验证: 手动转磁铁，raw 0→16383→0 平滑变化，范围正确
[ ] 0.5 验证: 静止时角度稳定在 ±1 LSB
[ ] 0.6 磁铁极对数确认: 360° 内恰好 1 次完整周期
[ ] 0.7 等待输出验证通过后再清理 printf 代码，移入驱动文件
```

预期输出（参考 `6_mt6701_spi` 实测）：

```
raw=0     angle_x10=0     ← 起点 (0°)
raw=2048  angle_x10=450
raw=4096  angle_x10=900   ← 1/4 圈
raw=8192  angle_x10=1800  ← 半圈
raw=12288 angle_x10=2700  ← 3/4 圈
raw=16383 angle_x10=3599  ← 接近一圈 (359.9°)
raw=227   angle_x10=50    ← 过零回到起点附近 (5.0°)
```

> ⚠ **如果出现异常，参考诊断表**：
> - 180~360° 范围异常 → SPI Mode 不对，检查 CPHA
> - 360° 内 2 次 0~16383 → `data >>=` shift 错误
> - 8800~16383 范围 → MOSI 送了 0x00，改回 `HAL_SPI_Receive`（内部送 0xFF）
> - 输出跳变/毛刺 → 磁铁未对中或距离远

### Phase 1: SPI 通信集成验证（在 encoder_task 中）

```
[ ] 1.1 在 encoder_task 中加入 MT6701 读取（仅读角度，不上 PID）
[ ] 1.2 烧录后通过 CAN 状态帧 0x325 的 current_angle 字段查看
[ ] 1.3 验证: 手动转轴，CAN 帧角度实时更新 (20Hz)
[ ] 1.4 验证: 角度 x10 0~3599 连续无跳变
[ ] 1.5 验证: 转一圈回到原位，angle_x10 正确归零
```

### Phase 2: 角度闭环调试

```
[ ] 2.1 CAN 发 0x13 motor_id=0 mode=1 → 进入角度模式
[ ] 2.2 CAN 发 0x12 motor_id=0 angle=900 → 目标 90.0°
[ ] 2.3 观察电机是否转到 90° 并稳定
[ ] 2.4 如振荡: 降 Kp / 升 Kd
[ ] 2.5 如响应慢: 升 Kp / 升 output_limit
[ ] 2.6 测试 0/360 过零: target=10° → 350° → 10°
[ ] 2.7 测试 180° 大角度转向
```

### Phase 3: 综合测试

```
[ ] 3.1 速度模式 ↔ 角度模式切换平滑
[ ] 3.2 角度模式下 CAN 发 CMD_SET_SPEED → 自动切回速度模式
[ ] 3.3 角度模式下 CAN 发 CMD_STOP → 停止 + 恢复速度模式
[ ] 3.4 同时控制动力电机 (CAN 0x126)，互不干扰
[ ] 3.5 连续运行 30 分钟，角度不漂移
```

---

## 十五、附录

### 15.1 数据帧结构（先验实测确认）

`6_mt6701_spi` 实测确认该模块的 SSI 16-bit 帧格式：

```
       bit 15                   bit 0
       +------------------------------+
       |  14-bit Angle   |  Extra   |
       |  (bits 15:2)    | (bits 1:0)|
       +------------------------------+
          ^                  ^
       MSB 先发           LSB 后发
```

**提取方式**: `data >>= 2; return data & 0x3FFF;`

角度范围: **0 ~ 16383** (14-bit)，对应 **0.00° ~ 359.98°**

对比标准 MT6701 数据手册的常见帧格式：

| 帧格式 | 说明 | 本模块 |
|--------|------|:------:|
| `[ERR(1) | PAR(1) | Angle(14)]` | 标准手册格式: 状态位在高位 | ❌ 不符 |
| `[Angle(14) | Extra(2)]` | 角度在高位, 需 >>2 | ✅ **实测匹配** |

> 说明该模块不是标准 DataSheet 排列，而是角度在 MSB 侧、附加位在 LSB 侧的变体。

### 15.2 MOSI 数据敏感性（先验实测确认）

| 条件 | 输出范围 | 结论 |
|------|---------|------|
| MOSI 送 0xFF (`HAL_SPI_Receive`) | 0~16383 ✅ | 模块正常工作 |
| MOSI 送 0x00 (`HAL_SPI_TransmitReceive` 送 `{0x00,0x00}`) | 8800~16383 ❌ | 该模块会读 MOSI 数据 |

**结论**: 必须使用 `HAL_SPI_Receive`（内部送 0xFF），不要使用 `HAL_SPI_TransmitReceive` 送 0x00。

### 15.3 角度误差过零处理 (x10 整数版)

```c
// 场景: target=3500 (350.0°), current=100 (10.0°)
// 普通减法: 3500 - 100 = 3400  (错误，应走 -200 → -20.0°)
// 归一化后: 3400 > 1800 → 3400 - 3600 = -200 → -20.0° ✅
int32_t error = target_x10 - current_x10;
if (error > 1800)  error -= 3600;
if (error < -1800) error += 3600;
```

### 15.4 位置外环 PID 误差驱动法

角度存储和通信用 int32_t x10 整数（仿照 logger_task.c 定标做法），
在喂给 PID 时转 float（因 PID 内部已使用 float，不新增 float 存储）：

```c
// 角度误差使用 int32_t 计算（避免浮点数）
int32_t angle_error_x10 = target_x10 - current_x10;
angle_error_x10 = ANGLE_NORMALIZE_ERROR_X10(angle_error_x10);

// 仅在 PID 边界转 float（PID 内部已使用 float）
float angle_error = (float)angle_error_x10 * 0.1f;
PID_SetSetpoint(&angle_pid, angle_error);
float speed_out = PID_Compute(&angle_pid, 0.0f);   // feedback = 0
```

PID 内部：`error = setpoint - feedback = angle_error - 0 = angle_error`

优点：
- 不存在 setpoint 跳变（target_angle 突变时，error 平滑过渡）
- 0/360 过零问题已在归一化中解决
- 微分项不会产生冲击

### 15.5 到达判定（可选增强）

```c
#define ANGLE_SETTLED_THRESHOLD_X10  20    // 到位误差阈值 (x10, 即 2.0°)
#define ANGLE_SETTLED_TIME_MS        100   // 持续到位时间

// 在位置外环中:
if (angle_error_x10 > -ANGLE_SETTLED_THRESHOLD_X10 && angle_error_x10 < ANGLE_SETTLED_THRESHOLD_X10) {
    if (angle_settled_tick == 0)
        angle_settled_tick = HAL_GetTick();
    else if (HAL_GetTick() - angle_settled_tick >= ANGLE_SETTLED_TIME_MS) {
        motor->pid.setpoint = 0.0f;     // 已到位，停转
        // 可选: 通过 CAN 状态帧的 bit 上报"到位"标志
    }
} else {
    angle_settled_tick = 0;
}
```

### 15.6 调参速查

| 现象 | 调参 |
|------|------|
| 响应慢，到位时间长 | ↑ `Kp`, ↑ `output_limit` |
| 过冲大，反复震荡 | ↓ `Kp`, ↑ `Kd` |
| 有静差（差几度到不了） | ↑ `Ki` |
| 到位后微振/抖动 | ↑ 死区角度, ↓ `Ki` |
| 转向时咔咔声 | ↓ `output_limit` (限速), ↑ `derivative_filter_alpha` |

安全起步参数：`Kp=1.0`, `output_limit=30`，确认机械正常后再逐步增加。

### 15.7 编译资源占用参考（来自 `6_mt6701_spi`）

| 项目 | 大小 | 占比 |
|------|------|------|
| Flash (text+data) | 33,460 B | 51.1% (64KB) |
| RAM (data+bss) | 3,248 B | 15.9% (20KB) |

> 角度数据使用 int32_t x10 整数输出，不再需要 `_printf_float`（相比旧版节省约 12KB Flash）。

### 15.8 与 `6_mt6701_spi` 测试项目的迁移对照

| 要点 | 测试项目 | 生产项目 |
|:----|:---------|:---------|
| SCK/MISO 引脚 | PA5/PA6 (SPI1 默认) | PB3/PB4 (SPI1_REMAP) |
| CS 引脚 | PA4 (CubeMX 命名 `MT6701_CS_GPIO_Port`) | PA4 (手动 GPIO Init) |
| CS 宏 | `MT6701_CS_GPIO_Port, MT6701_CS_Pin` | `GPIOA, GPIO_PIN_4` |
| SPI 句柄 | `hspi1` | `hspi1` (相同) |
| 读取函数 | `HAL_SPI_Receive` (送 0xFF) | `HAL_SPI_Receive` (送 0xFF) — **相同，已验证** |
| 帧提取 | `data >>= 2; return data & 0x3FFF` | 同左 |
| 输出方式 | printf 串口 | CAN 状态帧 0x325 |
| 角度数据格式 | float (printf 输出) | int32_t x10 整数 (CAN 状态帧) |
| 磁铁极对数验证 | 已确认 1 对极 | 需重新确认（不同电机轴） |

---

### 参考文档

- [build_config_260602.md](../../../../../6_MT6701/6_mt6701_spi/doc/build_config_260602.md) — 先验项目完整构建与测试记录
- [test_csv.csv](../../../../../6_MT6701/6_mt6701_spi/csv/test_csv.csv) — 实测 232 行角度数据
- [goal_260602.md](../../../../../6_MT6701/6_mt6701_spi/doc/goal_260602.md) — 先验项目原始目标
- [CSDN: STM32HAL库使用SPI读取MT6701传感器数据](https://blog.csdn.net/yaolei5/article/details/155005022)
- [CSDN: HAL STM32 SSI/SPI方式读取MT6701磁编码器获取角度例程](https://blog.csdn.net/weixin_42880082/article/details/137921359)
