![[Pasted image 20260512162742.png]]
![[Pasted image 20260512163117.png]]

## 第二次尝试出现问题

https://chatgpt.com/c/6a02e0b6-eb00-83ec-a5ca-ad3438d93f43

###  虚拟机&windows以太网设置问题

#### 若虚拟机为桥接模式，则windows-以太网ip可以不管，虚拟机为与windows并列。
#### 但是vmware内浏览器卡顿，还是windows启用，专门 http://10.10.3.6/ 修改参数较好

1. 意外修改了ip,host ip ，还好没改动gateway ip,不然可能导致机器失效（ip混乱）
2. 当前参数保存![[Pasted image 20260514121520.png]]

### vmware设置

#### wireshark抓包

sudo wireshark


1. ip a查询当前ens37，桥接下ip 
2. 清理ens37
	1. sudo ip addr flush dev ens37
	2. sudo ip addr add 10.10.3.30/24 dev ens37
	3. sudo ip link set ens37 up
3. ip a确认

wireshark显示（长时间后，这里的笔记是后补的）
![[Pasted image 20260514123002.png]]

#### 直接启动launch读取ip，实际并非默认的ip,且更新传参无效
```
lin@lin-virtual-machine:~$ ros2 launch velodyne_driver velodyne_driver_node-VLP16-launch.py [INFO] [launch]: All log files can be found below /home/lin/.ros/log/2026-05-14-11-59-02-414089-lin-virtual-machine-4405 [INFO] [launch]: Default logging verbosity is set to INFO [INFO] [velodyne_driver_node-1]: process started with pid [4406] [velodyne_driver_node-1] [INFO] [1778731142.509699690] [velodyne_driver_node]: Velodyne VLP-16 rotating at 600.000000 RPM [velodyne_driver_node-1] [INFO] [1778731142.509781420] [velodyne_driver_node]: publishing 76 packets per scan [velodyne_driver_node-1] [INFO] [1778731142.509788317] [velodyne_driver_node]: Cut at specific angle feature deactivated. [velodyne_driver_node-1] [INFO] [1778731142.509791991] [velodyne_driver_node]: expected frequency: 9.921 (Hz) [velodyne_driver_node-1] [INFO] [1778731142.509813599] [velodyne_driver_node]: Only accepting packets from IP address: 192.168.1.201 [velodyne_driver_node-1] [INFO] [1778731142.509821748] [velodyne_driver_node]: Opening UDP socket: port 2368
```
#### 因为传递参数问题，选择这个指令

启动指令
```
ros2 run velodyne_driver velodyne_driver_node \
  --ros-args \
  -p device_ip:=10.10.3.6 \
  -p frame_id:=velodyne \
  -p model:=VLP16
```
反馈
```
lin@lin-virtual-machine:~$ ros2 run velodyne_driver velodyne_driver_node \
  --ros-args \
  -p device_ip:=10.10.3.6 \
  -p frame_id:=velodyne \
  -p model:=VLP16
[INFO] [1778731677.546450248] [velodyne_driver_node]: Velodyne VLP-16 rotating at 600.000000 RPM
[INFO] [1778731677.546527629] [velodyne_driver_node]: publishing 76 packets per scan
[INFO] [1778731677.546548616] [velodyne_driver_node]: Cut at specific angle feature deactivated.
[INFO] [1778731677.546558010] [velodyne_driver_node]: expected frequency: 9.921 (Hz)
[INFO] [1778731677.546579406] [velodyne_driver_node]: Only accepting packets from IP address: 10.10.3.6
[INFO] [1778731677.546601594] [velodyne_driver_node]: Opening UDP socket: port 2368

```

transform指令
```
ros2 launch velodyne_pointcloud velodyne_transform_node-VLP16-launch.py
```
反馈
```
lin@lin-virtual-machine:~$ ros2 launch velodyne_pointcloud velodyne_transform_node-VLP16-launch.py
[INFO] [launch]: All log files can be found below /home/lin/.ros/log/2026-05-14-12-08-07-567087-lin-virtual-machine-3687
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [velodyne_transform_node-1]: process started with pid [3688]
[velodyne_transform_node-1] [INFO] [1778731687.624293080] [velodyne_transform_node]: correction angles: /opt/ros/humble/share/velodyne_pointcloud/params/VLP16db.yaml
[velodyne_transform_node-1] 0.000 2.304 4.608 6.912 9.216 11.520 13.824 16.128 18.432 20.736 23.040 25.344 27.648 29.952 32.256 34.560 55.296 57.600 59.904 62.208 64.512 66.816 69.120 71.424 73.728 76.032 78.336 80.640 82.944 85.248 87.552 89.856 
[velodyne_transform_node-1] 110.592 112.896 115.200 117.504 119.808 122.112 124.416 126.720 129.024 131.328 133.632 135.936 138.240 140.544 142.848 145.152 165.888 168.192 170.496 172.800 175.104 177.408 179.712 182.016 184.320 186.624 188.928 191.232 193.536 195.840 198.144 200.448 
[velodyne_transform_node-1] 221.184 223.488 225.792 228.096 230.400 232.704 235.008 237.312 239.616 241.920 244.224 246.528 248.832 251.136 253.440 255.744 276.480 278.784 281.088 283.392 285.696 288.000 290.304 292.608 294.912 297.216 299.520 301.824 304.128 306.432 308.736 311.040 
[velodyne_transform_node-1] 331.776 334.080 336.384 338.688 340.992 343.296 345.600 347.904 350.208 352.512 354.816 357.120 359.424 361.728 364.032 366.336 387.072 389.376 391.680 393.984 396.288 398.592 400.896 403.200 405.504 407.808 410.112 412.416 414.720 417.024 419.328 421.632 
[velodyne_transform_node-1] 442.368 444.672 446.976 449.280 451.584 453.888 456.192 458.496 460.800 463.104 465.408 467.712 470.016 472.320 474.624 476.928 497.664 499.968 502.272 504.576 506.880 509.184 511.488 513.792 516.096 518.400 520.704 523.008 525.312 527.616 529.920 532.224 
[velodyne_transform_node-1] 552.960 555.264 557.568 559.872 562.176 564.480 566.784 569.088 571.392 573.696 576.000 578.304 580.608 582.912 585.216 587.520 608.256 610.560 612.864 615.168 617.472 619.776 622.080 624.384 626.688 628.992 631.296 633.600 635.904 638.208 640.512 642.816 
[velodyne_transform_node-1] 663.552 665.856 668.160 670.464 672.768 675.072 677.376 679.680 681.984 684.288 686.592 688.896 691.200 693.504 695.808 698.112 718.848 721.152 723.456 725.760 728.064 730.368 732.672 734.976 737.280 739.584 741.888 744.192 746.496 748.800 751.104 753.408 
[velodyne_transform_node-1] 774.144 776.448 778.752 781.056 783.360 785.664 787.968 790.272 792.576 794.880 797.184 799.488 801.792 804.096 806.400 808.704 829.440 831.744 834.048 836.352 838.656 840.960 843.264 845.568 847.872 850.176 852.480 854.784 857.088 859.392 861.696 864.000 
[velodyne_transform_node-1] 884.736 887.040 889.344 891.648 893.952 896.256 898.560 900.864 903.168 905.472 907.776 910.080 912.384 914.688 916.992 919.296 940.032 942.336 944.640 946.944 949.248 951.552 953.856 956.160 958.464 960.768 963.072 965.376 967.680 969.984 972.288 974.592 
[velodyne_transform_node-1] 995.328 997.632 999.936 1002.240 1004.544 1006.848 1009.152 1011.456 1013.760 1016.064 1018.368 1020.672 1022.976 1025.280 1027.584 1029.888 1050.624 1052.928 1055.232 1057.536 1059.840 1062.144 1064.448 1066.752 1069.056 1071.360 1073.664 1075.968 1078.272 1080.576 1082.880 1085.184 
[velodyne_transform_node-1] 1105.920 1108.224 1110.528 1112.832 1115.136 1117.440 1119.744 1122.048 1124.352 1126.656 1128.960 1131.264 1133.568 1135.872 1138.176 1140.480 1161.216 1163.520 1165.824 1168.128 1170.432 1172.736 1175.040 1177.344 1179.648 1181.952 1184.256 1186.560 1188.864 1191.168 1193.472 1195.776 
[velodyne_transform_node-1] 1216.512 1218.816 1221.120 1223.424 1225.728 1228.032 1230.336 1232.640 1234.944 1237.248 1239.552 1241.856 1244.160 1246.464 1248.768 1251.072 1271.808 1274.112 1276.416 1278.720 1281.024 1283.328 1285.632 1287.936 1290.240 1292.544 1294.848 1297.152 1299.456 1301.760 1304.064 1306.368 
[velodyne_transform_node-1] [WARN] [1778731687.626137960] [velodyne_pointcloud]: No Azimuth Cache configured for model VLP16


```

#### 打开rviz2
frame，手动输入velodyne
add->topic->pointclaud2

结果![[Pasted image 20260514122656.png]]

现在的topic
```
lin@lin-virtual-machine:~$ ros2 topic list 
/clicked_point
/diagnostics
/goal_pose
/initialpose
/parameter_events
/rosout
/tf
/tf_static
/velodyne_packets
/velodyne_points
lin@lin-virtual-machine:~$ 
```

## 尝试kiss-icp
### 当前仓库为clone下来的，如果想要撤销更改，可以直接

cd ~/Lin_workspace/vlp16_slam_ws/src/kiss-icp
git checkout ros/config/config.yaml

#### 查看更改了什么
cd ~/Lin_workspace/vlp16_slam_ws/src/kiss-icp
git diff ros/config/config.yaml

giff
```
in@lin-virtual-machine:~/Lin_workspace/vlp16_slam_ws/src/kiss-icp$ git diff ros/config/config.yaml
diff --git a/ros/config/config.yaml b/ros/config/config.yaml
index f7281f0..59022a8 100644
--- a/ros/config/config.yaml
+++ b/ros/config/config.yaml
@@ -17,11 +17,11 @@ kiss_icp_node:
 
     data:
       deskew: True
-      max_range: 100.0
-      min_range: 0.0
+      max_range: 30.0
+      min_range: 1.5
 
     mapping:
-      # voxel_size: 1.0 # <- optional, default = max_range / 100.0
+      voxel_size: 0.2 # <- optional, default = max_range / 100.0
       max_points_per_voxel: 20
 
     adaptive_threshold:

```

#### 启动
ros2 launch kiss_icp odometry.launch.py     topic:=/velodyne_points     odom_frame:=odom     child_frame:=velodyne     visualize:=false


ros2 topic hz /velodyne_points

source ~/.bashrc
rviz2


尝试decay time,（停留时间，开2就很好，10非常卡），感受slam（非）

![[Pasted image 20260514133447.png]]
长时间启动后，动作过的物体都会被标记为白点（也就是墙）![[Pasted image 20260514155621.png]]

新开终端，运行ros2 service call /kiss/reset std_srvs/srv/Empty {}，可以清理白点
```
lin@lin-virtual-machine:~$ ros2 service call /kiss/reset std_srvs/srv/Empty {}
requester: making request: std_srvs.srv.Empty_Request()

response:
std_srvs.srv.Empty_Response()

lin@lin-virtual-machine:~$ 
```

## 第三次（2026-08-02）：交换机接入方案 ✅

之前的 10.10.3.x 直连方案废弃，现在雷达经交换机接入 VMware，链路已通（tcpdump 可见大量 2368 包）。

### 链路

```
VLP-16 ──RJ45── 交换机（无 VLAN，管理 IP 10.18.18.251，勿改）
    ──RJ45── Windows 宿主机有线网口
    ──VMware 桥接── 虚拟机 ens37（静态 10.18.18.30/24）
```

### 雷达网页配置（当前生效）

| 项 | 值 |
|:---|:---|
| Sensor (Network) IP | 10.18.18.6 / 255.255.255.0 |
| Host (Destination) IP | 10.18.18.30（= ens37 静态地址，单播直达） |
| Gateway | 10.18.18.1（同网段直发用不到） |
| Data Port / Telemetry | 2368 / 8308 |
| DHCP | Off |

虚拟机：ens33 = 192.168.1.204/24（公司网），ens37 = 10.18.18.30/24（雷达网，静态，网关留空）。

### 经验

1. **网页改配置后必须 Save + 重启雷达才生效**（写 NVRAM，重启才应用并重建网络栈，顺带清 ARP 缓存）
2. 换接收端 MAC 收不到 → 断电重启雷达清 ARP 固化缓存
3. VMware 桥接要手动指定桥接到宿主机**有线网口**，不要"自动"
4. 雷达独立网段与公司网隔离，广播不骚扰局域网

### 启动（两终端）

```
# 终端 1：驱动
ros2 run velodyne_driver velodyne_driver_node --ros-args \
  -p device_ip:=10.18.18.6 \
  -p frame_id:=velodyne \
  -p model:=VLP16

# 终端 2：点云转换
ros2 run velodyne_pointcloud velodyne_transform_node --ros-args \
  -p calibration:=/opt/ros/humble/share/velodyne_pointcloud/params/VLP16db.yaml \
  -p model:=VLP16 \
  -p frame_id:=velodyne \
  -p fixed_frame:=velodyne

# 验证
ros2 topic hz /velodyne_points     # ~10Hz
sudo tcpdump -i ens37 udp port 2368 -n -c 10
```

完整一键 launch（driver + transform + laserscan）：`/home/lin/.ros/velodyne_n97.launch.py`（其中 device_ip 需改为 10.18.18.6）

