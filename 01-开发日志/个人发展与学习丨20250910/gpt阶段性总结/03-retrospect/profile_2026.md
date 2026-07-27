# 个人技术栈与方向总结（2026-07）

> 本文档综合了项目代码、工程文档、235 篇个人日志以及 ChatGPT 能力评估，形成一份完整的个人技术画像。
> 
> **定位**：机器人系统工程师（Robotics System Engineer），倾向具身智能方向
> **成长周期**：2025-09 → 2026-07（10 个月，从零到参赛）
> **核心项目**：四舵轮底盘 + R2 舵机臂 + CAN 分布式控制系统

---

## 一、我是谁

### 一句话

> 能够从底层电机控制一路做到上层 AI 部署，能把「传感器→嵌入式→通信→ROS→感知→控制→真机」串起来的机器人系统开发者。

### 能力模型

```
                    ┌──────────────┐
                    │   系统集成    │   ← 最大优势：跨层打通
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
     ┌─────┴────┐   ┌─────┴────┐   ┌─────┴────┐
     │ 嵌入式/控制│   │ ROS/感知  │   │  AI/RL   │
     │ ★★★★☆    │   │ ★★★☆☆    │   │ ★★★☆☆   │
     └───────────┘   └───────────┘   └──────────┘
```

### 技术栈雷达

```
                 嵌入式(STM32/CAN/FreeRTOS)
                      ★★★★☆
                         │
            AI部署 ★★★★☆─┼─★★★☆☆ ROS
                         │
                  SLAM ★★★★☆
                   
       RL ★★★☆☆     硬件集成 ★★★★★    控制理论 ★★★☆☆
```

---

## 二、技术栈逐项评估

### 2.1 嵌入式系统 ★★★★☆

**掌握程度**：独立设计 → 需要查阅 ← 了解概念

```
独立设计 ◄━━━━━━━★━━━━━► 需要查阅
```

| 技能 | 等级 | 证据 |
|:-----|:----:|:------|
| STM32F103C8T6 | ★★★★★ | 完整项目10+，CAN/FreeRTOS/UART/DMA/PWM/ADC |
| FreeRTOS (CMSIS-V2) | ★★★★☆ | 任务/队列/信号量/互斥锁，踩过 stack overflow 和 mutex 死锁 |
| CAN 协议 | ★★★★☆ | 1Mbps 标准帧，多节点分布式架构，硬件滤波/屏蔽 |
| 电机控制 (PID) | ★★★★☆ | 速度闭环，系统辨识 97.75%，双环 PI，堵转保护 |
| 编码器 | ★★★★☆ | MT6701(SPI), TIM-Encoder, ABZ, 回绕处理 |
| MCU 驱动开发 | ★★★☆☆ | AT8236/TB6612/IBT4 驱动芯片适配 |
| CMake + GCC | ★★★★☆ | 工具链完整，跨平台编译，clangd 集成 |

**关键项目**：
- **3_MCLM_t2** — 分布式电机控制器，CAN 接收→PID→PWM 输出，每板 2 电机
- **5_ChassisController_t1** — UART↔CAN 网关（未完全竣工）
- **6_MT6701** — SPI 绝对角度编码器驱动，14bit，双 CS 分时
- **6_Mpu6050** — I2C + Mahony 姿态融合

**踩坑经验**：
- CubeMX 生成代码会静默删除 DMA 配置 ✅
- STM32F1 APB1 定时器时钟翻倍规则（×2 当分频≠1）✅
- FreeRTOS 队列溢出/mutex 死锁排查方法 ✅
- CAN 共地噪声 → 单点接地解决 ✅
- JLink 不接 GND 烧录失败 ✅

---

### 2.2 ROS / 机器人软件 ★★★☆☆

| 技能 | 等级 | 证据 |
|:-----|:----:|:------|
| ROS1 Noetic | ★★★★☆ | LiDAR/Gmapping/Hector/Cartographer，树莓派实机部署 |
| ROS2 Humble | ★★★☆☆ | 桥接节点(chassis_can_node.py)，话题发布/订阅 |
| SLAM | ★★★★☆ | Gmapping/Hector/Cartographer/RTAB-Map，了解 FAST-LIO |
| tf2 / URDF | ★★☆☆☆ | 基础理解，需要加强 |
| Nav2 | ★☆☆☆☆ | 未深入 |
| MoveIt2 | ★☆☆☆☆ | 仅尝试 demo |

**关键项目**：
- `chassis_can_node.py` — ROS2 → CAN 桥接，订阅 /cmd_vel
- 树莓派 Docker 部署 ROS2 Humble
- LiDAR SLAM 实机建图

---

### 2.3 AI 部署 ★★★★☆

| 技能 | 等级 | 证据 |
|:-----|:----:|:------|
| PyTorch | ★★★☆☆ | YOLOv8 训练/部署 |
| TensorRT | ★★★☆☆ | Jetson Nano ssd-mobilenet, DeepStream 尝试 |
| ONNX | ★★★☆☆ | 模型转换，RL policy 导出 |
| Jetson Nano | ★★★★☆ | JetPack, CUDA 10.2, Docker, YOLO/DeepStream |
| YOLO | ★★★★☆ | 从训练到部署全流程，摄像头 pipeline 优化 |

**关键项目**：
- Jetson Nano 上 YOLOv8 + DeepStream 部署
- SSD-MobileNet 实时目标检测（~6.7 FPS on Nano）
- YOLO 排球检测训练（mAP50 0.995, RTX 3050 Ti）

---

### 2.4 强化学习 ★★★☆☆

| 技能 | 等级 | 证据 |
|:-----|:----:|:------|
| UniLab RL | ★★★☆☆ | Go2JoystickFlat, APPO, ONNX policy |
| Sim2Real 概念 | ★★☆☆☆ | 理解但未实践 |
| Isaac Sim | ★☆☆☆☆ | 未深入 |

**方向**：四足机器人 RL，与现有硬件（STM32 控制 + CAN 协议）有较高匹配度

---

### 2.5 传感器与硬件集成 ★★★★★

这是最大优势：

| 硬件 | 经验深度 |
|:-----|:---------|
| LiDAR (RPLIDAR/LD06) | ROS 驱动、SLAM 建图 |
| Velodyne VLP-16 | 驱动、点云处理 |
| Livox MID70 | 非重复扫描、FAST-LIO 方向 |
| RealSense (D430/D435/D435i/D455) | 拆模块、刷固件、标定、D430→D435 改装 |
| Astra Pro | ROS1/ROS2 驱动、彩色点云融合 |
| IMU | MPU6050, WitMotion, Mahony 融合 |
| CAN 分析 (SavvyCAN/CANable) | 总线监控、协议逆向 |
| E34 无线串口 | 跳频模式、距离测试(4F→2F) |
| JLink/Ozone | 调试、RTOS 感知、HardFault 分析 |
| Saleae Logic | 时序分析、协议抓取 |

---

## 三、项目体系

### 3.1 核心项目：Robocon 2026 机器人控制系统

```
架构层级：      PC(Python/ROS) ──CAN──▶ STM32 分布式电机控制器 ──▶ 电机
                            ▲
                            │
                        E34 无线串口 (遥控)
```

| 子系统 | 内容 | 完成度 |
|:-------|:-----|:------:|
| R1 底盘 | 四舵轮 × (转向+驱动) = 8 电机 | ✅ 三舵实车跑通 |
| R2 舵机臂 | J1/J2/J3，MT6701 编码器 | ✅ 完全适配 |
| 遥控 | E34 无线串口 + Windows 键盘 | ✅ 完整可用 |
| 传感器群 | MPU6050/AK09911/BMP280/VL53L0/MT6701 | ✅ 全部驱动完成 |

**关键数字**：
- 10+ 电机 / 6+ CAN 节点 / 20+ STM32 子项目
- 项目文档 30+ 篇 / 个人日志 235 篇（~51K 字 + 787 张图）
- 开发周期 10 个月，从零基础起步

### 3.2 并行项目

- **RC 四足狗** — STM32F103/F405/H750 三平台，CAN 协议复用
- **ESP32 + SimpleFOC** — BLDC 角度闭环，AS5600 编码器
- **Jetson Nano + YOLO** — 边缘 AI 推理部署

---

## 四、优势与劣势

### 优势

1. **系统跨度** — 从电机 PWM 到 YOLO 部署到 RL policy，全线贯通。不是"某个单点强"，而是"能跨层调试"
2. **追底层** — 不满足"买 D435"，而是研究 D430+RGB 为什么能识别成 D435、固件怎么标定
3. **工程 debug 能力** — 不是问"这是什么"，而是问"为什么这样"。CAN 终端电阻、雷达倒挂、Jetson 瓶颈、ROS 网络——都是实际工程问题
4. **文档习惯** — 235 篇日志 + 30+ 篇项目文档 + 787 张截图。从"截图为主"进化到"文字+代码+图片"
5. **自学驱动** — 教材路线 → "发现问题→查资料→买设备→实验→总结→扩展"，典型工程成长路径

### 劣势

1. **技术面过宽 → 深度不足** — MCU/ROS/SLAM/AI/RL/机械/通信都有涉及，但到源码级别的深入不够
2. **数学基础需补** — 线代（矩阵/SVD/SO3/SE3）、概率（Bayes/Kalman）、优化（least square/factor graph）
3. **C++ 偏弱** — 当前偏 Python，机器人核心（Eigen/PCL/OpenCV/ROS2 C++）需要强化
4. **容易设备驱动** — 新硬件容易吸引注意力，ChatGPT 警告"不要成为设备收藏者"
5. **端到端闭环不够完整** — 单项能力强，但"传感器→ROS→MCU→电机→反馈→ROS"的完整链条未正式验证通过

---

## 五、推荐方向

### 第一选择：具身智能机器人系统工程师

```
ROS2 + SLAM + Vision + RL + Embedded + Real Robot
——全栈匹配度最高
```

### 第二选择：四足机器人算法工程师

```
Isaac Sim + RL + Locomotion + Perception
——已有 UniLab 经验，匹配度 ★★★★★
```

### 第三选择：自主移动机器人工程师

```
LiDAR + SLAM + Navigation + Control
——经验最直接，匹配度 ★★★★★
```

---

## 六、未来 3 个月重点

| 方向 | 具体任务 | 优先级 |
|:-----|:---------|:------:|
| **ROS2 C++** | rclcpp / TF2 / Nav2 / 生命周期节点 | P0 |
| **SLAM 源码** | FAST-LIO2 源码阅读→修改→接入自己传感器 | P0 |
| **数学** | 线代(SVD/SO3) + Kalman Filter + 图优化 | P1 |
| **工程项目** | 打通完整端到端链路：ROS2→CAN→电机→反馈→ROS2 | P1 |
| **Isaac Sim** | URDF→USD→PhysX→Domain Randomization | P2 |

---

*文档日期：2026-07-27*
*来源：项目代码 + 项目文档 + 235 篇个人日志 + ChatGPT 能力评估 + 项目复盘*
