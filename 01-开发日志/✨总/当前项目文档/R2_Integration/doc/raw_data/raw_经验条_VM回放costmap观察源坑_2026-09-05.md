# 暂存经验条 2：nav2 costmap 观察源 × bag 回放（sim time）—— 验证过程证据

> 会话 2026-09-05（低物盲区修法 B VM 验收排障）
> 证据副本：doc/raw_data/raw_vmreplay_*_2026-09-05.{log,txt,jsonl}（costmap_v4 / midcheck_v4 / bagplay_v4 / newmarks_v4）

## 已确证事实（非推断）
1. **standalone nav2_costmap_2d 节点全名 = /costmap/costmap**（可执行自带 ns=costmap）；yaml 段名必须完全匹配（08-25 同坑）
2. **humble observation_sources 是 string 型、空格分隔多源**（`"scan velodyne_low"`）——YAML list `["a","b"]` 会 configure 报
   "Wrong parameter type... is of type {string}... setting to {string_array}"（v1 实锤；官方 obstacle 文档 + docs issue #851）
3. **ros2 lifecycle set activate CLI 挂死**（20s+ 无响应；costmap 侧 transition 实际成功）——v1-v4 每轮复现；
   costmap log 同期出现 `failed to send response to /costmap/costmap/get_state (timeout)` → costmap 的 service server 处理异常
4. **ros2 bag play --topics 是 nargs='+'**：bag_path 放其后会被贪婪吃掉（报 "required: bag_path"）→ bag_path 必须前置（v3 实锤）
5. **static_transform_publisher 旧式位置参数可用**（odom→base_link / base_link→velodyne 均成功；v3/v4 costmap 的
   "Invalid frame ID odom" 报错在 static 注入后停止 = odom frame 就绪）
6. **sim time + bag 回放下 costmap 观察源不工作**：v2（bag tf）/v4（static tf + bag sensor）两轮，订阅建立（sub=1）但
   MessageFilter 无任何 ready/Map update 日志 → 0 mark（jsonl 空）。v4 时 scan pub1/sub1、costmap raw 正常发布空图（2Hz）
   但数据不进图。nav2 官方 ROS Index 页面明示 bag+sim clock 是 pointcloud 观测 known trouble 区（[index.ros.org/p/nav2_costmap_2d](https://index.ros.org/p/nav2_costmap_2d/#humble)）
7. **costmap_experiment.md（08-25）已记录同方向结论**：「bag 回放… use_sim_time 探测 → odom frame does not exist (TF buffer 空) →
   放弃 bag 回放」→ 08-25 定案 wall time + static tf + 极简实时 scan。本会话绕回 bag 回放 4 轮才回到同一认知（教训）

## 悬而未决（未深究，方向已弃）
- sim 轴下 MessageFilter 不 ready 的精确机制（tf buffer 时间窗 vs message_filter 行为）—— 未继续下钻（纠结即止）

## 方向（用户定夺中）
A. 整栈 nav2.launch.py sim time（官方 launch 覆盖 use_sim_time，可能规避 standalone 参数路径问题）——重、AMCL 噪音
B. wall 链路 + 静态 tf + 从 bag 抽矮物帧改 stamp 实时重发（08-25 验证形态 + 真实点云，变量最少）——倾向
C. 继续调 standalone sim 轴（方向未明，成本高）
