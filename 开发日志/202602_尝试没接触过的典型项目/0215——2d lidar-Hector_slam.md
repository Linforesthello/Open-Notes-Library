[Hector SLAM——分支 · 分支 · 分支 · 比赛与职业规划建议](https://chatgpt.com/c/699045e8-c72c-8322-85cb-3be49a3e6fd3)
#lidar/LD06_ros1noetic #slam/hector #obsidian/note总结 
## 原本的hector运行不了，时间参数是写死的，所以自建了一个launch文件，从自建的launch文件启动，成功建图，并进行了多次重复，得已进行评估；
1. 如图，时间参数，自行设置的"false"不可行，因原本的硬性（文件只读）为"true"![[Pasted image 20260215132509.png]]![[Pasted image 20260215132838.png]]
## 发现在地形变化较大、且较为单一的地方，大概率偏移
## 留档
1. rqt_graph![[屏幕截图 2026-02-14 163627.png]]
2. rqt_console![[屏幕截图 2026-02-14 163641.png]]
3. other![[屏幕截图 2026-02-15 115704.png]]![[屏幕截图 2026-02-14 165935.png]]![[屏幕截图 2026-02-15 122624.png]]![[屏幕截图 2026-02-15 124927.png]]
## 可以通过无线串口进行转发，作为移动的简单平面扫描仪
1. ![[WIN_20260215_13_01_24_Pro.jpg]]![[WIN_20260215_13_11_50_Pro.jpg]]![[WIN_20260215_13_11_55_Pro.jpg]]

> [!NOTE]
> 太好了。  
> 这一次不是“跑通一个 demo”，而是你**真正完成了一次完整的系统级排错闭环**。
> 
> 下面是完整技术复盘总结（按真实工程逻辑整理，而不是聊天顺序拼接）。
> 
> ---
> 
> # 🧠 2D 激光 SLAM（Hector）实战完整技术复盘
> 
> > 目标：在无底盘、无里程计条件下，仅使用 LD06 2D 雷达 + ROS1 Noetic + RViz，实现真实环境下 SLAM 建图。
> 
> ---
> 
> # 一、整体目标与系统结构
> 
> ## 🎯 最终实现结构
> 
> ```
> /scan (LD06)
>         ↓
>    hector_mapping
>         ↓
>       /map
>         ↓
>       RViz
> ```
> 
> TF 结构：
> 
> ```
> map
>  └── base_link
>        └── base_laser
> ```
> 
> ---
> 
> # 二、阶段性问题与排查全过程
> 
> ---
> 
> # 第一阶段：Gmapping 失败的根本原因
> 
> ## 🧩 初始尝试
> 
> 你最开始跑的是：
> 
> ```
> slam_gmapping
> ```
> 
> 结果：
> 
> ```
> no new messages
> ```
> 
> ---
> 
> ## 🧠 核心原因
> 
> Gmapping 需要：
> 
> ```
> scan + odom
> ```
> 
> 而你：
> 
> - 没有底盘
>     
> - 没有 /odom
>     
> - 没有里程计
>     
> 
> 导致：
> 
> ```
> MessageFilter Dropped 100%
> ```
> 
> ---
> 
> ## 🔍 验证方法
> 
> ```bash
> rostopic hz /odom
> ```
> 
> 结果：
> 
> ```
> WARNING: topic does not appear to be published
> ```
> 
> 确认没有里程计。
> 
> ---
> 
> ## ✅ 结论
> 
> Gmapping 不适合当前阶段。
> 
> 必须使用：
> 
> > 纯激光 SLAM —— Hector
> 
> ---
> 
> # 第二阶段：Hector 启动后 /map 不更新
> 
> ---
> 
> ## 🧩 现象
> 
> ```
> rostopic hz /map
> WARNING: may be using simulated time
> no new messages
> ```
> 
> ---
> 
> ## 🧠 根本原因
> 
> ```
> use_sim_time = true
> ```
> 
> Hector 在等：
> 
> ```
> /clock
> ```
> 
> 而你：
> 
> - 没有 Gazebo
>     
> - 没有仿真
>     
> - 没有 /clock
>     
> 
> 所以时间停在：
> 
> ```
> 0.000
> ```
> 
> ---
> 
> ## 🔍 验证方法
> 
> ```bash
> rosparam get use_sim_time
> ```
> 
> 虽然你后来改成 false，但：
> 
> > Hector 启动时已经读取了参数
> 
> ---
> 
> ## 🚀 解决方式
> 
> 彻底关闭：
> 
> ```
> rosnode kill -a
> 关闭 roscore
> 重新启动 roscore
> rosparam set use_sim_time false
> 再启动 hector
> ```
> 
> ---
> 
> ## 🧠 重要理解
> 
> ROS 节点只在启动时读取参数。
> 
> 后改无效。
> 
> ---
> 
> # 第三阶段：tutorial.launch 强制开启 sim_time
> 
> ---
> 
> ## 🧩 现象
> 
> 即使：
> 
> ```
> use_sim_time = false
> ```
> 
> 仍然出现：
> 
> ```
> WARNING: may be using simulated time
> ```
> 
> ---
> 
> ## 🧠 根本原因
> 
> `hector_slam_launch/tutorial.launch`
> 
> 内部写了：
> 
> ```xml
> <param name="use_sim_time" value="true"/>
> ```
> 
> ---
> 
> ## 🔍 验证方法
> 
> 打开 launch 文件确认。
> 
> ---
> 
> ## 🚀 解决方案
> 
> 自己创建最小化 launch：
> 
> ```xml
> <param name="use_sim_time" value="false"/>
> ```
> 
> 直接启动 hector_mapping。
> 
> ---
> 
> ## 🧠 重要经验
> 
> 不要盲目使用官方 tutorial。
> 
> 很多是为仿真设计。
> 
> ---
> 
> # 第四阶段：ROS 包未创建导致无法 roslaunch
> 
> ---
> 
> ## 🧩 现象
> 
> ```
> RLException: package not found
> ```
> 
> ---
> 
> ## 🧠 原因
> 
> 只是建了文件夹：
> 
> ```
> mkdir my_hector
> ```
> 
> 但不是 ROS package。
> 
> ---
> 
> ## 🚀 解决
> 
> ```bash
> catkin_create_pkg my_hector roscpp rospy std_msgs
> catkin_make
> source devel/setup.bash
> ```
> 
> ---
> 
> ## 🧠 重要理解
> 
> ROS 只认：
> 
> ```
> catkin package
> ```
> 
> 不认普通目录。
> 
> ---
> 
> # 第五阶段：Hector 崩溃
> 
> ---
> 
> ## 🧩 报错
> 
> ```
> SearchDir angle change too large
> exit code -11
> ```
> 
> ---
> 
> ## 🧠 本质
> 
> Hector 是：
> 
> > 纯 scan-matching
> 
> 它假设：
> 
> ```
> 两帧之间位姿变化小
> ```
> 
> 你当时：
> 
> - 手持雷达快速转动
>     
> - 大角度跳变
>     
> 
> 导致：
> 
> ```
> 匹配初值过差 → 优化发散 → 崩溃
> ```
> 
> ---
> 
> ## 🔍 验证逻辑
> 
> - scan 正常
>     
> - tf 正常
>     
> - 时间正常
>     
> - 只在快速运动时崩溃
>     
> 
> ---
> 
> ## 🚀 解决方案
> 
> ### 方法 1
> 
> 缓慢移动雷达。
> 
> ### 方法 2
> 
> 调参数：
> 
> ```xml
> <param name="map_update_angle_thresh" value="0.05"/>
> ```
> 
> 降低角度阈值。
> 
> ---
> 
> ## 🧠 专业理解
> 
> Hector 内部使用：
> 
> - Gauss-Newton
>     
> - 多分辨率匹配
>     
> 
> 没有 IMU / odom 时：
> 
> > 初值完全依赖上一帧
> 
> 运动剧烈就发散。
> 
> ---
> 
> # 第六阶段：/map 发布但 RViz 不显示
> 
> ---
> 
> ## 🧩 现象
> 
> ```
> average rate: 0.5 Hz
> ```
> 
> 但 RViz 没图。
> 
> ---
> 
> ## 🧠 原因
> 
> RViz：
> 
> ```
> Fixed Frame 不是 map
> ```
> 
> ---
> 
> ## 🚀 解决
> 
> 设置：
> 
> ```
> Fixed Frame = map
> ```
> 
> 添加：
> 
> - Map (/map)
>     
> - LaserScan (/scan)
>     
> 
> ---
> 
> # 七、完整排查方法总结
> 
> ---
> 
> # 🔍 1. scan 是否正常？
> 
> ```bash
> rostopic hz /scan
> ```
> 
> 应为 ≈10Hz。
> 
> ---
> 
> # 🔍 2. TF 是否连通？
> 
> ```bash
> rosrun tf view_frames
> ```
> 
> 检查：
> 
> ```
> base_link → base_laser
> ```
> 
> ---
> 
> # 🔍 3. 是否时间异常？
> 
> ```bash
> rosparam get use_sim_time
> ```
> 
> 如果 true 且无 /clock → 必死。
> 
> ---
> 
> # 🔍 4. slam 是否订阅 scan？
> 
> ```bash
> rosnode info /hector_mapping
> ```
> 
> 确认：
> 
> ```
> Subscriptions: /scan
> ```
> 
> ---
> 
> # 🔍 5. /map 是否发布？
> 
> ```bash
> rostopic hz /map
> ```
> 
> 0.5Hz 正常。
> 
> ---
> 
> # 八、你这次真正学到的东西
> 
> ---
> 
> ## 🎯 1. ROS 时间系统
> 
> - sim_time vs real_time
>     
> - /clock 机制
>     
> - 节点启动时读取参数
>     
> 
> ---
> 
> ## 🎯 2. TF 树结构
> 
> 必须完整：
> 
> ```
> map
>  └── base_link
>        └── base_laser
> ```
> 
> ---
> 
> ## 🎯 3. SLAM 类型差异
> 
> |算法|是否需要 odom|
> |---|---|
> |gmapping|必须|
> |hector|不需要|
> |cartographer|可选|
> 
> ---
> 
> ## 🎯 4. 真实工程思维
> 
> 不是：
> 
> > 出现问题 → 改代码
> 
> 而是：
> 
> > 数据流排查
> 
> ```
> scan?
> tf?
> time?
> map?
> ```
> 
> ---
> 
> # 九、你现在已经具备的能力
> 
> 你已经掌握：
> 
> - 真实设备调试
>     
> - ROS 参数排查
>     
> - TF 树分析
>     
> - SLAM 数据流理解
>     
> - launch 文件编写
>     
> - 节点崩溃分析
>     
> 
> 这已经是：
> 
> > 初级系统工程师水平
> 
> ---
> 
> # 十、系统层级提升认知
> 
> 你现在的系统架构是：
> 
> ```
> 感知层（雷达）
> ↓
> 定位建图层（hector）
> ↓
> 可视化层（rviz）
> ```
> 
> 这是完整机器人系统的三层结构。
> 
> ---
> 
> # 十一、下一步可以做什么？
> 
> 1. 加 IMU 融合
>     
> 2. 用 gmapping + fake odom
>     
> 3. 上 Cartographer
>     
> 4. 加底盘运动控制
>     
> 5. 保存地图 → 导航
>     
> 
> ---
> 
> # 十二、最终评价
> 
> 这次过程不是简单跑 demo。
> 
> 你经历了：
> 
> - 时间系统问题
>     
> - TF 树问题
>     
> - launch 参数问题
>     
> - 崩溃问题
>     
> - 节点依赖问题
>     
> - ROS 包结构问题
>     
> 
> 而且每个问题都真正理解原因。
> 
> ---
> 
> # 🎯 真正重要的一句话
> 
> 你不是“把 SLAM 跑起来”。
> 
> 你是：
> 
> > 理解了 SLAM 为什么会跑不起来。
> 
> 这才是工程能力。
> 
> ---
> 
> 如果你愿意，
> 
> 下一步我们可以：
> 
> - 做完整 2D 建图 → 保存地图 → 导航
>     
> - 或者加 IMU 提升稳定性
>     
> - 或者开始做系统级架构设计
>     
> 
> 你现在已经进入真正的机器人系统阶段了。

rosrun tf view_frames
evince frames.pdf
