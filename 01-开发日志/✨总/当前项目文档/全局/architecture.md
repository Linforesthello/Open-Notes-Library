# 机器人微控制器项目架构文档

## 概述

基于 STM32F103C8T6（Cortex-M3）的机器人控制系统，采用模块化分层架构，覆盖传感器采集、底盘控制、电机驱动、CAN/USART 通信等功能。

## 硬件平台

| 项目 | 规格 |
|------|------|
| MCU | STM32F103C8T6, Cortex-M3, 72MHz |
| 封装 | LQFP48 |
| Flash/RAM | 64KB / 20KB |
| IDE/构建 | STM32CubeMX + CMake + GCC (Linux) |
| 调试 | JLink OB + Ozone |
| RTOS | FreeRTOS (CMSIS v2 封装) |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    上层控制器 (ROS/PC)                       │
│                      USART / CAN                            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              5_ChassisController_t1 (底盘控制器)             │
│          USART 命令解析 → 环缓冲区 → FreeRTOS 任务调度       │
└───────┬─────────────────────────────────────┬───────────────┘
        │ CAN Bus                              │ CAN Bus
┌───────▼──────────────────┐   ┌──────────────▼────────────────┐
│ 3_MCLM_t2 (电机控制器)   │   │   其他 CAN 节点               │
│ ┌──────────────────────┐ │   │   (传感器/执行器)              │
│ │ App/tasks/           │ │   │                                │
│ │ ├── command_task     │ │   │                                │
│ │ ├── at8236_DC_task   │ │   │                                │
│ │ ├── tb6612_DC_task   │ │   │                                │
│ │ ├── encoder_task     │ │   │                                │
│ │ ├── heartbeat_task   │ │   │                                │
│ │ ├── logger_task      │ │   │                                │
│ │ └── Ack_task         │ │   │                                │
│ ├── App/modules/       │ │   │                                │
│ │ ├── pid              │ │   │                                │
│ │ ├── filter           │ │   │                                │
│ │ └── speed_map        │ │   │                                │
│ ├── App/services/      │ │   │                                │
│ │ ├── command          │ │   │                                │
│ │ ├── can_filter       │ │   │                                │
│ │ └── logger           │ │   │                                │
│ └── App/drivers/       │ │   │                                │
│   ├── motor_DC_at8236  │ │   │                                │
│   └── motor_DC_tb6612  │ │   │                                │
└──────────────────────────┘   └────────────────────────────────┘
```

## 模块说明

### 核心控制模块

| 模块 | 路径 | 功能 |
|------|------|------|
| **底盘控制器** | `5_ChassisController_t1` | USART 接收上层命令，环形缓冲区解析，FreeRTOS 任务调度，通过 CAN 转发至电机控制器 |
| **电机控制器** | `3_MCLM_t2` | CAN 接收控制指令，PID 闭环控制直流电机 (AT8236/TB6612)，编码器反馈，心跳/日志上报 |

### 传感器模块

| 模块 | 路径 | 通信 | 功能 |
|------|------|------|------|
| **MPU6050** | `6_Mpu6050/6_Mpu6050_t1` | I2C | 6 轴姿态 (加速度 + 陀螺仪) |
| **BMP280** | `6_BMP280/6_BMP280_t1` | I2C/SPI | 气压/温度 |
| **AK09911C** | `6_AK09911C/6_AK09911C_test` | I2C | 3 轴磁力计 (电子罗盘) |
| **VL53L0X** | `6_VL53L0/6_VL53L0XV2_test` | I2C | 激光测距 (ToF) |
| **MT6701** | `6_MT6701/6_MT6701_test` | I2C/SSI | 磁编码器 (角度) |

### 外设驱动模块

| 模块 | 路径 | 功能 |
|------|------|------|
| USART 通信 | `5_Tec_USART` | DMA + 中断方式串口收发 |
| CAN 总线 | `5_Tec_CAN` | CAN 协议栈，滤波配置 |
| ADC 采样 | `5_Tec_ADC` | DMA 多通道模拟量采集 |
| 编码器 | `5_Tec_Encoder` | 正交编码器接口 |
| I2C 传感器 | `5_Tec_IIC` | I2C 总线驱动 |
| 直流电机 | `6_DC_Motor` | 直流电机驱动 (AT8236/TB6612) |
| LED | `6_LED_PC13_` | 板载 LED 及扩展指示 |
| 按键 | `6_KEY_PC13` | 按键输入与中断处理 |
| 摇杆 | `6_Joystick_Module` | 双轴摇杆 ADC 采样 |

## 软件架构分层

每个 CMake 项目遵循统一目录结构：

```
<project>/
├── CMakeLists.txt          # 构建配置
├── CMakePresets.json       # CMake 预设
├── Core/                   # CubeMX 生成的 HAL 层
│   ├── Inc/                #   头文件
│   └── Src/                #   源文件 (main.c, freertos.c, stm32f1xx_*.c)
├── App/                    # 应用层 (用户代码)
│   ├── config/             #   全局配置 (app_config.h, app_globals.h)
│   ├── tasks/              #   FreeRTOS 任务
│   ├── modules/            #   功能模块 (PID, Filter, 算法)
│   ├── services/           #   服务层 (Command, CAN Filter, Logger)
│   └── drivers/            #   外设驱动抽象 (电机驱动芯片)
├── Drivers/                # STM32 HAL 驱动库
├── Middlewares/             # FreeRTOS 中间件
├── cmake/                  # CMake 辅助脚本
└── doc/                    # 开发文档
```

### 架构原则

- **Core/** — CubeMX 自动生成，不手动修改
- **App/config/** — 全局配置开关与参数
- **App/tasks/** — 每个 FreeRTOS 任务独立文件(c/h)，由 app_task.c 统一创建
- **App/modules/** — 无状态算法模块 (PID, 滤波器)
- **App/services/** — 有状态服务 (命令解析, CAN 滤波)
- **App/drivers/** — 硬件驱动抽象层 (隔离底层 HAL)

## 通信协议

### USART (底盘控制器 ←→ 上层)

```
上层 (ROS/PC) ──USART──▶ 5_ChassisController_t1 ──CAN──▶ 3_MCLM_t2
```

- USART 采用 DMA 环形缓冲区接收
- 命令格式：帧头 + ID + 数据 + 校验
- FreeRTOS 队列进行任务间通信

### CAN (电机控制器)

- CAN 2.0, 标准帧 11bit ID
- 功能：控制指令下发、状态反馈、心跳检测
- 支持 CAN 滤波 (can_filter 模块)
- 支持 CAN FD 扩展预留

## 构建系统

- **构建工具**: CMake + Ninja
- **工具链**: arm-none-eabi-gcc 14.3.1
- **代码分析**: clangd (st-arm-clangd 19.1.2+)
- **调试**: JLink + Ozone / ST-Link + CubeProgrammer
- **下载**: `flash.jlink` 脚本一键烧录

## 开发环境

| 工具 | 用途 |
|------|------|
| Ubuntu 22.04.5 | 开发主机系统 |
| STM32CubeMX | 外设配置与代码生成 |
| VS Code | 主要 IDE |
| CMake + Ninja | 构建系统 |
| JLink OB | 调试器 |
| Ozone | 调试器 UI |
| SavvyCAN / canable | CAN 总线分析 |
| Git + GitHub | 版本管理 |

## 文档与 AI 协作

项目开发中大量使用 AI 辅助编程，相关文档存储在各自 `doc/` 目录下：

- `doc/all/` — 功能迭代记录（goal/result/fix）
- `doc/Fix/` — Bug 修复记录
- `doc/ai_session/` — AI 协作对话记录
- `doc/DesignComparison/` — 设计方案对比

## 工作区配置

当前 VS Code 工作区文件：`robot.code-workspace`（位于项目根目录）

包含模块：MPU6050、BMP280、AK09911C、VL53L0、MT6701、LED、电机控制器(3_MCLM_t2)、底盘控制器(5_ChassisController_t1)
