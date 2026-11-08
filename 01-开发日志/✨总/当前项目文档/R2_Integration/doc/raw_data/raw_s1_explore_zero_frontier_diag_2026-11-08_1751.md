# 原始数据：S1 explore 零前沿诊断（N97，AI 代执行）

> **来源**：2026-11-08 AI 经 SSH 在 N97（`lin-Default-string`）亲手执行，终端输出原样留档。
> **会话话题**：② 链路联调后续——explore_lite 报 `No frontiers found` 的诊断重跑（用户指令「你来执行诊断重跑操作」）。
> **执行时段**：2026-11-08 17:48 ~ 18:02。
> **环境**：N97 本机；仓库 HEAD `ecd457d`；**CPU 治理器 = powersave**（`sudo` 需密码，AI 无法切 performance——与 ② 轮条件不同，记录在案）。
> **关联**：[raw_s1_chain_rerun_n97_2026-11-08_1727.md](raw_s1_chain_rerun_n97_2026-11-08_1727.md)（② 轮链路重跑）｜[old-car/startup.md](../old-car/startup.md)｜[sensor-mount §6.1](../phase0/sensor-mount.md)

---

## §0 执行命令序列（AI 侧）

```text
1. LD06:        ros2 launch ldlidar_stl_ros2 ld06.launch.py
2. 静态 TF:      ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_link
3. slam_toolbox: ros2 launch slam_toolbox online_async_launch.py \
                  slam_params_file:=.../slam_toolbox_mapping.yaml use_sim_time:=false
4. Nav2:        ros2 launch r2_bringup nav2_explore.launch.py rviz:=false
5. 探针 ×3:      /tmp/frontier_probe.py /tmp/explore_replica.py /tmp/frag_analysis.py /tmp/scan_geom.py
6. explore:     ros2 run explore_lite explore --ros-params-file .../explore_params.yaml
```

---

## §1 启动阶段（关键行）

```text
[ldlidar_stl_ros2_node-1] [INFO] [1794131107.497] [LD06]: ldlidar communication is normal.
[ldlidar_stl_ros2_node-1] [INFO] [1794131107.498] [LD06]: Publish topic message:ldlidar scan data.
[static_transform_publisher-2] translation: ('0.275000', '0.290000', '0.040000')
[static_transform_publisher-2] rotation: ('0.000000', '0.000000', '-0.707108', '0.707105')

[async_slam_toolbox_node-1] [INFO] [1794131123.956] [slam_toolbox]: Using solver plugin solver_plugins::CeresSolver
[async_slam_toolbox_node-1] Registering sensor: [Custom Described Lidar]

[planner_server-1] [ERROR] [1794131472.899] [global_costmap.global_costmap]: The configured inflation radius (0.300) is smaller than the computed inscribed radius (0.340) of your footprint, ...
[controller_server-2] [ERROR] [1794131473.220] [local_costmap.local_costmap]: The configured inflation radius (0.300) is smaller than the computed inscribed radius (0.340) ...
[planner_server-1] [INFO] [1794131473.241] [global_costmap.global_costmap]: StaticLayer: Resizing costmap to 161 X 161 at 0.050000 m/pix
[lifecycle_manager-7] [INFO] [1794131475.325] [lifecycle_manager_navigation]: Managed nodes are active
```

`/map`（Nav2 起来前采样）：`161 x 161 @ 0.050000006`，`origin=(-3.3789, -0.6316)`，
即 x∈[−3.379, 4.671]、y∈[−0.632, 7.418]。**注意：② 轮为 161×132，本轮 161×161（+y 方向多 29 格 ≈1.45 m），地图仍在增长。**

---

## §2 探针一：朴素前沿计数（17:51:42）

```text
===== 采样时刻 17:51:42 =====

== /map == 161x161 @ 0.050 frame=map
   origin=(-3.379,-0.632) 范围 x[-3.38,4.67] y[-0.63,7.42]
   未知(-1)= 24941 自由(0)=   859 0<v<100=     0 占据(100)=   121
   机器人格 (67,12) 值 = -1
   >>> 前沿格（未知∧4邻有自由）= 423

== /global_costmap/costmap == 161x161 @ 0.050 frame=map
   origin=(-3.379,-0.632) 范围 x[-3.38,4.67] y[-0.63,7.42]
   未知(-1)= 19880 自由(0)=  1843 0<v<100=  3895 占据(100)=   303
   机器人格 (67,12) 值 = 99
   >>> 前沿格（未知∧4邻有自由）= 434
   前沿簇 185 个，top10=[15, 10, 10, 10, 9, 9, 9, 9, 9, 9]（explore 只留 ≥10 格）
```

---

## §3 explore_lite 实际判定（复现 ② 轮结果）

```text
[INFO] [1794131530.271598133] [explore_node]: Waiting for costmap to become available, topic: /global_costmap/costmap
[INFO] [1794131534.286654074] [explore_node]: Waiting to connect to move_base nav2 server
[INFO] [1794131534.286908734] [explore_node]: Connected to move_base nav2 server
[WARN] [1794131534.287128613] [explore_node]: No frontiers found, stopping.
[INFO] [1794131534.287150191] [explore_node]: Exploration stopped.
```

---

## §4 explore 判定链逐字复刻（同一帧 costmap，17:58:04）

复刻依据（N97 `~/Lin_workspace/explore_ws/src/m-explore-ros2/explore/`）：

- `src/costmap_client.cpp:260-280` `init_translation_table()`：
  `[0]=0(FREE)`, `[99]=253(INSCRIBED)`, `[100]=254(LETHAL)`, `[255]=255(NO_INFORMATION)`，
  其余 `1+(251*(i-1))/97`
- `src/frontier_search.cpp:55` BFS 起点 = `nearestCell(clear, robot_pos, FREE_SPACE)`（nhood8 全图搜索）
- `src/frontier_search.cpp:71` BFS 展开条件 `map_[nbr] <= map_[idx]`（下降搜索，**只能穿越同为 free 的格**）
- `src/frontier_search.cpp:177` `isNewFrontierCell` 要求 `map_[idx] == NO_INFORMATION` 且 4 邻有 `FREE_SPACE`
- `src/frontier_search.cpp:79` 保留条件 `new_frontier.size * resolution >= min_frontier_size`（0.5 m ⇒ 10 格）

```text
采样 17:58:04  161x161 @ 0.05000000074505806  origin=(-3.379,-0.632)
char 分布: free=2102 inscribed=4464 lethal=366 noinfo=18989 其它=0
机器人格=(67,12) idx=1999 char值=253
nearestCell: 找到 free clear=(64,10) 搜索访问 29 格
BFS 可达格数 = 18（其中 free = 18）
通过 min_frontier_size 前的簇数 = 1
min_frontier_size=0.5m 过滤后 = 0 簇
```

> **结论**：复刻结果与 explore 实际输出完全一致（0 簇）。零前沿不是转换表/参数问题，
> 而是**机器人可达的自由区只有 18 格，挂在其上的唯一前沿簇长度 <0.5 m 被过滤**。

---

## §5 自由区连通域分布（同帧附近，4 邻，同 explore 可穿越口径）

```text
=== 自由格连通域（4 邻，同 explore 可穿越口径）===
自由格总数=2163  连通域=55 个
  #1   825 格  bbox x[-2.83,-0.48] y[1.67,5.07]
  #2   294 格  bbox x[-0.83,0.97] y[0.17,1.22]
  #3   248 格  bbox x[0.72,1.27] y[4.92,7.12]
  #4   226 格  bbox x[0.42,0.97] y[1.87,4.37]
  #5   134 格  bbox x[-2.73,-1.43] y[1.72,2.87]
  #6   127 格  bbox x[2.77,4.42] y[2.17,3.52]
  机器人格 (67,12) 值=99 属于连通域 #0 大小=0
  单格/≤20格 的碎片连通域数 = 46

=== /scan ===  453 束, 有效 409, 无效 44
  min=0.02 p10=0.16 中位=0.99 p90=2.03 max=7.14
  [0,0.5) m: 131 束
  [0.5,1) m: 88 束
  [1,2) m: 147 束
  [2,4) m: 23 束
  [4,8) m: 20 束
  [8,99) m: 0 束
```

---

## §6 近距离回波的几何归属（决定性）

坐标变换 `base_laser → base_link`：`x_link = y_laser + 0.275`、`y_link = -x_laser + 0.290`
（与 `tf2_echo` 矩阵 `[[0,1,0,0.275],[-1,0,0,0.290]]` 一致）；车体物理 0.80×0.60 → 半长 0.40 / 半宽 0.30。

```text
=== 回波在 base_link 系的落点 ===
  距车心[0,0.3) m:  94 束  x_link[-0.12,+0.28] y_link[-0.28,+0.25]
  距车心[0.3,0.5) m:  37 束  x_link[+0.03,+0.32] y_link[-0.09,+0.34]
  距车心[0.5,0.8) m:  37 束  x_link[-0.74,+0.78] y_link[-0.63,+0.22]
  距车心[0.8,1.5) m: 133 束  x_link[-1.22,+1.49] y_link[-0.47,+1.35]
  距车心[1.5,99) m: 105 束  x_link[-3.38,+4.67] y_link[-0.26,+7.40]

落在车体矩形内的回波: 128 / 406 束
<0.5 m 回波 129 束，扫描角（发布角，逆时针）连续段：
      +0.0° ~   +19.1°
    +259.1° ~  +260.7°
    +271.0° ~  +273.4°
    +276.6° ~  +289.3°
    +292.5° ~  +334.6°
    +338.5° ~  +359.2°
  参考：车头=+90°，车左=+180°，车尾=270°/−90°，车右=0°
  这些回波在 base_link 系距车心: 中位 0.25 m, min 0.09, max 0.39
  其中落在车体矩形内的: 126 / 129 束
```

> **几何判读**：短距回波集中在 259°~359°（车尾—右侧扇区），正是「从 LD06 装点 (0.275, 0.29)
> 指向车体中心 (0,0)」的方向；129 束短距回波中 126 束落在车体矩形内，最近距车心 0.09 m
> ——**约 1/3（128/406）的光束打在机器人自身结构上**。

---

## §7 收尾

```text
收尾顺序（按 launch 层）：explore 节点 → nav2 launch（SIGTERM，子节点成孤儿后逐 PID SIGINT）
                          → slam launch → tf → LD06
复验：ps -eo pid,cmd | grep -iE "ldlidar|slam|tf2_ros|explore|nav2"   → 无匹配进程
      ros2 daemon stop; ros2 node list --no-daemon                  → 空
VM 侧同模式 grep                                                      → 无残留进程
```

> **收尾教训**：`kill -INT <ros2 launch PID>` 在 N97（无 tty、setsid 启动）下 **rc=0 但不生效**；
> SIGTERM 能杀 launch 包装但**子节点成孤儿继续运行**（与 ros2-ops §10 一致）——必须逐子 PID 再发 SIGINT。
