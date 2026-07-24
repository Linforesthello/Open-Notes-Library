## 收货
查验原系统，发现网络配置很多wifi,也有不少yabhoom的wifi配置，很混乱
且不知道原机密码
原机内并无很重要的文件，用户目录只有一个arm包，有点python和模型

## 开始操作

### 板子信息确认
lin@lin-desktop:~$ free -h
              total        used        free      shared  buff/cache   available
Mem:           3.9G        1.6G        1.3G         27M        1.0G        2.2G
Swap:          1.9G          0B        1.9G
lin@lin-desktop:~$ lsusb
Bus 002 Device 003: ID 05e3:0626 Genesys Logic, Inc. 
Bus 002 Device 002: ID 0bda:0411 Realtek Semiconductor Corp. 
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 003: ID 8087:0a2b Intel Corp. 
Bus 001 Device 006: ID 1c4f:0034 SiGma Micro 
Bus 001 Device 005: ID c0f4:07c0  
Bus 001 Device 004: ID 05e3:0610 Genesys Logic, Inc. 4-port hub
Bus 001 Device 002: ID 0bda:5411 Realtek Semiconductor Corp. 
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
lin@lin-desktop:~$ ifconfig eth0
eth0: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500
        ether 00:04:4b:ec:b3:b9  txqueuelen 1000  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
        device interrupt 150  base 0xc000  

lin@lin-desktop:~$ tegrastop
-bash: tegrastop: command not found
lin@lin-desktop:~$ sudo tegrastats
[sudo] password for lin: 
RAM 1655/3956MB (lfb 311x4MB) SWAP 0/1978MB (cached 0MB) IRAM 0/252kB(lfb 252kB) CPU [12%@102,10%@102,11%@102,12%@102] EMC_FREQ 3%@1600 GR3D_FREQ 0%@76 APE 25 PLL@36.5C CPU@39C iwlwifi@44C PMIC@50C GPU@37C AO@47.5C thermal@38C POM_5V_IN 2132/2132 POM_5V_GPU 78/78 POM_5V_CPU 275/275
RAM 1655/3956MB (lfb 311x4MB) SWAP 0/1978MB (cached 0MB) IRAM 0/252kB(lfb 252kB) CPU [14%@204,14%@204,10%@204,11%@204] EMC_FREQ 3%@1600 GR3D_FREQ 16%@76 APE 25 PLL@36C CPU@39C iwlwifi@44C PMIC@50C GPU@37C AO@47C thermal@38C POM_5V_IN 2247/2189 POM_5V_GPU 78/78 POM_5V_CPU 275/275
RAM 1655/3956MB (lfb 311x4MB) SWAP 0/1978MB (cached 0MB) IRAM 0/252kB(lfb 252kB) CPU [16%@204,11%@204,13%@204,9%@204] EMC_FREQ 3%@1600 GR3D_FREQ 0%@76 APE 25 PLL@36.5C CPU@39C iwlwifi@44C PMIC@50C GPU@37C AO@47C thermal@38.25C POM_5V_IN 2132/2170 POM_5V_GPU 78/78 POM_5V_CPU 236/262
^C
lin@lin-desktop:~$ nvcc -V
-bash: nvcc: command not found
lin@lin-desktop:~$ 
lin@lin-desktop:~$ nvcc -V
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2021 NVIDIA Corporation
Built on Sun_Feb_28_22:34:44_PST_2021
Cuda compilation tools, release 10.2, V10.2.300
Build cuda_10.2_r440.TC440_70.29663091_0
lin@lin-desktop:~$ nmcli device
DEVICE   TYPE      STATE        CONNECTION 
wlan0    wifi      connected    LinDesktop 
docker0  bridge    connected    docker0    
eth0     ethernet  unavailable  --         
l4tbr0   bridge    unmanaged    --         
dummy0   dummy     unmanaged    --         
rndis0   ethernet  unmanaged    --         
usb0     ethernet  unmanaged    --         
lo       loopback  unmanaged    --         
lin@lin-desktop:~$ 

lin@lin-desktop:~$ nmcli device
DEVICE   TYPE      STATE        CONNECTION 
wlan0    wifi      connected    LinDesktop 
docker0  bridge    connected    docker0    
eth0     ethernet  unavailable  --         
l4tbr0   bridge    unmanaged    --         
dummy0   dummy     unmanaged    --         
rndis0   ethernet  unmanaged    --         
usb0     ethernet  unmanaged    --         
lo       loopback  unmanaged    --         
lin@lin-desktop:~$ iwconfig
dummy0    no wireless extensions.

docker0   no wireless extensions.

lo        no wireless extensions.

usb0      no wireless extensions.

eth0      no wireless extensions.

l4tbr0    no wireless extensions.

wlan0     IEEE 802.11  ESSID:"LinDesktop"  
          Mode:Managed  Frequency:2.437 GHz  Access Point: 60:83:E2:11:CC:74   
          Bit Rate=150 Mb/s   Tx-Power=22 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=70/70  Signal level=-27 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:50   Missed beacon:0

rndis0    no wireless extensions.

lin@lin-desktop:~$ 


### 指令

1. 关闭 Wi-Fi 省电（重要）
sudo iwconfig wlan0 power off


### 常用指令

1. 查看功耗/温度
	1. sudo tegrastats
2. 重启
	1. sudo reboot
3. 关机
	1. sudo poweroff

# tmux保存pane

## 这条命令的作用

tmux capture-pane -p -S - > ~/pane.log

- `capture-pane`：捕获当前 pane（窗格）的内容
- `-p`：将捕获的内容输出到 stdout（标准输出），而不是保存到粘贴缓冲区
- `-S -`：从历史最开头（-S 指定起始行，`-` 表示负无穷，即全部历史）开始捕获
- `> ~/pane.log`：将输出的内容重定向到家目录下的 `pane.log` 文件

**所以，在当前 window 下执行这条命令，保存的是当前 pane 的可见内容 + 回滚缓冲区（scrollback）的全部内容。**

---

## 如何保存其他 window 的内容

你需要指定目标 window，用 `-t` 参数：

### 按 window 索引保存

```bash
# 保存 window 0 的内容
tmux capture-pane -p -S - -t 0 > ~/pane0.log

# 保存 window 2 的内容
tmux capture-pane -p -S - -t 2 > ~/pane2.log
```

### 按 window 名称保存

```bash
tmux capture-pane -p -S - -t window名称 > ~/pane.log
```

### 其他常见用法

```bash
# 保存其他 window 的第一个 pane
tmux capture-pane -p -S - -t 0.1 > ~/pane.log

# 只保存可见区域（不加 -S -）
tmux capture-pane -p -t 2 > ~/pane.log
```

### 确认当前 window 编号

如果不确定目标 window 的编号或名称，先列出所有 window：

```bash
tmux list-windows
```

输出类似：

```
0: bash* (3 panes) [120x40]
1: vim (1 panes) [120x40]
2: server (1 panes) [120x40]
```

然后就可以用 `-t 1`、`-t 2` 来指定了。


# sshfs挂载
你现在最推荐立刻尝试的方案
VMware Ubuntu：
1

安装：

sudo apt install sshfs
2

挂载：

mkdir ~/nano
sshfs lin@192.168.1.207:/home/lin ~/nano
3

VSCode 打开：

~/nano
4

另开一个终端：

ssh lin@192.168.1.207

运行程序。

#### linux可以直接查找蓝牙？也可以直接发送蓝牙信息！
```
lin@lin-desktop:~$ bluetoothctl
[NEW] Controller A4:C3:F0:EE:3E:63 lin-desktop [default]
Agent registered
[bluetooth]# scan on
Discovery started
[CHG] Controller A4:C3:F0:EE:3E:63 Discovering: yes
[NEW] Device 77:4A:F9:F1:B2:42 77-4A-F9-F1-B2-42
[NEW] Device 5C:D6:3D:0F:C6:92 5C-D6-3D-0F-C6-92
[NEW] Device 88:81:B9:26:9C:09 Lin
[NEW] Device 7C:85:8C:FF:79:76 7C-85-8C-FF-79-76
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Key: 0x0837
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Value:
  85 40 66 64 33 32 32 30 60 14 0b 76 69 76 6f 74  .@fd3220`..vivot
  65 07 2d ba 69 bb 00 00                          e.-.i...        
[NEW] Device 41:12:A4:EB:E0:BC 41-12-A4-EB-E0-BC
[CHG] Device 88:81:B9:26:9C:09 RSSI: -38
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Key: 0x0837
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Value:
  0a f5 7a 85 6f 20 58 20 4e 00 00 00 00 00        ..z.o X N.....  
[CHG] Device 88:81:B9:26:9C:09 RSSI: -29
[CHG] Device 5C:D6:3D:0F:C6:92 RSSI: -69
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Key: 0x0837
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Value:
  0a f5 7a 85 6f 20 58 20 4e 00 00 00 00 00        ..z.o X N.....  
[NEW] Device 59:2F:FB:FA:1E:B8 59-2F-FB-FA-1E-B8
[NEW] Device 45:E2:3C:FA:67:85 45-E2-3C-FA-67-85
[CHG] Device 5C:D6:3D:0F:C6:92 RSSI: -77
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Key: 0x0837
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Value:
  0a f5 7a 85 6f 20 58 20 4e 00 00 00 00 00        ..z.o X N.....  
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Key: 0x0837
[CHG] Device 5C:D6:3D:0F:C6:92 ManufacturerData Value:
  0a f5 7a 85 6f 20 58 20 4e 00 00 00 00 00        ..z.o X N.....  
[bluetooth]# 

```

### 尝试了tmux，好用！

> [!NOTE]
> 你现在其实已经到了：
> 
> # “tmux 真正有意义”的阶段。
> 
> 因为你已经不是：
> 
> ```text id="uwclmu"
> 单机Linux练习
> ```
> 
> 而是：
> 
> * VMware Ubuntu
> * SSH 到 Nano
> * ROS2
> * CUDA
> * 多节点
> * 长时间运行
> 
> 这种典型“远程 Linux 系统开发”场景。
> 
> ---
> 
> # 先彻底讲清 tmux 的核心概念
> 
> tmux 官方结构是：
> 
> ```text id="2m6shw"
> session
>  └── window
>       └── pane
> ```
> 
> 官方 wiki 也是这样定义的。 ([GitHub][1])
> 
> ---
> 
> # 一、session（最重要）
> 
> # session = 一个完整工作空间
> 
> 你可以理解成：
> 
> # “一个长期存活的远程桌面”
> 
> 例如：
> 
> ```bash id="92g8uo"
> tmux new -s robot
> ```
> 
> 这里：
> 
> ```text id="m1u2fd"
> robot
> ```
> 
> 就是 session 名字。
> 
> ---
> 
> # 这个 session 里面：
> 
> 可以有：
> 
> * 多窗口
> * 多 pane
> * 多 ROS 节点
> 
> 而且：
> 
> # SSH断了 session 也不会死。
> 
> 这是 tmux 最核心能力。 ([GitHub][1])
> 
> ---
> 
> # 二、window
> 
> # window ≈ 标签页(tab)
> 
> 例如：
> 
> ```text id="79vx8g"
> window0 : ROS
> window1 : YOLO
> window2 : DEBUG
> ```
> 
> 类似：
> 
> ```text id="7nq1vw"
> Chrome 标签页
> ```
> 
> ---
> 
> # 三、pane
> 
> # pane = 分屏
> 
> 例如：
> 
> ```text id="6e67bo"
> 左边 ros2 topic echo
> 右边 tegrastats
> 下面 candump
> ```
> 
> ---
> 
> # 所以：
> 
> # session 才是真正核心
> 
> 很多新手误以为：
> 
> tmux = 分屏工具。
> 
> 其实：
> 
> # tmux 的灵魂是 session。
> 
> ---
> 
> # 你现在应该怎么用（非常重要）
> 
> # 错误思路（很多新人）
> 
> SSH 上 Nano：
> 
> ```bash id="78zjlwm"
> tmux
> ```
> 
> 用完关掉。
> 
> ---
> 
> # 正确思路
> 
> # “长期养 session”
> 
> 例如：
> 
> ## robot session
> 
> 永远存在。
> 
> ---
> 
> # 以后：
> 
> 你 SSH 上 Nano：
> 
> 第一件事：
> 
> ```bash id="tjlwm1"
> tmux attach -t robot
> ```
> 
> ---
> 
> # 你会瞬间回到：
> 
> * ROS
> * YOLO
> * topic
> * debug
> 
> 之前的所有现场。
> 
> ---
> 
> # 这就是：
> 
> # “远程工作空间”
> 
> 概念。
> 
> ---
> 
> # 你现在最推荐的实际结构
> 
> # Session 1：robot
> 
> 运行：
> 
> ```bash id="jlwmv1"
> ros2 launch bringup.launch.py
> ```
> 
> 负责：
> 
> * 底盘
> * 驱动
> * 传感器
> 
> ---
> 
> # Session 2：vision
> 
> 运行：
> 
> ```bash id="jlwmv2"
> python3 detect.py
> ```
> 
> 负责：
> 
> * YOLO
> * TensorRT
> * 摄像头
> 
> ---
> 
> # Session 3：debug
> 
> 运行：
> 
> ```bash id="jlwmv3"
> candump can0
> ```
> 
> 或者：
> 
> ```bash id="jlwmv4"
> ros2 topic echo
> ```
> 
> ---
> 
> # 你会逐渐发现：
> 
> Nano 已经不是：
> 
> ```text id="jlwmv5"
> SSH shell
> ```
> 
> 而是：
> 
> # “远程机器人系统”
> 
> 了。
> 
> ---
> 
> # 下面详细解读命令
> 
> ---
> 
> # 1 创建 session
> 
> ```bash id="jlwmv6"
> tmux new -s robot
> ```
> 
> 含义：
> 
> | 部分    | 作用        |
> | ----- | --------- |
> | new   | 创建        |
> | -s    | session名字 |
> | robot | session名  |
> 
> ---
> 
> # 效果
> 
> 创建：
> 
> ```text id="jlwmv7"
> robot session
> ```
> 
> 并进入。
> 
> ---
> 
> # 2 查看 session
> 
> ```bash id="jlwmv8"
> tmux ls
> ```
> 
> 例如：
> 
> ```text id="jlwmv9"
> robot: 2 windows
> vision: 1 windows
> ```
> 
> ---
> 
> # 说明：
> 
> 当前 Nano 后台：
> 
> 还有哪些 session 活着。
> 
> ---
> 
> # 3 重新进入
> 
> ```bash id="jlwmva"
> tmux attach -t robot
> ```
> 
> 含义：
> 
> | 参数     | 作用          |
> | ------ | ----------- |
> | attach | 连接已有session |
> | -t     | target      |
> | robot  | session名    |
> 
> ---
> 
> # 作用
> 
> 回到：
> 
> ```text id="jlwmvb"
> robot session
> ```
> 
> 现场。
> 
> ---
> 
> # 4 detach（最重要）
> 
> 快捷键：
> 
> ```text id="jlwmvc"
> Ctrl+b
> d
> ```
> 
> 注意：
> 
> 不是同时按。
> 
> 是：
> 
> 1. Ctrl+b
> 2. 松开
> 3. d
> 
> ---
> 
> # 作用
> 
> # “人离开”
> 
> 但
> 
> # “session继续运行”
> 
> 官方叫：
> 
> ```text id="jlwmvd"
> detach
> ```
> 
> ([GitHub][1])
> 
> ---
> 
> # 5 kill session
> 
> ```bash id="jlwmve"
> tmux kill-session -t robot
> ```
> 
> 作用：
> 
> 彻底关闭：
> 
> ```text id="jlwmvf"
> robot session
> ```
> 
> 以及：
> 
> * ROS
> * python
> * 所有 pane
> 
> 全部结束。
> 
> ---
> 
> # 6 新建 window
> 
> 快捷键：
> 
> ```text id="jlwmvg"
> Ctrl+b
> c
> ```
> 
> 官方就是：
> 
> ```text id="jlwmvh"
> create window
> ```
> 
> ([GitHub][1])
> 
> ---
> 
> # 效果
> 
> 新增：
> 
> ```text id="jlwmvi"
> window1
> ```
> 
> 类似新标签页。
> 
> ---
> 
> # 7 切换 window
> 
> ## 下一个
> 
> ```text id="jlwmvj"
> Ctrl+b
> n
> ```
> 
> ---
> 
> ## 上一个
> 
> ```text id="jlwmvk"
> Ctrl+b
> p
> ```
> 
> ---
> 
> ## 指定窗口
> 
> ```text id="jlwmvl"
> Ctrl+b
> 0
> Ctrl+b
> 1
> ```
> 
> ---
> 
> # 8 分屏 pane
> 
> ## 左右分屏
> 
> ```text id="jlwmvm"
> Ctrl+b
> %
> ```
> 
> ---
> 
> ## 上下分屏
> 
> ```text id="jlwmvn"
> Ctrl+b
> "
> ```
> 
> 官方定义： ([GitHub][1])
> 
> ---
> 
> # 例如：
> 
> ```text id="jlwmvo"
> +-------------+-------------+
> | ros2 topic  | tegrastats  |
> +-------------+-------------+
> ```
> 
> ---
> 
> # 9 pane切换
> 
> ```text id="jlwmvp"
> Ctrl+b
> 方向键
> ```
> 
> ---
> 
> # 10 放大 pane（特别好用）
> 
> ```text id="jlwmvq"
> Ctrl+b
> z
> ```
> 
> ---
> 
> # 效果
> 
> 当前 pane：
> 
> # 全屏。
> 
> 再次：
> 
> ```text id="jlwmvr"
> Ctrl+b
> z
> ```
> 
> 恢复。
> 
> 这个你后面 debug ROS 特别舒服。
> 
> ---
> 
> # 你现在最该形成的习惯
> 
> # 错误习惯
> 
> SSH 上去：
> 
> ```bash id="jlwmvs"
> ros2 launch ...
> ```
> 
> 直接跑。
> 
> ---
> 
> # 正确习惯
> 
> SSH 上去：
> 
> ```bash id="jlwmvt"
> tmux attach -t robot
> ```
> 
> 没有就：
> 
> ```bash id="jlwmvu"
> tmux new -s robot
> ```
> 
> 然后再跑。
> 
> ---
> 
> # 你现在最适合的 tmux 工作流
> 
> # Window0：bringup
> 
> ```bash id="jlwmvv"
> ros2 launch bringup.launch.py
> ```
> 
> ---
> 
> # Window1：debug
> 
> ```bash id="jlwmvw"
> ros2 topic echo /odom
> ```
> 
> ---
> 
> # Window2：system
> 
> ```bash id="jlwmvx"
> tegrastats
> ```
> 
> ---
> 
> # Window3：can
> 
> ```bash id="jlwmvy"
> candump can0
> ```
> 
> ---
> 
> # Window4：vision
> 
> ```bash id="jlwmvz"
> python3 detect.py
> ```
> 
> ---
> 
> # 这样会发生什么？
> 
> 你：
> 
> * 关 SSH
> * 换网络
> * 重启 VMware
> * 电脑睡眠
> 
> ---
> 
> # Nano 上所有东西继续运行。
> 
> ---
> 
> # 为什么这对你特别重要
> 
> 因为你现在已经进入：
> 
> # “机器人系统调试”
> 
> 阶段了。
> 
> 你后面会大量：
> 
> * 长时间 rosbag
> * CUDA 推理
> * VLP16
> * D435i
> * FAST-LIO
> * ROS2 bringup
> * 多节点
> 
> 这些都不能：
> 
> ```text id="jlwmw0"
> SSH断一下
> 全没
> ```
> 
> ---
> 
> # 最后给你一个最推荐习惯（非常关键）
> 
> # 永远不要：
> 
> ```text id="jlwmw1"
> 直接 exit tmux
> ```
> 
> ---
> 
> # 你真正应该：
> 
> ```text id="jlwmw2"
> Ctrl+b
> d
> ```
> 
> detach。
> 
> ---
> 
> # 因为：
> 
> ## exit = 杀死 shell
> 
> 而：
> 
> ## detach = 人离开，系统继续运行
> 
> 很多新人第一次 tmux “没效果”，就是因为：
> 
> ```bash id="jlwmw3"
> exit
> ```
> 
> 把 session 自己杀了。 ([Reddit][2])
> 
> [1]: https://github.com/tmux/tmux/wiki/Getting-Started?utm_source=chatgpt.com "Getting Started · tmux/tmux Wiki · GitHub"
> [2]: https://www.reddit.com/r/tmux/comments/11or36s?utm_source=chatgpt.com "What am I getting wrong with tmux?"

### 鼠标拖动选择复制，shift+鼠标

> [!NOTE]
> 对，这就是 tmux 开启：
> 
> ```text id="v7m4cp"
> set-option -g mouse on
> ```
> 
> 以后最经典的问题。
> 
> 因为：
> 
> # 鼠标事件被 tmux 接管了
> 
> 所以：
> 
> 你原本 terminal（Tilix/Terminator）的：
> 
> ```text id="g2k8wr"
> 左键拖选
> ```
> 
> 被 tmux 截获了。
> 
> 这是 tmux 官方 mouse mode 的典型行为。 ([github.com](https://github.com/tmux/tmux/wiki/Getting-Started?utm_source=chatgpt.com))
> 
> ---
> 
> # 现在有几种解决方案
> 
> ---
> 
> # 方案1（最推荐）
> 
> # 按住 Shift 再拖动
> 
> 例如：
> 
> ```text id="j5n1tx"
> Shift + 鼠标左键拖动
> ```
> 
> ---
> 
> # 这是：
> 
> # “绕过 tmux”
> 
> 直接让：
> 
> * Tilix
> * Terminator
> * xterm
> 
> 接管鼠标。
> 
> ---
> 
> # 这是目前最主流方式
> 
> 很多 terminal 都支持。 ([superuser.com](https://superuser.com/questions/210125/scoll-shell-output-with-mouse-in-tmux?utm_source=chatgpt.com))
> 
> ---
> 
> # 所以你以后：
> 
> ## 普通点击
> 
> 给 tmux。
> 
> ---
> 
> ## Shift + 拖动
> 
> 给 terminal。
> 
> ---
> 
> # 这是最推荐方案。
> 
> ---
> 
> # 方案2
> 
> # 不开 mouse
> 
> 很多老 tmux 用户就是：
> 
> ```text id="o8f4ye"
> 完全不用 mouse
> ```
> 
> ---
> 
> 只用键盘：
> 
> * pane切换
> * copy-mode
> * scroll
> 
> ---
> 
> 但：
> 
> 对你当前阶段：
> 
> # 不推荐。
> 
> 因为：
> 
> 你还在：
> 
> * ROS log
> * 调试
> * 复制命令
> 
> 高频鼠标阶段。
> 
> ---
> 
> # 方案3（你后面可能会用）
> 
> # tmux copy-mode
> 
> 这是 tmux 原生复制系统。
> 
> 但：
> 
> # 学习成本高。
> 
> ---
> 
> 例如：
> 
> 进入 copy mode：
> 
> ```text id="d3q9va"
> Ctrl+b
> [
> ```
> 
> ---
> 
> 然后：
> 
> * 空格开始选择
> * 回车复制
> 
> ---
> 
> # 这个更像：
> 
> ```text id="x1w6rf"
> vim
> ```
> 
> 而不是 GUI terminal。
> 
> ---
> 
> # 对你当前：
> 
> # 不推荐优先学习。
> 
> ---
> 
> # 我对你现在最推荐的配置
> 
> ## 保持：
> 
> ```text id="m9c5zu"
> set-option -g mouse on
> ```
> 
> ---
> 
> # 然后：
> 
> ## 复制文本时：
> 
> # Shift + 左键拖动
> 
> ---
> 
> # 这是：
> 
> # “GUI terminal + tmux”
> 
> 组合里最经典操作。
> 
> ---
> 
> # 还有一个你后面会高频用的东西
> 
> # Shift + 滚轮
> 
> 很多 terminal：
> 
> ## 普通滚轮
> 
> tmux scroll。
> 
> ---
> 
> ## Shift + 滚轮
> 
> terminal 原生 scrollback。
> 
> ---
> 
> # Tilix/Terminator 基本都支持。
> 
> ---
> 
> # 你现在其实已经进入：
> 
> # “tmux + GUI terminal 共存”
> 
> 阶段了。
> 
> 这时候：
> 
> # tmux 不再是“唯一终端层”
> 
> 而只是：
> 
> # “后台 session 管理器”
> 
> ---
> 
> # 所以：
> 
> ## 鼠标复制
> 
> 交给：
> 
> * Tilix
> * Terminator
> 
> ---
> 
> ## session persistence
> 
> 交给：
> 
> * tmux
> 
> ---
> 
> # 这其实才是现代 Linux GUI 下最舒服的模式。

### git clone轻量化拉取，浅克隆
https://chatgpt.com/c/6a1185dd-5218-8322-b2e6-c2d9cae5ab7e


sshfs lin@192.168.1.207:/home/lin ~/nano


#### tmux保存，tmux-resurrect
所以：

你现在真正的保存目录是：

~/.local/share/tmux/resurrect

```
lin@lin-desktop:~$ ls ~/.local/share/tmux/resurrect
last                                tmux_resurrect_20260524T160430.txt  tmux_resurrect_20260524T160438.txt  tmux_resurrect_20260524T160611.txt
tmux_resurrect_20260524T160423.txt  tmux_resurrect_20260524T160434.txt  tmux_resurrect_20260524T160608.txt
lin@lin-desktop:~$
```

> [!NOTE]
> 然后：
> 
> 你甚至可以测试：
> 
> kill tmux server
> tmux kill-server
> 再重新进入：
> tmux new -s robot
> 然后恢复：
> Ctrl+b
> Ctrl+r
> 你会看到：
> window 名字
> pane 布局
> shell 路径
> 
> 回来。
> 
> 不过：
> ROS 进程不一定恢复。
> 
> 这是正常的。

## 部署了nvidia docker,以及注册成功
https://chatgpt.com/c/6a12b5ab-edc0-8320-8f69-f11ad1a88a0b

### 开始yolo

在nano本机部署了venv

```
二、进入虚拟环境（关键一步）
source yolo_env/bin/activate

成功后你会看到：

(yolo_env) lin@lin-desktop:~$
```


# 终于跑通了Jetson Nano B01 + SSD-MobileNet 检测部署（jetson-inference)，Hello AI World，uff格式


python3 ~/detect_headless.py

文档
jetson_nano_yolo.md

温度低是因为在拿风机在吹

![[Pasted image 20260525142642.png]]

![[Pasted image 20260525142746.png]]

![[Pasted image 20260525142836.png]]

# 尝试yolo部署

## docker代理
阿里云的 `registry.cn-hangzhou.aliyuncs.com` **不是 Docker Hub 代理**，它只是阿里云自己的镜像仓库。Docker 设置它为 mirror 后，拉取时仍然需要连接 Docker Hub 做认证（`registry-1.docker.io`），认证被墙就失败了。

换用社区维护的 Docker Hub 全代理，它会转发包括认证在内的所有流量：

```bash
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
sudo systemctl restart docker
docker pull dustynv/jetson-inference:r32.7.1
```

**`docker.1ms.run`** 是目前国内比较稳定的全功能 Docker Hub 代理，它能代理包括认证在内的所有请求，所以即使 Docker Hub 被墙，也可以通过它正常拉取。

如果 `1ms.run` 也不行，还有备选方案——直接在 Jetson Nano 上用 `jetson-inference` 仓库里的 Dockerfile 本地构建，不依赖外部镜像拉取：

```bash
cd ~/jetson-inference
docker build -t dustynv/jetson-inference:r32.7.1 -f Dockerfile .
```

## docker成功部署

~/nano/Lin_doc/2

cd /jetson-inference
detectnet.py /dev/video0

![[Pasted image 20260525205250.png]]

![[Pasted image 20260525205425.png]]

## rgb单目图片不知道去哪了
## 加装调速风扇
全速运行
sudo sh -c 'echo 255 > /sys/devices/pwm-fan/target_pwm'

## 这次使用了tornado d2,很清晰

要在docker启动前进行
![[Pasted image 20260529171109.png]]


# 帧率低检查
https://chatgpt.com/c/6a189d25-3d54-83a5-a99f-241d9fb73894

已经更换到了5v4a dc 电源供电

## 其他都没问题

### tegrastats
```
@41C PMIC@50C GPU@28C AO@35.5C thermal@29C RAM 2629/3956MB (lfb 66x4MB) SWAP 74/1978MB (cached 1MB) CPU [70%@1479,97%@1479,50%@1479,46%@1479] EMC_FREQ 0% GR3D_FREQ 99% PLL@27C CPU@29.5C iwlwifi@41C PMIC@50C GPU@28.5C AO@36C thermal@29C RAM 2610/3956MB (lfb 68x4MB) SWAP 74/1978MB (cached 1MB) CPU [73%@1479,83%@1479,33%@1479,69%@1479] EMC_FREQ 0% GR3D_FREQ 3% PLL@27C CPU@30C iwlwifi@41C PMIC@50C GPU@28C AO@35.5C thermal@29C RAM 2610/3956MB (lfb 68x4MB) SWAP 74/1978MB (cached 1MB) CPU [78%@1479,65%@1479,68%@1479,52%@1479] EMC_FREQ 0% GR3D_FREQ 99% PLL@27.5C CPU@30C iwlwifi@39C PMIC@50C GPU@28C AO@35.5C thermal@29C RAM 2610/3956MB (lfb 68x4MB) SWAP 74/1978MB (cached 1MB) CPU [47%@1479,96%@1479,73%@1479,37%@1479] EMC_FREQ 0% GR3D_FREQ 99% PLL@27.5C CPU@30C iwlwifi@40C PMIC@50C GPU@28.5C AO@35.5C thermal@29C RAM 2627/3956MB (lfb 67x4MB) SWAP 74/1978MB (cached 1MB) CPU [48%@1479,96%@1479,66%@1479,55%@1479] EMC_FREQ 0% GR3D_FREQ 99% PLL@27C CPU@30C iwlwifi@41C PMIC@50C GPU@28C AO@35.5C thermal@29C RAM 2610/3956MB (lfb 68x4MB) SWAP 74/1978MB (cached 1MB) CPU [81%@1479,55%@1479,89%@1479,45%@1479] EMC_FREQ 0% GR3D_FREQ 0% PLL@27C CPU@30C iwlwifi@41C PMIC@50C GPU@28C AO@35.5C thermal@29C

```
### sudo jetson_clocks --show

```
lin@lin-desktop:~$ sudo jetson_clocks --show                                                                                      [90/90]
[sudo] password for lin:                                                                                                                 
SOC family:tegra210  Machine:NVIDIA Jetson Nano Developer Kit                                                                            
Online CPUs: 0-3                                                                                                                         
cpu0: Online=1 Governor=schedutil MinFreq=1200000 MaxFreq=1479000 CurrentFreq=1479000 IdleStates: WFI=1 c7=1                             
cpu1: Online=1 Governor=schedutil MinFreq=1200000 MaxFreq=1479000 CurrentFreq=1479000 IdleStates: WFI=1 c7=1                             
cpu2: Online=1 Governor=schedutil MinFreq=1200000 MaxFreq=1479000 CurrentFreq=1479000 IdleStates: WFI=1 c7=1                             
cpu3: Online=1 Governor=schedutil MinFreq=1200000 MaxFreq=1479000 CurrentFreq=1479000 IdleStates: WFI=1 c7=1                             
GPU MinFreq=76800000 MaxFreq=921600000 CurrentFreq=921600000                                                                             
EMC MinFreq=204000000 MaxFreq=1600000000 CurrentFreq=1600000000 FreqOverride=0                                                           
Fan: PWM=255                                                                                                                             
NV Power Mode: MAXN 

```
#### 先test.py
```
import cv2

import time

  

cap = cv2.VideoCapture(0)

  

for i in range(100):

  

t0 = time.perf_counter()

  

ret, frame = cap.read()

  

t1 = time.perf_counter()

  

if not ret:

continue

  

# 模拟推理

time.sleep(0.01)

  

t2 = time.perf_counter()

  

# 模拟后处理

time.sleep(0.01)

  

t3 = time.perf_counter()

  

print(

f"cap={(t1-t0)*1000:.1f}ms "

f"infer={(t2-t1)*1000:.1f}ms "

f"post={(t3-t2)*1000:.1f}ms "

f"total={(t3-t0)*1000:.1f}ms"

)

  

cap.release()


```

root@lin-desktop:/jetson-inference# cd data/
root@lin-desktop:/jetson-inference/data# python3 test.py
[ WARN:0] global /opt/opencv/modules/videoio/src/cap_gstreamer.cpp (935) open OpenCV | GStreamer warning: Cannot query video position: status=0, value=-1, duration=-1
cap=19.3ms infer=10.2ms post=10.3ms total=39.7ms
cap=487.2ms infer=10.3ms post=10.3ms total=507.8ms
cap=593.2ms infer=10.3ms post=10.3ms total=613.8ms
cap=497.5ms infer=12.5ms post=10.3ms total=520.2ms
cap=596.5ms infer=10.1ms post=10.3ms total=616.9ms
cap=472.6ms infer=10.3ms post=10.2ms total=493.2ms
cap=630.3ms infer=10.2ms post=10.3ms total=650.8ms
cap=527.7ms infer=10.2ms post=10.3ms total=548.1ms
cap=527.4ms infer=10.2ms post=10.1ms total=547.7ms
cap=508.3ms infer=10.2ms post=10.2ms total=528.7ms
cap=609.5ms infer=10.2ms post=10.2ms total=629.9ms

https://chatgpt.com/c/6a20038b-c118-83a5-947e-c516d41b3b40

```
v4l2-ctl --get-fmt-video
```
```
v4l2-ctl -d /dev/video0 \
  --set-fmt-video=width=640,height=480,pixelformat=MJPG
```
```
v4l2-ctl --stream-mmap --stream-count=100
```


## 放弃当前道路（raw TensorRT），可能是gpu瓶颈，转向DeepStream + YOLO Docker

成功运行，但是还是不行，后续更换方向
```
root@lin-desktop:/opt/nvidia/deepstream/deepstream-6.0# cd /opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app root@lin-desktop:/opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app# ls config_infer_primary.txt source12_1080p_dec_infer-resnet_tracker_tiled_display_fp16_tx2.txt config_infer_primary_nano.txt source1_csi_dec_infer_resnet_int8.txt config_infer_secondary_carcolor.txt source1_usb_dec_infer_resnet_int8.txt config_infer_secondary_carmake.txt source2_1080p_dec_infer-resnet_demux_int8.txt config_infer_secondary_vehicletypes.txt source2_csi_usb_dec_infer_resnet_int8.txt config_preprocess.txt source30_1080p_dec_infer-resnet_tiled_display_int8.txt config_tracker_DeepSORT.yml source30_1080p_dec_preprocess_infer-resnet_tiled_display_int8.txt config_tracker_IOU.yml source4_1080p_dec_infer-resnet_tracker_sgie_tiled_display_int8.txt config_tracker_NvDCF_accuracy.yml source6_csi_dec_infer_resnet_int8.txt config_tracker_NvDCF_max_perf.yml source8_1080p_dec_infer-resnet_tracker_tiled_display_fp16_nano.txt config_tracker_NvDCF_perf.yml source8_1080p_dec_infer-resnet_tracker_tiled_display_fp16_tx1.txt root@lin-desktop:/opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app# source1_usb_dec_infer_resnet_int8.txt bash: source1_usb_dec_infer_resnet_int8.txt: command not found root@lin-desktop:/opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app# cd /opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-a pp root@lin-desktop:/opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app# deepstream-app -c source1_usb_dec_infer_resnet_int8.txt ERROR: Deserialize engine failed because file path: /opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app/../../models/Primary_Detector/resne t10.caffemodel_b30_gpu0_int8.engine open error 0:00:05.429939643 25 0x37670270 WARN nvinfer gstnvinfer.cpp:635:gst_nvinfer_logger:<primary_gie> NvDsInferContext[UID 1]: Warning fro m NvDsInferContextImpl::deserializeEngineAndBackend() <nvdsinfer_context_impl.cpp:1889> [UID = 1]: deserialize engine from file :/opt/nvidia/deepstream/deep stream-6.0/samples/configs/deepstream-app/../../models/Primary_Detector/resnet10.caffemodel_b30_gpu0_int8.engine failed 0:00:05.431822969 25 0x37670270 WARN nvinfer gstnvinfer.cpp:635:gst_nvinfer_logger:<primary_gie> NvDsInferContext[UID 1]: Warning fro m NvDsInferContextImpl::generateBackendContext() <nvdsinfer_context_impl.cpp:1996> [UID = 1]: deserialize backend context from engine from file :/opt/nvidia /deepstream/deepstream-6.0/samples/configs/deepstream-app/../../models/Primary_Detector/resnet10.caffemodel_b30_gpu0_int8.engine failed, try rebuild 0:00:05.431879781 25 0x37670270 INFO nvinfer gstnvinfer.cpp:638:gst_nvinfer_logger:<primary_gie> NvDsInferContext[UID 1]: Info from N vDsInferContextImpl::buildModel() <nvdsinfer_context_impl.cpp:1914> [UID = 1]: Trying to create engine from model files WARNING: INT8 not supported by platform. Trying FP16 mode. 0:02:44.566303273 25 0x37670270 INFO nvinfer gstnvinfer.cpp:638:gst_nvinfer_logger:<primary_gie> NvDsInferContext[UID 1]: Info from N vDsInferContextImpl::buildModel() <nvdsinfer_context_impl.cpp:1947> [UID = 1]: serialize cuda engine to file: /opt/nvidia/deepstream/deepstream-6.0/samples/ models/Primary_Detector/resnet10.caffemodel_b1_gpu0_fp16.engine successfully INFO: [Implicit Engine Info]: layers num: 3 0 INPUT kFLOAT input_1 3x368x640 1 OUTPUT kFLOAT conv2d_bbox 16x23x40 2 OUTPUT kFLOAT conv2d_cov/Sigmoid 4x23x40 0:02:44.997741677 25 0x37670270 INFO nvinfer gstnvinfer_impl.cpp:313:notifyLoadModelStatus:<primary_gie> [UID 1]: Load new model:/opt /nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app/config_infer_primary.txt sucessfully Runtime commands: h: Print this help q: Quit p: Pause r: Resume NOTE: To expand a source in the 2D tiled display and view object details, left-click on the source. To go back to the tiled display, right-click anywhere on the window. **PERF: FPS 0 (Avg) **PERF: 0.00 (0.00) ** INFO: <bus_callback:194>: Pipeline ready ** INFO: <bus_callback:180>: Pipeline running **PERF: 6.71 (6.58) **PERF: 6.71 (6.71) **PERF: 6.71 (6.67) **PERF: 6.72 (6.70) **PERF: 6.65 (6.68) **PERF: 6.72 (6.70) **PERF: 6.71 (6.69) **PERF: 6.72 (6.70) **PERF: 6.73 (6.69) **PERF: 6.71 (6.70) **PERF: 6.72 (6.71) **PERF: 6.72 (6.70) ^C** ERROR: <_intr_handler:140>: User Interrupted.. Quitting App run successful root@lin-desktop:/opt/nvidia/deepstream/deepstream-6.0/samples/configs/deepstream-app#
```

## 因为要自己的模型，所以转到YOLOv5/YOLOv8 → ONNX → TensorRT engine + EfficientNMS plugin


