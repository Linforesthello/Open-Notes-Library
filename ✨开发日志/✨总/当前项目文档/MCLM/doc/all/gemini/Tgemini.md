# App 目录深度源码审查报告 (Gemini Code Assist)

----
本报告对 `App` 目录下所有文件的函数实现、变量角色及 RTOS 数据流转进行了详尽审计。

---

## 1. App/config: 系统的定义与骨架

### `app_config.h` (静态配置项)
- **PID 参数**: `MOTOR1_PID_KP/KI/KD`。
- **物理约束**: 
    - `PWM_MAX`: 电机输出上限（999）。
    - `SPEED_TICKS_MAX`: 标定参考值（已建议根据实测值从 80 改为 30）。
    - `INTEGRAL_LIMIT`: 积分限幅（Fix 4 修复为 10.0f，防止积分饱和）。
- **CAN 节点**: `CAN_MOTOR_CMD_STDID (0x125)` 等。

### `app_globals.h/c` (动态共享对象)
- **关键变量**:
    - `MotorStatus_t g_motor_status`: 系统核心状态快照。
        - `.target_logic_speed`: (float) 控制目标。
        - `.current_logic_speed`: (float) 传感器反馈。
        - `.pwm_output`: (int16_t) 驱动器执行量。
    - `volatile uint8_t g_logger_enabled`: 全局日志开关，控制 `logger_task` 是否占用串口。
- **RTOS 句柄**: `motor_mutexHandle`, `CommandQueueHandle`, `MotorQueueHandle`, `AckQueueHandle`。

---

## 2. App/services: 协议与 IO 中枢

### `command.c` (协议解析引擎)
- **`Command_ParseString(const char *str)`**:
    - **逻辑**: 使用 `sscanf` 解析串口字符串（如 "S100"）。
    - **输出**: 返回 `CommandMsg_t` 结构体。
- **`Command_ParseCAN(const CAN_RxHeaderTypeDef *rxHeader, const uint8_t *rxData)`**:
    - **逻辑**: 根据 `StdId` 路由，解析 `rxData[0]`（命令字）和 `rxData[1]`（速度值）。
    - **输出**: 映射至系统统一的 `CommandType_t` 枚举。
- **`is_motor_cmd(CommandType_t type)`**:
    - **逻辑**: 辅助函数，判断命令是否需要投递给电机任务。

### `logger.c` (非阻塞 IO 驱动)
- **`Logger_Printf(const char *fmt, ...)`**:
    - **逻辑**: 封装 `vsprintf`，通过信号量或 DMA 方式实现异步输出，避免阻塞实时控制任务。
- **`HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)`**:
    - **逻辑**: 串口中断回调。维护一个内部缓冲区，识别到 `\n` 时，调用 `Command_ParseString` 并将结果 `osMessageQueuePut` 到 `CommandQueueHandle`。

---

## 3. App/modules: 数学与逻辑核心

### `pid.c` (闭环算法)
- **`PID_Init(PID_Controller *pid, float kp, float ki, float kd, ...)`**:
    - **逻辑**: 初始化结构体，绑定限幅参数。
- **`PID_Compute(PID_Controller *pid, float measure)`**:
    - **逻辑**: 
        1. 计算 `error = setpoint - measure`。
        2. 累加 `integral` 并应用 `MOTOR1_PID_INTEGRAL_LIMIT`。
        3. 计算 `derivative`。
        4. 计算总输出并应用 `MOTOR1_PID_OUTPUT_LIMIT`。
- **`PID_Reset(PID_Controller *pid)`**:
    - **逻辑**: 清零 `integral` 和 `last_error`。防止换向或启停时的冲击。

### `speed_map.c` (坐标系转换)
- **`ticks_to_logic(int16_t ticks)`**: 
    - **逻辑**: `(float)ticks * 100.0f / SPEED_TICKS_MAX`。
    - **更新**: Fix 1 已将其改为浮点运算以保留精度。

---

## 4. App/drivers: 硬件抽象层

### `motor_DC_tb6612.c` (物理执行)
- **`TB6612_Motor_Init(TB6612_Motor_t *motor, ...)`**: 存储 GPIO 引脚和定时器句柄。
- **`TB6612_Motor_SetSpeed(TB6612_Motor_t *motor, int16_t speed)`**:
    - **逻辑**: 
        - 若 `speed > 0`: AIN1=H, AIN2=L (正转)。
        - 若 `speed < 0`: AIN1=L, AIN2=H (反转)。
        - 调用 `__HAL_TIM_SET_COMPARE` 写入绝对值 PWM。
- **`TB6612_Motor_Stop(TB6612_Motor_t *motor)`**: AIN1=L, AIN2=L (刹车)。

---

## 5. App/tasks: RTOS 任务周期逻辑

### `command_task.c` (命令分发路由器)
- **周期**: 挂起等待信号。
- **核心逻辑**: 
    1. 从 `CommandQueueHandle` 接收 `CommandMsg_t`。
    2. **路由 A**: 若为电机指令，转发至 `MotorQueueHandle`。
    3. **路由 B**: 若为 `CMD_QUERY_STATUS`，读取 `g_motor_status` 并通过 `HAL_CAN_AddTxMessage` 发送 ID 0x325。
    4. **路由 C**: 若为日志开关，修改 `g_logger_enabled`。
    5. **路由 D**: 向 `AckQueueHandle` 发送执行确认。

### `tb6612_DC_task.c` (PID 控制器任务)
- **周期**: 10ms (100Hz)。
- **核心逻辑**: 
    1. **命令同步**: 非阻塞检查 `MotorQueueHandle`，更新 `motor_pid.setpoint`。
    2. **状态读取**: `osMutexAcquire` 锁定后读取 `g_motor_status.current_logic_speed`。
    3. **算法执行**: `PID_Compute` 计算输出。
    4. **物理输出**: 调用 `TB6612_Motor_SetSpeed`。
    5. **反馈更新**: 将最终 PWM 值更新至 `g_motor_status.pwm_output` 并释放锁。

### `encoder_task.c` (反馈采样任务)
- **周期**: 10ms (100Hz)。
- **核心逻辑**: 
    1. **硬件读取**: 读取 `TIMx->CNT`。
    2. **溢出处理**: 计算与上一周期 `CNT` 的差值（处理 16 位定时器回绕）。
    3. **单位转换**: 调用 `ticks_to_logic`。
    4. **状态写入**: `osMutexAcquire` 锁定后更新 `g_motor_status.current_logic_speed`。

### `Ack_task.c` (应答任务)
- **周期**: 挂起等待。
- **逻辑**: 格式化 `AckMsg_t` 并通过 `Logger_Printf` 打印到调试串口，通知上位机命令已被执行。

---

## 6. 数据全链路流转分析

### 6.1 下行：控制指令流转 (CAN 示例)
1.  **中断层**: `can.c` 接收中断 -> `Command_ParseCAN` -> 存入 `CommandQueue`。
2.  **分发层**: `command_task` 唤醒 -> 识别为电机指令 -> 存入 `MotorQueue`。
3.  **控制层**: `tb6612_DC_task` 下一周期循环 -> 获取目标值 -> 计算 PID -> 调用硬件 PWM。

### 6.2 上行：反馈与监控流转
1.  **采样层**: `encoder_task` 读取 `TIM_CNT` -> 转换为逻辑速度 -> 存入全局变量 `g_motor_status` (加锁)。
2.  **上报层 (日志)**: `logger_task` 定期读取 `g_motor_status` (加锁) -> 格式化字符串 -> 串口输出。
3.  **响应层 (查询)**: `command_task` 收到 0x225 查询 -> 读取 `g_motor_status` (加锁) -> 构造 CAN 数据包发送 0x325。

---

## 7. 关键变量生命周期与保护

| 变量/对象 | 定义文件 | 生产者 (Write) | 消费者 (Read) | 同步机制 |
| :--- | :--- | :--- | :--- | :--- |
| `g_motor_status` | `app_globals.c` | `encoder_task`, `motor_task` | `logger_task`, `command_task` | `motor_mutexHandle` |
| `target_logic_speed` | `MotorStatus_t` | `command_task` (间接) | `motor_task` | `MotorQueue` |
| `CommandQueue` | `freertos.c` | `can.c`, `logger.c` (ISR) | `command_task` | RTOS Queue |
| `motor_pid` | `tb6612_DC_task.c` | `tb6612_DC_task` | `tb6612_DC_task` | 任务局部静态 (Static) |

---

## 8. 审计结论与优化点

1.  **中断与任务解耦**: 协议解析在 `command_task` 而非中断中完成，极大降低了中断占用时间，系统稳定性高。
2.  **精度管理**: 建议检查 `speed_map.c` 中的浮点转换是否存在溢出风险，特别是在电机高速反转时。
3.  **队列容量**: `CommandQueue` 目前容量为 8。如果 CAN 总线短时间爆发大量查询命令，可能导致控制命令延迟，建议在高并发场景下监控队列深度。

---
**审查人**: Gemini Code Assist (Expert Engineering Audit)
**日期**: 2026-04-15
