#底盘/3_MCLM_Cmake_test 
## command_task.c
### 发送数据包0x201,返回0x301数据包，重复四次。这是提取后的数据“55 00 57 00 4F 00 00 00 ”“55 00 56 00 59 00 00 00 ”“55 00 56 00 4F 00 00 00 ”“55 00 57 00 4F 00 00 00 ”。解析
---
	command_task.c
	发送数据包0x201,返回0x301数据包，重复四次。这是提取后的数据“55 00 57 00 4F 00 00 00 ”“55 00 56 00 59 00 00 00 ”“55 00 56 00 4F 00 00 00 ”“55 00 57 00 4F 00 00 00 ”。解析
	Let me look at the relevant code to understand the 0x301 packet format.
	
	Grep "0x301|0x201" (in ., type: c)
	4 lines of output
	Grep "0x301" (in ., type: c)
	13 lines of output
	Read command_task.c (lines 42-71)
	格式确认：[target(2B LE), current(2B LE), pwm(2B LE), reserved(2B)]，全部 int16_t 小端序。
	
	解析四帧数据：
	
	帧格式： target[0:1] | current[2:3] | pwm[4:5] | reserved[6:7]
	
	帧	原始数据	target (int16 LE)	current (int16 LE)	pwm (int16 LE)
	1	55 00 57 00 4F 00 00 00	0x0055 = 85	0x0057 = 87	0x004F = 79
	2	55 00 56 00 59 00 00 00	0x0055 = 85	0x0056 = 86	0x0059 = 89
	3	55 00 56 00 4F 00 00 00	0x0055 = 85	0x0056 = 86	0x004F = 79
	4	55 00 57 00 4F 00 00 00	0x0055 = 85	0x0057 = 87	0x004F = 79
	结论：
	
	target_logic_speed 固定为 85（目标速度稳定）
	current_logic_speed 在 86~87 之间小幅波动（已基本跟上目标）
	pwm_output 在 79~89 之间波动（闭环调节中）
	电机处于稳态运行，速度误差 ≤ 2，系统正常


![[Pasted image 20260322095253.png]]

### 测试过程
#### 
![[Pasted image 20260323170146.png]]


cansend can0 124#1155
cansend can0 124#1100

cansend can0 224#0100000101

## 当前架构梳理

> [!NOTE]
> 架构梳理完毕，以下是分析与优化建议：
> 
> 架构梳理
> 
> CommandQueueHandle ──► Command_Task ──► MotorQueueHandle ──► TB6612_DC_Task (PID)
>                                     └──► AckQueueHandle  ──► Ack_Task (UART)
> 
> Encoder_Task (TIM2) ──► g_motor_status (mutex) ──► Logger_Task (UART DMA)
>                     └──► osThreadFlagsSet ──────────────────────────────────►┘
> 
> CAN RX ──► CommandQueueHandle (via can_service)
> 优化建议
> 1. encoder_task.c — 主要问题
> 问题1：溢出处理逻辑冗余
> 
> 
> // 当前代码
> int32_t diff = (int16_t)(now - last_cnt);
> if (diff > 32768) diff -= 65536;
> else if (diff < -32768) diff += 65536;
> (int16_t)(now - last_cnt) 本身已经利用了 int16_t 的自然溢出回绕完成了差值计算，后面的 if/else 判断是多余的。直接用：
> 
> 
> int16_t diff = (int16_t)(now - last_cnt);
> 问题2：static 局部变量在任务函数中
> 
> last_cnt 声明在 for(;;) 循环体内，每次循环都会"重新声明"（虽然 static 只初始化一次），但这是不良风格，应提到循环外：
> 
> 
> static int16_t last_cnt = 0;  // 移到 for 循环之前
> for(;;) { ... }
> 问题3：Logger 唤醒与编码器耦合
> 
> Encoder_Task 直接调用 osThreadFlagsSet(Logger_TaHandle, 0x01) 唤醒 Logger，造成两个任务强耦合。Logger 的触发频率应由自身决定，或通过队列/信号量解耦。当前设计中 Logger 完全依赖 Encoder 的节拍，若 Encoder 任务被修改，Logger 也会受影响。
> 
> 建议：Logger 改为独立定时（osDelay(10)）或使用独立的信号量，Encoder 只负责更新数据。
> 
> 2. tb6612_DC_task.c — 双重 delay 问题
> 
> if (!messageProcessed) {
>     osDelay(5);   // ← 条件延时
> }
> osDelay(10);      // ← 无条件延时，始终执行
> 无论是否处理了消息，都会执行 osDelay(10)，前面的 osDelay(5) 实际上只是在没有消息时多等 5ms，逻辑混乱。
> 
> 建议：统一为固定 10ms 周期，或改为阻塞等待队列（osWaitForever）+ 超时触发 PID：
> 
> 
> status = osMessageQueueGet(MotorQueueHandle, &cmdMsg, NULL, 10); // 10ms超时
> // 无论是否收到消息，都执行PID
> 3. logger_task.c — 注释残留代码
> logger_task.c 中有一行损坏的注释：
> 
> 
> // --- Release Mutex ---\n        
> \n 是字面字符串，不是换行，是复制粘贴遗留的垃圾。
> 
> 4. command_task.c — 轻微问题
> CMD_FORWARD / CMD_REVERSE 在 is_motor_cmd() 中被识别为电机命令，但 tb6612_DC_task.c 里没有处理这两个类型（只处理 CMD_SET_SPEED 和 CMD_STOP），命令会被静默丢弃。需要确认这两个命令是否已废弃，若是则从 is_motor_cmd() 中移除。
> 
> 5. 整体架构建议
> 问题	建议
> g_motor_status 每次读写都加 mutex，粒度过细	考虑将 Encoder 写入和 Motor 读取分离为两个独立结构体，减少竞争
> Logger 读取 htim2 计数器（cnt_val）但同时 Encoder 也在读，存在竞态	Logger 直接从 g_motor_status.current_ticks 读取即可，无需再读硬件寄存器
> 空文件（BLDC_task.c, can_task.c, ibt4_DC_task.c）占位	若暂不实现，删除或加 #error 提示
> 最高优先级修复：encoder_task.c 的冗余溢出处理 + tb6612_DC_task.c 的双重 delay。需要我直接修改这两处吗？

---
## 单路供电不足，导致的时好时坏（接入调试器后，会从usb口取电）
### 在四块mcu上均有出现，目前3.3v线路由单排换成双排，已经得到缓解
### 在更换到双层控制系统后，问题未发生
## encoder_task.c
### 开始修改，一个一个来

> [!NOTE]
> 从优先级最高的开始，先修 encoder_task.c。
> 
> Read encoder_task.c
> Edit encoder_task.c
> Removed 14 lines
> encoder_task.c 修改完成，改动点：
> 
> 溢出补偿修复：去掉 (int16_t) 强转，改为 int32_t 相减后补偿，溢出逻辑现在真正生效
> static 移出循环：last_cnt 移到 for 外，语义更清晰
> 唤醒 LogTask 移入 mutex 块内：只有数据成功写入后才通知，避免打印旧数据
> 下一个：tb6612_DC_task.c 的双重 delay 问题，继续吗？

---
#### 当前源代码
```

#include "app_includes.h"
#include "speed_map.h"


void Encoder_Task(void *argument)
{
  HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);

  int16_t last_cnt = 0;

  for(;;)
  {
    int16_t now = (int16_t)__HAL_TIM_GET_COUNTER(&htim2);

    // 正确处理16位计数器溢出
    int32_t diff = (int32_t)now - (int32_t)last_cnt;
    if (diff > 32767)       diff -= 65536;
    else if (diff < -32768) diff += 65536;
    last_cnt = now;

    if (osMutexAcquire(motor_mutexHandle, osWaitForever) == osOK)
    {
        g_motor_status.current_ticks = diff;
        g_motor_status.current_logic_speed = ticks_to_logic(diff);
        osMutexRelease(motor_mutexHandle);

        // 数据更新成功后才唤醒 LogTask
        if (Logger_TaHandle != NULL)
            osThreadFlagsSet(Logger_TaHandle, 0x01);
    }

    osDelay(10);
  }
}
```

### ==当前修改未测试==

## Logger功能
### prompt&ack

> [!NOTE]
> 这份工程文件是作为一个末端控制器，控制一个电机的程序，同时具有接受外部can控制命令进行电机运动、外部can查询命令进行反馈、外部串口命令进行单mcu调试、同时开机起就一直在输出电机端侧的信息。
> 当前，logger程序是运用的串口发送一定格式的数据到外部（方便外部软件比如vofa+去进行绘图） ，这是开机就会运行的，很浪费资源和末端的控制器占用。
> （tick,pwm,logic等等  @App/services/logger.c   @App/tasks/logger_task.c @App/services/logger.h  ）
> 1、有什么好的办法，给他优化一下？列出可行项目。
> 2、我想要在当前的工程中成立一个统一的数据管理中心，主要是接受 @Core/Src/can.c @App/tasks/command_task.c @App/services/command.h  接受到的外部can数据，进行响应（比如说受到can命令，开始/停止发送实时的电机端侧数据，）


> [!NOTE]
> 看了你的代码，给你分析一下：
> 
> 1. Logger 优化可行方案
> 当前问题： Logger_Task 开机就一直跑，每次 TIM3 中断都触发发送，持续占用 UART1 + CPU。
> 
> 可行优化项：
> 
> A. 按需开关（推荐）
> 用一个全局 flag g_logger_enabled，默认 0（关闭），收到 CAN/UART 命令后才开启。最小改动，效果最直接。
> 
> B. 降频发送
> 不是每次 TIM3 中断都发，而是每 N 次才发一次（计数器取模）。适合"一直开但不想太频繁"的场景。
> 
> C. 触发式快照
> 不用周期发送，只在状态变化超过阈值时才发（速度变化 > X，PWM 变化 > Y）。适合调试用，平时静默。
> 
> D. 改用 DMA + 环形缓冲
> 当前 UART1 用 DMA 但没有缓冲保护，忙时直接丢帧。加环形缓冲可以减少丢帧，但不减少发送频率本身。
> 
> 2. 统一数据管理中心设计
> 你的需求本质是：CAN 命令能控制 Logger 的开/停，同时集中管理"谁在控制什么"。
> 
> 最小可行方案：在现有架构上加一个 g_logger_enabled flag，扩展 CommandType_t 加两个命令，CAN 收到后通过 CommandQueue → CommandTask 处理。
> 
> 新增命令类型（command.h）：
> 
> 
> CMD_LOG_START,   // CAN 命令：开始发送电机数据
> CMD_LOG_STOP,    // CAN 命令：停止发送电机数据
> CAN 协议映射（can.c switch 里加）：
> 
> 
> case 0x02:  // 开始日志
>     cmdMsg.type = CMD_LOG_START;
>     break;
> case 0x03:  // 停止日志
>     cmdMsg.type = CMD_LOG_STOP;
>     break;
> CommandTask 处理（command_task.c）：
> 
> 
> if (cmd.type == CMD_LOG_START) { g_logger_enabled = 1; continue; }
> if (cmd.type == CMD_LOG_STOP)  { g_logger_enabled = 0; continue; }
> Logger_Task 加判断（logger_task.c）：
> 
> 
> osThreadFlagsWait(0x01, osFlagsWaitAny, osWaitForever);
> if (!g_logger_enabled) continue;  // 加这一行
> // ... 后续发送逻辑不变
> 你想先做哪个？ 我可以直接帮你改代码。方案 A（按需开关）+ CAN 控制是改动最小、收益最大的组合。
> 
> 第二个数据中心管理吧
> 先看一下现有的文件结构和相关文件。
> 
> Agent:Explore project structure
> IN
> Explore the project at /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test and give me:
> 1. The full directory tree of App/ folder
> 2. Contents of App/includes/app_includes.h (or wherever app_includes.h is)
> 3. Contents of App/includes/app_config.h (or wherever app_config.h is)
> 4. Contents of Core/Src/freertos.c (just the queue/mutex/task handle declarations and task creation parts)
> 5. Contents of App/tasks/encoder_task.c
> 6. Contents of App/services/motor_control.h or similar motor status header
> 
> Focus on finding: where g_motor_status is declared, where osMessageQueueId_t handles are declared (CommandQueueHandle, AckQueueHandle, MotorQueueHandle), and the CMakeLists.txt source file list.
> Bash
> IN
> find /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test -type f -name "*.h" -o -name "*.c" -o -name "CMakeLists.txt" | head -50
> 
> OUT
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/cmake/stm32cubemx/CMakeLists.txt
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/CMakeLists.txt
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/app_task.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/app_includes.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/app_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/services/command.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/services/can_service.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/services/logger.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/services/command.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/services/logger.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/services/can_service.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/encoder_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/can_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/ibt4_DC_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/Ack_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/command_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/heartbeat_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/tb6612_DC_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/BLDC_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/at8236_DC_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/logger_task.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/modules/speed_map.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/modules/pid.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/modules/filter.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/modules/pid.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/modules/speed_map.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/app_config.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_DC_tb6612.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/encoder.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_DC_tb6612.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_BLDC.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_DC_at8236.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_DC_ibt4.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/encoder.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_BLDC.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_DC_ibt4.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/drivers/motor_DC_at8236.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/app_globals.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/freertos_mpool.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/freertos_os2.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/list.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/timers.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/event_groups.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/queue.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM3/portmacro.h
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM3/port.c
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Middlewares/Third_Party/FreeRTOS/Source/portable/MemMang/heap_4.c
> Bash
> IN
> tree /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App -L 3 2>/dev/null || find /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App -type f | sort
> 
> OUT
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App
> |-- app_config.h
> |-- app_globals.h
> |-- app_includes.h
> |-- app_task.c
> |-- app_task.h
> |-- drivers
> |   |-- encoder.c
> |   |-- encoder.h
> |   |-- motor_BLDC.c
> |   |-- motor_BLDC.h
> |   |-- motor_DC_at8236.c
> |   |-- motor_DC_at8236.h
> |   |-- motor_DC_ibt4.c
> |   |-- motor_DC_ibt4.h
> |   |-- motor_DC_tb6612.c
> |   `-- motor_DC_tb6612.h
> |-- modules
> |   |-- filter.c
> |   |-- pid.c
> |   |-- pid.h
> |   |-- speed_map.c
> |   `-- speed_map.h
> |-- services
> |   |-- can_service.c
> |   |-- can_service.h
> |   |-- command.c
> |   |-- command.h
> |   |-- logger.c
> |   `-- logger.h
> `-- tasks
>     |-- Ack_task.c
>     |-- BLDC_task.c
>     |-- at8236_DC_task.c
>     |-- can_task.c
>     |-- command_task.c
>     |-- encoder_task.c
>     |-- heartbeat_task.c
>     |-- ibt4_DC_task.c
>     |-- logger_task.c
>     `-- tb6612_DC_task.c
> 
> 4 directories, 36 files
> Bash
> IN
> find /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test -name "freertos.c" -type f
> 
> OUT
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/Core/Src/freertos.c
> Read encoder_task.c
> Read CMakeLists.txt
> Bash
> IN
> grep -r "g_motor_status" /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App --include="*.c" | head -20
> 
> OUT
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/app_task.c:MotorStatus_t g_motor_status;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/encoder_task.c:        g_motor_status.current_ticks = diff;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/encoder_task.c:        g_motor_status.current_logic_speed = ticks_to_logic(diff);
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/command_task.c:            status = g_motor_status;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/tb6612_DC_task.c:                    g_motor_status.target_logic_speed = motor_pid.setpoint;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/tb6612_DC_task.c:                float current_speed = g_motor_status.current_logic_speed; // 使用实际速度作为当前速度
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/tb6612_DC_task.c:                g_motor_status.pwm_output = tb6612_motor.pwm_output;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/tb6612_DC_task.c:                g_motor_status.pwm_output = 0;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/at8236_DC_task.c:                    g_motor_status.target_logic_speed = motor_pid.setpoint;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/at8236_DC_task.c:                    g_motor_status.target_logic_speed = 0.0f;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/at8236_DC_task.c:                float current_speed = g_motor_status.current_logic_speed;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/at8236_DC_task.c:                g_motor_status.pwm_output = at8236_A.pwm_output; // Update global status
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/at8236_DC_task.c:                g_motor_status.pwm_output = 0;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/logger_task.c:        speed_val = g_motor_status.current_ticks;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/logger_task.c:        target_logic_speed = g_motor_status.target_logic_speed;
> /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_Cmake_test/App/tasks/logger_task.c:        pwm_output = g_motor_status.pwm_output;
> Read app_task.c
> 再看几个关键文件。
> 
> Read app_globals.h
> Read app_includes.h
> Read Ack_task.c
> 现在清楚了整个架构，开始实现。
> 
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> Read app_task.c
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> Step 1: command.h 新增两个命令类型
> 
> Edit command.h
> Added 4 lines
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> Step 2: app_globals.h 添加 g_logger_enabled
> 
> Edit app_globals.h
> Added 1 line
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> Step 3: app_task.c 定义 g_logger_enabled
> 
> Edit app_task.c
> Added 1 line
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> Step 4: can.c 添加 0x04/0x05 命令解析
> 
> Edit can.c
> Added 8 lines
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> Step 5: command_task.c 处理 CMD_LOG_START/STOP
> 
> Edit command_task.c
> Edit failed
> Edit command_task.c
> Added 4 lines
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> Step 6: logger_task.c 加 flag 判断
> 
> Edit logger_task.c
> Added 3 lines
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> CMakeLists.txt 不需要改动，所有修改都在已有文件里。
> 
> Update Todos
> 
> 新增 CMD_LOG_START / CMD_LOG_STOP 到 command.h
> 
> 在 app_globals.h 添加 g_logger_enabled 全局 flag
> 
> 在 app_task.c 定义 g_logger_enabled
> 
> can.c 添加 CAN 开/停日志命令解析
> 
> command_task.c 处理 CMD_LOG_START/STOP
> 
> logger_task.c 加 flag 判断
> 
> CMakeLists.txt 确认无需改动
> 完成。改动汇总：
> 
> 改动了 5 个文件，新增 0 个文件：
> 
> 文件	改动
> command.h	新增 CMD_LOG_START / CMD_LOG_STOP
> app_globals.h	新增 extern volatile uint8_t g_logger_enabled
> app_task.c	定义 g_logger_enabled = 0（默认关闭）
> can.c	case 0x04 → CMD_LOG_START，case 0x05 → CMD_LOG_STOP
> command_task.c	收到命令直接设 flag，continue 跳过后续处理
> logger_task.c	osThreadFlagsWait 之后加 if (!g_logger_enabled) continue
> CAN 协议：
> 
> 任意已过滤 ID（0x123/0x101/0x102/0x223）发送 [0x04, ...] → 开始发送电机数据
> 发送 [0x05, ...] → 停止
> 数据流路径：
> 
> 
> CAN中断 → CommandQueue → CommandTask → g_logger_enabled = 1/0
>                                               ↓
>                                        Logger_Task 检查 flag
> Logger_Task 本身还是靠 TIM3 中断唤醒，只是唤醒后如果 flag=0 就直接 continue，不做任何 UART 发送，几乎零开销。