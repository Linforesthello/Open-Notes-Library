[main] 正在生成文件夹: /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/build/Debug 
[build] 正在启动生成
[driver] 注意: 你正在使用预设 Debug 进行生成，但正在从 VS Code 设置中应用一些替代。
[proc] 正在执行命令: cube-cmake --build /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/build/Debug --
[build] [1/2] Building C object CMakeFiles/3_MCLM_t2.dir/App/tasks/logger_task.c.obj
[build] FAILED: [code=1] CMakeFiles/3_MCLM_t2.dir/App/tasks/logger_task.c.obj 
[build] /home/lin/.local/share/stm32cube/bundles/gnu-tools-for-stm32/14.3.1+st.2/bin/arm-none-eabi-gcc -DDEBUG -DSTM32F103xB -DSTM32_THREAD_SAFE_STRATEGY=4 -DUSE_HAL_DRIVER -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/Core/Inc -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/Drivers/STM32F1xx_HAL_Driver/Inc -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/Drivers/CMSIS/Device/ST/STM32F1xx/Include -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/Drivers/CMSIS/Include -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/Middlewares/Third_Party/FreeRTOS/Source/include -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/drivers -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/modules -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/services -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/config -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Core/Inc -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Drivers/STM32F1xx_HAL_Driver/Inc -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Middlewares/Third_Party/FreeRTOS/Source/include -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM3 -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I/home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/cmake/stm32cubemx/../../Drivers/CMSIS/Include -mcpu=cortex-m3  -Wall -fdata-sections -ffunction-sections -fstack-usage -O0 -g3 -std=gnu11 -MD -MT CMakeFiles/3_MCLM_t2.dir/App/tasks/logger_task.c.obj -MF CMakeFiles/3_MCLM_t2.dir/App/tasks/logger_task.c.obj.d -o CMakeFiles/3_MCLM_t2.dir/App/tasks/logger_task.c.obj -c /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c
[build] /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c: In function 'Logger_Task':
[build] /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c:57:42: error: implicit declaration of function 'fabsf' [-Wimplicit-function-declaration]
[build]    57 |     int32_t target_speed_dec = (int32_t)(fabsf(target_logic_speed - (float)target_speed_int) * 10.0f);
[build]       |                                          ^~~~~
[build] /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c:3:1: note: include '<math.h>' or provide a declaration of 'fabsf'
[build]     2 | #include "app_includes.h"
[build]   +++ |+#include <math.h>
[build]     3 | #include "stdio.h"
[build] /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c:57:42: warning: incompatible implicit declaration of built-in function 'fabsf' [-Wbuiltin-declaration-mismatch]
[build]    57 |     int32_t target_speed_dec = (int32_t)(fabsf(target_logic_speed - (float)target_speed_int) * 10.0f);
[build]       |                                          ^~~~~
[build] /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c:57:42: note: include '<math.h>' or provide a declaration of 'fabsf'
[build] /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c:60:33: warning: format '%d' expects argument of type 'int', but argument 7 has type 'long int' [-Wformat=]
[build]    60 |                    "%lu,%lu,%d,%d.%d,%d\r\n",
[build]       |                                ~^
[build]       |                                 |
[build]       |                                 int
[build]       |                                %ld
[build] ......
[build]    64 |                    (long)target_speed_int,
[build]       |                    ~~~~~~~~~~~~~~~~~~~~~~
[build]       |                    |
[build]       |                    long int
[build] /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/App/tasks/logger_task.c:60:36: warning: format '%d' expects argument of type 'int', but argument 8 has type 'long int' [-Wformat=]
[build]    60 |                    "%lu,%lu,%d,%d.%d,%d\r\n",
[build]       |                                   ~^
[build]       |                                    |
[build]       |                                    int
[build]       |                                   %ld
[build] ......
[build]    65 |                    (long)target_speed_dec,
[build]       |                    ~~~~~~~~~~~~~~~~~~~~~~
[build]       |                    |
[build]       |                    long int
[build] ninja: build stopped: subcommand failed.
[proc] 命令“cube-cmake --build /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now/3_MotorControl_LowMachine/lin_cmake/3_MCLM_t2/build/Debug --”已退出，代码为 1
[driver] 生成完毕: 00:00:00.083
[build] 生成已完成，退出代码为 1
