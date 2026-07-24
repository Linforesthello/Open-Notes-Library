# 反馈环路修复计划

## 问题清单与修复方案

### Fix 1: `ticks_to_logic` 返回类型改为 `float`
- **文件**: `App/modules/speed_map.h` / `speed_map.c`
- **问题**: 返回 `int16_t` 赋给 `float current_logic_speed`，精度丢失，PID 微分项产生阶跃噪声
- **修复**: 将 `ticks_to_logic` 返回类型改为 `float`，内部做浮点除法

### Fix 2: Stop 时 Reset PID 积分项
- **文件**: `App/tasks/tb6612_DC_task.c`
- **问题**: `CMD_STOP` 时未调用 `PID_Reset()`，重启后积分残留导致超调冲击
- **修复**: 在 `CMD_STOP` 分支加 `PID_Reset(&motor_pid)`

### Fix 3: `logger_task` 类型截断
- **文件**: `App/tasks/logger_task.c`
- **问题**: `current_ticks` 是 `int32_t`，赋给 `int16_t speed_val` 存在截断风险
- **修复**: 将 `speed_val` 改为 `int32_t`，snprintf 格式符对应修改

## 执行状态
- [x] Fix 1: speed_map 浮点化
- [x] Fix 2: Stop 时 PID Reset
- [x] Fix 3: logger_task 类型修正

---

# 第二阶段：PWM 饱和 / 积分饱和问题

## 现象（来自 result.md data3 及选区诊断）

- `speed_val` ~35~40，`target` 降至 32 后仍接近，但 `pwm_output` 持续 999
- 说明 PID 积分项已大量累积，即使误差接近 0，积分残留仍将输出顶满

## 根本原因分析

### 问题 A：`MOTOR1_PID_INTEGRAL_LIMIT` 设置严重偏大

**文件**: `App/config/app_config.h` 第 63 行

```
MOTOR1_PID_INTEGRAL_LIMIT = 500.0f
MOTOR1_PID_OUTPUT_LIMIT   = 100.0f
MOTOR1_PID_KI             = 10.01f
```

积分项对输出的贡献 = `Ki * integral = 10.01 * integral`。
当 `integral = 500` 时，积分贡献 = 5005，远超 output_limit 100。
积分限幅应满足：`integral_limit ≤ output_limit / Ki = 100 / 10.01 ≈ 10`。

**修复**：将 `MOTOR1_PID_INTEGRAL_LIMIT` 从 `500.0f` 改为 `10.0f`

### 问题 B：运行中积分饱和无 anti-windup

`PID_Reset` 只在 `CMD_STOP` 时触发，运行中 setpoint 变化（如从 85 降到 32）时积分不清零，导致超调后长时间无法收敛。

**修复**：在 `tb6612_DC_task.c` 的 `CMD_SET_SPEED` 分支，若新 setpoint 与旧 setpoint 符号相反或变化超过阈值，调用 `PID_Reset`

### 问题 C（次要）：`logger_task.c` 局部变量类型不一致

`target_logic_speed` 和 `pwm_output` 仍为 `int16_t`，而 `g_motor_status` 对应字段为 `float`/`int16_t`，赋值时截断小数。
**修复**：将两者改为 `float` 和 `int32_t`，snprintf 格式符对应修改

## 修复方案

### Fix 4: 修正积分限幅
- **文件**: `App/config/app_config.h`
- `MOTOR1_PID_INTEGRAL_LIMIT` 从 `500.0f` → `10.0f`
- 原则：`integral_limit * Ki ≤ output_limit`

### Fix 5: setpoint 变化时条件性 PID Reset
- **文件**: `App/tasks/tb6612_DC_task.c`
- 在 `CMD_SET_SPEED` 处理后，若新旧 setpoint 符号不同，调用 `PID_Reset`

### Fix 6: logger_task 类型完整修正
- **文件**: `App/tasks/logger_task.c`
- `target_logic_speed` → `float`，`pwm_output` → `int32_t`
- snprintf 格式符：`%d` → `%.1f` / `%d`

## 执行状态
- [x] Fix 4: 积分限幅修正
- [x] Fix 5: setpoint 变化时条件性 Reset
- [x] Fix 6: logger_task 类型完整修正

---

# 第三阶段：CAN 命令不灵敏 / 高速目标 PWM 饱和

## 现象（来自 result.md claude-2）

- `cansend can17 125#1120` → target=32，speed=25~26，pwm=69~79，**正常收敛**
- `cansend can17 125#1140` → target=64，pwm=999，速度设置失效
- `cansend can17 125#1155` → target=85，pwm=999，速度设置失效

## 根本原因分析

### 问题 A：电机物理极限约为逻辑速度 32

数据推算：每周期 ticks ≈ 25~26，`ticks_to_logic(26) = 26 * 100 / 80 = 32.5`。
`SPEED_TICKS_MAX = 80` 对应的是电机在当前供电下**无法达到**的转速。
target=64/85 时误差持续 ~40/60，积分虽然限幅为 10，但 `Ki=10.01` 使积分贡献 = `10 * 10.01 = 100.1`，直接顶满 output_limit，PWM 永远 999。

**两个方向可选：**
1. 降低 `SPEED_TICKS_MAX` 至实测最大值（约 30），重新标定逻辑速度范围
2. 保持标定不变，接受电机在高目标下全功率运行（开环行为）

### 问题 B：`can.c` 中 `0x11` 分支使用 `CMD_SET_SPEED` 而非 `CAN_CMD_SET_SPEED`

**文件**: `Core/Src/can.c` 第 58 行

```c
case 0x11:
    cmdMsg.type = CMD_SET_SPEED;   // ← 应为 CAN_CMD_SET_SPEED
```

语义不一致，虽然 `is_motor_cmd()` 两者都处理，但 ACK 回复走 `CMD_SET_SPEED` 分支而非 `CAN_CMD_SET_SPEED`，导致 ACK 日志混乱。

### 问题 C：CAN 命令不灵敏的根本原因

`CommandQueueHandle` 在中断中用 `osMessageQueuePut(..., 0U, 0U)` 发送（timeout=0）。
若 CommandQueue 满（默认容量通常为 1~4），中断中的命令会被**静默丢弃**，不报错。
高频 CAN 帧或 CommandTask 处理慢时会出现命令丢失。

## 修复方案

### Fix 7: 修正 can.c 中 0x11 分支命令类型
- **文件**: `Core/Src/can.c` 第 58 行
- `CMD_SET_SPEED` → `CAN_CMD_SET_SPEED`

### Fix 8: 重新标定 SPEED_TICKS_MAX
- **文件**: `App/config/app_config.h`
- 实测电机每周期最大 ticks ≈ 28~30，将 `SPEED_TICKS_MAX` 从 `80` 降至 `30`
- 效果：逻辑速度 100 对应实际最大转速，target=85 时电机能真正达到 ~85% 最大转速
- **注意**：修改后需同步验证 `logic_to_pwm` 映射是否仍然合理

### Fix 9（可选）: 增大 CommandQueue 容量
- **文件**: FreeRTOS 配置（freertos.c 或 CubeMX 生成的队列定义处）
- 将 CommandQueueHandle 容量从默认值增大至 8，减少中断中命令丢失

## 执行状态
- [x] Fix 7: can.c 命令类型修正（CMD_SET_SPEED → CAN_CMD_SET_SPEED）
- [x] Fix 8: PID 参数重整定（Kp: 0.01362→1.5，Ki: 10.01→0.5，积分贡献从100降至5）
- [ ] Fix 9: CommandQueue 容量扩大（可选，待观察是否仍有丢帧）
- [ ] Fix 10: SPEED_TICKS_MAX 重新标定（需实测电机最大 ticks/周期 后修改）

---

# 总结

## 已完成修复一览

| Fix | 文件 | 问题 | 修复内容 |
|---|---|---|---|
| Fix 1 | `App/modules/speed_map.h/.c` | `ticks_to_logic` 返回 `int16_t`，精度丢失 | 返回类型改为 `float`，内部浮点除法 |
| Fix 2 | `App/tasks/tb6612_DC_task.c` | `CMD_STOP` 时未清积分，重启超调 | 加 `PID_Reset(&motor_pid)` |
| Fix 3 | `App/tasks/logger_task.c` | `current_ticks`(int32) 赋给 `int16_t speed_val` 截断 | `speed_val` 改为 `int32_t` |
| Fix 4 | `App/config/app_config.h` | `INTEGRAL_LIMIT=500`，积分贡献 5005 远超 output_limit 100 | 改为 `10.0f` |
| Fix 5 | `App/tasks/tb6612_DC_task.c` | setpoint 符号反转时积分残留导致换向超调 | setpoint 符号变化时调用 `PID_Reset` |
| Fix 6 | `App/tasks/logger_task.c` | `target_logic_speed` 局部变量为 `int16_t`，截断 float | 改为 `float`，snprintf 用整数拆分（F103 不支持 `%f`） |
| Fix 7 | `Core/Src/can.c` | `0x11` 分支用 `CMD_SET_SPEED` 而非 `CAN_CMD_SET_SPEED` | 改为 `CAN_CMD_SET_SPEED`，ACK 路径对齐 |
| Fix 8 | `App/config/app_config.h` | `Kp=0.01362` 过小，`Ki=10.01` 过大，控制器退化为纯积分饱和 | `Kp: 0.01362→1.5`，`Ki: 10.01→0.5` |

## 当前参数状态（TB6612）

```c
SPEED_TICKS_MAX     = 80       // ← 待标定（实测最大约 26，建议改为 30）
SPEED_LOGIC_MAX     = 100
PWM_MAX             = 999      // 对应定时器 ARR，100% 占空比

MOTOR1_PID_KP       = 1.5f
MOTOR1_PID_KI       = 0.5f
MOTOR1_PID_KD       = 0.0025f
MOTOR1_PID_INTEGRAL_LIMIT  = 10.0f   // 积分饱和贡献 = 10*0.5 = 5
MOTOR1_PID_OUTPUT_LIMIT    = 100.0f
MOTOR1_PID_TS              = 0.01f
```

## 调试结论

- **速度反馈**：已正常，`cnt_val` 递增，`speed_val` 非零
- **target=32**：收敛正常，pwm=69~79，误差 ≤ 7
- **target=64/85**：超出电机当前物理极限（约逻辑速度 32），需完成 Fix 10 标定后才能有效控制
- **CAN 协议**：`125#11xx` 格式中 `xx` 为逻辑速度（十六进制），如 `125#1120` = 速度 32

## 下一步

1. 完成 Fix 10：串口观察 `cnt_val` 相邻行差值，取稳定最大值，更新 `SPEED_TICKS_MAX`
2. 完成 Fix 10 后重新验证 target=64/85 是否能正常收敛
3. 若仍有 CAN 命令偶发丢失，再处理 Fix 9（扩大 CommandQueue 容量至 8）

# 第四阶段：USART1 DMA TX 无输出

## 现象

- 发送 `0x04` 后有 CAN `0xCF` 回包，确认 `g_logger_enabled = 1` 已执行
- huart2 诊断输出：`gs=32`（HAL_UART_STATE_BUSY_TX），`st=0`（HAL_OK）
- 每次调用 `HAL_UART_Transmit_DMA` 返回成功，但 gState 永远不回到 READY
- huart1（USART1）串口助手无任何数据输出

## 根本原因

**DMA1_Channel4（USART1_TX）的 NVIC 中断未使能。**

`stm32f1xx_it.c` 中 `DMA1_Channel4_IRQHandler` 已存在且调用了 `HAL_DMA_IRQHandler(&hdma_usart1_tx)`，但 `usart.c` 的 `HAL_UART_MspInit` 中只配置了 USART1 的 UART 中断，**漏掉了 DMA TX channel 的 NVIC 使能**：

```c
// usart.c 中缺失的两行（应加在 __HAL_LINKDMA(uartHandle,hdmatx,...) 之后）
HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 5, 0);
HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
```

DMA 传输完成后中断无法触发 → `HAL_UART_DMAConvCpltCallback` 永远不被调用 → HAL 状态机卡死在 `BUSY_TX` → 后续所有 `HAL_UART_Transmit_DMA` 因 `gState != READY` 被跳过。

这是 CubeMX 的已知遗漏：生成代码时 DMA TX IRQ Handler 写入 it.c，但 MspInit 中不自动添加对应的 `HAL_NVIC_EnableIRQ`。

## 修复方案

### Fix 11: usart.c 补充 DMA1_Channel4 NVIC 使能

**文件**: `Core/Src/usart.c`，`HAL_UART_MspInit` 的 USART1 分支

在 `__HAL_LINKDMA(uartHandle,hdmatx,hdma_usart1_tx);` 之后、USART1 interrupt Init 之前添加：

```c
/* USART1 DMA TX interrupt Init */
HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 5, 0);
HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
```

**注意**：usart.c 是 CubeMX 生成文件，重新生成代码会覆盖此修改。需要在 `.ioc` 中手动勾选 DMA1 Channel4 的 NVIC 中断，或将修改放在 `USER CODE BEGIN` 区域内。

## 执行状态
- [ ] Fix 11: usart.c 补充 DMA1_Channel4_IRQn NVIC 使能（已被 linter/CubeMX 覆盖，待重新添加）
