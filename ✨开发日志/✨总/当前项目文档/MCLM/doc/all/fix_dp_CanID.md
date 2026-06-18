# CAN ID 组选择：告别手动注释切换

## 背景
代码需要兼容两套 CAN ID（0x125/0x126 和 0x123/0x124 系列），之前靠手动注释/取消注释宏定义来切换，易错且繁琐。

## 改动

### `App/config/app_config.h`
- 引入 `#define CAN_ID_GROUP  2` 作为唯一选择点
- 将原本的手动注释块改为 `#if CAN_ID_GROUP == 1 / #elif CAN_ID_GROUP == 2` 条件编译
- 非法值触发 `#error`

### `CMakeLists.txt`
- 回退了试加的 `option()` / `target_compile_definitions`，保持原有状态

## 讨论与取舍

### 被否定的方案

| 方案 | 原因 |
|---|---|
| **CMake `option()` + 编译命令行传参** | 用户使用 STM32CubeIDE 自动编译，不走手动 cmake，无效 |
| **CubeIDE Preprocessor 宏定义** | 需额外配置 IDE，徒增步骤，不如改一个数字直接 |
| **运行时自动识别 CAN ID** | 需要把 `#define` 改成全局变量，改动量大，对 F103 来说过于复杂 |

### 遗留疑问

- 在 CMakeLists.txt 中 `target_compile_definitions(... CAN_ID_GROUP=${CAN_ID_GROUP})` 与 app_config.h 中 `#define CAN_ID_GROUP 2` 同时存在时，GCC 对**相同值**重定义默认不会产生任何 warning/error（只有不同值才会警告）。因此实际不会冲突，但最终选择删掉 CMake 侧以避免死代码。

## 使用方法
改 `app_config.h` 中一个数字即可：
```c
#define CAN_ID_GROUP  1   // → 0x125/0x126 系列
#define CAN_ID_GROUP  2   // → 0x123/0x124 系列
```
不影响现有 ST for vscode 自动编译流程。
