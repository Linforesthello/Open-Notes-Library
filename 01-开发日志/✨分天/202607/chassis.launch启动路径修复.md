# chassis.launch.py 启动路径修复（2026-07-31）

> 完整版: `Lin_workspace/r2_integration/doc/retrospect/2026-07-31_chassis_launch_fix.md`
> 机器: 本地 VM + N97（192.168.1.210）

## 一句话结论

旧 launch 文件用 `__file__` 推导路径，只有**从源码树以文件路径方式启动**时才成立；
N97 上用**包名方式** `ros2 launch r2_bringup chassis.launch.py` 启动，launch 文件从 install
目录加载，路径推导立刻失效 → `can't open file .../share/r2_bringup/r2_bringup/chassis_node.py`。

## 三个连续报错

1. `can't open file '.../share/r2_bringup/r2_bringup/chassis_node.py'`（exit 2）— 主因
2. `Package 'r2_bringup' not found` — 新 SSH 会话没 source（操作问题）
3. `libexec directory '.../lib/r2_bringup' does not exist` — 本环境 colcon 把
   console_script 装在 `bin/`，而 launch_ros 硬编码只搜 `lib/<pkg>/`（潜伏坑，
   旧 launch 走 ExecuteProcess+python3 没触发；`ros2 run` 同样会报这个错）

## 为什么之前一直是好的

VM 上习惯用文件路径启动（bash_history 有据）：`ros2 launch ~/Lin_workspace/.../launch/chassis.launch.py`
→ `__file__` 指向源码树 → 推导出的 `r2_bringup/r2_bringup/chassis_node.py` 真实存在。
是"启动方式巧合"掩盖了脆弱写法，不是代码本来就对。

## 修复要点

- 弃用 `__file__` 推导 → `get_package_prefix` + `get_package_share_directory`
- 入口脚本兼容两种布局：`lib/<pkg>/`（标准）和 `bin/`（本机 colcon）
- `ekf.launch.py` 无需改（它推导的 config/ 确实装在 share 下）

## 教训

1. launch 文件不写 `__file__` 相对推导
2. 跨机器统一包名方式启动
3. 新机器全新构建 = 最好的体检，老机器"能用"可能是巧合
4. 启动问题先翻 `~/.ros/log/<时间戳>/launch.log`
