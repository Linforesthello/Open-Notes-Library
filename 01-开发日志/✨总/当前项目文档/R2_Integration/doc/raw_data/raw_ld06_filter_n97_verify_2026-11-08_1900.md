# N97 LD06 自车回波过滤链（方案 B）实车验证原始数据

> 日期时间：2026-11-08 18:53 ~ 19:00（N97 本机时间）
> session 话题：老车 S1 explore 零前沿（LD06 低装自车遮挡）→ 方案 B 激光滤波链 N97 实车验证
> 来源：① 用户终端粘贴（18:53 首次启动）；② VM 经 SSH 在 N97（192.168.1.210，lin-Default-string）执行
> 相关：commit e82bc39（代码）｜[sensor-mount §6.1.2](../phase0/sensor-mount.md)｜[s1-readiness-gap G24](../old-car/s1-readiness-gap.md)
> 本地留档，不入 git

---

## 一、用户首次启动（18:53，用户终端）

```text
$ source ~/Lin_workspace/r2_integration/install/setup.bash
$ ros2 launch ldlidar_stl_ros2 ld06.launch.py
[INFO] [launch]: All log files can be found below /home/lin/.ros/log/2026-11-08-18-53-07-266529-lin-Default-string-7526
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [ldlidar_stl_ros2_node-1]: process started with pid [7527]
[INFO] [static_transform_publisher-2]: process started with pid [7529]
[INFO] [scan_to_scan_filter_chain-3]: process started with pid [7531]
[static_transform_publisher-2] [WARN] [1794135187.324620321] []: Old-style arguments are deprecated; see --help for new-style arguments
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339492349] [LD06]: LDLiDAR SDK Pack Version is: v3.0.3
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339601461] [LD06]: <product_name>: LDLiDAR_LD06
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339616870] [LD06]: <topic_name>: scan_raw
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339626211] [LD06]: <frame_id>: base_laser
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339634688] [LD06]: <port_name>: /dev/r2_ld06_a
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339642974] [LD06]: <port_baudrate>: 230400
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339651394] [LD06]: <laser_scan_dir>: Counterclockwise
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339660187] [LD06]: <enable_angle_crop_func>: false
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339668737] [LD06]: <angle_crop_min>: 135.000000
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.339682693] [LD06]: <angle_crop_max>: 225.000000
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.340029671] [LD06]: ldlidar node start is success
[static_transform_publisher-2] [INFO] [1794135187.343772583] [base_link_to_base_laser_ld06]: Spinning until stopped - publishing transform
[static_transform_publisher-2] translation: ('0.275000', '0.290000', '0.040000')
[static_transform_publisher-2] rotation: ('0.000000', '0.000000', '-0.707108', '0.707105')
[static_transform_publisher-2] from 'base_link' to 'base_laser'
[scan_to_scan_filter_chain-3] [WARN] [1794135187.345269616] [rcl.logging_rosout]: Publisher already registered for provided node name. If this is due to multiple nodes with the same name then all logs for that logger name will go out over the existing publisher. As soon as any node with that name is destructed it will unregister the publisher, preventing any further logs for that name from being published on the rosout topic.
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.350620512] [LD06]: ldlidar communication is normal.
[ldlidar_stl_ros2_node-1] [INFO] [1794135187.352142328] [LD06]: Publish topic message:ldlidar scan data.
[scan_to_scan_filter_chain-3] [WARN] [1794135188.343246023] [scan_to_scan_filter_chain]: diagnostic_updater: No HW_ID was set. This is probably a bug. Please report it. For devices that do not have a HW_ID, set this value to 'none'. This warning only occurs once all diagnostics are OK. It is okay to wait until the device is open before calling setHardwareID.
[ldlidar_stl_ros2_node-1] [LDS][INFO][1794135187.339942136][Actual BaudRate reported:230400]

$ ros2 topic hz /scan_raw
average rate: 10.000
	min: 0.100s max: 0.100s std dev: 0.00004s window: 11
average rate: 10.000
	min: 0.100s max: 0.100s std dev: 0.00007s window: 21
average rate: 10.000
	min: 0.100s max: 0.100s std dev: 0.00007s window: 31
average rate: 10.000
	min: 0.100s max: 0.100s std dev: 0.00007s window: 42

$ ros2 topic info /scan
Type: sensor_msgs/msg/LaserScan
Publisher count: 1
Subscription count: 0
```

---

## 二、/scan 发布者身份确认（18:57，SSH）

```text
=== identity ===
lin-Default-string
2026-11-08 18:57:14
=== bashrc DDS vars ===
(none)
=== env DDS vars ===
(none)
=== topic info /scan --verbose ===
Type: sensor_msgs/msg/LaserScan

Publisher count: 1

Node name: scan_to_scan_filter_chain
Node namespace: /
Topic type: sensor_msgs/msg/LaserScan
Endpoint type: PUBLISHER
GID: 01.0f.99.fd.b8.1d.92.bb.00.00.00.00.00.00.32.03.00.00.00.00.00.00.00.00
QoS profile:
  Reliability: RELIABLE
  History (Depth): UNKNOWN
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 0

=== topic info /scan_raw ===
Type: sensor_msgs/msg/LaserScan
Publisher count: 1
Subscription count: 1
```

> 注：此处 `ros2 topic info` 由本机 daemon 答复；同一时刻用户的 launch 已被 Ctrl-C。

---

## 三、第 1 次计数（SSH 重启 launch，18:58）

```text
--- 结果（N97 实机，LD06 实扫）---
/scan_raw body=132 (31.8% of valid) padded=132 valid=415 nan= 39 zero/inf=  0 total=454
/scan     body=  2 ( 0.7% of valid) padded=  2 valid=285 nan=169 zero/inf=  0 total=454
frame_id=base_laser  angle_min=0.0000  inc=0.01387  range=[0.02, 25.00]
--- launch log tail ---
[ldlidar_stl_ros2_node-1] [INFO] [1794135529.391382943] [LD06]: ldlidar node start is success
[static_transform_publisher-2] [INFO] [1794135529.394212074] [base_link_to_base_laser_ld06]: Spinning until stopped - publishing transform
[static_transform_publisher-2] translation: ('0.275000', '0.290000', '0.040000')
[static_transform_publisher-2] rotation: ('0.000000', '0.000000', '-0.707108', '0.707105')
[static_transform_publisher-2] from 'base_link' to 'base_laser'
[ldlidar_stl_ros2_node-1] [INFO] [1794135529.396983227] [LD06]: ldlidar communication is normal.
--- 残留检查 ---
(clean)
```

判定：车身矩形（±0.40/±0.30）内有效波束 **132 → 2**；新增 NaN 130 个 = 被滤掉的车体回波数。

---

## 四、第 2 次计数：残留逐点定位（SSH 重启 launch，19:00）

`/scan` 残留 3 束，全部为 **range < range_min(0.02 m)** 的雷达自身窗口回波：

```text
=== /scan_raw : padded-box hits = 129 ===
  idx=  0 ang=   0.00deg r=0.326  x_link=+0.275 y_link=-0.036  core=True
  idx=  1 ang=   0.79deg r=0.326  x_link=+0.280 y_link=-0.036  core=True
  idx=  3 ang=   2.38deg r=0.364  x_link=+0.290 y_link=-0.074  core=True
  idx=  4 ang=   3.18deg r=0.341  x_link=+0.294 y_link=-0.050  core=True
  idx=  5 ang=   3.97deg r=0.131  x_link=+0.284 y_link=+0.159  core=True
  idx=  6 ang=   4.77deg r=0.102  x_link=+0.283 y_link=+0.188  core=True
  idx=  7 ang=   5.56deg r=0.079  x_link=+0.283 y_link=+0.211  core=True
  idx=  8 ang=   6.36deg r=0.049  x_link=+0.280 y_link=+0.241  core=True
  idx=  9 ang=   7.15deg r=0.026  x_link=+0.278 y_link=+0.264  core=True
  idx= 10 ang=   7.95deg r=0.019  x_link=+0.278 y_link=+0.271  core=True
  idx= 11 ang=   8.74deg r=0.024  x_link=+0.279 y_link=+0.266  core=True
  idx= 12 ang=   9.54deg r=0.015  x_link=+0.277 y_link=+0.275  core=True
  idx= 13 ang=  10.33deg r=0.017  x_link=+0.278 y_link=+0.273  core=True
  idx= 14 ang=  11.13deg r=0.021  x_link=+0.279 y_link=+0.269  core=True
  idx= 15 ang=  11.92deg r=0.029  x_link=+0.281 y_link=+0.262  core=True
  idx= 16 ang=  12.72deg r=0.044  x_link=+0.285 y_link=+0.247  core=True
  idx= 17 ang=  13.51deg r=0.054  x_link=+0.288 y_link=+0.237  core=True
  idx= 18 ang=  14.30deg r=0.075  x_link=+0.294 y_link=+0.217  core=True
  idx= 19 ang=  15.10deg r=0.079  x_link=+0.296 y_link=+0.214  core=True
  idx= 20 ang=  15.89deg r=0.087  x_link=+0.299 y_link=+0.206  core=True
  idx= 21 ang=  16.69deg r=0.103  x_link=+0.305 y_link=+0.191  core=True
  idx= 22 ang=  17.48deg r=0.115  x_link=+0.310 y_link=+0.180  core=True
  idx= 23 ang=  18.28deg r=0.120  x_link=+0.313 y_link=+0.176  core=True
  idx= 24 ang=  19.07deg r=0.130  x_link=+0.317 y_link=+0.167  core=True
  idx= 341 ang= 270.99deg r=0.200  x_link=+0.075 y_link=+0.287  core=True
  idx= 342 ang= 271.79deg r=0.196  x_link=+0.079 y_link=+0.284  core=True
  idx= 343 ang= 272.58deg r=0.187  x_link=+0.088 y_link=+0.282  core=True
  idx= 344 ang= 273.38deg r=0.184  x_link=+0.091 y_link=+0.279  core=True
  idx= 345 ang= 274.17deg r=0.179  x_link=+0.096 y_link=+0.277  core=True
  idx= 346 ang= 274.97deg r=0.169  x_link=+0.107 y_link=+0.275  core=True
  idx= 347 ang= 275.76deg r=0.163  x_link=+0.113 y_link=+0.274  core=True
  idx= 348 ang= 276.56deg r=0.167  x_link=+0.109 y_link=+0.271  core=True
  idx= 349 ang= 277.35deg r=0.175  x_link=+0.101 y_link=+0.268  core=True
  idx= 350 ang= 278.15deg r=0.344  x_link=-0.066 y_link=+0.241  core=True
  idx= 351 ang= 278.94deg r=0.362  x_link=-0.083 y_link=+0.234  core=True
  idx= 352 ang= 279.74deg r=0.383  x_link=-0.102 y_link=+0.225  core=True
  idx= 353 ang= 280.53deg r=0.379  x_link=-0.098 y_link=+0.221  core=True
  idx= 354 ang= 281.32deg r=0.371  x_link=-0.089 y_link=+0.217  core=True
  idx= 355 ang= 282.12deg r=0.295  x_link=-0.013 y_link=+0.228  core=True
  idx= 356 ang= 282.91deg r=0.280  x_link=+0.002 y_link=+0.227  core=True
  idx= 357 ang= 283.71deg r=0.280  x_link=+0.003 y_link=+0.224  core=True
  idx= 358 ang= 284.50deg r=0.280  x_link=+0.004 y_link=+0.220  core=True
  idx= 359 ang= 285.30deg r=0.341  x_link=-0.054 y_link=+0.200  core=True
  idx= 360 ang= 286.09deg r=0.400  x_link=-0.109 y_link=+0.179  core=True
  idx= 361 ang= 286.89deg r=0.412  x_link=-0.119 y_link=+0.170  core=True
  idx= 362 ang= 287.68deg r=0.409  x_link=-0.115 y_link=+0.166  core=True
  idx= 363 ang= 288.48deg r=0.416  x_link=-0.120 y_link=+0.158  core=True
  idx= 364 ang= 289.27deg r=0.416  x_link=-0.118 y_link=+0.153  core=True
  idx= 368 ang= 292.45deg r=0.186  x_link=+0.103 y_link=+0.219  core=True
  idx= 369 ang= 293.25deg r=0.182  x_link=+0.108 y_link=+0.218  core=True
  idx= 370 ang= 294.04deg r=0.174  x_link=+0.116 y_link=+0.219  core=True
  idx= 371 ang= 294.83deg r=0.173  x_link=+0.118 y_link=+0.217  core=True
  idx= 372 ang= 295.63deg r=0.171  x_link=+0.121 y_link=+0.216  core=True
  idx= 373 ang= 296.42deg r=0.167  x_link=+0.125 y_link=+0.216  core=True
  idx= 374 ang= 297.22deg r=0.160  x_link=+0.133 y_link=+0.217  core=True
  idx= 375 ang= 298.01deg r=0.160  x_link=+0.134 y_link=+0.215  core=True
  idx= 376 ang= 298.81deg r=0.160  x_link=+0.135 y_link=+0.213  core=True
  idx= 377 ang= 299.60deg r=0.160  x_link=+0.136 y_link=+0.211  core=True
  idx= 378 ang= 300.40deg r=0.160  x_link=+0.137 y_link=+0.209  core=True
  idx= 379 ang= 301.19deg r=0.160  x_link=+0.138 y_link=+0.207  core=True
  idx= 380 ang= 301.99deg r=0.160  x_link=+0.139 y_link=+0.205  core=True
  idx= 381 ang= 302.78deg r=0.160  x_link=+0.140 y_link=+0.203  core=True
  idx= 382 ang= 303.58deg r=0.160  x_link=+0.142 y_link=+0.202  core=True
  idx= 383 ang= 304.37deg r=0.160  x_link=+0.143 y_link=+0.200  core=True
  idx= 384 ang= 305.17deg r=0.161  x_link=+0.143 y_link=+0.197  core=True
  idx= 385 ang= 305.96deg r=0.163  x_link=+0.143 y_link=+0.194  core=True
  idx= 386 ang= 306.75deg r=0.167  x_link=+0.141 y_link=+0.190  core=True
  idx= 387 ang= 307.55deg r=0.175  x_link=+0.136 y_link=+0.183  core=True
  idx= 388 ang= 308.34deg r=0.175  x_link=+0.138 y_link=+0.181  core=True
  idx= 389 ang= 309.14deg r=0.175  x_link=+0.139 y_link=+0.180  core=True
  idx= 390 ang= 309.93deg r=0.176  x_link=+0.140 y_link=+0.177  core=True
  idx= 391 ang= 310.73deg r=0.178  x_link=+0.140 y_link=+0.174  core=True
  idx= 392 ang= 311.52deg r=0.182  x_link=+0.139 y_link=+0.169  core=True
  idx= 393 ang= 312.32deg r=0.190  x_link=+0.135 y_link=+0.162  core=True
  idx= 394 ang= 313.11deg r=0.190  x_link=+0.136 y_link=+0.160  core=True
  idx= 395 ang= 313.91deg r=0.191  x_link=+0.137 y_link=+0.158  core=True
  idx= 396 ang= 314.70deg r=0.193  x_link=+0.138 y_link=+0.154  core=True
  idx= 397 ang= 315.50deg r=0.197  x_link=+0.137 y_link=+0.149  core=True
  idx= 398 ang= 316.29deg r=0.205  x_link=+0.133 y_link=+0.142  core=True
  idx= 399 ang= 317.09deg r=0.285  x_link=+0.081 y_link=+0.081  core=True
  idx= 400 ang= 317.88deg r=0.291  x_link=+0.080 y_link=+0.074  core=True
  idx= 401 ang= 318.68deg r=0.302  x_link=+0.076 y_link=+0.063  core=True
  idx= 402 ang= 319.47deg r=0.309  x_link=+0.074 y_link=+0.055  core=True
  idx= 403 ang= 320.26deg r=0.308  x_link=+0.078 y_link=+0.053  core=True
  idx= 404 ang= 321.06deg r=0.302  x_link=+0.085 y_link=+0.055  core=True
  idx= 405 ang= 321.85deg r=0.295  x_link=+0.093 y_link=+0.058  core=True
  idx= 406 ang= 322.65deg r=0.280  x_link=+0.105 y_link=+0.067  core=True
  idx= 407 ang= 323.44deg r=0.280  x_link=+0.108 y_link=+0.065  core=True
  idx= 408 ang= 324.24deg r=0.265  x_link=+0.120 y_link=+0.075  core=True
  idx= 409 ang= 325.03deg r=0.280  x_link=+0.115 y_link=+0.061  core=True
  idx= 410 ang= 325.83deg r=0.295  x_link=+0.109 y_link=+0.046  core=True
  idx= 411 ang= 326.62deg r=0.296  x_link=+0.112 y_link=+0.043  core=True
  idx= 412 ang= 327.42deg r=0.297  x_link=+0.115 y_link=+0.040  core=True
  idx= 413 ang= 328.21deg r=0.299  x_link=+0.117 y_link=+0.036  core=True
  idx= 414 ang= 329.01deg r=0.304  x_link=+0.118 y_link=+0.029  core=True
  idx= 415 ang= 329.80deg r=0.299  x_link=+0.125 y_link=+0.032  core=True
  idx= 416 ang= 330.60deg r=0.288  x_link=+0.134 y_link=+0.039  core=True
  idx= 417 ang= 331.39deg r=0.282  x_link=+0.140 y_link=+0.042  core=True
  idx= 418 ang= 332.19deg r=0.299  x_link=+0.135 y_link=+0.026  core=True
  idx= 419 ang= 332.98deg r=0.318  x_link=+0.131 y_link=+0.007  core=True
  idx= 420 ang= 333.77deg r=0.310  x_link=+0.138 y_link=+0.012  core=True
  idx= 421 ang= 334.57deg r=0.310  x_link=+0.142 y_link=+0.010  core=True
  idx= 425 ang= 337.75deg r=0.548  x_link=+0.067 y_link=-0.217  core=True
  idx= 426 ang= 338.54deg r=0.191  x_link=+0.205 y_link=+0.112  core=True
  idx= 428 ang= 340.13deg r=0.178  x_link=+0.215 y_link=+0.123  core=True
  idx= 429 ang= 340.93deg r=0.166  x_link=+0.221 y_link=+0.133  core=True
  idx= 430 ang= 341.72deg r=0.157  x_link=+0.226 y_link=+0.141  core=True
  idx= 431 ang= 342.52deg r=0.125  x_link=+0.237 y_link=+0.171  core=True
  idx= 432 ang= 343.31deg r=0.120  x_link=+0.241 y_link=+0.175  core=True
  idx= 433 ang= 344.11deg r=0.110  x_link=+0.245 y_link=+0.184  core=True
  idx= 434 ang= 344.90deg r=0.110  x_link=+0.246 y_link=+0.184  core=True
  idx= 435 ang= 345.70deg r=0.110  x_link=+0.248 y_link=+0.183  core=True
  idx= 436 ang= 346.49deg r=0.111  x_link=+0.249 y_link=+0.182  core=True
  idx= 437 ang= 347.28deg r=0.112  x_link=+0.250 y_link=+0.181  core=True
  idx= 438 ang= 348.08deg r=0.115  x_link=+0.251 y_link=+0.177  core=True
  idx= 439 ang= 348.87deg r=0.120  x_link=+0.252 y_link=+0.172  core=True
  idx= 440 ang= 349.67deg r=0.111  x_link=+0.255 y_link=+0.181  core=True
  idx= 441 ang= 350.46deg r=0.112  x_link=+0.256 y_link=+0.180  core=True
  idx= 442 ang= 351.26deg r=0.114  x_link=+0.258 y_link=+0.177  core=True
  idx= 443 ang= 352.05deg r=0.118  x_link=+0.259 y_link=+0.173  core=True
  idx= 444 ang= 352.85deg r=0.127  x_link=+0.259 y_link=+0.164  core=True
  idx= 445 ang= 353.64deg r=0.145  x_link=+0.259 y_link=+0.146  core=True
  idx= 446 ang= 354.44deg r=0.191  x_link=+0.256 y_link=+0.100  core=True
  idx= 447 ang= 355.23deg r=0.208  x_link=+0.258 y_link=+0.083  core=True
  idx= 448 ang= 356.03deg r=0.212  x_link=+0.260 y_link=+0.079  core=True
  idx= 449 ang= 356.82deg r=0.205  x_link=+0.264 y_link=+0.085  core=True
  idx= 450 ang= 357.62deg r=0.205  x_link=+0.266 y_link=+0.085  core=True
  idx= 451 ang= 358.41deg r=0.265  x_link=+0.268 y_link=+0.025  core=True
  idx= 452 ang= 359.21deg r=0.326  x_link=+0.270 y_link=-0.036  core=True
=== /scan : padded-box hits = 3 ===
  idx= 10 ang=   7.95deg r=0.019  x_link=+0.278 y_link=+0.271  core=True
  idx= 12 ang=   9.54deg r=0.015  x_link=+0.277 y_link=+0.275  core=True
  idx= 13 ang=  10.33deg r=0.017  x_link=+0.278 y_link=+0.273  core=True
--- 残留检查 ---
(clean)
```

### 判读

- 原始包车体矩形内 129 束；过滤后仅剩 3 束，且这 3 束的 range = **0.015 / 0.017 / 0.019 m**，全部 **< `range_min` = 0.02 m**。
- 所有 range ≥ 0.021 m 的车体回波（126 束）全部被置 NaN。→ 与「`LaserScanPolygonFilter` 跳过 range 越界点」一致（该跳过规则为**推断**，未查源码核实）。
- 残留 3 束物理含义 = 雷达自身窗口/内部回波（距光心 1.5~1.9 cm），非车体表面，且低于驱动声明的 range_min。

---

## 五、环境与进程

- N97 本机 `~/.bashrc` 与 SSH 会话均无 `ROS_DOMAIN_ID` / `RMW_*` / `FASTRTPS_*` 变量（grep 输出 `(none)`）。
- 两次 SSH 验证均由 VM 侧 `setsid nohup ros2 launch ...` 启动、结束后 `kill -TERM` + pgrep 清理，收尾 `(clean)`。
- 遗留日志：N97 `/tmp/ld06_filter_check.log`、`/tmp/ld06_filter_check2.log`（可删）。
