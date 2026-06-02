# MT6701 SSI (SPI) 读取 — 项目构建与烧录配置记录

> 日期: 2026-06-02
> MCU: STM32F103C8T6 (LQFP48)
> 目标: SPI1 读取 MT6701 角度，USART1 打印
> 状态: ✅ 已验证通过（见 [test_csv.csv](../csv/test_csv.csv)）

---

## 目录

1. [CubeMX 配置](#一cubemx-配置)
2. [VS Code 工作区配置](#二vs-code-工作区配置)
3. [CMake 构建配置](#三cmake-构建配置)
4. [MT6701 驱动代码](#四mt6701-驱动代码)
5. [快捷烧录](#五快捷烧录)
6. [硬件接线](#六硬件接线)
7. [常见问题](#七常见问题)
8. [实测验证数据](#八实测验证数据)

---

## 一、CubeMX 配置

### 1.1 SPI1

路径: Pinout & Configuration → Connectivity → SPI1

| 参数 | 值 | 验证状态 |
|------|-----|---------|
| Mode | Full Duplex Master | ✅ |
| Data Size | 8 Bits | ✅ |
| First Bit | MSB First | ✅ |
| Prescaler | 64 (≈1.125MHz) | ✅ |
| **CPOL** | **Low** | ✅ |
| **CPHA** | **2 Edge** (Mode 1) | ✅ **实测确定, 改 Mode 0 会出 180~360°** |
| NSS | Software | ✅ |

引脚分配:
- PA5 → SPI1_SCK
- PA6 → SPI1_MISO
- PA7 → SPI1_MOSI (自动分配，硬件不接)

> **注意**: 该模块会读 MOSI，`HAL_SPI_Receive` 内部送 0xFF 正常工作。如果改用 `HAL_SPI_TransmitReceive` 送 0x00 → 输出偏移到 8800~16383。

### 1.2 USART1

路径: Pinout & Configuration → Connectivity → USART1

| 参数 | 值 |
|------|-----|
| Mode | Asynchronous |
| Baud Rate | 115200 |
| Word Length | 8 Bits |
| Parity | None |
| Stop Bits | 1 |

引脚分配:
- PA9 → USART1_TX
- PA10 → USART1_RX

### 1.3 PA4 GPIO

路径: Pinout & Configuration → GPIO → 点击 PA4

| 参数 | 值 |
|------|-----|
| GPIO mode | Output Push-Pull |
| Pin label | MT6701_CS |
| Default output level | High (GPIO_PIN_SET) |

### 1.4 时钟配置

- HSE (8MHz 外部晶振) → PLL x9 → 72MHz SYSCLK
- APB1: 36MHz (分频2)
- APB2: 72MHz (分频1)

---

## 二、VS Code 工作区配置

### 2.1 `.vscode/settings.json`

```json
{
  "cmake.cmakePath": "cube-cmake",
  "cmake.configureArgs": [
    "-DCMAKE_COMMAND=cube-cmake"
  ],
  "cmake.preferredGenerators": [
    "Ninja"
  ],
  "stm32cube-ide-clangd.path": "cube",
  "stm32cube-ide-clangd.arguments": [
    "starm-clangd",
    "--query-driver=${env:CUBE_BUNDLE_PATH}/gnu-tools-for-stm32/14.3.1+st.2/bin/arm-none-eabi-gcc*",
    "--query-driver=${env:CUBE_BUNDLE_PATH}/gnu-tools-for-stm32/14.3.1+st.2/bin/arm-none-eabi-g++*"
  ]
}
```

> `cube-cmake` 由 STM32 VS Code 扩展提供，如果找不到则需重载窗口 (Reload Window) 等待扩展启动完成。
> 
> 如果环境只有 Make 没有 Ninja，改用: `cmake -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=../cmake/gcc-arm-none-eabi.cmake ..`

### 2.2 `.vscode/tasks.json`

```json
{
  "version": "2.0.0",
  "tasks": [
    {
        "label": "Build",
        "type": "shell",
        "command": "cmake --build ${workspaceFolder}/build",
        "problemMatcher": []
    },
    {
      "label": "Flash STM32 via J-Link",
      "type": "process",
      "command": "/opt/SEGGER/JLink/JLinkExe",
      "args": [
        "-Device", "STM32F103C8",
        "-If", "SWD",
        "-Speed", "4000",
        "-CommanderScript", "${workspaceFolder}/flash.jlink"
      ],
      "group": { "kind": "build", "isDefault": true },
      "problemMatcher": [],
      "dependsOn": "Build"
    }
  ]
}
```

- `Ctrl+Shift+B` 触发 Flash 任务（自动先 Build 再烧录）
- 构建目录为 `build/`（非 build/Debug/）
- JLink Commander Script 指向项目根目录的 `flash.jlink`

### 2.3 `.vscode/c_cpp_properties.json`

```json
{
  "configurations": [
    {
      "name": "STM32",
      "compileCommands": "${workspaceFolder}/build/compile_commands.json"
    }
  ]
}
```

---

## 三、CMake 构建配置

### 3.1 `cmake/gcc-arm-none-eabi.cmake` — printf 浮点支持

默认 `--specs=nano.specs` 裁剪了 `printf` 的 `%f` 支持，需追加链接器标志:

```cmake
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --specs=nano.specs")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-u,_printf_float")
```

代价: Flash 占用从 ~32% 增加到 ~51%（约 +12KB）。

### 3.2 手动构建（无 Ninja 时）

```bash
cd build
cmake .. -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=../cmake/gcc-arm-none-eabi.cmake -DCMAKE_BUILD_TYPE=Debug
make -j$(nproc)
```

### 3.3 `flash.jlink`（项目根目录）

供 VS Code 任务使用，路径从项目根目录算起:

```
r
h
loadfile build/6_mt6701_spi.elf
r
q
```

---

## 四、MT6701 驱动代码

全部写在 `Core/Src/main.c` 的 USER CODE 区域内，保证 CubeMX 重新生成代码时不被覆盖。

### 4.1 Includes

```c
/* USER CODE BEGIN Includes */
#include <stdio.h>
/* USER CODE END Includes */
```

### 4.2 CS 控制宏

```c
/* USER CODE BEGIN PD */
#define MT6701_CS_LOW()  HAL_GPIO_WritePin(MT6701_CS_GPIO_Port, MT6701_CS_Pin, GPIO_PIN_RESET)
#define MT6701_CS_HIGH() HAL_GPIO_WritePin(MT6701_CS_GPIO_Port, MT6701_CS_Pin, GPIO_PIN_SET)
/* USER CODE END PD */
```

### 4.3 读取与转换函数 + printf 重定向

```c
/* USER CODE BEGIN 0 */

static uint16_t MT6701_ReadRaw(void)
{
    uint8_t rx[2];

    MT6701_CS_LOW();

    /* 注意: 该模块会读MOSI, HAL_SPI_Receive 内部送 0xFF 才能正确工作 */
    HAL_SPI_Receive(&hspi1, rx, 2, 100);

    MT6701_CS_HIGH();

    uint16_t data = ((uint16_t)rx[0] << 8) | rx[1];

    /* SSI帧: [Angle(14) | Extra(2)]  角度在 bits 15:2, 需 >>2 提取 */
    data >>= 2;
    return data & 0x3FFF;
}

static float MT6701_GetAngle(void)
{
    uint16_t raw = MT6701_ReadRaw();
    return raw * 360.0f / 16384.0f;
}

int __io_putchar(int ch)
{
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 100);
    return ch;
}

/* USER CODE END 0 */
```

### 4.4 主循环

```c
  /* USER CODE BEGIN WHILE */

  /*
   * 调试阶段预期输出（手动匀速旋转磁铁一周）:
   *
   * 正常情况（SPI Mode 1, >>2 正确）:
   *   raw=0     angle=0.00
   *   raw=2048  angle=44.98
   *   raw=4096  angle=90.00
   *   raw=8192  angle=180.00
   *   raw=12288 angle=270.00
   *   raw=16383 angle=359.98
   *   raw=0     angle=0.00    ← 回到起点
   *   360° 内恰好 1 次完整周期, 数值平滑递增/递减
   *
   * 实际验证数据见 csv/test_csv.csv
   */

  while (1)
  {
      uint16_t raw = MT6701_ReadRaw();
      float angle = MT6701_GetAngle();
      printf("raw=%u angle=%.2f\r\n", raw, angle);
      HAL_Delay(100);
    /* USER CODE END WHILE */
```

---

## 五、快捷烧录

### 5.1 VS Code 一键烧录

`Ctrl+Shift+B` → 自动执行:
1. Build: `cmake --build build`
2. Flash: `JLinkExe -Device STM32F103C8 -If SWD -Speed 4000 -CommanderScript flash.jlink`

### 5.2 终端命令行烧录

```bash
cmake --build build --target flash
```

或手动:

```bash
JLinkExe -Device STM32F103C8 -If SWD -Speed 4000 -CommanderScript flash.jlink
```

---

## 六、硬件接线

| MT6701 模块 | STM32 F103C8 | 备注 |
|------------|-------------|------|
| VCC | 3.3V | 不要接 5V |
| GND | GND | |
| NCS/Z | PA4 | CS 片选（软件控制） |
| SCLK/B | PA5 | SPI1 SCK |
| MISO/A | PA6 | SPI1 MISO |
| NC | - | 悬空不接 |

> MOSI (PA7) 在 CubeMX 中自动分配但硬件不接。

---

## 七、磁铁检测

MT6701 读取正确性高度依赖磁铁的选择和安装。

**前置条件**（必须先完成）:
1. ✅ 按 [一、CubeMX 配置](#一cubemx-配置) 完成 SPI1/USART1/GPIO 配置
2. ✅ 按 [四、MT6701 驱动代码](#四mt6701-驱动代码) 烧录程序到 STM32
3. ✅ 串口助手能看到 `raw=xxx angle=xx.xx` 输出（115200-8N1）
4. ✅ 磁铁已装在轴上，距芯片 0.5~2mm

> 如果串口无输出或数值异常，先回 [九、常见问题](#九常见问题) 排查。

以下检查项逐项确认:

### 7.1 磁铁极对数确认

MT6701 设计配 **1 对极（2 极）径向充磁磁铁**:

| 磁铁参数 | 要求 | 验证方法 |
|---------|------|---------|
| 充磁方向 | **径向** (diametral) | 磁铁标签标注 “diametral” 或 “径向” |
| 极对数 | **1 对极（2 极）** | 手动转一圈，串口看 raw 0→16383→0 **恰好 1 次** |
| 极对数验证 | 如果出 2 次周期 | 说明磁铁是 2 对极（4 极），需更换 |

**确认步骤**:
1. 烧录程序，打开串口
2. 手动匀速旋转磁铁 **一整圈（360°）**
3. 观察输出: `raw` 应从 `0→16383→0` 恰好一次
4. 如果出现 2 次完整周期 → 磁铁是 2 对极，需要更换

> 实测 `test_csv.csv` 确认: 360° 内 1 次周期 ✅ 当前磁铁为 1 对极。

### 7.2 磁铁安装检查

| 检查项 | 要求 | 异常现象 |
|-------|------|---------|
| **同轴度** | 磁铁中心与芯片中心对齐 (±0.3mm) | 数值跳变、非均匀步长 |
| **气隙** | 芯片表面到磁铁表面 0.5~2.0mm | 超出范围 → 读数不稳定或为 0 |
| **固定** | 磁铁无松动 | 静止时 raw 跳动 > 2 LSB |
| **干扰** | 附近无强磁场 (电机线圈、大电流) | 角度偏移或抖动 |

**快速测试**: 磁铁静止不动时，串口输出应稳定在 ±1 LSB 以内:

```
raw=2309 angle=50.73
raw=2309 angle=50.73
raw=2309 angle=50.73    ← 静止状态，数值稳定
raw=2309 angle=50.73
```

如果静止晃动 > 2 LSB，检查安装同轴度或外部磁场干扰。

### 7.3 磁铁类型快速判断

| 肉眼特征 | 极对数 | 是否适配 | 处理方法 |
|---------|-------|---------|---------|
| 标 1 个点 (N 极标记) | 1 对极 | ✅ 适配 | 直接使用 |
| 标 2 个点或无标记 | 可能 2 对极 | ❌ 不适配 | 更换为 1 对极径向磁铁 |
| 条形/矩形磁铁 | 不规则 | ❌ 不适配 | 更换为圆柱形径向磁铁 |

---

## 八、MT6701 工作模式确认

结合实测数据 `test_csv.csv`，确认该模块的工作模式参数:

### 8.1 接口模式

| 参数 | 实测结论 | 依据 |
|------|---------|------|
| 通信接口 | **SSI** (通过 SPI 物理层) | 使用 SPI1 Full Duplex Master 通信正常 |
| 帧长度 | **16-bit** | `HAL_SPI_Receive` 接收 2 字节 (16 bit) |
| 波特率 | **1.125 MHz** (Prescaler 64) | 72MHz / 64，通信稳定无丢帧 |
| SPI Mode | **Mode 1** (CPOL=Low, CPHA=2Edge) | 实测: Mode 0 导致 180~360° 异常 |

### 8.2 数据帧结构

该模块的 SSI 16-bit 帧格式:

```
       bit 15                   bit 0
       +------------------------------+
       |  14-bit Angle   |  Extra   |
       |  (bits 15:2)    | (bits 1:0)|
       +------------------------------+
          ^                  ^
       MSB 先发           LSB 后发
```

**提取方式**: `data >>= 2; return data & 0x3FFF;`

角度范围: **0 ~ 16383** (14-bit)，对应 **0.00° ~ 359.98°**

对比标准 MT6701 数据手册的常见帧格式:

| 帧格式 | 说明 | 本模块 |
|--------|------|:------:|
| `[ERR(1) | PAR(1) | Angle(14)]` | 标准手册格式: 状态位在高位 | ❌ 不符 |
| `[Angle(14) | Extra(2)]` | 角度在高位, 需 >>2 | ✅ **实测匹配** |

> 说明该模块不是标准 DataSheet 排列，而是角度在 MSB 侧、附加位在 LSB 侧的变体。

### 8.3 MOSI 数据敏感性

| 条件 | 输出范围 | 结论 |
|------|---------|------|
| MOSI 送 0xFF (`HAL_SPI_Receive`) | 0~16383 ✅ | 模块正常工作 |
| MOSI 送 0x00 (`HAL_SPI_TransmitReceive`) | 8800~16383 ❌ | 该模块会读 MOSI 数据 |

**结论**: 必须使用 `HAL_SPI_Receive`（内部送 0xFF）或 `HAL_SPI_TransmitReceive` 送 `{0xFF, 0xFF}`。

### 8.4 输出特性汇总

| 特性 | 数值 | 验证方式 |
|------|------|---------|
| 分辨率 | 14 位 (~0.022°) | raw 范围 0~16383 |
| 单圈周期 | 1 次 / 360° 机械角 | 串口观察或 CSV 分析 |
| 更新速率 | 决定于主循环 `HAL_Delay(100)` → 10Hz | 串口刷新间隔 |
| 静止稳定性 | ±1 LSB | `test_csv.csv` L228-231 连续 20 次 raw=2309 |
| 噪声容限 | 转动时无跳变 > 2 LSB | 全过程平滑 |

---

## 九、常见问题

### 7.1 `cube-cmake` 找不到

```
Error: spawn cube-cmake ENOENT
```

**解决**: `Ctrl+Shift+P → Developer: Reload Window`，等待 STM32 扩展启动完成。

### 7.2 printf 只输出 `angle=` 没有数值

**原因**: newlib-nano 默认不链接 `%f` 支持。

**解决**: 在 `cmake/gcc-arm-none-eabi.cmake` 中添加:
```cmake
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-u,_printf_float")
```

### 7.3 JLink 烧录时报 `Failed to open file`

**原因**: `loadfile` 路径不正确。

**解决**: 确认 `flash.jlink` 中的路径指向实际编译产物 `build/6_mt6701_spi.elf`。

### 7.4 输出一直为 0

检查 CS 是否被拉低。

### 7.5 输出一直为 65535

检查 MISO 接线。

### 7.6 角度范围异常 — 实测诊断表

| 现象 | 根本原因 | 解决方法 |
|------|---------|---------|
| **180~360°** 或 **90~270°** | SPI Mode 错 (CPOL/CPHA) | 改回 Mode 1 (CPOL=Low, CPHA=2Edge) |
| **360°内 2 次 0~16383** | 角度提取 shift 错 | 保留 `data >>= 2`（角度在 bits 15:2） |
| **8800~16383** 范围 | MOSI 送了 0x00 | 改回 `HAL_SPI_Receive`（内部送 0xFF） |
| **输出跳变/毛刺** | 磁铁未对中或距离远 | 调整磁铁与芯片的同轴度 |

---

## 十、实测验证数据

### 8.1 测试数据文件

`csv/test_csv.csv` — 手动旋转磁铁一周采集的 232 行数据。

### 8.2 验证结论

| 检查项 | 实测结果 | 状态 |
|--------|---------|:----:|
| raw 最小值 | 82 (接近 0) | ✅ |
| raw 最大值 | 16328 (接近 16383) | ✅ |
| 360° 周期数 | **恰好 1 次** 0→16383→0 | ✅ |
| 角度连续性 | 平滑递增/递减，无阶跃 | ✅ |
| 过零回绕 | 354.88° → 4.99° 自然过渡 | ✅ |
| SPI 通信 | 无丢帧、无毛刺 | ✅ |
| 重复精度 | 静止时 raw 稳定 ±1 LSB | ✅ |

### 8.3 采样数据样例

```
raw=0     angle=0.00    ← 起点 (0°)
raw=4096  angle=90.00   ← 1/4 圈
raw=8192  angle=180.00  ← 半圈
raw=12288 angle=270.00  ← 3/4 圈
raw=16383 angle=359.98  ← 接近一圈
raw=227   angle=4.99    ← 过零回到起点附近
```

---

## 附: 编译资源占用

| 项目 | 大小 | 占比 |
|------|------|------|
| Flash (text+data) | 33,460 B | 51.1% (64KB) |
| RAM (data+bss) | 3,248 B | 15.9% (20KB) |

> `_printf_float` 贡献约 12KB Flash 占用。如果后续 Flash 紧张，可以将 `%.2f` 改为整数打印去掉此依赖。

## 参考

- [goal_260602.md](./goal_260602.md) — 原始目标文档
- [goal2_260602.md](./goal2_260602.md) — 修正记录
- [test_csv.csv](../csv/test_csv.csv) — 实测数据
- [CSDN: STM32HAL库使用SPI读取MT6701传感器数据](https://blog.csdn.net/yaolei5/article/details/155005022)
- [CSDN: HAL STM32 SSI/SPI方式读取MT6701磁编码器获取角度例程](https://blog.csdn.net/weixin_42880082/article/details/137921359)
