# CAN 指令过滤 — 变更总结

## 改了什么

| 文件 | 操作 | 说明 |
|------|------|------|
| `App/services/can_filter.h` | **新建** | 4 个公共 API 声明 |
| `App/services/can_filter.c` | **新建** | 表格驱动白名单 + 命令字节映射 + 值提取 |
| `Core/Src/can.c` | **修改** | 回调从 ~70 行内联逻辑 → ~20 行数据流调用 |
| `CMakeLists.txt` | **修改** | 添加 can_filter.c 到编译 |

零改动：`command.h`、`command_task.c`、`app_config.h`，保持完全兼容。

---

## 架构变化

```
改前 (can.c 回调):
  ┣━ if 白名单 (7 个 ID 硬编码)
  ┣━ if-else 路由 motor_id
  ┣━ switch 命令字节解析
  ┗━ 推队列

改后 (can.c 回调):
  ┣━ CAN_Filter_Accept()         查白名单表: ID + 命令字节
  ┣━ CAN_Filter_GetMotorId()     查表: ID → motor_id
  ┣━ CAN_Filter_CmdByteToType()  查映射: 命令字节 → CommandType_t
  ┣━ CAN_Filter_GetValue()       提取速度值 (0x11/0x07 时读 rxData[1])
  ┗━ 推队列
```

---

## 白名单表 (`App/services/can_filter.c`)

| CAN ID | Motor | 允许的命令字节 |
|--------|-------|-------|
| `CAN_MOTOR_TURN_CMD_STDID` | 0 | `0x11` 调速, `0x07` 调速, `0x08` 停止, `0x02` 倒转 |
| `CAN_MOTOR_POWER_CMD_STDID` | 1 | `0x11` 调速, `0x07` 调速, `0x08` 停止, `0x02` 倒转 |
| `CAN_MOTOR_TURN_CMD_STATUS_STDID` | 0 | `0x01` 查询, `0x04` 日志开始, `0x05` 日志停止 |
| `CAN_MOTOR_POWER_CMD_STATUS_STDID` | 1 | `0x01` 查询, `0x04` 日志开始, `0x05` 日志停止 |
| `CAN_CMD_STOP_STDID` (`0x101`) | 广播 | `0x08` 停止, `0x11` 调速 |
| `CAN_CMD_TURN_STDID` (`0x102`) | 0 | `0x07` 调速, `0x08` 停止, `0x02` 倒转, `0x11` 调速 |
| `CAN_CMD_POWER_STDID` (`0x103`) | 1 | `0x07` 调速, `0x08` 停止, `0x02` 倒转, `0x11` 调速 |

表项使用 `CAN_MOTOR_TURN_CMD_STDID` 等宏，由 `CAN_ID_GROUP` 编译时展开，一套表兼容两套 ID 组。

---

## 修复记录

### 实测发现的问题

**现象**：`0x101`（全车停止）指令失效。

**原因**：原代码中 switch 的 `0x11`/`0x07`/`0x08`/`0x02` case 均不检查 ID，通过外层白名单的任意 ID 上发这些字节都会被接受。新白名单表最初只给 `0x101` 配了 `{0x08}`，但上位机实际发的是 `0x11`（设速度=0）来停车：

```python
# 网关代码实测命令
ord('s'): 'AA 01 01 01 00 00 02 11 00',  # ID=0x101, data[0]=0x11
```

**修复**：`CAN_CMD_STOP_STDID` 行增加 `0x11`：

```c
{ CAN_CMD_STOP_STDID,  0xFF, {0x08, 0x11, 0xFF} },
```

---

## 行为变更（有意的收紧）

原代码中 `0x11`/`0x07`/`0x08`/`0x02` 在任何 ID 上都接受（switch 不做 ID 校验）。新过滤表限制了 ID 与命令字节的合法组合：

- **STATUS ID** → 仅接受查询 / 日志控制（`0x01`/`0x04`/`0x05`）
- **CMD ID** → 仅接受电机控制（`0x11`/`0x07`/`0x08`/`0x02`）
- **全车 ID** → 仅接受对应的控制命令
