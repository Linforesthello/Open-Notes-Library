# CAN 数据增强 — 完整 Session Thinking 记录

> **项目：** `3_MCLM_t2` — STM32F103C8T6 电机控制器（末端节点）  
> **角色：** 移动机器人底盘执行层，控制两路直流电机（转向+动力），通过 CAN 总线下接主控  
> **日期：** 2026-05-18  
> **分支：** `fix_base`  
> **数据集：** `doc/Can_MainControl_t1.csv`（23974 帧 CAN 总线录制）  

---

## 目录

1. [问题起点：主控需要什么信息？](#1-问题起点主控需要什么信息)
2. [第一步：勘查现状（读了15个源文件）](#2-第一步勘查现状读了15个源文件)
3. [第二步：方案设计思考过程](#3-第二步方案设计思考过程)
4. [第三步：代码实现（改动前后对比）](#4-第三步代码实现改动前后对比)
5. [第四步：CSV 数据分析验证](#5-第四步csv-数据分析验证)
6. [第五步：逐电机行为分析](#6-第五步逐电机行为分析)
7. [核心发现与根因推测](#7-核心发现与根因推测)
8. [涉及文件清单](#8-涉及文件清单)
9. [后续改进方向](#9-后续改进方向)

---

## 1. 问题起点：主控需要什么信息？

### 1.1 原始需求

用户提问：

> "作为末端节点与下层主控对接的，主控需要什么信息？作为移动机器人底盘"

翻译成工程问题：**这个电机控制器应该主动告诉主控哪些信息，才能让主控做好底盘控制？**

### 1.2 原系统能力摸底

通过阅读约 15 个源文件，梳理出当前主控能获取的信息：

| 方向 | 当前能力 | 方式 |
|------|---------|------|
| 主控→节点 | 调速、停止、状态查询、全局命令 | CAN RX：0x123/0x124/0x101 等 |
| 节点→主控 | target, current, pwm（6字节，2字节保留） | CAN TX：0x323/0x324 收到查询才回复 |

### 1.3 三个核心缺口

| 缺口 | 严重性 | 描述 |
|------|--------|------|
| **里程计累计值未上报** | 🔴 致命 | 编码器已有 `accumulated_ticks`（int32），UART 日志也有输出，但 CAN 状态帧 bytes[6-7] 是保留 0x00，字节完全浪费 |
| **被动回复（无心跳）** | 🔴 致命 | 节点用 `osMessageQueueGet(..., osWaitForever)` 阻塞等待。有命令才回复，无命令完全静默。主控必须不断轮询，且无法判断节点是否存活 |
| **无故障检测** | 🟡 中等 | 电机堵转、PID 饱和等异常状态无任何检测和上报机制，主控对物理层异常完全盲视 |

---

## 2. 第一步：勘查现状（读了15个源文件）

### 2.1 关键文件阅读顺序

```
1. doc/all_motor.md           ← 电机参数清单，Motor_t 结构体，PID 参数，CAN ID
2. doc/deepseek_can.md        ← CAN 数据流文档，ID 定义，RX/TX 协议，过滤模块
3. App/config/app_globals.h   ← Motor_t 结构体定义（确认 accumulated_ticks 存在）
4. App/config/app_config.h    ← CAN ID 宏定义，PWM_MAX 等常量
5. App/services/command.h     ← CommandType_t, CommandMsg_t, AckMsg_t
6. App/services/can_filter.h/c ← 白名单过滤、命令字节校验、ID 映射
7. App/tasks/command_task.c   ← 命令路由、CAN TX 响应（被重构的核心文件）
8. App/tasks/tb6612_DC_task.c ← 电机控制任务、PID 循环（嵌入检测逻辑的位置）
9. App/tasks/motor_tb6612_task.c
10. App/tasks/encoder_tim.c
11. App/tasks/Ack_task.c
12. App/tasks/logger_timer_task.c
13. Core/Src/can.c            ← HAL 回调，收帧后调过滤模块推队列
14. Core/Src/main.c
15. Core/Src/freertos.c       ← 队列、互斥锁、信号量定义
```

### 2.2 现有关键数据流

```
CAN 总线
  │  RX: 0x123/0x124 (调速/停止), 0x223/0x224 (查询)
  ▼
can.c HAL_CAN_RxFifo0MsgPendingCallback
  → CAN_Filter_Accept() 白名单检查
  → CAN_Filter_CmdByteToType() 命令类型转换
  → osMessageQueuePut(CommandQueueHandle)
  ▼
Command_Task (原：阻塞等待)
  → CMD_QUERY_STATUS → 内联组包 8 字节 CAN TX 回复
  → 其他命令 → 路由到 MotorQueueHandle/MotorQueue1Handle
  ▼
TB6612_DC_Task (PID 循环, 10ms)
  → osMessageQueueGet 取命令
  → PID_Compute → TB6612_Motor_SetSpeed
  → 更新 motor->pwm_output
```

### 2.3 确认已有的但未用上的资源

```c
// Motor_t 已有 accumulated_ticks（line 28），但 CAN 帧里不包含它
typedef struct {
    ...
    int32_t  accumulated_ticks;     // 编码器累计计数值
    int16_t  pwm_output;
} Motor_t;

// CAN TX 帧占用了 6 字节，bytes[6-7] = 0x0000 (reserved)
// 旧格式: [0-1]target | [2-3]current | [4-5]pwm | [6-7]reserved
```

---

## 3. 第二步：方案设计思考过程

### 3.1 帧格式重新设计的决策树

**约束条件：** CAN 标准帧最多 8 字节数据。需要在 8 字节内塞入更多信息。

**旧格式占用：**
```
[0-1] target_logic_speed   (int16)    范围 -100..100 → 浪费了 6/8 的位
[2-3] current_logic_speed  (int16)    需要小数精度 → 保留
[4-5] pwm_output           (int16)    保留
[6-7] 0x0000 (reserved)               ← 等待利用
```

**需要新增：** `accumulated_ticks`（int32）+ `flags`（uint8），还得保留原有字段。

**决策过程：**

```
问题：8 字节要塞下原有字段 + accumulated_ticks(至少2字节) + flags(1字节)
      → 需要从某处挤出 3 字节

方案 A：target_speed 降宽度
  target_speed 范围 -100..100 → int8_t 完全够用
  节省 1 字节 ✅

方案 B：current_speed 降宽度  
  current_speed 需要小数精度 → int16 保留
  不可行 ❌

方案 C：pwm 降宽度
  PWM_MAX=7200 > 255 → int8 不够
  不可行 ❌

方案 D：accumulated_ticks 只发低 16 位
  这是 int32，完整发送需要 4 字节，但我们只有 2-3 字节可用
  → 只发低 16 位，主控端跟踪翻转

  翻转分析：满速 6600 ticks/s
  16 位 = 65536 ticks
  翻转周期 = 65536/6600 ≈ 9.93 秒
  主控 50ms 收一帧，一个翻转周期内最多收 200 帧
  每帧 delta 最大 = 6600 × 0.05 = 330 ticks << 65536
  → 主控可可靠跟踪翻转 ✅
```

**最终选型：方案 A + D**

```
新格式:
  [0-1] current_logic_speed    (int16)    ← 最有价值的放首位
  [2-3] accumulated_ticks      (uint16)   ← 里程计低16位
  [4-5] pwm_output             (int16)
  [6]   target_logic_speed     (int8)     ← -100..100 够用
  [7]   flags                  (uint8)    ← 故障标志位
```

### 3.2 主动上报策略的设计权衡

**旧方案：** `osMessageQueueGet(..., osWaitForever)` — 阻塞

**问题：** 没有命令时任务完全挂起，不发送任何 CAN 帧。

**备选方案对比：**

| 方案 | 优点 | 缺点 |
|------|------|------|
| A：单独心跳任务 | 职责分离清晰 | 增 TCB/栈开销，需额外同步机制 |
| B：命令任务加超时 | 零额外资源，现有架构小改 | 命令任务不再严格实时 |
| C：定时器回调发帧 | 最精确的定时 | 中断上下文不能调互斥锁 |

**选型 B** — 把 `osWaitForever` 改成 `50ms` 超时：
- 收到命令 → 正常处理（同原来逻辑）
- 超时（空闲）→ `send_motor_status(0); send_motor_status(1);`
- 主控端：若 100ms 无帧 → 判定节点离线

**为什么 50ms？（20Hz）**
- 太快：总线负载高
- 太慢：主控控制延迟大
- 50ms：与 PID 控制周期（10ms）解耦，20Hz 对底盘控制足够

### 3.3 堵转/饱和检测设计

**检测位置：** TB6612_DC_Task 的 10ms PID 循环

**堵转检测逻辑：**
```c
if (setpoint != 0 && fabsf(current_speed) < 1.0f) {
    counter++;
    if (counter > 5)  // 连续 6 个周期 (>50ms) 均为堵转
        flags |= STALL;
} else {
    counter = 0;
    flags &= ~STALL;
}
```

**为什么连续 5 周期才置位？**
- 因为 1 个周期（10ms）的速度测量可能有噪声
- 第 1 周期加速初期速度也可能接近 0
- 堵转是持续状态，不是瞬时事件，5 周期（50ms）既避免误报，又及时检测

**饱和检测逻辑（不需要计数，单一周期即可判定）：**
```c
if (pwm >= (PWM_MAX - 10) && fabsf(actual - target) > 10.0f)
    flags |= SATURATED;
else
    flags &= ~SATURATED;
```

**标志清除策略：**
- 电机停止时：直接清零
- 恢复正常时：各检测逻辑独立清除对应标志

### 3.4 字段顺序决策

为什么 `current_logic_speed` 放在 [0-1] 而不是 [6]？

```
考量：
1. current_speed 是主控最关心的数据（实际转速）
2. 调试时读 CAN 帧，第一个字节就是最有用的信息
3. PWM 放在中间，target 和 flags 放末尾 → 语义分组清晰

最终：current → ticks → pwm → target + flags
```

---

## 4. 第三步：代码实现（改动前后对比）

### 4.1 `App/config/app_globals.h` — Motor_t 结构体扩展

**改前：** 只有硬件句柄、PID、速度、编码器、PWM，无状态检测字段

**改后：**
```diff
+/* ===================== Motor Status Flags ===================== */
+#define MOTOR_FLAG_STALL      0x01U   // 堵转：setpoint != 0 但 speed ≈ 0
+#define MOTOR_FLAG_SATURATED  0x02U   // 饱和：PWM 已达上限但无法达到目标速度
+
 typedef struct {
     TB6612_Motor_t hardware;
     PID_Controller pid;
     float    target_logic_speed;
     float    current_logic_speed;
     int32_t  current_ticks;
     int32_t  accumulated_ticks;
     int16_t  pwm_output;
+    uint8_t  flags;                // 新增：电机状态标志
+    uint8_t  stall_counter;        // 新增：连续堵转周期计数
 } Motor_t;
```

### 4.2 `App/tasks/tb6612_DC_task.c` — 嵌入式检测

**改前：** PID 循环只做 `PID_Compute → SetSpeed → 更新 pwm_output`

**改后：** 在 PID 循环中嵌入两个检测块：

```c
// ===== 在 PID 计算之前：堵转检测 =====
float current_speed = motor->current_logic_speed;

if (fabsf(current_speed) < 1.0f)
{
    if (motor->stall_counter < 255) motor->stall_counter++;
    if (motor->stall_counter > 5)   /* stalled for > 50ms */
        motor->flags |= MOTOR_FLAG_STALL;
}
else
{
    motor->stall_counter = 0;
    motor->flags &= ~MOTOR_FLAG_STALL;
}

// ===== PID 计算 =====
float output = PID_Compute(&(motor->pid), current_speed);
TB6612_Motor_SetSpeed(&(motor->hardware), (int16_t)output);
motor->pwm_output = motor->hardware.pwm_output;

// ===== PID 计算之后：饱和检测 =====
if (motor->pwm_output >= (PWM_MAX - 10) &&
    fabsf(current_speed - motor->pid.setpoint) > 10.0f)
{
    motor->flags |= MOTOR_FLAG_SATURATED;
}
else
{
    motor->flags &= ~MOTOR_FLAG_SATURATED;
}
```

**停止分支也加强：**
```c
// else (setpoint == 0):
TB6612_Motor_Stop(&(motor->hardware));
motor->pwm_output = 0;
motor->stall_counter = 0;    // ← 新增
motor->flags = 0;             // ← 新增
```

### 4.3 `App/tasks/command_task.c` — 核心重构

这是改动最大的文件，从内联响应重构为统一发送函数 + 主动上报。

**改前（旧架构）：**
```c
Command_Task:
    osMessageQueueGet(..., osWaitForever)   // 阻塞，∞超时
  
    if (CMD_QUERY_STATUS) {
        // 内联组包（每个分支自己写 memcpy）
        uint32_t replyId = ...;
        CAN_TxHeaderTypeDef txHeader = {.StdId = replyId, ...};
        uint8_t txData[8] = {0};
        int16_t target = ..., current = ..., pwm = ...;
        memcpy(&txData[0], &target, 2);    // 旧格式：[0-1]=target
        memcpy(&txData[2], &current, 2);   //       [2-3]=current
        memcpy(&txData[4], &pwm, 2);       //       [4-5]=pwm
        //                                  //       [6-7]=0x0000
        HAL_CAN_AddTxMessage(...);
    }
    // 其他命令处理...
```

**问题：** 组包代码重复、格式硬编码、不主动发送。

**改后（新架构）：**
```c
// ★ 新增统一发送函数
static void send_motor_status(uint8_t mid) {
    osMutexId_t myMutex = (mid == 0) ? motor0_mutexHandle : motor1_mutexHandle;
    uint32_t replyId = (mid == 0) ? CAN_MOTOR_TURN_STATUS_STDID
                                   : CAN_MOTOR_POWER_STATUS_STDID;

    CAN_TxHeaderTypeDef txHeader = { .StdId = replyId, .DLC = 8, ... };
    uint8_t txData[8] = {0};

    osMutexAcquire(myMutex, osWaitForever);
    int16_t  current = (int16_t)             g_motors[mid].current_logic_speed;
    uint16_t accum   = (uint16_t)(            g_motors[mid].accumulated_ticks & 0xFFFF);
    int16_t  pwm     =                        g_motors[mid].pwm_output;
    int8_t   target  = (int8_t)               g_motors[mid].target_logic_speed;
    uint8_t  flags   =                        g_motors[mid].flags;
    memcpy(&txData[0], &current, 2);  // 【新格式】[0-1]=current
    memcpy(&txData[2], &accum,   2);  //          [2-3]=ticks
    memcpy(&txData[4], &pwm,     2);  //          [4-5]=pwm
    txData[6] = (uint8_t)target;      //          [6]  =target (int8)
    txData[7] = flags;                 //          [7]  =flags
    osMutexRelease(myMutex);
    HAL_CAN_AddTxMessage(&hcan, &txHeader, txData, &txMailbox);
}

Command_Task:
    uint32_t last_status_tick = 0;

    for(;;) {
        // ★ 改为 50ms 超时
        osStatus_t q_status = osMessageQueueGet(CommandQueueHandle, &cmd, NULL, 50);

        if (q_status == osOK && cmd.type != CMD_NONE) {
            // ★ CMD_QUERY_STATUS 简化为一行
            if (cmd.type == CMD_QUERY_STATUS)
                send_motor_status(mid);     // ← 原来 ~20 行内联代码

            // 其他命令处理...（不变）
        }

        // ★ 主动上报：无命令时 50ms 心跳
        uint32_t now = HAL_GetTick();
        if (now - last_status_tick >= 50) {
            send_motor_status(0);           // 转向电机
            send_motor_status(1);           // 动力电机
            last_status_tick = now;
        }
    }
```

### 4.4 `App/config/app_config.h` — 参数微调

| 参数 | 改前 | 改后 | 原因 |
|------|------|------|------|
| `CAN_ID_GROUP` | 2 | 1 | 切换 CAN ID 分组（0x125/0x126 系列） |
| `SPEED_TICKS_MAX` | 72 | 90 | 提高编码器上限，适配更高转速 |

### 4.5 CAN 帧格式前后对比（摘要）

| byte | 旧格式（不兼容） | 新格式 |
|------|-----------------|--------|
| [0-1] | `target` (int16) | **`current`** (int16) ← 最有价值的放首位 |
| [2-3] | `current` (int16) | **`accumulated_ticks`** (uint16) ← 里程计低16位 |
| [4-5] | `pwm` (int16) | `pwm` (int16) |
| [6] | `0x00` (reserved) | **`target`** (int8) ← -100~100 |
| [7] | `0x00` (reserved) | **`flags`** (uint8) ← 故障位 |

> ⚠️ 不兼容旧格式！主控侧必须同步更新解析逻辑。

---

## 5. 第四步：CSV 数据分析验证

> 数据集：`doc/Can_MainControl_t1.csv`，23974 行（含 1 行 header）  
> 用户说明："改过一版后外部录制的最新数据集"

### 5.1 数据格式确认

**CSV 列结构：**
```
Time Stamp, ID, Extended, Dir, Bus, LEN, D1, D2, D3, D4, D5, D6, D7, D8
```

**字段映射（关键！）：**
```
awk -F',' 下：
  $1=Time Stamp, $2=ID, $3=Extended, $4=Dir, $5=Bus, $6=LEN
  $7=D1, $8=D2, $9=D3, $10=D4, $11=D5, $12=D6, $13=D7, $14=D8
```

### 5.2 字节序验证

用户确认：**全部小端（Little-Endian）**

新格式小端解析：
```
current_logic_speed  = (D2 << 8) | D1    // int16, 小端
accumulated_ticks    = (D4 << 8) | D3    // uint16, 小端
pwm_output           = (D6 << 8) | D5    // int16, 小端
target_logic_speed   = D7                 // int8
flags                = D8                 // uint8
```

### 5.3 时间戳单位分析（关键发现）

**最初困惑：** 时间戳上的时间间隔看起来很大（~50000ms）

**验证过程：**
```
行2: ts=27734    (0x323)
行3: ts=28056    (0x324) → gap=322
行4: ts=28175    (0x325) → gap=119
行5: ts=28497    (0x326) → gap=322
行6: ts=77772    (0x323) → gap=49275

如果单位是 ms: 0x323→0x324 间隔 322ms 不合理（一帧要等 0.3 秒？）
如果单位是 μs: 322μs ≈ 0.3ms → 合理的中断处理间隔
           49275μs ≈ 49.3ms → 接近 50ms → 这就是 20Hz 上报!
```

**结论：时间戳单位是微秒（μs），不是毫秒（ms）**

```
单个电机帧间隔：50ms → 20Hz ✓
录制总时长：约 300 秒 = 5 分钟
```

### 5.4 CAN ID 映射验证

CSV 中出现的 ID 对应 `CAN_ID_GROUP=2`（录制时的固件配置）：

| CSV ID | 宏定义 | 方向 | 对应电机 |
|--------|--------|------|---------|
| `0x323` | `CAN_MOTOR_TURN_STATUS_STDID` | TX | 转向电机状态 |
| `0x324` | `CAN_MOTOR_POWER_STATUS_STDID` | TX | 动力电机状态 |
| `0x325` | (Group 1 的 TURN_STATUS) | TX | 另一设备/节点 |
| `0x326` | (Group 1 的 POWER_STATUS) | TX | 另一设备/节点 |
| `0x124` | `CAN_MOTOR_POWER_CMD_STDID` (Group 2) | RX | 动力电机指令 |
| `0x125` | `CAN_MOTOR_TURN_CMD_STDID` (Group 1) | RX | 另一设备指令 |
| `0x126` | `CAN_MOTOR_POWER_CMD_STDID` (Group 1) | RX | 另一设备指令 |

CSV 涵盖了整条 CAN 总线上的所有流量，包含多个节点。

### 5.5 数据模式分析方法

**第一步（awk 快速扫描）：**
```bash
# 统计每个 ID 的数据模式分布
awk -F',' 'NR>1 {id=$2; data=$7","$8","$9","$10","$11","$12","$13","$14; \
  key=id" "data; cnt[key]++} END {for(k in cnt) print cnt[k],k}' Can_MainControl_t1.csv
```

**第二步（Python 精准解析）：**
```python
# 按新格式解析每个字段
d1, d2, d3, d4, d5, d6, d7, d8 = [int(x,16) for x in d]
cur_speed = (d2 << 8) | d1       # int16 LE
if cur_speed >= 0x8000:
    cur_speed -= 0x10000
ticks = (d4 << 8) | d3            # uint16 LE
pwm = (d6 << 8) | d5             # int16 LE
target = d7                      # int8
if target >= 0x80:
    target -= 0x100
flags = d8
```

**第三步（时间序列分析）：** 将所有 RX 命令和 TX 状态按时间排序，重建完整事件链。

---

## 6. 第五步：逐电机行为分析

### 6.1 0x323（转向电机，Group 2）

| 属性 | 值 |
|------|-----|
| 帧数 | 5990 |
| 数据模式 | `00,00,FE,FF,00,00,00,00`（全部相同） |
| 解析值 | current=0, ticks=0xFFFE=65534, pwm=0, target=0, flags=0 |
| RX 命令 | **无** — 整个录制期间没收到任何指令 |

**分析：**
- 编码器 ticks 停留在 65534（近 uint16 最大值），从未变化
- 没有 RX 命令到达 → 主控可能未发送，或 CAN ID 不在该节点的白名单中
- 电机全程静止

### 6.2 0x324（动力电机，Group 2）— 堵转事件

**正常 idle 模式：** `00,00,FE,FF,00,00,00,00` × 5691 帧

**堵转全过程：**

```
t=7.9s    RX:0x124 SET_SPEED +0      ← 主控预置零（清状态）
t=9.0s    RX:0x124 SET_SPEED +50     ← 主控命令启动
t=9.07s   0x324 首次活跃：
          cur=0, ticks=65534, pwm=4824, target=50, flags=0
          → PWM 已经升到 4824，但 current=0 → PID 在努力

t=9.10s   PWM=7200, flags=0x03      ← 达到饱和！堵转+饱和标志置位！
t=9.10~12.9s  持续堵转 target=50
          PWM=7200, cur=0, flags=0x03
          (约 76 帧，持续 ~3.8 秒)

t=12.9s   RX:0x124 SET_SPEED +0     ← 主控放弃，置零
t=12.9~26.1s  idle（target=0, pwm=0）

t=26.1s   RX:0x124 SET_SPEED +50    ← 主控第二次尝试
t=26.2~28.7s  再次堵转 target=50
          PWM=7200, cur=0, flags=0x03

t=28.7s   RX:0x124 SET_SPEED +16    ← 主控降低期望值
t=28.7~30.3s  仍然堵转 target=16
          PWM=7200, cur=0, flags=0x03 (~32帧)

t=30.3s   RX:0x124 SET_SPEED +0     ← 主控再次放弃

t=42.6s   RX:0x124 SET_SPEED +50    ← 主控第三次尝试
t=42.6~49.5s  继续堵转 target=50
          (~140帧，持续 ~7 秒)

t=49.5s   RX:0x124 SET_SPEED +0     ← 最终放弃，不再尝试
t=49.5~300s  永远 idle 到录制结束
```

**flags 变化明细：**
- flags=0x03（STALL | SATURATED）：298 帧
- flags=0x02（SATURATED 仅，短暂脱离堵转）：2 帧
- flags=0x00（堵转前最后的正常状态）：1 帧

### 6.3 0x325（电机3，可能是 Group 1 转向）— 正常运行 ✅

**idle 模式两种：**
- 早期：`00,00,03,00,00,00,00,00` → ticks=0x0003=3
- 后期：`00,00,64,D1,00,00,00,00` → ticks=0xD164=53604

**delta = 53601 ticks** — 运动产生的编码器增量

**运行阶段：**

| 时间段 | 命令 | 行为 | 稳态 current |
|--------|------|------|-------------|
| 58.0s→94.3s | SET_SPEED 50 | 平稳加速到~50 | 48-51 |
| 94.3s→101.2s | SET_SPEED 80 | 加速到~79 | 78-80 |
| 101.2s→116.9s | SET_SPEED 32 | 减速到~32 | 30-32 |
| 116.9s→144.2s | SET_SPEED -30 | **反转运行** | -28 ~ -32 |
| 144.2s+ | SET_SPEED 0 | 停止 | 滑行→0 |

**加速时间（0→50）**：约 0.3 秒（6 帧），无超调无振荡。

### 6.4 0x326（电机4，可能是 Group 1 动力）— 最完整行程 ✅

**完整运动曲线：加速→高速→自由停车→反转→再反转→停车**

```
第一阶段：加速到 50（t=168.8s~185s）
  启动: cur=6, ticks=12, pwm=4464
  加速: cur=40@0.1s, cur=58@0.2s(超调)
  稳态: cur≈50, pwm≈4800, ticks 线性增长 12→7255

第二阶段：加速到 65（t=185.2s~192s）
  cur=53→65→71(超调), 稳态≈66
  pwm 从 5976→6408→5760

第三阶段：自由停车（t=192.4s~194.2s）
  PWM 瞬间归零，cur 指数衰减 64→0 ≈ 1.8 秒滑行
  ticks 停在 27000+

第四阶段：反转 -50（t=200.9s~211s）
  cur=-17→-43→-50, 稳态 -48~-52
  ticks 从 32065 递减到 22000（反向计数）

第五阶段：正转 48（t=215.2s~218s）
  PID 无缝切换方向：-50→11→35→50
  无振荡无反冲

第六阶段：再反转 -50（t=218.3s~231.5s）
  再次反向过渡平滑，稳态 -48~-53

第七阶段：最终停车（t=231.5s~231.7s）
  PWM=0, cur=-34→-16→-2→1 滑行停止
```

**全程 flags=0x00** → PID 调节正常，无饱和无堵转。

---

## 7. 核心发现与根因推测

### 7.1 ✅ 新格式验证通过

| 验证项 | 结果 | 证据 |
|--------|------|------|
| 帧格式正确 | ✅ | 所有字段按小端解析，数值合理 |
| 主动上报频率 | ✅ | 50.0ms±2ms，20Hz 稳定，5 分钟无丢帧 |
| `current_speed` | ✅ | 0→58 加速过程连续，-50 反转正确 |
| `accumulated_ticks` | ✅ | 正转增加，反转减少，线性度好 |
| `target_speed` (int8) | ✅ | 范围 -50~80，int8 完全够用 |
| `flags` 堵转检测 | ✅ | 0x324 真实堵转时正确上报 0x03 |
| `flags` 正常时 | ✅ | 0x325/0x326 全程 flags=0x00 |

### 7.2 ❌ 0x324 堵转根因推测

**现象数据：**
- target=50, PWM=7200(饱和), current_speed=0, flags=0x03
- 三次尝试（50→16→50）均失败
- 编码器 ticks 全程 65534 无变化

**可能原因（按优先级排列）：**

| # | 原因 | 验证方法 | 预期现象 |
|---|------|---------|---------|
| 1 | **电机物理堵转** — 转子卡死 | 手动旋转电机轴 | 阻力大或不转 |
| 2 | **电机线序/接线** — JST 端子脱落或接触不良 | 检查 MOTOR2 的 PWM/IN1/IN2 接线 | PWM 有输出但电机完全无反应 |
| 3 | **TB6612 驱动未使能** — EN 引脚未拉高或配置错误 | 测 EN 引脚电平 | 驱动芯片无输出 |
| 4 | **电源功率不足** — 电机启动瞬间电压跌落 | 示波器测电机端电压 | PWM 最大但电压不足 |
| 5 | **编码器故障** — 编码器不输出脉冲 | 示波器测编码器 A/B 相 | 电机转但 ticks 不更新 |

### 7.3 ⚠️ 0x323 全程 idle 分析

- ticks=65534 近 uint16 最大值（注意：`accumulated_ticks` 是 int32，CAN 帧发低 16 位刚好是 0xFFFE）
- 可能原因：主控未向该节点发送指令，或 CAN 验收过滤配置不对

### 7.4 0x325/0x326 正常但可优化

- 自由停车滑行约 1.8 秒，如果底盘急停需求可能需要主动刹车
- setpoint=0 时调用 `TB6612_Motor_Stop`(brake mode)，但惯性依然明显

---

## 8. 涉及文件清单

| 文件路径 | 操作 | 变更说明 | 行数变化 |
|----------|------|---------|---------|
| `App/config/app_globals.h` | 修改 | 新增 `MOTOR_FLAG_STALL`/`MOTOR_FLAG_SATURATED` 宏；Motor_t 新增 `flags`/`stall_counter` | +10 |
| `App/config/app_config.h` | 修改 | `CAN_ID_GROUP` 2→1；`SPEED_TICKS_MAX` 72→90 | +2/-2 |
| `App/tasks/tb6612_DC_task.c` | 修改 | PID 循环嵌入堵转检测+饱和检测逻辑；停止分支清零 | +23 |
| `App/tasks/command_task.c` | 重构 | 新增 `send_motor_status()` 统一发送函数；50ms 超时代替阻塞；CMD_QUERY_STATUS 简化；主动上报心跳 | 大幅变动 |
| `doc/all_motor.md` | 修改 | 更新 Motor_t 说明、flags 位定义 |
| `doc/deepseek_can.md` | 修改 | TX 帧新格式 + 主动上报说明 |
| `doc/MainControl_can_plan.md` | **新增** | 实施计划文档 |
| `doc/MainControl_can_result.md` | **新增** | 结果总结文档 |
| `doc/Can_MainControl_t1.csv` | **新增** | 录制数据集（23974 帧，1.3MB） |
| `doc/ai_session/can_data_analyze.md` | **新增** | **本文档** — 完整 thinking 记录 |

---

## 9. 后续改进方向

### 9.1 短期（硬件排查）

- [ ] 检查 0x324 动力电机物理接线（MOTOR2: PB12/PB13, TIM1_CH2）
- [ ] 检查 TB6612 驱动芯片供电和使能引脚
- [ ] 手动旋转电机轴感受阻力
- [ ] 用示波器测编码器 A/B 相输出

### 9.2 中期（固件优化）

- [ ] 主控侧 CAN 解析同步更新为新格式（不兼容旧格式！）
- [ ] 主控侧添加 `accumulated_ticks` 16→32 位翻转跟踪
- [ ] 考虑堵转后的自动恢复机制（PWM 缓启动 / 反冲脉冲）
- [ ] 考虑急停时主动刹车（而非自由滑行）

### 9.3 长期（功能增强）

- [ ] 支持 4 电机实例（当前 MOTOR_COUNT=2）
- [ ] CAN 总线负载监控（当前 160帧/s @500kbps，利用率约 2.6%）
- [ ] 固件版本号 / 诊断信息通过 CAN 上报
