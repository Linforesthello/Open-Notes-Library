# 原始数据留档 · 老车 S1 静态联调（N97，2026-11-08）

> **来源**：用户从 VMware 经 SSH 登录 N97（`lin-Default-string`）的终端实录，整块粘贴后落盘。
> **会话话题**：R2 老车 S1 静态联调——LD06 → 静态 TF 顶替里程计 → slam_toolbox → nav2_explore → explore_lite；只起不动机器人，无底盘/无 IMU/无图形界面。
> **采集时间**：2026-11-08 12:01–12:05（N97 本机时间；以各 launch 日志目录名 `2026-11-08-12-01-12…` 为证）。
> **整理**：2026-11-08 归档改名（原名 `261108_data.md`），**仅新增本头部，正文一字未改**；
> 各段为按终端粘贴的顺序，**块顺序不等于时间顺序**（时间线以行内 `[1794…]` 时间戳为准）。
> **对应留档**：[doc/retrospect/2026-11-08_oldcar_s1_static_bringup.md](../retrospect/2026-11-08_oldcar_s1_static_bringup.md)（结论/判读/复现清单）。
> **不入 git**：`doc/raw_data/` 已在 `.gitignore`（§1.13 轻量档纪律）。

---

lin@lin-Default-string:~$ source /opt/ros/humble/setup.bash
lin@lin-Default-string:~$ source ~/Lin_workspace/r2_integration/install/setup.bash
ros2 launch ldlidar_stl_ros2 ld06.launch.py
[INFO] [launch]: All log files can be found below /home/lin/.ros/log/2026-11-08-12-01-12-082083-lin-Default-string-4490
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [ldlidar_stl_ros2_node-1]: process started with pid [4491]
[INFO] [static_transform_publisher-2]: process started with pid [4493]
[static_transform_publisher-2] [WARN] [1794110472.139079792] []: Old-style arguments are deprecated; see --help for new-style arguments
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150361750] [LD06]: LDLiDAR SDK Pack Version is: v3.0.3
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150514160] [LD06]: <product_name>: LDLiDAR_LD06
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150529208] [LD06]: <topic_name>: scan
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150538846] [LD06]: <frame_id>: base_laser
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150547228] [LD06]: <port_name>: /dev/r2_ld06_a
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150555757] [LD06]: <port_baudrate>: 230400
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150564437] [LD06]: <laser_scan_dir>: Counterclockwise
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150572881] [LD06]: <enable_angle_crop_func>: false
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150581171] [LD06]: <angle_crop_min>: 135.000000
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150594726] [LD06]: <angle_crop_max>: 225.000000
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.150971644] [LD06]: ldlidar node start is success
[static_transform_publisher-2] [INFO] [1794110472.153060654] [base_link_to_base_laser_ld06]: Spinning until stopped - publishing transform
[static_transform_publisher-2] translation: ('0.000000', '0.000000', '0.180000')
[static_transform_publisher-2] rotation: ('0.000000', '0.000000', '0.000000', '1.000000')
[static_transform_publisher-2] from 'base_link' to 'base_laser'
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.154236856] [LD06]: ldlidar communication is normal.
[ldlidar_stl_ros2_node-1] [INFO] [1794110472.155640479] [LD06]: Publish topic message:ldlidar scan data.
[ldlidar_stl_ros2_node-1] [LDS][INFO][1794110472.150872302][Actual BaudRate reported:230400]
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[static_transform_publisher-2] [INFO] [1794110732.167946109] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[ldlidar_stl_ros2_node-1] [INFO] [1794110732.167939529] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[ldlidar_stl_ros2_node-1] [INFO] [1794110732.172141593] [LD06]: ldlidar_published is end
[INFO] [static_transform_publisher-2]: process has finished cleanly [pid 4493]
[INFO] [ldlidar_stl_ros2_node-1]: process has finished cleanly [pid 4491]
lin@lin-Default-string:~$ 

lin@lin-Default-string:~$ source /opt/ros/humble/setup.bash
lin@lin-Default-string:~$ ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_link
[WARN] [1794110486.420213628] []: Old-style arguments are deprecated; see --help for new-style arguments
[INFO] [1794110486.433175805] [static_transform_publisher_njclpnoahQauMSDd]: Spinning until stopped - publishing transform
translation: ('0.000000', '0.000000', '0.000000')
rotation: ('0.000000', '0.000000', '0.000000', '1.000000')
from 'odom' to 'base_link'
^C[INFO] [1794110731.590089752] [rclcpp]: signal_handler(SIGINT/SIGTERM)
lin@lin-Default-string:~$ 

lin@lin-Default-string:~$ source /opt/ros/humble/setup.bash
lin@lin-Default-string:~$ source ~/Lin_workspace/r2_integration/install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$HOME/Lin_workspace/r2_integration/install/r2_bringup/share/r2_bringup/config/slam_toolbox_mapping.yaml \
  use_sim_time:=false
[INFO] [launch]: All log files can be found below /home/lin/.ros/log/2026-11-08-12-02-23-398547-lin-Default-string-4592
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [async_slam_toolbox_node-1]: process started with pid [4593]
[async_slam_toolbox_node-1] [INFO] [1794110543.811156395] [slam_toolbox]: Node using stack size 40000000
[async_slam_toolbox_node-1] [INFO] [1794110543.852870276] [slam_toolbox]: Using solver plugin solver_plugins::CeresSolver
[async_slam_toolbox_node-1] [INFO] [1794110543.853126259] [slam_toolbox]: CeresSolver: Using SCHUR_JACOBI preconditioner.
[async_slam_toolbox_node-1] [WARN] [1794110543.862230641] [slam_toolbox]: minimum laser range setting (0.0 m) exceeds the capabilities of the used Lidar (0.0 m)
[async_slam_toolbox_node-1] Registering sensor: [Custom Described Lidar]
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[async_slam_toolbox_node-1] [INFO] [1794110731.046498575] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[INFO] [async_slam_toolbox_node-1]: process has finished cleanly [pid 4593]
lin@lin-Default-string:~$ 

lin@lin-Default-string:~$ source /opt/ros/humble/setup.bash
lin@lin-Default-string:~$ source ~/Lin_workspace/r2_integration/install/setup.bash
ros2 launch r2_bringup nav2_explore.launch.py rviz:=false
[INFO] [launch]: All log files can be found below /home/lin/.ros/log/2026-11-08-12-03-20-521330-lin-Default-string-4668
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [planner_server-1]: process started with pid [4669]
[INFO] [controller_server-2]: process started with pid [4671]
[INFO] [smoother_server-3]: process started with pid [4673]
[INFO] [behavior_server-4]: process started with pid [4675]
[INFO] [bt_navigator-5]: process started with pid [4677]
[INFO] [velocity_smoother-6]: process started with pid [4679]
[INFO] [lifecycle_manager-7]: process started with pid [4681]
[lifecycle_manager-7] [INFO] [1794110600.722759221] [lifecycle_manager_navigation]: Creating
[lifecycle_manager-7] [INFO] [1794110600.732133838] [lifecycle_manager_navigation]: Creating and initializing lifecycle service clients
[planner_server-1] [INFO] [1794110600.760222257] [planner_server]: 
[planner_server-1] 	planner_server lifecycle node launched. 
[planner_server-1] 	Waiting on external lifecycle transitions to activate
[planner_server-1] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[planner_server-1] [INFO] [1794110600.773962794] [planner_server]: Creating
[velocity_smoother-6] [INFO] [1794110600.792276079] [velocity_smoother]: 
[velocity_smoother-6] 	velocity_smoother lifecycle node launched. 
[velocity_smoother-6] 	Waiting on external lifecycle transitions to activate
[velocity_smoother-6] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[smoother_server-3] [INFO] [1794110600.794251791] [smoother_server]: 
[smoother_server-3] 	smoother_server lifecycle node launched. 
[smoother_server-3] 	Waiting on external lifecycle transitions to activate
[smoother_server-3] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[smoother_server-3] [INFO] [1794110600.806028716] [smoother_server]: Creating smoother server
[behavior_server-4] [INFO] [1794110600.810255984] [behavior_server]: 
[behavior_server-4] 	behavior_server lifecycle node launched. 
[behavior_server-4] 	Waiting on external lifecycle transitions to activate
[behavior_server-4] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[bt_navigator-5] [INFO] [1794110600.811118259] [bt_navigator]: 
[bt_navigator-5] 	bt_navigator lifecycle node launched. 
[bt_navigator-5] 	Waiting on external lifecycle transitions to activate
[bt_navigator-5] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[bt_navigator-5] [INFO] [1794110600.812054521] [bt_navigator]: Creating
[controller_server-2] [INFO] [1794110600.819092903] [controller_server]: 
[controller_server-2] 	controller_server lifecycle node launched. 
[controller_server-2] 	Waiting on external lifecycle transitions to activate
[controller_server-2] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[controller_server-2] [INFO] [1794110600.825214850] [controller_server]: Creating controller server
[planner_server-1] [INFO] [1794110600.829759371] [global_costmap.global_costmap]: 
[planner_server-1] 	global_costmap lifecycle node launched. 
[planner_server-1] 	Waiting on external lifecycle transitions to activate
[planner_server-1] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[planner_server-1] [INFO] [1794110600.832593736] [global_costmap.global_costmap]: Creating Costmap
[controller_server-2] [INFO] [1794110600.846591278] [local_costmap.local_costmap]: 
[controller_server-2] 	local_costmap lifecycle node launched. 
[controller_server-2] 	Waiting on external lifecycle transitions to activate
[controller_server-2] 	See https://design.ros2.org/articles/node_lifecycle.html for more information.
[controller_server-2] [INFO] [1794110600.847129948] [local_costmap.local_costmap]: Creating Costmap
[lifecycle_manager-7] [INFO] [1794110600.929673092] [lifecycle_manager_navigation]: Starting managed nodes bringup...
[lifecycle_manager-7] [INFO] [1794110600.929727667] [lifecycle_manager_navigation]: Configuring planner_server
[planner_server-1] [INFO] [1794110600.930116518] [planner_server]: Configuring
[planner_server-1] [INFO] [1794110600.930162392] [global_costmap.global_costmap]: Configuring
[planner_server-1] [INFO] [1794110600.936751991] [global_costmap.global_costmap]: Using plugin "static_layer"
[planner_server-1] [INFO] [1794110600.943757241] [global_costmap.global_costmap]: Subscribing to the map topic (/map) with transient local durability
[planner_server-1] [INFO] [1794110600.944930589] [global_costmap.global_costmap]: Initialized plugin "static_layer"
[planner_server-1] [INFO] [1794110600.944966250] [global_costmap.global_costmap]: Using plugin "obstacle_layer"
[planner_server-1] [INFO] [1794110600.945841138] [global_costmap.global_costmap]: Subscribed to Topics: scan
[planner_server-1] [INFO] [1794110600.948791435] [global_costmap.global_costmap]: Initialized plugin "obstacle_layer"
[planner_server-1] [INFO] [1794110600.948835056] [global_costmap.global_costmap]: Using plugin "inflation_layer"
[planner_server-1] [INFO] [1794110600.949242178] [global_costmap.global_costmap]: Initialized plugin "inflation_layer"
[planner_server-1] [ERROR] [1794110600.957139466] [global_costmap.global_costmap]: The configured inflation radius (0.300) is smaller than the computed inscribed radius (0.340) of your footprint, it is highly recommended to set inflation radius to be at least as big as the inscribed radius to avoid collisions
[planner_server-1] [INFO] [1794110600.959812522] [global_costmap.global_costmap]: StaticLayer: Resizing costmap to 112 X 172 at 0.050000 m/pix
[planner_server-1] [INFO] [1794110600.960863960] [planner_server]: Created global planner plugin GridBased of type nav2_navfn_planner/NavfnPlanner
[planner_server-1] [INFO] [1794110600.960902428] [planner_server]: Configuring plugin GridBased of type NavfnPlanner
[planner_server-1] [INFO] [1794110600.961262369] [planner_server]: Planner Server has GridBased  planners available.
[lifecycle_manager-7] [INFO] [1794110600.972712283] [lifecycle_manager_navigation]: Configuring controller_server
[controller_server-2] [INFO] [1794110600.972929068] [controller_server]: Configuring controller interface
[controller_server-2] [INFO] [1794110600.973065356] [controller_server]: getting goal checker plugins..
[controller_server-2] [INFO] [1794110600.973135544] [controller_server]: Controller frequency set to 30.0000Hz
[controller_server-2] [INFO] [1794110600.973173314] [local_costmap.local_costmap]: Configuring
[controller_server-2] [INFO] [1794110600.978914750] [local_costmap.local_costmap]: Using plugin "voxel_layer"
[controller_server-2] [INFO] [1794110600.982795912] [local_costmap.local_costmap]: Subscribed to Topics: scan
[controller_server-2] [INFO] [1794110600.988725707] [local_costmap.local_costmap]: Initialized plugin "voxel_layer"
[controller_server-2] [INFO] [1794110600.988765192] [local_costmap.local_costmap]: Using plugin "inflation_layer"
[controller_server-2] [INFO] [1794110600.989134215] [local_costmap.local_costmap]: Initialized plugin "inflation_layer"
[controller_server-2] [ERROR] [1794110600.994410208] [local_costmap.local_costmap]: The configured inflation radius (0.300) is smaller than the computed inscribed radius (0.340) of your footprint, it is highly recommended to set inflation radius to be at least as big as the inscribed radius to avoid collisions
[controller_server-2] [INFO] [1794110600.998640047] [controller_server]: Created progress_checker : progress_checker of type nav2_controller::SimpleProgressChecker
[controller_server-2] [INFO] [1794110601.000095908] [controller_server]: Created goal checker : general_goal_checker of type nav2_controller::SimpleGoalChecker
[controller_server-2] [INFO] [1794110601.000436784] [controller_server]: Controller Server has general_goal_checker  goal checkers available.
[controller_server-2] [INFO] [1794110601.004788992] [controller_server]: Created controller : FollowPath of type nav2_mppi_controller::MPPIController
[controller_server-2] [WARN] [1794110601.006610420] [controller_server]: Controller period is less then model dt, consider setting it equal
[controller_server-2] [INFO] [1794110601.009816083] [controller_server]: ConstraintCritic instantiated with 1 power and 4.000000 weight.
[controller_server-2] [INFO] [1794110601.009860942] [controller_server]: Critic loaded : mppi::critics::ConstraintCritic
[controller_server-2] [INFO] [1794110601.010419047] [controller_server]: InflationCostCritic instantiated with 1 power and 300.000000 / 0.015000 weights. Critic will collision check based on footprint cost.
[controller_server-2] [INFO] [1794110601.010456614] [controller_server]: Critic loaded : mppi::critics::CostCritic
[controller_server-2] [INFO] [1794110601.011363181] [controller_server]: GoalCritic instantiated with 1 power and 5.000000 weight.
[controller_server-2] [INFO] [1794110601.011395422] [controller_server]: Critic loaded : mppi::critics::GoalCritic
[controller_server-2] [INFO] [1794110601.011605718] [controller_server]: GoalAngleCritic instantiated with 1 power, 3.000000 weight, and 0.500000 angular threshold.
[controller_server-2] [INFO] [1794110601.011627213] [controller_server]: Critic loaded : mppi::critics::GoalAngleCritic
[controller_server-2] [INFO] [1794110601.011949407] [controller_server]: ReferenceTrajectoryCritic instantiated with 1 power and 14.000000 weight
[controller_server-2] [INFO] [1794110601.011971550] [controller_server]: Critic loaded : mppi::critics::PathAlignCritic
[controller_server-2] [INFO] [1794110601.013105485] [controller_server]: Critic loaded : mppi::critics::PathFollowCritic
[controller_server-2] [INFO] [1794110601.014071073] [controller_server]: PathAngleCritic instantiated with 1 power and 2.000000 weight. Reversing allowed.
[controller_server-2] [INFO] [1794110601.014105493] [controller_server]: Critic loaded : mppi::critics::PathAngleCritic
[controller_server-2] [INFO] [1794110601.014829075] [controller_server]: PreferForwardCritic instantiated with 1 power and 5.000000 weight.
[controller_server-2] [INFO] [1794110601.014861608] [controller_server]: Critic loaded : mppi::critics::PreferForwardCritic
[controller_server-2] [INFO] [1794110601.015573870] [controller_server]: TwirlingCritic instantiated with 1 power and 10.000000 weight.
[controller_server-2] [INFO] [1794110601.015613194] [controller_server]: Critic loaded : mppi::critics::TwirlingCritic
[controller_server-2] [INFO] [1794110601.025045854] [controller_server]: Optimizer reset
[controller_server-2] [INFO] [1794110601.027773103] [MPPIController]: Configured MPPI Controller: FollowPath
[controller_server-2] [INFO] [1794110601.027804545] [controller_server]: Controller Server has FollowPath  controllers available.
[lifecycle_manager-7] [INFO] [1794110601.034105151] [lifecycle_manager_navigation]: Configuring smoother_server
[smoother_server-3] [INFO] [1794110601.034328470] [smoother_server]: Configuring smoother server
[smoother_server-3] [INFO] [1794110601.046036328] [smoother_server]: Created smoother : simple_smoother of type nav2_smoother::SimpleSmoother
[smoother_server-3] [INFO] [1794110601.046871384] [smoother_server]: Smoother Server has simple_smoother  smoothers available.
[lifecycle_manager-7] [INFO] [1794110601.053903566] [lifecycle_manager_navigation]: Configuring behavior_server
[behavior_server-4] [INFO] [1794110601.054145168] [behavior_server]: Configuring
[behavior_server-4] [INFO] [1794110601.062054758] [behavior_server]: Creating behavior plugin spin of type nav2_behaviors/Spin
[behavior_server-4] [INFO] [1794110601.063861344] [behavior_server]: Configuring spin
[behavior_server-4] [INFO] [1794110601.068732463] [behavior_server]: Creating behavior plugin backup of type nav2_behaviors/BackUp
[behavior_server-4] [INFO] [1794110601.070413012] [behavior_server]: Configuring backup
[behavior_server-4] [INFO] [1794110601.074159101] [behavior_server]: Creating behavior plugin drive_on_heading of type nav2_behaviors/DriveOnHeading
[behavior_server-4] [INFO] [1794110601.075926471] [behavior_server]: Configuring drive_on_heading
[behavior_server-4] [INFO] [1794110601.079555810] [behavior_server]: Creating behavior plugin assisted_teleop of type nav2_behaviors/AssistedTeleop
[behavior_server-4] [INFO] [1794110601.083281656] [behavior_server]: Configuring assisted_teleop
[behavior_server-4] [INFO] [1794110601.088317607] [behavior_server]: Creating behavior plugin wait of type nav2_behaviors/Wait
[behavior_server-4] [INFO] [1794110601.089945630] [behavior_server]: Configuring wait
[lifecycle_manager-7] [INFO] [1794110601.093573176] [lifecycle_manager_navigation]: Configuring bt_navigator
[bt_navigator-5] [INFO] [1794110601.093868948] [bt_navigator]: Configuring
[lifecycle_manager-7] [INFO] [1794110601.183984097] [lifecycle_manager_navigation]: Configuring velocity_smoother
[velocity_smoother-6] [INFO] [1794110601.184234366] [velocity_smoother]: Configuring velocity smoother
[lifecycle_manager-7] [INFO] [1794110601.188713846] [lifecycle_manager_navigation]: Activating planner_server
[planner_server-1] [INFO] [1794110601.188870443] [planner_server]: Activating
[planner_server-1] [INFO] [1794110601.188921216] [global_costmap.global_costmap]: Activating
[planner_server-1] [INFO] [1794110601.188938972] [global_costmap.global_costmap]: Checking transform
[planner_server-1] [INFO] [1794110601.189057142] [global_costmap.global_costmap]: start
[planner_server-1] [INFO] [1794110602.239730033] [planner_server]: Activating plugin GridBased of type NavfnPlanner
[planner_server-1] [INFO] [1794110602.240657785] [planner_server]: Creating bond (planner_server) to lifecycle manager.
[lifecycle_manager-7] [INFO] [1794110602.345623935] [lifecycle_manager_navigation]: Server planner_server connected with bond.
[lifecycle_manager-7] [INFO] [1794110602.345682510] [lifecycle_manager_navigation]: Activating controller_server
[controller_server-2] [INFO] [1794110602.346005866] [controller_server]: Activating
[controller_server-2] [INFO] [1794110602.346056427] [local_costmap.local_costmap]: Activating
[controller_server-2] [INFO] [1794110602.346073707] [local_costmap.local_costmap]: Checking transform
[controller_server-2] [INFO] [1794110602.346195606] [local_costmap.local_costmap]: start
[controller_server-2] [WARN] [1794110602.597015868] [controller_server]: Parameter controller_server.verbose not found
[controller_server-2] [INFO] [1794110602.601893254] [controller_server]: Optimizer reset
[controller_server-2] [INFO] [1794110602.602136306] [MPPIController]: Activated MPPI Controller: FollowPath
[controller_server-2] [INFO] [1794110602.602171197] [controller_server]: Creating bond (controller_server) to lifecycle manager.
[lifecycle_manager-7] [INFO] [1794110602.705728597] [lifecycle_manager_navigation]: Server controller_server connected with bond.
[lifecycle_manager-7] [INFO] [1794110602.705772335] [lifecycle_manager_navigation]: Activating smoother_server
[smoother_server-3] [INFO] [1794110602.706027873] [smoother_server]: Activating
[smoother_server-3] [INFO] [1794110602.706067206] [smoother_server]: Creating bond (smoother_server) to lifecycle manager.
[lifecycle_manager-7] [INFO] [1794110602.809779628] [lifecycle_manager_navigation]: Server smoother_server connected with bond.
[lifecycle_manager-7] [INFO] [1794110602.809827414] [lifecycle_manager_navigation]: Activating behavior_server
[behavior_server-4] [INFO] [1794110602.810321111] [behavior_server]: Activating
[behavior_server-4] [INFO] [1794110602.810358913] [behavior_server]: Activating spin
[behavior_server-4] [INFO] [1794110602.810378962] [behavior_server]: Activating backup
[behavior_server-4] [INFO] [1794110602.810389173] [behavior_server]: Activating drive_on_heading
[behavior_server-4] [INFO] [1794110602.810399246] [behavior_server]: Activating assisted_teleop
[behavior_server-4] [INFO] [1794110602.810409317] [behavior_server]: Activating wait
[behavior_server-4] [INFO] [1794110602.810422649] [behavior_server]: Creating bond (behavior_server) to lifecycle manager.
[lifecycle_manager-7] [INFO] [1794110602.914926729] [lifecycle_manager_navigation]: Server behavior_server connected with bond.
[lifecycle_manager-7] [INFO] [1794110602.915001730] [lifecycle_manager_navigation]: Activating bt_navigator
[bt_navigator-5] [INFO] [1794110602.915396684] [bt_navigator]: Activating
[bt_navigator-5] [INFO] [1794110602.970553124] [bt_navigator]: Creating bond (bt_navigator) to lifecycle manager.
[lifecycle_manager-7] [INFO] [1794110603.074644119] [lifecycle_manager_navigation]: Server bt_navigator connected with bond.
[lifecycle_manager-7] [INFO] [1794110603.074808918] [lifecycle_manager_navigation]: Activating velocity_smoother
[velocity_smoother-6] [INFO] [1794110603.075153878] [velocity_smoother]: Activating
[velocity_smoother-6] [INFO] [1794110603.075228213] [velocity_smoother]: Creating bond (velocity_smoother) to lifecycle manager.
[lifecycle_manager-7] [INFO] [1794110603.180219395] [lifecycle_manager_navigation]: Server velocity_smoother connected with bond.
[lifecycle_manager-7] [INFO] [1794110603.180266077] [lifecycle_manager_navigation]: Managed nodes are active
[lifecycle_manager-7] [INFO] [1794110603.180278797] [lifecycle_manager_navigation]: Creating bond timer...
[bt_navigator-5] [INFO] [1794110673.880917846] [bt_navigator]: Begin navigating from current location (0.00, 0.00) to (-2.73, -1.62)
[planner_server-1] [WARN] [1794110673.881805878] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110673.881857068] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (-2.73, -1.62)
[planner_server-1] [WARN] [1794110673.881873715] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[planner_server-1] [INFO] [1794110673.901552516] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
[planner_server-1] [WARN] [1794110674.192446324] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110674.192510977] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (-2.73, -1.62)
[planner_server-1] [WARN] [1794110674.192527271] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[controller_server-2] [INFO] [1794110674.211257148] [local_costmap.local_costmap]: Received request to clear entirely the local_costmap
[planner_server-1] [INFO] [1794110674.211841864] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
[planner_server-1] [WARN] [1794110675.192549057] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110675.192598388] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (-2.73, -1.62)
[planner_server-1] [WARN] [1794110675.192613671] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[planner_server-1] [INFO] [1794110675.211281801] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
[planner_server-1] [WARN] [1794110676.191861114] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110676.191912975] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (-2.73, -1.62)
[planner_server-1] [WARN] [1794110676.191926978] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[behavior_server-4] [INFO] [1794110676.211749164] [behavior_server]: Running spin
[behavior_server-4] [INFO] [1794110676.211913971] [behavior_server]: Turning 1.57 for spin behavior.
[bt_navigator-5] [INFO] [1794110680.551174466] [bt_navigator]: Received goal preemption request
[bt_navigator-5] [INFO] [1794110680.551377267] [bt_navigator]: Begin navigating from current location (0.00, 0.00) to (0.17, 2.96)
[behavior_server-4] [WARN] [1794110686.212069023] [behavior_server]: Exceeded time allowance before reaching the Spin goal - Exiting Spin
[behavior_server-4] [WARN] [1794110686.212119312] [behavior_server]: spin failed
[behavior_server-4] [WARN] [1794110686.212138118] [behavior_server]: [spin] [ActionServer] Aborting handle.
[behavior_server-4] [INFO] [1794110686.231734491] [behavior_server]: Running wait
[bt_navigator-5] [INFO] [1794110687.221182968] [bt_navigator]: Received goal preemption request
[bt_navigator-5] [INFO] [1794110687.221338961] [bt_navigator]: Begin navigating from current location (0.00, 0.00) to (0.20, 2.96)
[behavior_server-4] [INFO] [1794110691.231948861] [behavior_server]: wait completed successfully
[planner_server-1] [ERROR] [1794110691.261705204] [planner_server]: worldToMap failed: mx,my: 112,126, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261789915] [planner_server]: worldToMap failed: mx,my: 112,127, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261804808] [planner_server]: worldToMap failed: mx,my: 112,128, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261816050] [planner_server]: worldToMap failed: mx,my: 112,129, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261826354] [planner_server]: worldToMap failed: mx,my: 112,130, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261836331] [planner_server]: worldToMap failed: mx,my: 112,131, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261846260] [planner_server]: worldToMap failed: mx,my: 112,132, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261856163] [planner_server]: worldToMap failed: mx,my: 112,133, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261866131] [planner_server]: worldToMap failed: mx,my: 112,134, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261875980] [planner_server]: worldToMap failed: mx,my: 112,135, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261886061] [planner_server]: worldToMap failed: mx,my: 112,136, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261896290] [planner_server]: worldToMap failed: mx,my: 112,137, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261906726] [planner_server]: worldToMap failed: mx,my: 112,138, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261916653] [planner_server]: worldToMap failed: mx,my: 112,139, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261926532] [planner_server]: worldToMap failed: mx,my: 112,140, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261936310] [planner_server]: worldToMap failed: mx,my: 112,141, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261946711] [planner_server]: worldToMap failed: mx,my: 112,142, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261958397] [planner_server]: worldToMap failed: mx,my: 112,143, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261966610] [planner_server]: worldToMap failed: mx,my: 112,144, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110691.261975314] [planner_server]: worldToMap failed: mx,my: 112,145, size_x,size_y: 112,172
[planner_server-1] [WARN] [1794110691.261983381] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110691.261993806] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (0.20, 2.96)
[planner_server-1] [WARN] [1794110691.262004736] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[planner_server-1] [INFO] [1794110691.281296621] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
[planner_server-1] [ERROR] [1794110692.192081960] [planner_server]: worldToMap failed: mx,my: 112,126, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192152926] [planner_server]: worldToMap failed: mx,my: 112,127, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192164798] [planner_server]: worldToMap failed: mx,my: 112,128, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192174098] [planner_server]: worldToMap failed: mx,my: 112,129, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192182634] [planner_server]: worldToMap failed: mx,my: 112,130, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192191444] [planner_server]: worldToMap failed: mx,my: 112,131, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192199890] [planner_server]: worldToMap failed: mx,my: 112,132, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192208509] [planner_server]: worldToMap failed: mx,my: 112,133, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192216917] [planner_server]: worldToMap failed: mx,my: 112,134, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192225216] [planner_server]: worldToMap failed: mx,my: 112,135, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192233630] [planner_server]: worldToMap failed: mx,my: 112,136, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192251804] [planner_server]: worldToMap failed: mx,my: 112,137, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192261884] [planner_server]: worldToMap failed: mx,my: 112,138, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192270457] [planner_server]: worldToMap failed: mx,my: 112,139, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192279005] [planner_server]: worldToMap failed: mx,my: 112,140, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192287192] [planner_server]: worldToMap failed: mx,my: 112,141, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192295700] [planner_server]: worldToMap failed: mx,my: 112,142, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192303820] [planner_server]: worldToMap failed: mx,my: 112,143, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192311999] [planner_server]: worldToMap failed: mx,my: 112,144, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110692.192320106] [planner_server]: worldToMap failed: mx,my: 112,145, size_x,size_y: 112,172
[planner_server-1] [WARN] [1794110692.192327875] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110692.192337706] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (0.20, 2.96)
[planner_server-1] [WARN] [1794110692.192349662] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[behavior_server-4] [INFO] [1794110692.211554868] [behavior_server]: Running backup
[behavior_server-4] [INFO] [1794110692.211694359] [behavior_server]: DriveOnHeading: no acceleration or deceleration limits set
[bt_navigator-5] [INFO] [1794110693.881200192] [bt_navigator]: Received goal preemption request
[bt_navigator-5] [INFO] [1794110693.881361560] [bt_navigator]: Begin navigating from current location (0.00, 0.00) to (-0.01, 2.89)
[bt_navigator-5] [INFO] [1794110700.551184930] [bt_navigator]: Received goal preemption request
[bt_navigator-5] [INFO] [1794110700.551330192] [bt_navigator]: Begin navigating from current location (0.00, 0.00) to (0.20, 2.96)
[behavior_server-4] [WARN] [1794110702.211776449] [behavior_server]: Exceeded time allowance before reaching the DriveOnHeading goal - Exiting DriveOnHeading
[behavior_server-4] [WARN] [1794110702.211831118] [behavior_server]: backup failed
[behavior_server-4] [WARN] [1794110702.211848382] [behavior_server]: [backup] [ActionServer] Aborting handle.
[controller_server-2] [INFO] [1794110702.231366778] [local_costmap.local_costmap]: Received request to clear entirely the local_costmap
[planner_server-1] [INFO] [1794110702.231869883] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
[planner_server-1] [ERROR] [1794110703.192636374] [planner_server]: worldToMap failed: mx,my: 112,126, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192714584] [planner_server]: worldToMap failed: mx,my: 112,127, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192729135] [planner_server]: worldToMap failed: mx,my: 112,128, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192740048] [planner_server]: worldToMap failed: mx,my: 112,129, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192750157] [planner_server]: worldToMap failed: mx,my: 112,130, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192763774] [planner_server]: worldToMap failed: mx,my: 112,131, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192771979] [planner_server]: worldToMap failed: mx,my: 112,132, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192780031] [planner_server]: worldToMap failed: mx,my: 112,133, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192788369] [planner_server]: worldToMap failed: mx,my: 112,134, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192796620] [planner_server]: worldToMap failed: mx,my: 112,135, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192804859] [planner_server]: worldToMap failed: mx,my: 112,136, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192813028] [planner_server]: worldToMap failed: mx,my: 112,137, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192821382] [planner_server]: worldToMap failed: mx,my: 112,138, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192829627] [planner_server]: worldToMap failed: mx,my: 112,139, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192839279] [planner_server]: worldToMap failed: mx,my: 112,140, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192849272] [planner_server]: worldToMap failed: mx,my: 112,141, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192859438] [planner_server]: worldToMap failed: mx,my: 112,142, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192869312] [planner_server]: worldToMap failed: mx,my: 112,143, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192879366] [planner_server]: worldToMap failed: mx,my: 112,144, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110703.192889264] [planner_server]: worldToMap failed: mx,my: 112,145, size_x,size_y: 112,172
[planner_server-1] [WARN] [1794110703.192898891] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110703.192910832] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (0.20, 2.96)
[planner_server-1] [WARN] [1794110703.192924637] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[planner_server-1] [INFO] [1794110703.211265726] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
[planner_server-1] [ERROR] [1794110704.192018717] [planner_server]: worldToMap failed: mx,my: 112,126, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192095219] [planner_server]: worldToMap failed: mx,my: 112,127, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192107792] [planner_server]: worldToMap failed: mx,my: 112,128, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192116316] [planner_server]: worldToMap failed: mx,my: 112,129, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192125330] [planner_server]: worldToMap failed: mx,my: 112,130, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192133581] [planner_server]: worldToMap failed: mx,my: 112,131, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192141705] [planner_server]: worldToMap failed: mx,my: 112,132, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192149787] [planner_server]: worldToMap failed: mx,my: 112,133, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192157930] [planner_server]: worldToMap failed: mx,my: 112,134, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192166098] [planner_server]: worldToMap failed: mx,my: 112,135, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192174362] [planner_server]: worldToMap failed: mx,my: 112,136, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192182625] [planner_server]: worldToMap failed: mx,my: 112,137, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192190772] [planner_server]: worldToMap failed: mx,my: 112,138, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192198814] [planner_server]: worldToMap failed: mx,my: 112,139, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192207035] [planner_server]: worldToMap failed: mx,my: 112,140, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192215044] [planner_server]: worldToMap failed: mx,my: 112,141, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192223597] [planner_server]: worldToMap failed: mx,my: 112,142, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192234187] [planner_server]: worldToMap failed: mx,my: 112,143, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192244320] [planner_server]: worldToMap failed: mx,my: 112,144, size_x,size_y: 112,172
[planner_server-1] [ERROR] [1794110704.192254193] [planner_server]: worldToMap failed: mx,my: 112,145, size_x,size_y: 112,172
[planner_server-1] [WARN] [1794110704.192263332] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110704.192274706] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (0.20, 2.96)
[planner_server-1] [WARN] [1794110704.192288645] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[behavior_server-4] [INFO] [1794110704.211439118] [behavior_server]: Running spin
[behavior_server-4] [INFO] [1794110704.211522571] [behavior_server]: Turning 1.57 for spin behavior.
[bt_navigator-5] [INFO] [1794110707.211123048] [bt_navigator]: Received goal preemption request
[bt_navigator-5] [INFO] [1794110707.211277660] [bt_navigator]: Begin navigating from current location (0.00, 0.00) to (-0.03, 3.16)
[behavior_server-4] [WARN] [1794110714.211714068] [behavior_server]: Exceeded time allowance before reaching the Spin goal - Exiting Spin
[behavior_server-4] [WARN] [1794110714.211759381] [behavior_server]: spin failed
[behavior_server-4] [WARN] [1794110714.211773168] [behavior_server]: [spin] [ActionServer] Aborting handle.
[behavior_server-4] [INFO] [1794110714.231420869] [behavior_server]: Running wait
[behavior_server-4] [INFO] [1794110719.231577899] [behavior_server]: wait completed successfully
[planner_server-1] [WARN] [1794110719.261640516] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110719.261701323] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (-0.03, 3.16)
[planner_server-1] [WARN] [1794110719.261717797] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[planner_server-1] [INFO] [1794110719.281269524] [global_costmap.global_costmap]: Received request to clear entirely the global_costmap
[planner_server-1] [WARN] [1794110720.191982264] [planner_server]: GridBased: failed to create plan with tolerance 0.50.
[planner_server-1] [WARN] [1794110720.192033342] [planner_server]: Planning algorithm GridBased failed to generate a valid path to (-0.03, 3.16)
[planner_server-1] [WARN] [1794110720.192047491] [planner_server]: [compute_path_to_pose] [ActionServer] Aborting handle.
[behavior_server-4] [INFO] [1794110720.211404996] [behavior_server]: Running backup
[bt_navigator-5] [INFO] [1794110720.551119060] [bt_navigator]: Received goal preemption request
[bt_navigator-5] [INFO] [1794110720.551281732] [bt_navigator]: Begin navigating from current location (0.00, 0.00) to (-0.10, 3.08)
[bt_navigator-5] [ERROR] [1794110724.261837350] [bt_navigator_navigate_to_pose_rclcpp_node]: Failed to get result for backup in node halt!
[bt_navigator-5] [INFO] [1794110724.261956149] [bt_navigator]: [navigate_to_pose] [ActionServer] Client requested to cancel the goal. Cancelling.
[bt_navigator-5] [INFO] [1794110724.262015103] [bt_navigator]: Goal canceled
[behavior_server-4] [INFO] [1794110724.311703859] [behavior_server]: Canceling backup
[behavior_server-4] [INFO] [1794110724.311784063] [behavior_server]: [backup] [ActionServer] Client requested to cancel the goal. Cancelling.
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[smoother_server-3] [INFO] [1794110729.199806738] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[smoother_server-3] [INFO] [1794110729.199899509] [smoother_server]: Running Nav2 LifecycleNode rcl preshutdown (smoother_server)
[smoother_server-3] [INFO] [1794110729.199952312] [smoother_server]: Deactivating
[smoother_server-3] [INFO] [1794110729.199974225] [smoother_server]: Destroying bond (smoother_server) to lifecycle manager.
[planner_server-1] [INFO] [1794110729.199806778] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[planner_server-1] [INFO] [1794110729.199879725] [planner_server]: Running Nav2 LifecycleNode rcl preshutdown (planner_server)
[planner_server-1] [INFO] [1794110729.199946023] [planner_server]: Deactivating
[planner_server-1] [INFO] [1794110729.199979911] [global_costmap.global_costmap]: Deactivating
[velocity_smoother-6] [INFO] [1794110729.199829303] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[velocity_smoother-6] [INFO] [1794110729.199905611] [velocity_smoother]: Running Nav2 LifecycleNode rcl preshutdown (velocity_smoother)
[velocity_smoother-6] [INFO] [1794110729.199956663] [velocity_smoother]: Deactivating
[velocity_smoother-6] [INFO] [1794110729.199980160] [velocity_smoother]: Destroying bond (velocity_smoother) to lifecycle manager.
[behavior_server-4] [INFO] [1794110729.200024349] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[behavior_server-4] [INFO] [1794110729.200066490] [behavior_server]: Running Nav2 LifecycleNode rcl preshutdown (behavior_server)
[behavior_server-4] [INFO] [1794110729.200107304] [behavior_server]: Deactivating
[behavior_server-4] [INFO] [1794110729.200140175] [behavior_server]: Destroying bond (behavior_server) to lifecycle manager.
[controller_server-2] [INFO] [1794110729.200294034] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[controller_server-2] [INFO] [1794110729.200386818] [controller_server]: Running Nav2 LifecycleNode rcl preshutdown (controller_server)
[controller_server-2] [INFO] [1794110729.200445646] [controller_server]: Deactivating
[controller_server-2] [INFO] [1794110729.200485240] [MPPIController]: Deactivated MPPI Controller: FollowPath
[controller_server-2] [INFO] [1794110729.200502506] [local_costmap.local_costmap]: Deactivating
[lifecycle_manager-7] [INFO] [1794110729.200572100] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[lifecycle_manager-7] [INFO] [1794110729.200649239] [lifecycle_manager_navigation]: Running Nav2 LifecycleManager rcl preshutdown (lifecycle_manager_navigation)
[lifecycle_manager-7] [INFO] [1794110729.200683810] [lifecycle_manager_navigation]: Terminating bond timer...
[bt_navigator-5] [INFO] [1794110729.200719424] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[bt_navigator-5] [INFO] [1794110729.200756743] [bt_navigator]: Running Nav2 LifecycleNode rcl preshutdown (bt_navigator)
[bt_navigator-5] [INFO] [1794110729.200801801] [bt_navigator]: Deactivating
[bt_navigator-5] [INFO] [1794110729.200827142] [bt_navigator]: Destroying bond (bt_navigator) to lifecycle manager.
[velocity_smoother-6] [INFO] [1794110729.210235870] [velocity_smoother]: Cleaning up
[velocity_smoother-6] [INFO] [1794110729.210311518] [velocity_smoother]: Destroying bond (velocity_smoother) to lifecycle manager.
[behavior_server-4] [INFO] [1794110729.211193456] [behavior_server]: Cleaning up
[smoother_server-3] [INFO] [1794110729.211555849] [smoother_server]: Cleaning up
[bt_navigator-5] [INFO] [1794110729.212575441] [bt_navigator]: Cleaning up
[behavior_server-4] [INFO] [1794110729.217145572] [behavior_server]: Destroying bond (behavior_server) to lifecycle manager.
[velocity_smoother-6] [INFO] [1794110729.219358544] [velocity_smoother]: Destroying
[smoother_server-3] [INFO] [1794110729.224630238] [smoother_server]: Destroying bond (smoother_server) to lifecycle manager.
[smoother_server-3] [INFO] [1794110729.228317050] [smoother_server]: Destroying
[behavior_server-4] [INFO] [1794110729.267407819] [behavior_server]: Destroying
[lifecycle_manager-7] [INFO] [1794110729.284967840] [lifecycle_manager_navigation]: Destroying lifecycle_manager_navigation
[bt_navigator-5] [INFO] [1794110729.308013398] [bt_navigator]: Completed Cleaning up
[bt_navigator-5] [INFO] [1794110729.308072739] [bt_navigator]: Destroying bond (bt_navigator) to lifecycle manager.
[bt_navigator-5] [INFO] [1794110729.314299625] [bt_navigator]: Destroying
[controller_server-2] [INFO] [1794110729.346479030] [controller_server]: Destroying bond (controller_server) to lifecycle manager.
[INFO] [smoother_server-3]: process has finished cleanly [pid 4673]
[INFO] [velocity_smoother-6]: process has finished cleanly [pid 4679]
[controller_server-2] [INFO] [1794110729.356675545] [controller_server]: Cleaning up
[controller_server-2] [INFO] [1794110729.356752314] [MPPIController]: Cleaned up MPPI Controller: FollowPath
[controller_server-2] [INFO] [1794110729.356905590] [local_costmap.local_costmap]: Cleaning up
[controller_server-2] [INFO] [1794110729.365043153] [controller_server]: Destroying bond (controller_server) to lifecycle manager.
[controller_server-2] [INFO] [1794110729.368049345] [local_costmap.local_costmap]: Destroying
[controller_server-2] [INFO] [1794110729.373554323] [controller_server]: Destroying
[INFO] [behavior_server-4]: process has finished cleanly [pid 4675]
[INFO] [lifecycle_manager-7]: process has finished cleanly [pid 4681]
[INFO] [bt_navigator-5]: process has finished cleanly [pid 4677]
[INFO] [controller_server-2]: process has finished cleanly [pid 4671]
[planner_server-1] [INFO] [1794110730.189398408] [planner_server]: Deactivating plugin GridBased of type NavfnPlanner
[planner_server-1] [INFO] [1794110730.189461071] [planner_server]: Destroying bond (planner_server) to lifecycle manager.
[planner_server-1] [INFO] [1794110730.199763922] [planner_server]: Cleaning up
[planner_server-1] [INFO] [1794110730.204125247] [global_costmap.global_costmap]: Cleaning up
[planner_server-1] [INFO] [1794110730.205798677] [planner_server]: Cleaning up plugin GridBased of type NavfnPlanner
[planner_server-1] [INFO] [1794110730.205929247] [planner_server]: Destroying plugin GridBased of type NavfnPlanner
[planner_server-1] [INFO] [1794110730.209226281] [planner_server]: Destroying bond (planner_server) to lifecycle manager.
[planner_server-1] [INFO] [1794110730.211135125] [global_costmap.global_costmap]: Destroying
[planner_server-1] [INFO] [1794110730.215908659] [planner_server]: Destroying
[INFO] [planner_server-1]: process has finished cleanly [pid 4669]
lin@lin-Default-string:~$ 

lin@lin-Default-string:~$ ros2 run tf2_ros tf2_echo base_link base_laser
[INFO] [1794110509.962703158] [tf2_echo]: Waiting for transform base_link ->  base_laser: Invalid frame ID "base_link" passed to canTransform argument target_frame - frame does not exist
At time 0.0
- Translation: [0.000, 0.000, 0.180]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.180
  0.000  0.000  0.000  1.000
At time 0.0
- Translation: [0.000, 0.000, 0.180]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.180
  0.000  0.000  0.000  1.000
At time 0.0
- Translation: [0.000, 0.000, 0.180]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.180
  0.000  0.000  0.000  1.000
At time 0.0
- Translation: [0.000, 0.000, 0.180]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.180
  0.000  0.000  0.000  1.000
^C[INFO] [1794110514.321126655] [rclcpp]: signal_handler(SIGINT/SIGTERM)
lin@lin-Default-string:~$ ros2 run tf2_ros tf2_echo odom base_link   
[INFO] [1794110528.329253366] [tf2_echo]: Waiting for transform odom ->  base_link: Invalid frame ID "odom" passed to canTransform argument target_frame - frame does not exist
At time 0.0
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 0.0
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 0.0
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 0.0
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
^C[INFO] [1794110532.622149585] [rclcpp]: signal_handler(SIGINT/SIGTERM)
lin@lin-Default-string:~$ source /opt/ros/humble/setup.bash
lin@lin-Default-string:~$ source ~/Lin_workspace/r2_integration/install/setup.bash
source ~/Lin_workspace/explore_ws/install/setup.bash
ros2 run explore_lite explore --ros-args \
  --params-file $HOME/Lin_workspace/r2_integration/install/r2_bringup/share/r2_bringup/config/explore_params.yaml
[INFO] [1794110671.856543874] [explore_node]: Waiting for costmap to become available, topic: /global_costmap/costmap
[INFO] [1794110673.877181122] [explore_node]: Waiting to connect to move_base nav2 server
[INFO] [1794110673.877406749] [explore_node]: Connected to move_base nav2 server
^C[INFO] [1794110724.239228342] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[INFO] [1794110724.239413379] [explore_node]: Exploration stopped.
lin@lin-Default-string:~$ 

lin@lin-Default-string:~$ ros2 run tf2_ros tf2_echo map odom 
[INFO] [1794110554.752014001] [tf2_echo]: Waiting for transform map ->  odom: Invalid frame ID "map" passed to canTransform argument target_frame - frame does not exist
At time 1794110555.855863966
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110556.855753452
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110557.855867679
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110558.855842527
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110559.855864422
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110560.855864735
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110561.855862670
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110562.855868765
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110563.855866084
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110564.855708826
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
At time 1794110565.855707790
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
- Rotation: in RPY (radian) [0.000, -0.000, 0.000]
- Rotation: in RPY (degree) [0.000, -0.000, 0.000]
- Matrix:
  1.000  0.000  0.000  0.000
  0.000  1.000  0.000  0.000
  0.000  0.000  1.000  0.000
  0.000  0.000  0.000  1.000
^C[INFO] [1794110566.117824825] [rclcpp]: signal_handler(SIGINT/SIGTERM)
lin@lin-Default-string:~$ ros2 topic echo /map --qos-durability transient_local --field info 
map_load_time:
  sec: 0
  nanosec: 0
resolution: 0.05000000074505806
width: 112
height: 172
origin:
  position:
    x: -4.926224923247754
    y: -3.8331794873772087
    z: 0.0
  orientation:
    x: 0.0
    y: 0.0
    z: 0.0
    w: 1.0
---
map_load_time:
  sec: 0
  nanosec: 0
resolution: 0.05000000074505806
width: 112
height: 172
origin:
  position:
    x: -4.926224923247754
    y: -3.8331794873772087
    z: 0.0
  orientation:
    x: 0.0
    y: 0.0
    z: 0.0
    w: 1.0
---
^Clin@lin-Default-string:~$ 
lin@lin-Default-string:~$ ros2 lifecycle get /planner_server 
active [3]
lin@lin-Default-string:~$ ros2 lifecycle get /controller_server
active [3]
lin@lin-Default-string:~$ ros2 lifecycle get /bt_navigator
active [3]
lin@lin-Default-string:~$ ros2 topic echo /global_costmap/costmap --field info 
map_load_time:
  sec: 0
  nanosec: 0
resolution: 0.05000000074505806
width: 112
height: 172
origin:
  position:
    x: -4.926224923247754
    y: -3.8331794873772087
    z: 0.0
  orientation:
    x: 0.0
    y: 0.0
    z: 0.0
    w: 1.0
---
^Clin@lin-Default-string:~ros2 param get /explore_node planner_frequency y 
Double value is: 0.15
lin@lin-Default-string:~$ ros2 node list | grep -i explore 
/explore_node
lin@lin-Default-string:~$ ps aux | grep -iE "ldlidar|slam_toolbox|nav2|explore|static_transform" | grep -v grep
lin@lin-Default-string:~$ ros2 node list
lin@lin-Default-string:~$ 
