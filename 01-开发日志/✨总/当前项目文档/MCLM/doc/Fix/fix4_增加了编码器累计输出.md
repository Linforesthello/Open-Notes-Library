# fix4: 增加编码器累计输出

## 目标

在反馈数据中加入 `accumulated_ticks`（编码器累计计数值），反映电机绝对位置，而非仅每周期差值。

## 改动文件

| 文件 | 改动 |
|------|------|
| `App/config/app_globals.h` | `Motor_t` 新增 `int32_t accumulated_ticks` |
| `App/services/logger.h` | `LogMotorData_t` 新增 `int32_t accumulated_ticks` |
| `App/tasks/encoder_task.c` | 每周期 `motor->accumulated_ticks += diff` 累加，填入日志包 |
| `App/tasks/logger_task.c` | 缓冲区 64→128 字节；CSV 增加累计值列 |

## CSV 输出格式

**两路合并行**（原 7 列 → 9 列）：
```
timestamp, ticks0, acc_ticks0, speed0_int.speed0_frac, pwm0, ticks1, acc_ticks1, speed1_int.speed1_frac, pwm1
```

**单路行**（原 5 列 → 6 列）：
```
timestamp, motor_id, ticks, acc_ticks, speed_int.speed_frac, pwm
```

## 验证

- `accumulated_ticks` 由 encoder_task 每 10ms 累加一次，随 LogMotorData_t 经 LogQueue 投递
- 类型 `int32_t`，范围 ±21 亿，正常使用不会溢出
- 上电后从 0 开始累加，反转时递减
