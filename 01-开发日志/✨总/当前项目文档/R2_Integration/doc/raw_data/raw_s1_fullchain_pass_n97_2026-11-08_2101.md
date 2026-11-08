# 原始数据：老车 S1 全链实车首跑（含底盘/IMU/EKF）· N97

> 日期时间：2026-11-08 21:01:00 ~ 21:26:25（N97 本机时间）
> session 话题：老车 S1 explore 零前沿 → 方案 B 自车回波过滤 → **全链实车首跑验收（真实里程计 + Nav2 目标导航）**
> 来源：N97（192.168.1.210，lin-Default-string）本机 `~/.ros/log/` 采集；
> 仓库 HEAD `f033f7b`（filter polygon 放宽版）；CPU 治理器未记录
> 采集方式：VM 经 SSH 只读读取（`ls -lt ~/.ros/log/`、`cat/grep` 各节点日志），未在 N97 上重启任何进程
> 关联：[2026-11-08_oldcar_s1_fullchain_pass.md](../retrospect/2026-11-08_oldcar_s1_fullchain_pass.md)（事件记录）｜
> [raw_s1_chain_rerun_n97_2026-11-08_1727.md](raw_s1_chain_rerun_n97_2026-11-08_1727.md)（静态 TF 前序）
> 本地留档，不入 git

---

## §0 运行时间线（由 `~/.ros/log/<时间戳目录>/launch.log` 反推）

| 时刻 | launch 目录 | 起停节点 | 备注 |
|:---|:---|:---|:---|
| 21:01:00 | `2026-11-08-21-01-00-614022-…-12871` | ldlidar_stl_ros2_node / static_transform_publisher / scan_to_scan_filter_chain | LD06 launch（含过滤链 + 静态 TF base_link→base_laser） |
| 21:01:10 | `2026-11-08-21-01-10-964962-…-12919` | chassis_node | 底盘 |
| 21:01:15 | `2026-11-08-21-01-15-813702-…-12941` | imu_node | IMU（其后 250 帧校准通过） |
| 21:01:24 | `2026-11-08-21-01-24-381190-…-12962` | static_transform_publisher(base_link→imu_link) / ekf_node | EKF |
| 21:01:53 | `2026-11-08-21-01-53-481227-…-13024` | async_slam_toolbox_node | slam 首启，21:02:35 被 Ctrl-C |
| 21:02:22 | `2026-11-08-21-02-22-124799-…-13062` | Nav2 七节点 + rviz2 | 首次 Nav2；rviz2 于 21:02:45 崩溃（exit −6），21:02:50 Ctrl-C |
| 21:02:36 | `2026-11-08-21-02-36-221207-…-13195` | async_slam_toolbox_node | slam 重启（正式运行） |
| 21:05:33 | `2026-11-08-21-05-33-043582-…-13377` | —（启动即失败） | `rviz:=ture` 拼写错误，launch 异常退出 |
| 21:06:10 | `2026-11-08-21-06-10-127091-…-13467` | Nav2 七节点 + rviz2 | **正式运行**，至 21:26:18 收尾 |
| 21:07:28 | — | — | 首个 Nav2 目标开始 |
| 21:21:00 | — | — | 最后一个目标成功 |
| 21:26:25 | — | — | 全部 Ctrl-C 收尾 |

---

## §1 LD06 + 过滤链

```text
[INFO] [1794142860.682579110] [LD06]: LDLiDAR SDK Pack Version is: v3.0.3
[INFO] [1794142860.682683715] [LD06]: <product_name>: LDLiDAR_LD06
[INFO] [1794142860.682701836] [LD06]: <topic_name>: scan_raw
[INFO] [1794142860.682711836] [LD06]: <frame_id>: base_laser
[INFO] [1794142860.682720219] [LD06]: <port_name>: /dev/r2_ld06_a
[INFO] [1794142860.682728469] [LD06]: <port_baudrate>: 230400
[INFO] [1794142860.682736935] [LD06]: <laser_scan_dir>: Counterclockwise
[INFO] [1794142860.682746099] [LD06]: <enable_angle_crop_func>: false
[INFO] [1794142860.683057040] [LD06]: ldlidar node start is success
[INFO] [1794142860.685202545] [LD06]: ldlidar communication is normal.
[INFO] [1794142860.687105997] [LD06]: Publish topic message:ldlidar scan data.
```

静态 TF（`static_transform_publisher-2`）：

```text
translation: ('0.275000', '0.290000', '0.040000')
rotation:    ('0.000000', '0.000000', '-0.707108', '0.707105')
from 'base_link' to 'base_laser'
```

过滤链日志（无报错，仅两条已知提示）：

```text
[WARN] [rcl.logging_rosout]: Publisher already registered for provided node name. …
[WARN] [scan_to_scan_filter_chain]: diagnostic_updater: No HW_ID was set. …
[INFO] [1794144385.479703497] [rclcpp]: signal_handler(SIGINT/SIGTERM)
```

---

## §2 IMU 校准

```text
[INFO] [1794142877.095162011] [g354_imu_node]: Calib 50/250
[INFO] [1794142877.626818853] [g354_imu_node]: Calib 100/250
[INFO] [1794142878.158379459] [g354_imu_node]: Calib 150/250
[INFO] [1794142878.689990777] [g354_imu_node]: Calib 200/250
[INFO] [1794142879.221639890] [g354_imu_node]: Gyro bias (dps): X=0.0716 Y=-0.0018 Z=-0.0311
```

收尾：`imu_node-1: process has died [pid 12942, exit code 1]`（Ctrl-C 时非 clean 退出，未追因）

---

## §3 EKF

```text
[INFO] [static_transform_publisher_Bp6Wvxp49xOzUl0U]: Spinning until stopped - publishing transform
translation: ('0.000000', '0.000000', '0.000000')
rotation:    ('0.000000', '0.000000', '0.000000', '1.000000')
from 'base_link' to 'imu_link'
[INFO] [ekf_node-2] … process has finished cleanly [pid 12965]（收尾）
```

---

## §4 slam_toolbox

```text
[INFO] [1794142956.306612355] [slam_toolbox]: Node using stack size 40000000
[INFO] [1794142956.346767389] [slam_toolbox]: Using solver plugin solver_plugins::CeresSolver
[INFO] [1794142956.347027801] [slam_toolbox]: CeresSolver: Using SCHUR_JACOBI preconditioner.
[WARN] [1794142956.427573564] [slam_toolbox]: minimum laser range setting (0.0 m) exceeds the capabilities of the used Lidar (0.0 m)
[INFO] [1794143133.613513288] [slam_toolbox]: Message Filter dropping message: frame 'base_laser' at time 1794143133.287 for reason 'the timestamp on the message is earlier than all the data in the transform cache'
[INFO] [1794143136.302529446] [slam_toolbox]: Message Filter dropping message: frame 'base_laser' at time 1794143134.496 for reason 'discarding message because the queue is full'
[INFO] [1794143139.996489744] [slam_toolbox]: Message Filter dropping message: frame 'base_laser' at time 1794143139.895 for reason 'discarding message because the queue is full'
```

> 三次 Message Filter 丢弃均落在 21:05:13~21:05:40（Nav2 首次失败重启窗口），正式运行段无丢弃。

---

## §5 Nav2 目标导航结果（bt_navigator）

```text
$ grep -c "Begin navigating"  bt_navigator_13476_*.log   → 39
$ grep -c "Goal succeeded"    bt_navigator_13476_*.log   → 39
$ grep -iE "fail|abort|reject|cancel|error" bt_navigator_13476_*.log → （无输出）
```

节选（前 8 条）：

```text
[INFO] [1794143248.333963151] [bt_navigator]: Begin navigating from current location (-1.03, 0.25) to (-0.48, 0.34)
[INFO] [1794143250.274355553] [bt_navigator]: Goal succeeded
[INFO] [1794143259.074529353] [bt_navigator]: Begin navigating from current location (-0.70, 0.29) to (-0.13, 0.45)
[INFO] [1794143261.144796254] [bt_navigator]: Goal succeeded
[INFO] [1794143264.411766256] [bt_navigator]: Begin navigating from current location (-0.34, 0.29) to (0.50, 0.42)
[INFO] [1794143268.112052587] [bt_navigator]: Goal succeeded
[INFO] [1794143272.006403498] [bt_navigator]: Begin navigating from current location (0.30, 0.30) to (0.99, 0.31)
[INFO] [1794143274.976666785] [bt_navigator]: Goal succeeded
[INFO] [1794143297.283922266] [bt_navigator]: Begin navigating from current location (0.76, 0.33) to (1.40, 0.43)
[INFO] [1794143299.984283891] [bt_navigator]: Goal succeeded
[INFO] [1794143306.225964742] [bt_navigator]: Begin navigating from current location (1.17, 0.39) to (0.83, 0.40)
[INFO] [1794143307.226305907] [bt_navigator]: Goal succeeded
[INFO] [1794143314.128023047] [bt_navigator]: Begin navigating from current location (1.06, 0.40) to (0.49, 0.33)
[INFO] [1794143316.358318773] [bt_navigator]: Goal succeeded
[INFO] [1794143320.003984240] [bt_navigator]: Begin navigating from current location (0.71, 0.28) to (0.52, 0.30)
[INFO] [1794143320.074321621] [bt_navigator]: Goal succeeded
```

末 5 条：

```text
[INFO] [1794144030.064440543] [bt_navigator]: Begin navigating from current location (0.60, 0.36) to (0.79, 0.43)
[INFO] [1794144033.089494321] [bt_navigator]: Begin navigating from current location (0.60, 0.36) to (1.08, 0.54)
[INFO] [1794144042.721284224] [bt_navigator]: Begin navigating from current location (0.87, 0.48) to (0.10, 0.54)
[INFO] [1794144055.306643404] [bt_navigator]: Begin navigating from current location (0.14, 0.52) to (0.33, 0.48)
[INFO] [1794144057.697653852] [bt_navigator]: Begin navigating from current location (0.14, 0.52) to (0.79, 0.56)
[INFO] [1794144060.186679599] [controller_server]: Reached the goal!
```

> `current location` 在连续目标之间持续变化（−1.03 → +1.17 → … → 0.14），说明 `map→base_link` 真实移动，
> 非静止空转。

---

## §6 已知告警（Nav2 启动期）

```text
[ERROR] [1794143172.616020783] [global_costmap.global_costmap]: The configured inflation radius (0.300) is smaller than the computed inscribed radius (0.340) of your footprint, it is highly recommended to set inflation radius to be at least as big as the inscribed radius to avoid collisions
[ERROR] [1794143173.310864823] [local_costmap.local_costmap]: The configured inflation radius (0.300) is smaller than the computed inscribed radius (0.340) of your footprint, it is highly recommended to set inflation radius to be at least as big as the inscribed radius to avoid collisions
[WARN]  [1794143173.328776874] [controller_server]: Controller period is less then model dt, consider setting it equal
[WARN]  [1794143175.314777284] [controller_server]: Parameter controller_server.verbose not found
[WARN]  [1794143248.354897163] [controller_server]: No goal checker was specified in parameter 'current_goal_checker'. Server will use only plugin loaded general_goal_checker . This warning will appear once.
```

planner_server 除上述 inflation ERROR 外无其它 fail/error/warn。

---

## §7 底盘异常

```text
[INFO] [1794142871.411169159] [r2_chassis_node]: CAN 接口已打开: can0
[INFO] [1794142871.412063237] [r2_chassis_node]: R2 底盘节点已启动
[INFO] [1794142871.412689159] [r2_chassis_node]:   半对角线 R = 0.330 m
[INFO] [1794142871.413082507] [r2_chassis_node]:   wheel_diameter = 0.152 m
[INFO] [1794142871.413474505] [r2_chassis_node]:   ticks_per_rev = 4241
[INFO] [1794142871.413861527] [r2_chassis_node]:   m_per_tick = 0.000113 m
[INFO] [1794142871.414241723] [r2_chassis_node]:   speed_scale = 94.5 (m/s→CAN逻辑速度)
[INFO] [1794142871.414633238] [r2_chassis_node]:   限速: vx=0.5, vy=0.3, ω=0.8
[WARN] [1794143395.336857593] [r2_chassis_node]: STALL [FR] ID=0x326 speed=0 pwm=720
[WARN] [1794143886.336707545] [r2_chassis_node]: MOTOR_LOST [FL] ID=0x323 last=0.7s ago
[WARN] [1794143886.337179301] [r2_chassis_node]: MOTOR_LOST [FR] ID=0x326 last=0.7s ago
[WARN] [1794143886.337614091] [r2_chassis_node]: MOTOR_LOST [RL] ID=0x324 last=0.7s ago
[WARN] [1794143886.338026560] [r2_chassis_node]: MOTOR_LOST [RR] ID=0x325 last=0.7s ago
…
[WARN] [1794144385.338086953] [r2_chassis_node]: MOTOR_LOST [RR] ID=0x325 last=186.1s ago
[INFO] [1794144385.920057654] [r2_chassis_node]: 用户中断
```

统计：

```text
$ grep -c MOTOR_LOST python3_12920_*.log   → 848
$ grep -c STALL      python3_12920_*.log   → 1
```

> **前置说明（用户 2026-11-08 说明）**：本节电机中断是**用户主动注入的测试**，
> 目的是验证「电机中断后上层是否受影响」，**不是故障**。下面的现象与统计据此判读。

判读：
- `_check_motor_health` 为 1 Hz 检查，`dt > 0.3` 即告警（[chassis_node.py:507-518](../../r2_bringup/r2_bringup/chassis_node.py#L507-L518)）；
  848 / (499 s × 4 电机) ≈ **42%** 的检查命中 → **状态帧间歇性缺失**，非全程断链
- 末条告警 `last=186.1s ago` 反推最后一帧 ≈ 21:23:19，此后彻底无状态帧
- **21:18:06 ~ 21:21:00 期间仍有 5 个目标全部 `Reached the goal!`**（§5 末 5 条）→ **上层未受影响**，指令下发与行驶未中断（本轮测试目的达成）

---

## §8 rviz2 崩溃

```text
[ERROR] [1794142943.6406479] [rviz2-8]: process has died [pid 13092, exit code -6, cmd '/opt/ros/humble/lib/rviz2/rviz2 -d …/config/nav2.rviz --ros-args -r __node:=rviz2']
[ERROR] [1794144377.2402496] [rviz2-8]: process has died [pid 13486, exit code -11, cmd '/opt/ros/humble/lib/rviz2/rviz2 -d …/config/nav2.rviz --ros-args -r __node:=rviz2']
```

- 第一次：21:02:45，exit −6（SIGABRT），Nav2 首次启动窗口，5 s 后 Ctrl-C
- 第二次：21:26:17，exit −11（SIGSEGV），正式运行末（Ctrl-C 前 1.4 s）
- **两次崩溃均未影响 Nav2 主体**（第二次崩溃后目标早已全部完成）

---

## §9 启动失败一次（拼写）

```text
[ERROR] [launch]: Caught exception in launch (see debug for traceback): invalid condition expression,
expected one of [true, 1, false, 0] but got 'ture', expanded from '<launch.substitutions.launch_configuration.LaunchConfiguration object …>'
```

时间 21:05:33，用户 21:06:10 重跑成功。

---

## §10 采集命令（复现）

```bash
# 在 N97 本机（或 VM 经 SSH）只读采集：
ls -d ~/.ros/log/2026-11-08-21-*                       # 运行目录清单（目录名含起跑时刻 + 主机名 + pid）
cat  ~/.ros/log/<dir>/launch.log                       # 每轮起停节点 + 退出码
grep -c "Begin navigating" ~/.ros/log/bt_navigator_*.log
grep -c "Goal succeeded"   ~/.ros/log/bt_navigator_*.log
grep -iE "fail|abort|reject|cancel|error" ~/.ros/log/bt_navigator_*.log
grep  -c MOTOR_LOST ~/.ros/log/python3_<chassis_pid>_*.log
```

---

## §11 未采集项（本轮缺，后续补）

| 项 | 原因 | 影响 |
|:---|:---|:---|
| `/scan` `/scan_raw` 实测 Hz | 运行时未采，已停机 | 沿用 11-07 基线（10.00 Hz） |
| `/odometry/filtered` Hz | 同上 | 沿用 VLP-16 基线（~30 Hz） |
| 最终 `/map` 尺寸 / 覆盖率 | 未保存地图、未采 `/map` 元数据 | S1 验收「覆盖率 >80%」无法判定 |
| 实际行驶视频/轨迹 | 未录制 | 只有 bt_navigator 的 from→to 位置串可作轨迹佐证 |
| bag | 未录 | 本轮无 bag 归档 |
