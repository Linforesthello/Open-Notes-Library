# Claude for VS Code 聊天记录迁移指南

## 背景

Claude for VS Code 的聊天记录是按 **工作区根目录** 隔离的。切换 workspace（如从单文件夹切换到 `robot.code-workspace`）后，旧聊天记录不会自动出现在新工作区。

## 存储结构

聊天记录分两部分存储：

| 内容 | 位置 | 说明 |
|------|------|------|
| 会话主文件 | `~/.claude/projects/{路径哈希}/{会话UUID}.jsonl` | **按项目隔离**，迁移时需复制 |
| 消息快照 | `~/.claude/file-history/{会话UUID}/` | **全局共享**，不需要迁移 |

## 路径哈希算法

```
原始路径: /home/lin/ProjectRequirement/MCU/Lin_STM32/STM32_F103C8T6/STM32_Now
规则: 去掉根 /，将路径分隔符 / 替换为连字符 -，整体加前缀 -
```

> 注意：下划线 `_` 的处理存在版本差异——早期生成的哈希（如 `test1`）会将下划线替换为连字符 `-`，近期生成的哈希则保留原样。以实际磁盘上的目录名为准。

### 本项目中已知的项目哈希

| 工作区根目录 | 项目哈希 |
|-------------|---------|
| `STM32_F103C8T6/test1`（单文件夹） | `-home-lin-...-Lin-STM32-STM32-F103C8T6-test1` |
| `STM32_F103C8T6/STM32_Now`（单文件夹） | `-home-lin-...-Lin-STM32-STM32_F103C8T6-STM32-Now` |
| `robot.code-workspace` | 同上 `-home-lin-...-STM32_F103C8T6-STM32-Now`（当前首文件夹 `3_MCLM_t2`） |

## 迁移步骤

### 必要条件

- 源项目的 `.jsonl` 文件存在于 `~/.claude/projects/{源哈希}/` 下
- 目标项目哈希目录存在于 `~/.claude/projects/{目标哈希}/` 下（只要在目标工作区触发过一次对话即会自动创建）
- `file-history/` 全局共享，无需额外操作

### 操作

```bash
# 1. 找到源会话文件
SRC=~/.claude/projects/{源项目哈希}/{会话UUID}.jsonl

# 2. 复制到目标项目目录
DST=~/.claude/projects/{目标项目哈希}/
cp "$SRC" "$DST"

# 3. 验证
ls -la "$DST"
```

### 示例

```bash
# 迁移 test1 → STM32_Now（单文件夹或 robot.code-workspace）
cp ~/.claude/projects/-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32-F103C8T6-test1/session-uuid-here.jsonl \
   ~/.claude/projects/-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32_F103C8T6-STM32-Now/
```

### 迁移后

重启 VS Code（或 `Ctrl+Shift+P` → `Developer: Reload Window`）以刷新聊天历史列表。

## 批量迁移脚本参考

```bash
#!/bin/bash
# 迁移所有旧项目会话到当前工作区
# 用法: ./migrate_conversations.sh <源项目哈希> <目标项目哈希>

SRC_HASH="$1"
DST_HASH="$2"

SRC_DIR="$HOME/.claude/projects/$SRC_HASH"
DST_DIR="$HOME/.claude/projects/$DST_HASH"

if [ ! -d "$SRC_DIR" ]; then
    echo "错误: 源项目目录不存在 $SRC_DIR"
    exit 1
fi

if [ ! -d "$DST_DIR" ]; then
    echo "错误: 目标项目目录不存在 $DST_DIR"
    echo "请先在目标工作区触发一次对话以创建项目目录"
    exit 1
fi

count=0
for f in "$SRC_DIR"/*.jsonl; do
    uuid=$(basename "$f" .jsonl)
    if [ ! -f "$DST_DIR/$uuid.jsonl" ]; then
        cp "$f" "$DST_DIR/"
        echo "已迁移: $uuid"
        ((count++))
    else
        echo "已存在(跳过): $uuid"
    fi
done

echo ""
echo "完成。共迁移 $count 条会话。"
echo "请重启 VS Code 以刷新聊天历史列表。"
```

---

## 迁移记录

### 2026-05-27：迁移两个旧会话到 `3_MCLM_t2` 子项目

**背景**：`robot.code-workspace` 是多根工作区，当前会话位于子项目 `3_MCLM_t2`（哈希后缀 `-3-MotorControl-LowMachine-lin-cmake-3-MCLM-t2`）下。旧会话存储在根项目哈希目录下，跨子项目不可见。

**已迁移的会话**：

| # | 会话UUID | 标题 | 大小 | 说明 |
|---|----------|------|------|------|
| 1 | `ac66af5c-7a69-47a7-b43b-1661e1463d4f` | 工作区的创建 | 808KB | |
| 2 | `b790632d-7aa9-4171-996a-b7dac609d188` | 迁移会话历史 | 251KB | 标题续：claude插件会话锁定文件夹，迁移会话历史成功，生成了自动命令 |

**路径哈希对照**：

| 工作区 | 项目哈希 |
|--------|---------|
| 根工作区 `STM32_Now`（源） | `-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32_F103C8T6-STM32-Now` |
| 子项目 `3_MCLM_t2`（目标） | `-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32_F103C8T6-STM32-Now-3-MotorControl-LowMachine-lin-cmake-3-MCLM-t2` |

**操作步骤**：

```bash
# 1. 从根项目哈希复制到子项目哈希
SRC=~/.claude/projects/-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32_F103C8T6-STM32-Now
DST=~/.claude/projects/-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32_F103C8T6-STM32-Now-3-MotorControl-LowMachine-lin-cmake-3-MCLM-t2

cp "$SRC/ac66af5c-7a69-47a7-b43b-1661e1463d4f.jsonl" "$DST/"
cp "$SRC/b790632d-7aa9-4171-996a-b7dac609d188.jsonl" "$DST/"

# 2. 验证
ls -la "$DST"/{ac66af5c,b790632d}*

# 3. 刷新 VSCode 后即可在聊天历史中看到
```

**注意事项**：
- 多根工作区（`robot.code-workspace`）下，每个子项目有独立的项目哈希目录，JSONL 文件需复制到当前子项目哈希下才可见。
- 之前已复制到根项目哈希（`-STM32-Now` 带连字符版本）的文件对子项目会话不可见。
- 全局协调类会话应从 `0_Workspace` 目录发起，归属其独立哈希。

### 2026-05-27（续）：迁移全局会话到 `0_Workspace`

**背景**：新增 `0_Workspace` 文件夹用于承载全局协调话题，将之前误放在 `3_MCLM_t2` 下的两个全局会话迁移至此。

**操作步骤**：

```bash
# 从 3_MCLM_t2 复制到 0_Workspace
SRC=~/.claude/projects/-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32_F103C8T6-STM32-Now-3-MotorControl-LowMachine-lin-cmake-3-MCLM-t2
DST=~/.claude/projects/-home-lin-ProjectRequirement-MCU-Lin-STM32-STM32_F103C8T6-STM32-Now-0-Workspace

cp "$SRC/ac66af5c-7a69-47a7-b43b-1661e1463d4f.jsonl" "$DST/"
cp "$SRC/b790632d-7aa9-4171-996a-b7dac609d188.jsonl" "$DST/"
```

**结果**：全局会话出现在 `0_Workspace` 的聊天历史中，不再与 MCLM 会话混合。

---

### 2026-07-25：迁移 ProjectLearner（单文件夹）→ learnmap.code-workspace（多根工作区）

**背景**：Windows 本地开发，VSCode 原以单文件夹形式打开 `ProjectLearner`，后创建 `learnmap.code-workspace` 将 `ProjectLearner`（LearnMap）与 `Open_Notes_Library`（Notes）组合为多根工作区。

**路径哈希对照**：

| 工作区 | 项目哈希 |
|--------|---------|
| 单文件夹 `ProjectLearner`（源） | `c--Users-86173-Desktop-ProjectLearner` |
| 工作区 `learnmap.code-workspace`（目标） | `c--Users-86173-Desktop-ProjectLearner-learnmap-code-workspace` |

**操作步骤（PowerShell）**：

```powershell
# 1. 创建目标目录
mkdir "$env:USERPROFILE\.claude\projects\c--Users-86173-Desktop-ProjectLearner-learnmap-code-workspace"

# 2. 复制所有会话
Copy-Item "$env:USERPROFILE\.claude\projects\c--Users-86173-Desktop-ProjectLearner\*.jsonl" `
          "$env:USERPROFILE\.claude\projects\c--Users-86173-Desktop-ProjectLearner-learnmap-code-workspace\"

# 3. 验证
Get-ChildItem "$env:USERPROFILE\.claude\projects\c--Users-86173-Desktop-ProjectLearner-learnmap-code-workspace\"
```

**已迁移的会话（共 4 条）**：

| 会话 | 大小 | 说明 |
|------|------|------|
| `31c9d321...` | 12KB | 新工作区首次对话（你好） |
| `431fa52e...` | 1.7MB | 主要设计对话（Schema + Pipeline + 可视化） |
| `5dfa3941...` | 142KB | 早期对话 |
| `aec53410...` | 2.1MB | HTTP 服务器调试对话 |

**注意事项**：
- Windows 路径哈希规则：`C:\path\to\folder` → `c--path-to-folder`（小写驱动器字母 + `--` + 路径段以 `-` 连接）
- 工作区文件内嵌于项目根目录时，哈希在原有单文件夹哈希后追加 `-learnmap-code-workspace`
- 迁移前需在目标工作区触发至少一次 Claude 对话以自动创建哈希目录，或手动 `mkdir`
- 迁移后重启 VSCode 以使聊天历史列表刷新
