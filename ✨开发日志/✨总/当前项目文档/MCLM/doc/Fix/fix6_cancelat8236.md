# fix6: 废弃 AT8236 电机驱动

## 背景

项目中同时维护了 TB6612、AT8236、IBT4 三种电机驱动，当前实际使用的是 TB6612。废弃 AT8236 以减少维护成本。

## 变更内容

### 删除文件
- `App/drivers/motor_DC_at8236.c` — AT8236 驱动实现
- `App/drivers/motor_DC_at8236.h` — AT8236 驱动头文件
- `App/tasks/at8236_DC_task.c` — AT8236 FreeRTOS 任务

### 清理引用

| 文件 | 变更 |
|------|------|
| `App/config/app_config.h` | 移除 `MOTOR_DRIVER_AT8236 2` 宏定义；移除注释掉的宏；删除整个 `#elif` 配置块 |
| `App/config/app_includes.h` | 移除 `#include "motor_DC_at8236.h"` |
| `App/config/app_task.h` | 移除 `AT8236_DC_Task` 声明 |
| `CMakeLists.txt` | 移除两个 AT8236 源文件条目 |
| `Core/Src/freertos.c` | 移除两处 `AT8236_DC_Task` 条件分支 |

## 验证

`grep -r -i "at8236\|AT8236" --include="*.c" --include="*.h" --include="*.txt" --include="*.cmake" .` 无输出，已无残留引用。
