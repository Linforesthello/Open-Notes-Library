#Rasp #Tools/docker #Tools/linux
https://chatgpt.com/c/69e987ae-eff8-83e8-9cbd-25b0c945289c

> [!NOTE]
> 这个报错很典型，不是网络问题，而是 **SSH 安全机制拦住了你**。
> 
> ---
> 
> # 🧠 一、报错本质
> 
> 远程主机密钥已更改，端口转发已禁用
> 
> 意思是：
> 
> > 你这台电脑“记住的旧 SSH 指纹”，和现在这台 `192.168.1.199` 的指纹不一致
> 
> SSH 判定为：
> 
> - 可能是系统重装
> - 可能是 IP 对应设备变了
> - 也可能是中间人攻击（安全保护）
> 
> ---
> 
> # 🧭 二、最常见真实原因（树莓派场景）
> 
> 对你这种树莓派 5（Raspberry Pi 5）开发环境，基本是：
> 
> ### ✔ 1. 重新烧录系统（最常见）
> 
> - SD卡重刷
> - Ubuntu / Raspberry Pi OS 重装  
>     👉 SSH key 全变
> 
> ---
> 
> ### ✔ 2. IP 复用了另一台设备
> 
> 路由器 DHCP 可能把 `192.168.1.199` 分给了新设备
> 
> ---
> 
> ### ✔ 3. 树莓派重装/换机
> 
> host key 必然变化
> 
> ---
> 
> # 🧨 三、解决方法（正确做法）
> 
> ## 🥇 方法1：删除旧 SSH 记录（推荐）
> 
> 在你的电脑上执行：
> 
> ssh-keygen -R 192.168.1.199
> 
> ---
> 
> 然后重新连接：
> 
> ssh pi@192.168.1.199

```
lin-virtual-machine% ssh-keygen -R 192.168.1.199
# Host 192.168.1.199 found: line 1
# Host 192.168.1.199 found: line 2
# Host 192.168.1.199 found: line 3
/home/lin/.ssh/known_hosts updated.
Original contents retained as /home/lin/.ssh/known_hosts.old
lin-virtual-machine% 

```

vscode正常

## 更改风扇策略

> [!NOTE]
> # ✅ 一、你现在这个文件是正常的
> 
> 你当前内容属于标准初始化配置，没有问题：
> 
> [all]  
> arm_64bit=1  
> kernel=vmlinuz  
> ...  
> dtparam=audio=on  
> dtparam=i2c_arm=on  
> dtparam=spi=on
> 
> 👉 **可以直接在最后追加配置，不用改已有内容**
> 
> ---
> 
> # 🧊 二、风扇策略正确添加方式（重点）
> 
> 把光标移到文件**最底部**，然后加👇
> 
> # ==== Fan control (提前启动风扇) ====  
> dtparam=fan_temp0=50000  
> dtparam=fan_temp0_hyst=5000  
> dtparam=fan_temp0_speed=150

### ubuntu上看当前温度

> [!NOTE]
> 
> # ✅ 三、在 Ubuntu 上正确看温度的方法
> 
> ## 🥇 方法1（最标准）
> 
> cat /sys/class/thermal/thermal_zone0/temp
> 
> 输出类似：
> 
> 52000
> 
> 👉 表示：
> 
> 52.0°C
> 
> ---
> 
> ## 🥈 方法2（更直观）
> 
> watch -n 1 cat /sys/class/thermal/thermal_zone0/temp
> 
> 👉 每秒刷新温度
> 
> ---
> 
> ## 🥉 方法3（推荐你用）
> 
> sudo apt install lm-sensors -y  
> sensors
> 
> ---
> 
> # 🔥 四、你真正要关心的不是 vcgencmd
> 
> 而是👇
> 
> ### ✔ CPU 是否在狂跑
> 
> htop

## docker
![[Pasted image 20260423140215.png]]

### 拉错了，x86的这是。目前要arm

## 固定docker工作空间

> [!NOTE]
> ## 🥈 第二步：在主机上创建开发容器
> 
> docker run -it \  
> --name ros2_humble_dev \  
> --network host \  
> --privileged \  
> -v /dev:/dev \  
> -v ~/ros_ws:/root/ros_ws \  
> arm64v8/ros:humble

> [!NOTE]
> ## ❌ 不要再用
> 
> docker run ...
> 
> ---
> 
> ## ✅ 正确方式
> 
> 退出容器：
> 
> exit
> 
> 以后进入：
> 
> docker start -ai ros2_humble_dev

> [!NOTE]
> ## 2️⃣ 再开一个终端（新窗口）
> 
> 👉 不要 `docker run`，而是：
> 
> docker exec -it ros2_humble_dev bash

## pipx下载

## 查docker启动挂载参数
```sh
lin@lin-desktop:~$ runlike ros2_humble_dev
docker run --name=ros2_humble_dev --hostname=lin-desktop --volume /dev:/dev --volume /home/lin/ros_ws:/root/ros_ws --network=host --privileged --runtime=runc -t arm64v8/ros:humble bash
lin@lin-desktop:~$ 


```

> [!NOTE]
> # 🧠 一、你这个容器的真实启动参数是
> 
> docker run \  
> --name=ros2_humble_dev \  
> --hostname=lin-desktop \  
> --volume /dev:/dev \  
> --volume /home/lin/ros_ws:/root/ros_ws \  
> --network=host \  
> --privileged \  
> --runtime=runc \  
> -t arm64v8/ros:humble \  
> bash

docker ps -a

> [!NOTE]
> 
> # 🚀 三、重新进入（核心）
> 
> ## ✔ 方法1：启动 + 进入
> 
> docker start ros2_humble_dev  
> docker exec -it ros2_humble_dev bash
> 
> ---
> 
> ## ✔ 方法2（一条命令）
> 
> docker start -ai ros2_humble_dev
> 
> ---
> 
> # 🧩 四、两种“继续”的区别
> 
> ---
> 
> ## 🥇 exec（推荐 ⭐）
> 
> docker exec -it ros2_humble_dev bash
> 
> 👉 特点：
> 
> - 不重启容器
> - 直接进入已有环境
> - ROS进程还能在后台继续跑
> 
> ---
> 
> ## 🥈 start -ai
> 
> docker start -ai ros2_humble_dev
> 
> 👉 特点：
> 
> - 直接回到“上一次 bash”
> - 类似“恢复现场”

## docker内运行python(gpt_commandline)成功

## 在原来的docker内下载ros2-humble-desktop-full