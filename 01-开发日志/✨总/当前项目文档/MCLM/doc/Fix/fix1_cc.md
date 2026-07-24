# Fix1 修复记录

> 工程：`3_MCLM_t2`  日期：2026-04-19  
> 问题现象：速度稍微拉高后 PWM 顶限运行，伴随震荡

---

## 数据格式说明

串口日志格式：`tick, encoder_cnt, speed(ticks/10ms), target, pwm_output`

---

## 修复迭代一（引入新 Bug）

### 修改内容

| 文件 | 修改点 | 修改前 | 修改后 |
|---|---|---|---|
| `app_config.h` | `PWM_MAX` | `999` | `99` |
| `app_config.h` | `MOTOR1_PID_INTEGRAL_LIMIT` | `10.0f` | `5.66f` |
| `tb6612_DC_task.c` | `TB6612_Motor_Init()` 参数 | `MIN_PWM_OUTPUT=0, DEAD_ZONE=10` | `DEAD_ZONE=10, Polarity=0` |
| `pid.c` | 积分策略 | 简单限幅 | 增加条件积分（Anti-windup） |

### 反馈数据（fix1_result.md）分析

```
[16:40:31.931] 67013,35443,-35,32.0,99
[16:40:32.039] ...  ,35211,  0,32.0,99   ← 短暂归零
[16:40:32.308] ...  ,35191,-14,32.0,99   ← 再次反转
...（周期性：反转约250ms → 归零约150ms → 再反转）
```

| 观测 | 含义 |
|---|---|
| `speed` 全为负值 | 电机在**反转** |
| `encoder_cnt` 持续递减 | 电机持续向负方向旋转 |
| `pwm_output` 恒定 `99` | PWM 永远顶限 |
| `target = 32.0`（正） | 目标为正方向 |

**结论**：`error = 32 - (-35) = 67`（极大正误差）→ PID 输出最大正值 → PWM=99 → 电机反转更快 → 形成**正反馈死循环**，震荡比修复前更剧烈。

### 新引入 Bug 的定位

`Polarity=0`（正向）改变了上一轮修复中的 `Polarity=0`。  
原始代码中 `Polarity` 实际传入的是 `MOTOR1_DEAD_ZONE=10`（位置传错），虽然是"事故"，但 `10 != 0` → 极性反转效果是正确的——该电机**物理接线本身需要极性反转**才能使编码器正方向与指令正方向一致。

```
迭代一修复前: DeadZone=0(错), Polarity=10(偶然正确) → 电机正转
迭代一修复后: DeadZone=10(对), Polarity=0(错)        → 电机反转 ← 新 Bug
```

---

## 修复迭代二（当前状态）

### 修改内容

| 文件 | 行 | 修改 |
|---|---|---|
| `tb6612_DC_task.c` | 28 | `Polarity: 0 → 1`（恢复极性反转，明确标注原因） |

```c
// 修复后
TB6612_Motor_Init(..., MOTOR1_DEAD_ZONE,
                  1,   // Polarity=1: 此电机硬件接线需要极性反转
                  TB6612_MOTOR_STOP_BRAKE);
```

### 当前所有有效修复汇总

| # | 文件 | 问题 | 修复 |
|---|---|---|---|
| 1 | `app_config.h` | `PWM_MAX=999` 是 TIM3 ARR(99) 的 10 倍，任何输出都 100% 占空比 | 改为 `99` |
| 2 | `tb6612_DC_task.c` | `DeadZone` 传入 `MIN_PWM_OUTPUT=0`，`Polarity` 传入 `DEAD_ZONE=10`（位置错） | `DeadZone=MOTOR1_DEAD_ZONE(10)`, `Polarity=1` |
| 3 | `app_config.h` | `integral_limit=10` 时 `Ki×limit=176.6`，远超 `output_limit=100`，积分深度饱和 | 改为 `5.66f`（使 `Ki×limit≈100=output_limit`） |
| 4 | `pid.c` | 无 Anti-windup，输出饱和时积分继续累积，切换目标时震荡 | 增加条件积分：饱和且误差同向时锁定积分 |

---

## 根因链路图

```
PWM_MAX=999 (×10倍)
    └→ CCR 写入值 > ARR → 硬件强制 100% 占空比
        └→ 任何 speed 都全速运转
            └→ PID 永远看到大误差 → 永远输出最大
                └→ 震荡（积分无限累积加剧）

Polarity 参数位置传错 (原: DEAD_ZONE 当 Polarity 传)
    └→ 偶然正确（=1=反转）→ 电机实际正转
        └→ 迭代一错误修复为 Polarity=0
            └→ 电机反转 → 正反馈 → 震荡更剧烈
```

---

## 修复迭代三（最终验证通过）

### 问题根因补充：TIM2 编码器输入无硬件滤波 + 计数模式不完整

迭代二修复方向问题后，系统可以闭环，但仍有震荡。  
根本原因定位到 **TIM2 编码器配置**：

#### 问题一：Input Filter = 0（无滤波）

编码器信号存在毛刺/抖动（电机换向干扰、导线耦合噪声），  
`Filter = 0` 时每个毛刺都被计入脉冲，导致：

```
真实速度（稳定）:  35 ticks/10ms
读取速度（无滤波）: 35, 12, 47, 31, 0, 58, ...  ← 巨大噪声
```

PID 吃到的是噪声速度 → 微分项剧烈跳变 → 输出震荡。

**修复**：在 CubeMX 中为 TIM2 的 TI1/TI2 开启输入滤波  
（推荐 Filter = **4~8**，对应 CK_INT × N 次采样滤波，滤除高频毛刺）

```c
// tim.c 中对应参数（CubeMX 生成）
sConfig.IC1Filter = 8;   // 原来是 0，无滤波
sConfig.IC2Filter = 8;
```

#### 问题二：编码器模式为 TI1 Only → 改为 TI1+TI2

| 模式 | 计数触发沿 | 分辨率 |
|---|---|---|
| `TIM_ENCODERMODE_TI1` | 仅 A 相上升/下降沿 | 2x |
| `TIM_ENCODERMODE_TI2` | 仅 B 相上升/下降沿 | 2x |
| **`TIM_ENCODERMODE_TI12`** | **A 相 + B 相双边沿** | **4x（正交解码）** |

原来只用单相计数（2x），分辨率低，每个采样周期内的脉冲数少，  
速度计算值量化误差大（低速时尤为明显）：

```
电机实际: 17.5 ticks/10ms
TI1(2x):  17 或 18 → 量化步长 = 1/17.5 = 5.7% 误差
TI12(4x): 35 ticks/10ms → 量化步长 = 1/35 = 2.9% 误差，且读数更稳定
```

**修复**：CubeMX 中 TIM2 Encoder Mode 改为 `Encoder Mode TI1 and TI2`

```c
// tim.c 中对应参数
sConfig.EncoderMode = TIM_ENCODERMODE_TI12;  // 原来是 TIM_ENCODERMODE_TI1
```

### 两项修复的协同效果

```
无滤波 + TI1 Only
    └→ 速度信号：噪声大 + 分辨率低 → PID 微分项乱跳 → 震荡

开启滤波 + TI1+TI2
    └→ 速度信号：毛刺消除 + 分辨率翻倍 → PID 计算稳定 → 闭环正常
```

---

## 全部修复汇总（最终）

| # | 文件/配置 | 问题 | 修复 |
|---|---|---|---|
| 1 | `app_config.h` | `PWM_MAX=999`，是 TIM3 ARR(99) 的 10 倍，CCR>ARR 硬件强制 100% 占空比 | 改为 `99` |
| 2 | `tb6612_DC_task.c` | `DeadZone/Polarity` 参数位置传错，Polarity 偶然为 10 | `DeadZone=10, Polarity=1`（明确反转） |
| 3 | `app_config.h` | `integral_limit=10`，`Ki×limit=176.6` 远超 `output_limit=100`，积分深度饱和 | 改为 `5.66f`（`Ki×limit≈100`） |
| 4 | `pid.c` | 无 Anti-windup，饱和时积分持续累积 | 饱和且误差同向时锁定积分 |
| 5 | TIM2（CubeMX） | 编码器输入无硬件滤波（Filter=0），毛刺直接进入计数 | 开启输入滤波（Filter=8） |
| 6 | TIM2（CubeMX） | 编码器模式 TI1 Only（2x），分辨率低，低速量化误差大 | 改为 TI1+TI2（4x 正交解码） |

---

## 根因链路图（完整版）

```
【硬件层】
TIM2 无输入滤波
    └→ 电气噪声 / 换向毛刺直接计数 → 速度信号噪声大

TIM2 编码器 TI1 Only (2x)
    └→ 分辨率低 → 低速量化误差大 → 速度信号跳变

【配置层】
PWM_MAX=999 (应为 99)
    └→ CCR > ARR → 硬件强制 100% 占空比 → PID 失控

Polarity 参数传错位置
    └→ 迭代一错误修复为 0 → 电机反转 → 正反馈 → 发散

【算法层】
integral_limit 过大
    └→ 积分深度饱和 → 目标切换时残留积分 → 震荡

无 Anti-windup
    └→ 饱和期间积分无限累积 → 加剧震荡

以上问题叠加 → 速度稍微拉高即 PWM 顶限 + 强烈震荡
```
