
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


