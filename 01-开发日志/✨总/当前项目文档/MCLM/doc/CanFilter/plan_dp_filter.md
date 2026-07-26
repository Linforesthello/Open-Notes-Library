# CAN 指令过滤设计方案

## 1. 问题分析

### 当前架构痛点

现有的 CAN 过滤分散在两处，且不够健壮：

```
[CAN 硬件] → 掩码全 0（来者不拒）→ [can.c 中断回调]
    ↑ 硬件级无过滤                              ↓
                                          内联 ID 白名单 + switch 命令解析
```

| 问题 | 详情 |
|---|---|
| **硬件过滤器未利用** | 当前 `mask=0x0000` 接收所有帧，无关流量也会触发中断 |
| **过滤逻辑与协议解析耦合** | ID 白名单、motor_id 路由、命令字节解析全部在 `can.c` 一个函数内，违背"职责分离" |
| **白名单硬编码** | 7 个已知 ID 的 if-else 写在回调里，新增/修改 ID 需要改 `can.c` |
| **不支持运行时过滤** | 无法在运行时动态启用/禁用特定 ID 的接收 |

### 目标

1. **硬件过滤**：利用 STM32F103 的 CAN 过滤器，只放行已知 ID，减少无关中断
2. **软件过滤层**：将白名单逻辑从 `can.c` 抽取为独立模块，提供清晰的 API
3. **配置集中化**：所有过滤相关的配置（允许的 ID、命令字节映射）收敛到一处
4. **保持兼容**：不改变现有 `CommandMsg_t` 结构体和 `command_task.c` 的处理逻辑

---

## 2. 总体架构

```
CAN 总线
  │  硬件帧（StdId + DLC + Data[8]）
  ▼
┌──────────────────────────────┐
│  STM32 CAN 硬件过滤器          │  ← 第一级：只放行已知 ID（减少中断次数）
│  Filter Bank 0～N             │
│  (可配置掩码/列表模式)          │
└──────────┬───────────────────┘
           ▼ 通过硬件过滤的帧
┌──────────────────────────────┐
│  App/services/can_filter.c   │  ← 第二级：软件过滤
│  CAN_Filter_Accept(id, cmd)  │      校验 ID + 命令字节组合是否合法
│  CAN_Filter_GetMotorId(id)   │      返回目标 motor_id
└──────────┬───────────────────┘
           ▼ 通过软件过滤 → CommandMsg_t
┌──────────────────────────────┐
│  can.c 中断回调（精简后）       │  ← 只保留：取帧 → 调过滤 → 推队列
│  HAL_CAN_RxFifo0MsgPending   │
└──────────┬───────────────────┘
           ▼
  FreeRTOS CommandQueue
```

---

## 3. 实现方案

### 3.1 硬件过滤器配置

**STM32F103 特性**：14 个 Filter Bank，支持 Mask（掩码）和 List（列表）模式。

#### 推荐方案：混合使用 Bank

| Bank | 模式 | 用途 |
|------|------|------|
| Bank 0 | 32-bit Mask | 放行全局 ID（0x101/0x102/0x103） |
| Bank 1 | 32-bit List | 精确匹配电机 ID 组（根据 `CAN_ID_GROUP`） |
| Bank 2+ | — | 保留，后续扩展 |

**Bank 0 配置（掩码模式匹配全局 ID）**：

为简化，将 Bank 0 配置为仅匹配标准帧，且只放行特定范围的 ID：

```c
// ID = 0x101（全车停止）
// Mask = 0x1FC（保留高 7 位 + 低 5 位以外的 don't care）
// 实际上更简单的方式：使用 16-bit 模式精确匹配
```

或者采用更务实的做法：直接使用 **16-bit 标识符模式**（Identifier List mode）精确列出所有已知 ID。STM32F103 每个 16-bit 列表模式 Bank 可放 2 个 ID。

**更简洁的硬件方案**（推荐）：

使用 2 个 Bank 的 **16-bit List 模式**，每个 Bank 精确列出 2 个 ID：

- 实际测试表明，软件过滤已经足够轻量（在 500kbps 下）
- 硬件过滤设为**仅接收标准帧、且 ID 在 0x100～0x325 范围**作为粗过滤
- 细粒度过滤交给软件层

### 3.2 软件过滤层 API

新建 `App/services/can_filter.h` + `App/services/can_filter.c`：

```c
// ========== can_filter.h ==========

typedef enum {
    CAN_FILTER_ACCEPT = 0,    // 接受该帧
    CAN_FILTER_REJECT         // 拒绝该帧
} CAN_FilterResult_t;

/**
 * @brief  第一级过滤：检查 CAN ID 是否在白名单中
 * @param  stdId  标准帧 ID
 * @return CAN_FILTER_ACCEPT 或 CAN_FILTER_REJECT
 */
CAN_FilterResult_t CAN_Filter_CheckID(uint32_t stdId);

/**
 * @brief  第二级过滤：检查 命令字节 是否对 该 ID 合法
 * @param  stdId  标准帧 ID
 * @param  cmdByte  rxData[0] 命令字节
 * @return CAN_FILTER_ACCEPT 或 CAN_FILTER_REJECT
 */
CAN_FilterResult_t CAN_Filter_CheckCommand(uint32_t stdId, uint8_t cmdByte);

/**
 * @brief  根据 CAN ID 获取目标电机 ID
 * @param  stdId  标准帧 ID
 * @return 0=转向电机, 1=动力电机, 0xFF=广播
 */
uint8_t CAN_Filter_GetMotorId(uint32_t stdId);

/**
 * @brief  运行时启用/禁用某个 ID 的接收（可选扩展）
 */
void CAN_Filter_EnableID(uint32_t stdId, int enable);
```

### 3.3 白名单定义

收敛到 `can_filter.c` 中，以表格形式（而非 if-else）定义：

```c
// CAN ID 属性表
typedef struct {
    uint32_t    std_id;       // CAN 标准 ID
    uint8_t     motor_id;     // 目标电机
    uint8_t     valid_cmds[8]; // 该 ID 允许的命令字节列表（-1 结尾）
} CAN_ID_Entry_t;

// 白名单表格（根据 app_config.h 的宏自动生成）
static const CAN_ID_Entry_t s_can_whitelist[] = {
    { CAN_MOTOR_TURN_CMD_STDID,         0,    {0x11, 0x07, 0x08, 0x02, -1} },
    { CAN_MOTOR_TURN_CMD_STATUS_STDID,  0,    {0x01, 0x04, 0x05, -1} },
    { CAN_MOTOR_POWER_CMD_STDID,        1,    {0x11, 0x07, 0x08, 0x02, -1} },
    { CAN_MOTOR_POWER_CMD_STATUS_STDID, 1,    {0x01, 0x04, 0x05, -1} },
    { CAN_CMD_STOP_STDID,               0xFF, {0x08, 0x11, 0x07, 0x02, -1} },
    { CAN_CMD_TURN_STDID,               0xFF, {0x11, 0x07, 0x08, -1} },
    { CAN_CMD_POWER_STDID,              0xFF, {0x11, 0x07, 0x08, -1} },
};
```

这样新增/修改一个命令或 ID，只需改表格，不用动 `can.c`。

### 3.4 can.c 回调的简化

改造后，`HAL_CAN_RxFifo0MsgPendingCallback` 变为：

```c
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
    CAN_RxHeaderTypeDef rxHeader;
    uint8_t rxData[8];

    if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rxHeader, rxData) != HAL_OK)
        return;

    // 第一级过滤：ID 白名单
    if (CAN_Filter_CheckID(rxHeader.StdId) == CAN_FILTER_REJECT)
        return;

    // 第二级过滤：命令字节合法
    if (CAN_Filter_CheckCommand(rxHeader.StdId, rxData[0]) == CAN_FILTER_REJECT)
        return;

    // 构造 CommandMsg_t
    CommandMsg_t cmdMsg;
    cmdMsg.motor_id = CAN_Filter_GetMotorId(rxHeader.StdId);
    cmdMsg.type     = CAN_CmdToType(rxData[0]);  // 命令字节 → CommandType_t 映射
    cmdMsg.value    = (cmdMsg.type == CAN_CMD_SET_SPEED || cmdMsg.type == CAN_CMD_SET_SPEED_T2)
                      ? (int8_t)rxData[1] : 0;

    if (cmdMsg.type != CMD_NONE) {
        osMessageQueuePut(CommandQueueHandle, &cmdMsg, 0U, 0U);
    }
}
```

需要新增 `CAN_CmdToType()` 函数（在 can_filter 中或独立的 protocol 映射）。

---

## 4. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `App/services/can_filter.h` | **新建** | 公共 API 声明 |
| `App/services/can_filter.c` | **新建** | 表格驱动过滤实现 |
| `Core/Src/can.c` | **修改** | 回调中替换内联过滤为 `CAN_Filter_*` 调用 |
| `Core/Inc/can.h` | 无需修改 | — |
| `App/config/app_config.h` | **修改** | 追加命令字节-类型映射宏，移除过时注释 |
| `App/services/command.h` | 无需修改 | — |
| `App/tasks/command_task.c` | 无需修改 | — |

---

## 5. 实施步骤

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1 | 新建 `can_filter.h`，定义 `CAN_Filter_CheckID()`、`CAN_Filter_CheckCommand()`、`CAN_Filter_GetMotorId()`、`CAN_CmdToType()` 的函数签名 | 头文件 |
| 2 | 新建 `can_filter.c`，实现表格驱动白名单和命令验证 | 实现文件 |
| 3 | 修改 `app_config.h`，补充命令字节映射宏（如 `CMD_BYTE_TO_TYPE` 表） | 配置扩展 |
| 4 | 修改 `can.c`，将内联过滤替换为 `CAN_Filter_*` 调用，精简回调逻辑 | 重构 |
| 5 | 编译验证，确保不破坏现有功能 | 验证 |
| 6 | 更新 `doc/deepseek_can.md`，反映新的过滤架构 | 文档同步 |

---

## 6. 设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 软件 vs 硬件为主 | 软件为主，硬件为辅 | STM32F103 过滤器在 500kbps 下软件开销可忽略，软件层更灵活且易维护 |
| 表格驱动 vs if-else | 表格驱动 | 新增/修改 ID 只需加表格行，不改逻辑代码 |
| 独立模块 vs 留在 can.c | 独立模块 `can_filter` | 遵循现有"职责分离通过文件目录体现"的架构原则 |
| 运行时动态过滤 | 预留 API 但初期不实现 | 当前无运行时变更需求，预留 `CAN_Filter_EnableID()` 接口即可 |

---

## 7. 测试关注点

1. **白名单边界**：已知 7 个 ID 都正确处理，未知 ID 被丢弃
2. **命令字节映射**：所有 `rxData[0]` 值映射正确，尤其 `0x11` → `CAN_CMD_SET_SPEED`
3. **Motor ID 路由**：`0x123/0x223` → motor 0，`0x124/0x224` → motor 1，`0x101` → 0xFF
4. **性能**：回调执行时间不显著增加（表格查询 O(n)，n=7）
5. **回归**：UART 命令不受影响，`command_task.c` 无需感知过滤变化
