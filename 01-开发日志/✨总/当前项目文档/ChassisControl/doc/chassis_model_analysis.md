# 底盘构型分析与网关抽象层设计

> 本文档从「数据处理与整合中心」的定位出发，阐述 ChassisController 作为 UART↔CAN 网关对上（计算机板卡）对下（电机控制器）的数据流设计。

---

## 一、物理架构

本网关服务于两类底盘构型，对外暴露统一接口：

```
上层计算机 (PC / 树莓派 / Jetson)
  ┃ UART (115200)
  ▼
┌──────────────────────────────────────────────────┐
│  ChassisController (STM32F103)                    │
│  角色：数据处理与整合中心 / 运动学抽象层            │
└────────────────────┬─────────────────────────────┘
                     ┃ CAN
                     ▼
┌──────────────────────────────────────────────────┐
│  下层：CAN 总线上的 MCLM_t2 电机控制器             │
├──────────────────────────────────────────────────┤
│  构型 A：舵轮底盘   │  构型 B：四全向轮底盘        │
│  2~4 个动力单元     │  4 个全向轮                  │
│  每单元 = 驱动+转向  │  每轮 = 1 个电机            │
│  共 4~8 个电机       │  共 4 个电机                │
└──────────────────────────────────────────────────┘
```

---

## 二、两种底盘构型详解

### 构型 A：舵轮底盘（Steering Wheel）

```
          动力单元1               动力单元2
        ┌────────┐             ┌────────┐
        │ ⚙️驱动  │             │ ⚙️驱动  │
        │ 🛞转向   │             │ 🛞转向   │
        └────────┘             └────────┘
             车  体  中  心
        ┌────────┐             ┌────────┐
        │ ⚙️驱动  │             │ ⚙️驱动  │
        │ 🛞转向   │             │ 🛞转向   │
        └────────┘             └────────┘
          动力单元3               动力单元4
```

- 每个**动力单元**由两个电机构成：**驱动电机** + **转向电机**
- 一车配置 2~4 个动力单元，对应 4~8 个电机
- 驱动电机控制轮子转速，转向电机控制轮子朝向
- 运动学模型：每个单元的驱动力和转向角合成车体速度矢量

### 构型 B：四全向轮底盘（Omni-wheel）

```
          ╱  ①  ╲
         ╱  ↑    ╲
     ④ ╱  中心   ╲ ②
         ╲  ↓    ╱
          ╲  ③  ╱
```

- 4 个电机，轴向外射，延长线交于车体中心
- 运动学模型：标准四轮全向模型（麦克纳姆轮或全向轮）
- 无需转向机构，每个轮子独立控制正反转

---

## 三、核心设计原则

### 3.1 网关不是管道

| 错误做法 | 正确做法 |
|---------|---------|
| `CAN RX \| ID: 0x323 \| Data: 20 00 4E 00 ...` 原始帧直接上抛 | 原始字节 → 解码 → 融合 → 抽象为车体级消息 |
| 每 50ms 收到就每 50ms 转发 | 按需上报，限频，事件驱动 |
| 上报 `Motor0 speed=32` 这类电机级数据 | 上层只关心车体级数据 `vx/vy/omega` |

### 3.2 上层不感知底盘构型

上层计算机看到的接口是**构型无关**的：

```
发:   vx, vy, omega, 急停, 模式选择        ← 车体速度指令
收:   vx, vy, omega, estop, 事件, 里程     ← 车体速度反馈
```

- 上层不关心下面有几个电机
- 上层不关心是舵轮还是全向轮
- 上层不关心运动学怎么算的

### 3.3 网关是数据处理与整合中心

网关在数据流中执行四层处理：

```
输入（CAN 原始帧）             网关处理逻辑                  输出（UART 给上层）
────────────────────      ──────────────────      ──────────────────────────
0x323: 20 00 4E 00      一级 · 解码                  不需要直接输出
00 00 32 00             → speed=32, pwm=78,          解码后数据存入 SystemState
                          target=50, flags=0         内部消化，供后续处理
                         
SystemState.motor[]      二级 · 融合 
转向电机: speed=32       → 运动学正解                  CHASSIS_STATE:
动力电机: speed=-20       → 车体 vx, vy, omega         vx=0.48, vy=0.02, omega=0.49
共同作用                              
                         
Motor[0].flags=STALL     三级 · 推理                   
+ motor[0].speed=0       → "转向电机堵转"              EVENT: type=STALL motor_idx=0
+ motor[0].pwm=100                                            

accumulated_ticks[]      四级 · 推导
各电机累计脉冲            → 换算为车体移动距离           ODOM: x=1.23, y=0.45, heading=15.2°
```

---

## 四、数据流完整设计

### 4.1 上行：上层 → 下层（命令下发）

```
上层 → UART
  │  AA 0x20 [vx_f][vy_f][omega_f] ...
  ▼
CommandProcess_Task
  │  提取 vx, vy, omega（车体速度指令）
  │  根据 g_chassis_cfg.type 选择运动学模型
  │  ├─ 构型 A（舵轮）   → 逆解 → 各动力单元的驱动速度 + 转向角度
  │  └─ 构型 B（全向轮） → 逆解 → 4 个电机各自的目标速度
  │  更新 SystemState.chassis.target
  │  各电机分别构建 CAN 帧 → canTxQueue
  │  回传 CMD_ACK
  ▼
UartToCan_Task → CAN 总线 → MCLM_t2 各电机控制器
```

### 4.2 下行：下层 → 上层（状态反馈）

```
CAN 总线 ← MCLM_t2（每 50ms 主动上报状态帧）
  │  0x323: 电机0 状态帧
  │  0x324: 电机1 状态帧
  ▼
CanRxProcess_Task
  │  decode_motor_status() → SystemState.motor[i]
  │  根据构型做运动学正解
  │  ├─ 构型 A（舵轮）   → 各单元驱动+转向 → 车体 vx, vy, omega
  │  └─ 构型 B（全向轮） → 4 轮速度 → 车体 vx, vy, omega
  │  ↓  更新 SystemState.chassis.current
  │  异常检测（超时 / 堵转 / PWM饱和 / 通信丢失）
  │  ↓  eventQueue
  ▼
Report_Task（周期 20Hz）
  │  读取 SystemState.chassis.current
  │  → CHASSIS_STATE 帧 → uart1_send
  │
  ▼
Event_Task（事件驱动）
  │  阻塞等待 eventQueue
  │  → 有事件立即打包 EVENT 帧 → uart1_send
```

### 4.3 往上层发送的消息清单

**CHASSIS_STATE（P0，周期 20Hz，与 MCLM 状态帧同步）**

状态反馈的核心消息，网关将下层各电机速度经运动学正解后，上报**车体速度矢量**。

```
CHASSIS_STATE | vx=0.48 vy=0.02 omega=0.49 estop=0 mode=1 uptime=30s
```

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `vx` | float | m/s | 车体前进方向速度 |
| `vy` | float | m/s | 车体侧向速度 |
| `omega` | float | rad/s | 车体旋转角速度 |
| `estop` | uint8 | — | 急停状态（0=正常，1=已触发） |
| `mode` | uint8 | — | 当前系统模式 |
| `uptime` | uint32 | seconds | 系统运行时间 |

**上层收到这个消息后**，不需要再问"电机怎么样了"——它直接知道**车体在怎么运动**。

---

**EVENT（P0，事件触发）**

异常事件主动上报，网关检测到异常后立即通知上层。这是安全关键路径。

```
EVENT | type=STALL motor_idx=0 msg="转向电机可能堵转"
EVENT | type=MOTOR_LOST motor_idx=1 msg="动力电机通信丢失"
EVENT | type=ESTOP_TRIGGERED msg="紧急停止已触发"
EVENT | type=QUEUE_DROP queue=canTxQueue count=5 msg="CAN 发送队列丢帧"
```

| 事件类型 | 检测条件 | 安全等级 |
|----------|---------|---------|
| `STALL` | 目标速度 ≠ 0 但当前速度 = 0，且 PWM > 90% | ⚠️ **高** |
| `MOTOR_LOST` | 超过 200ms 未收到电机的状态帧 | ⚠️ **高** |
| `ESTOP_TRIGGERED` | 收到急停命令或急停标志置位 | 🚨 **最高** |
| `QUEUE_DROP` | 消息队列入队失败 | ⚠️ 中 |
| `PWM_SATURATED` | PWM 输出 ≥ 100% 但速度未达到目标 | ℹ️ 低 |
| `MODE_CHANGE` | 系统模式切换 | ℹ️ 低 |

---

**CHASSIS_ODOM（P1，周期 20Hz）**

里程计信息，将电机累计脉冲换算为车体位姿。这是导航和定位的基础。

```
CHASSIS_ODOM | x=1.23 y=0.45 heading=15.2 speed=0.5 
```

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `x, y` | float | meters | 车体在平面上位置（从启动开始累计） |
| `heading` | float | degrees | 车体朝向（与初始方向夹角） |
| `speed` | float | m/s | 当前合速度（标量） |

---

**SYS_HEALTH（P1，周期 1Hz）**

系统健康状态，辅助诊断通信质量和系统状态。

```
SYS_HEALTH | uptime=30s cfg=OMNI_4WHEEL estop=0 mode=1 can_tx_ok=120 can_rx_ok=240 drop_uart_to_can=0 drop_can_tx=0
```

| 字段 | 说明 |
|------|------|
| `cfg` | 当前底盘构型（STEER 或 OMNI） |
| `can_tx_ok` | CAN 发送成功累计次数 |
| `can_rx_ok` | CAN 接收成功累计次数 |
| `drop_*` | 各队列丢帧计数 |

---

## 五、运动学模块设计（待实现）

网关内部需要根据构型做**正向和逆向**运动学解算：

```c
// 底盘构型枚举
typedef enum {
    CHASSIS_TYPE_STEER,     // 舵轮底盘
    CHASSIS_TYPE_OMNI_4     // 四全向轮底盘
} ChassisType_t;

// 车体速度（上层看到的数据）
typedef struct {
    float vx;       // 前进速度 (m/s)
    float vy;       // 侧向速度 (m/s)
    float omega;    // 旋转角速度 (rad/s)
} ChassisSpeed_t;

// 运动学接口（同一套接口，不同构型有不同实现）
void kinematics_init(ChassisType_t type);
void kinematics_inverse(ChassisSpeed_t *cmd, MotorTarget_t *motors, uint8_t *count);
void kinematics_forward(MotorState_t *motors, uint8_t count, ChassisSpeed_t *result);
```

### 5.1 构型 B（四全向轮）的运动学参考

对于四全向轮底盘（电机轴向外射，交于车体中心），标准运动学模型：

**逆解**（车体速度 → 各轮速度）：

```
ω₁ = -vx + vy + L·omega
ω₂ =  vx + vy - L·omega
ω₃ =  vx - vy - L·omega
ω₄ = -vx - vy + L·omega
```

其中 L 为轮子到车体中心的距离，ω₁~ω₄ 为四个轮子的目标转速。

**正解**（各轮速度 → 车体速度）：

```
vx    = (-ω₁ + ω₂ + ω₃ - ω₄) / 4
vy    = ( ω₁ + ω₂ - ω₃ - ω₄) / 4
omega = ( ω₁ - ω₂ - ω₃ + ω₄) / (4·L)
```

### 5.2 构型 A（舵轮）的运动学参考

舵轮底盘每个动力单元有两个自由度（驱动速度 + 转向角）。逆解需要根据车体目标速度和各单元安装位置，计算出每个单元的驱动速度和转向角。

---

## 六、当前实现状态与演进路线

| 层面 | 功能 | 当前状态 | 阶段 |
|------|------|---------|------|
| CAN 帧解码 | MCLM 状态帧 → SystemState.motor[] | ✅ 已完成 | Phase 1 |
| 命令解释 | CMD_SET_SPEED/ESTOP 等 → SystemState 更新 | ✅ 已完成 | Phase 1 |
| 命令解释 | CMD_SET_SPEED → CAN 命令字节替换 0x11 | ✅ 已完成 | Phase 1 |
| 底盘构型 | ChassisType_t 枚举定义 | ❌ 待实现 | Phase 2 |
| 运动学模块 | 正解/逆解算法 | ❌ 待实现 | Phase 2 |
| CHASSIS_STATE | 车体速度主动上报 | ❌ 待实现 | Phase 2 |
| EVENT | 异常检测与主动上报 | ❌ 待实现 | Phase 2 |
| CMD_ACK | 命令确认回复 | ❌ 待实现 | Phase 2 |
| SYS_HEALTH | 周期健康上报 | ❌ 待实现 | Phase 2 |
| IMU 集成 | MPU6050 + Mahony → SystemState.imu | ❌ 待实现 | Phase 3 |
| 里程计 | ticks → 位姿 | ❌ 待实现 | Phase 3 |

---

## 七、核心原则重申

1. **网关不是管道。** 任何往上发送的数据都必须是经过解码、融合、抽象后的信息。原始 CAN 帧或电机级数据不得直接上抛。

2. **上层不感知构型。** 上层只和车体速度 `vx/vy/omega` 打交道，不关心舵轮还是全向轮、不关心有几个电机。

3. **异常主动报。** 堵转、通信丢失、急停等事件由网关主动检测并立即上报，不等待上层查询。

4. **只报值得报的。** 正常状态 = 周期上报（如 CHASSIS_STATE 20Hz）；异常状态 = 事件驱动（立即上报）；调试状态 = 低频率（SYS_HEALTH 1Hz）。

---

## 附录：术语对照

| 术语 | 英文 | 说明 |
|------|------|------|
| 舵轮底盘 | Steering wheel chassis | 每个动力单元含驱动+转向两个电机 |
| 全向轮底盘 | Omni-wheel chassis | 四个全向轮，轴向外射交于中心 |
| 动力单元 | Drive unit | 舵轮底盘的最小驱动单位（含驱动轴和转向轴） |
| 运动学正解 | Forward kinematics | 各电机速度 → 车体速度 |
| 运动学逆解 | Inverse kinematics | 车体速度 → 各电机目标速度 |
| 堵转 | Stall | 电机通电但转子不转 |
| 车体速度 | Chassis speed | 车体 vx/vy/omega 三个自由度的速度 |
