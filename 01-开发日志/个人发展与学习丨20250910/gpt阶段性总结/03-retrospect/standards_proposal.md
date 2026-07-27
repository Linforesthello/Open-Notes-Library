# 嵌软标准体系建议

> **适用团队**：嵌入式软件起步 1 年左右的新手团队
> **核心原则**：先立最痛的，再想最全的。不堆砌标准。
> **建议日期**：2026-07-27

---

## 一、指导思想

### 1.1 为什么现在要谈标准

复盘总结的不足中，有一条贯穿全局的原因：

> 不是"某个技术不会"，而是**缺少让团队稳定输出的流程规范**。

具体表现：
- CAN ID 硬编码两次 → 重复劳动
- 方向取反漏一处 → 电机烧毁
- R1 机械臂配置没测 → 未验证的代码合入
- 测试靠记忆 → 漏测
- 没有统一的编码风格 → 每个人的代码阅读成本高

标准不是束缚，是**让团队少犯重复错误的防呆机制**。

### 1.2 分级原则

```
P0 🔴 基石级    — 没有这个，项目会出严重问题（烧硬件 / 代码不可维护）
P1 🟡 增强级    — 有这个，团队效率提升 30%+
P2 🟢 成熟级    — 团队 3 人以上 / 项目 6 个月以上时需要
```

**建议节奏**：
- **比赛结束后立即建 P0**（趁记忆还新鲜）
- **下一个项目开始前建 P1**
- **团队扩展到 3+ 人时建 P2**

---

## 二、P0 🔴 基石级（立刻建立）

### 2.1 Git 工作流规范

#### 现状问题
- 分支命名不统一（`fix_base` / `main` 之外没有规范）
- 提交信息格式靠自由发挥
- 缺少 Code Review 流程

#### 建议标准

**分支命名**：
```
main        ← 生产分支，只合不入
develop     ← 开发主分支
feat/xxx    ← 新功能（feat/steering-arm-can）
fix/xxx     ← 修 Bug（fix/motor-stall-detection）
docs/xxx    ← 文档（docs/retrospective）
```

**提交信息格式**（参考本项目的"标签化"风格，这个做得挺好）：
```
<子系统>|<简要描述>

例子：
MCLM|修复 CAN ID 映射表越界问题
ChassisController|新增 CMD_CHASSIS_SPEED 命令处理
Arm|R2 夹爪限位从 2800 调整到 2930
Docs|补充 MT6701 标定参数
```

**合并策略**：
```
feat/xxx → develop    需要 ≥1 人 Review，不可自行合并
develop  → main       发版前合并，需测试通过
禁止直接推 main
```

**Code Review 底线**（每条 PR 必须确认）：
1. 编译通过（`cmake --build .` 零警告）
2. 不影响现有功能（在已知硬件上跑通了）
3. 文档同步更新了（如果有）

#### 为什么是 P0
没有 Git 规范 → 合并灾难 → 回滚困难 → 比赛前不敢改代码。

---

### 2.2 C 编码规范

#### 现状问题
从复盘看，代码质量波动大：早期有魔术数字、硬编码重复、部分函数无注释。

#### 建议标准

**命名约定**：
```c
// 宏 — 全大写下划线
#define CAN_ID_STEER_CMD_BASE  0x121

// 类型 — 驼峰 + _t 后缀
typedef struct { ... } MotorState_t;

// 函数 — 模块前缀 + 驼峰
uint8_t CAN_Map_StatusIdToMotorIdx(uint32_t status_id);
void    Motor_Stall_Check(void);

// 全局变量 — g_ + 模块前缀
extern MotorState_t g_motor_state[];

// 局部变量 — 小写驼峰
uint8_t motor_idx;

// 枚举 — 全大写下划线 + 类型名_前缀
typedef enum {
    MOTOR_STATE_IDLE,
    MOTOR_STATE_RUNNING,
    MOTOR_STATE_STALL,
} MotorState_e;
```

**头文件结构**（参考现有的 `app_system_state.h`，这个风格值得推广）：
```c
#ifndef APP_SYSTEM_STATE_H_
#define APP_SYSTEM_STATE_H_

/* Includes — 本项目头文件 → 标准库 → HAL */
#include "app_config.h"
#include <stdint.h>

/* Defines — 常量宏 */
#define MOTOR_MAX_COUNT  8

/* Typedefs — 类型定义 */
typedef struct { ... } SystemState_t;

/* Exported Variables — extern 全局变量 */
extern SystemState_t g_system_state;

/* Exported Functions — 函数声明 */
void System_State_Init(void);

#endif /* APP_SYSTEM_STATE_H_ */
```

**函数注释模板**：
```c
/**
 * @brief 从 CAN 状态 ID 查找电机索引
 * @param status_id  CAN 状态帧 ID（如 0x323）
 * @return uint8_t   电机索引（0~MOTOR_MAX_COUNT-1），未找到返回 0xFF
 * @note  查表时间 O(n)，n ≤ 8，不阻塞
 */
uint8_t CAN_Map_StatusIdToMotorIdx(uint32_t status_id);
```

#### 为什么是 P0
没有编码规范 → 团队代码风格分裂 → 互相看不懂 → 协作效率低。

---

### 2.3 模块接口标准（Init/Run/Deinit 模式）

本项目的 `App/tasks/` 和 `App/modules/` 已经自然地遵循了这个模式。把它明确化。

```c
// 每个模块提供三个函数：
void Module_Init(void);     // 初始化（硬件配置、状态清零）
void Module_Run(void);      // 周期执行（或被事件触发）
void Module_Deinit(void);   // 反初始化（关断输出、释放资源）
```

**已有范例**：
- `App/modules/pid.c` → `PID_Init()` / `PID_Calc()`
- `App/services/can_filter.c` → `CAN_Filter_Init()` / `CAN_Filter_Check()`

**禁止模式**：
- 在 `.h` 文件中定义变量（应该在 `.c` 中 `static` + `.h` 中 `extern`）
- 函数超过 200 行（超过应拆分）
- 在中断回调中写复杂业务逻辑

#### 为什么是 P0
没有接口规范 → 代码耦合严重 → 改一处炸一片。

---

### 2.4 CAN 协议模板

#### 现状问题
本项目 CAN 协议是逐步演进的，没有一次成型的"协议文档"。复盘时发现信息分散在各处。

#### 建议标准

每个 CAN 节点发布一份协议文档：

```markdown
# CAN 协议 — <节点名>

## 总线参数
| 参数 | 值 |
|------|-----|
| 波特率 | 1 Mbps |
| 帧类型 | 标准帧 / 扩展帧 |
| ID 长度 | 11 bit |

## ID 分配表
| ID | 方向 | 功能 | 周期 | P0/P1 |
|:--:|:----:|------|:----:|:-----:|
| 0x121 | 接收 | UNIT1 转向 CMD | 事件 | P0 |
| 0x321 | 发送 | UNIT1 转向 STATUS | 50ms | P0 |
| ... | ... | ... | ... | ... |

## 帧格式

### 0x121 — UNIT1 转向 CMD
| Byte | 字段 | 类型 | 说明 |
|:----:|:-----|:----:|------|
| 0 | cmd | uint8 | 0x11=SET_SPEED, 0x08=STOP |
| 1 | speed | int8 | -100~+100 |
| 2~7 | reserved | — | 填充 0x00 |

### 0x321 — UNIT1 转向 STATUS
| Byte | 字段 | 类型 | 说明 |
|:----:|:-----|:----:|------|
| 0~1 | current_speed | int16 LE | 当前速度 |
| 2~3 | accumulated_ticks | uint16 LE | 编码器脉冲 |
| 4~5 | pwm_output | int16 LE | PWM 输出值 |
| 6 | target_speed | int8 | 目标速度 |
| 7 | flags | uint8 | bit0=STALL, bit1=SATURATED |

## 版本历史
| 版本 | 日期 | 变更 |
|:----:|:----:|------|
| v1.0 | 2026-04-01 | 初始定义 |
| v1.1 | 2026-06-15 | 新增 flags 定义 |
```

**CAN ID 分配规则**（本项目实际使用的规则，应固化下来）：
```
B = Board Index (0-based)
M = Motor Index on Board (0 or 1)

CMD        = 0x121 + B*2 + M    → 0x121, 0x122, 0x123, 0x124, ...
CMD_STATUS = CMD + 0x100        → 0x221, 0x222, ...
STATUS     = CMD + 0x200        → 0x321, 0x322, ...

广播/特殊命令：0x101 (STOP_ALL)
```

#### 为什么是 P0
没有协议文档 → 新成员接手靠口口相传 → 不同模块实现不一致 → 联调时躺平。

---

## 三、P1 🟡 增强级（下一个项目前建立）

### 3.1 硬件抽象层（HAL）接口规范

**目标**：隔离硬件变化。换 MCU 型号 / 换驱动芯片时只改 drivers/ 层。

**标准**：
```c
// 每个外设驱动提供统一接口
// Init:   初始化硬件
// Read:   读取数据（阻塞/非阻塞通过参数控制）
// Write:  写入数据
// IOCtrl: 控制命令（改变配置、复位等）

typedef struct {
    int32_t (*Init)(void *config);
    int32_t (*Read)(void *buf, uint32_t len, uint32_t timeout_ms);
    int32_t (*Write)(const void *data, uint32_t len, uint32_t timeout_ms);
    int32_t (*IOCtrl)(uint32_t cmd, void *param);
} DrvOps_t;
```

### 3.2 系统状态 / 日志规范

**目标**：所有系统信息通过统一通道输出，不靠"感觉"排查问题。

**标准**：
- 每个任务都有 `TASK_XX` 宏标识
- 所有状态变化通过 `SYS_LOG()` 宏输出，格式统一
- 日志分等级：`ERROR > WARN > INFO > DEBUG`
- 生产模式只开 ERROR + WARN，调试模式开 INFO + DEBUG

**参考**：本项目的 `EVENT` 消息设计（STALL / MOTOR_LOST / ESTOP_TRIGGERED）已经是好范例，应固化推广。

### 3.3 代码审查 Checklist

每次 PR 必须确认的事项：

```
□ 编译通过（零警告）
□ 不影响其他模块（grep 检查是否有全局变量意外修改）
□ 动态内存分配是否合理（嵌入式尽量不用 malloc）
□ 中断服务函数是否足够短（不超过 50 行）
□ 魔术数字是否已宏定义
□ 硬编码的 ID / 地址是否已表驱动
□ 文档是否同步更新
□ 已测试的硬件环境和测试结果附在 PR 描述中
```

### 3.4 文档模板标准

本项目已有 `doc/` 下的丰富文档，但模板风格不统一。建议固化四种文档模板：

| 模板 | 用途 | 参考范例 |
|------|------|---------|
| **架构文档** | 系统设计、模块划分、数据流 | `architecture.md` / `chassis_model.md` |
| **接口文档** | 函数接口、CAN 协议、数据结构 | `CAN_QUICK_REF.md` / `can_protocol_plan.md` |
| **测试指南** | 操作步骤、命令集、验收条件 | `测试指南.md` / `step_by_step.md` |
| **调试日志** | 问题现象、根因、修复方案 | `debug_log.md` / `tim4_clock_fix.md` |

---

## 四、P2 🟢 成熟级（团队 3+ 人时建立）

### 4.1 自动化测试（硬件在环）
- 每个模块有单元测试（Mock HAL 层）
- 关键路径有硬件在环测试（如 CAN 收发测试脚本）
- 比赛前有"一键回归测试"脚本

### 4.2 CI/CD 流水线
- Git push 自动触发编译
- 编译警告视为错误
- 自动运行单元测试
- 自动生成固件产物（.bin / .hex）

### 4.3 设计评审流程
- 新架构设计需要评审（不需要全员，但需要至少一位非参与者）
- 评审焦点：接口设计、异常处理、资源估算（RAM/Flash/CPU）
- 记录评审结论和待办

### 4.4 版本管理
- 遵循语义化版本 `vMAJOR.MINOR.PATCH`
- 每个发版有 Release Notes
- 固件与上位机 Python 脚本版本对齐

---

## 五、差距分析（当前项目 vs 标准）

| 标准 | 当前符合度 | 说明 |
|:----|:---------:|:-----|
| **P0: Git 工作流** | ⭐⭐⭐✩✩ | 有基本的分支/提交规范，但缺少 Code Review 流程 |
| **P0: C 编码规范** | ⭐⭐⭐✩✩ | 后期代码质量好于前期，但无明确规范文档 |
| **P0: 模块接口标准** | ⭐⭐⭐⭐✩ | 自然遵循了 Init/Run 模式，应明确化 |
| **P0: CAN 协议模板** | ⭐⭐⭐✩✩ | 协议信息分散在多处，没有单点权威文档 |
| **P1: HAL 接口规范** | ⭐⭐✩✩✩ | 现有 drivers/ 层未统一接口模式 |
| **P1: 日志规范** | ⭐⭐⭐✩✩ | EVENT 设计好，但日志分级未推广 |
| **P1: 审查 Checklist** | ⭐✩✩✩✩ | 没有正式审查流程 |
| **P1: 文档模板** | ⭐⭐⭐⭐✩ | 文档丰富但模板不统一 |
| **P2: 自动化测试** | ⭐✩✩✩✩ | 无 |
| **P2: CI/CD** | ⭐✩✩✩✩ | 无 |
| **P2: 设计评审** | ⭐⭐✩✩✩ | 自然发生的讨论，无正式流程 |
| **P2: 版本管理** | ⭐⭐✩✩✩ | Git tag 不系统 |

**结论**：P0 层面已有"肌肉记忆"（知道该怎么做），但缺一张纸把规则写下来。P1 层面有零星实践但不系统。P2 层面完全是空白。

---

## 六、实施路线图

```
比赛结束（现在）
  │
  ├── 第 1 周 🔴 P0
  │   ├── 定 Git 工作流规范（写在 REPO 根目录 GIT_WORKFLOW.md）
  │   ├── 定 C 编码规范（写在 REPO 根目录 CODING_STYLE.md）
  │   ├── 把现有 CAN 协议整理成一份文档
  │   └── 清理代码中的硬编码和魔术数字
  │
  ├── 第 2~3 周 🔴 P0 落地
  │   ├── 把现有分支按新规范重命名
  │   ├── 建立 Code Review 习惯（每条 PR 至少一人看）
  │   └── 所有 .h 文件按头文件规范整理
  │
  ├── 第 4 周 🟡 P1 起步
  │   ├── 统一日志输出格式（所有 DEBUG_PRINTF 改为 SYS_LOG）
  │   ├── 检查 Checklist 模板写好
  │   └── 最重要的 CAN 协议文档用模板重写
  │
  └── 下一个项目开始前 🟡 P1 完成
      ├── HAL 接口规范（drivers/ 层重构）
      ├── 验收测试清单落地
      └── 文档模板推广
```

---

## 七、一句话总结

> **P0 防烧、P1 提效、P2 扩编。先别追求完美，追求"下次不会犯同一个错"。**

P0 的四条标准（Git 工作流、C 编码规范、模块接口标准、CAN 协议模板）——这周就可以开始，下周就能落地。它们不会让你的代码一夜之间变好，但它们会让 3 个月后的你少骂现在的自己三次。
