## Linux,ubuntu22.04.05
---
[Linux部署开发环境](https://chatgpt.com/c/69b0dc09-3468-8321-a8ea-ac1238ebc8d4)

---
### 已经预装了vmtools

### 常见工具链见ubuntu2004
### 输入法fcitx4在ubuntu2204下支持不好（vscode无法输入中文，但命令行和浏览器均可）
#### 换为fcitx5，成功解决
---
[Linux部署开发环境](https://chatgpt.com/c/69b0dc09-3468-8321-a8ea-ac1238ebc8d4)![[Pasted image 20260311135209.png]]
### 替换了terminator的配置文件
[Linux部署开发环境](https://chatgpt.com/c/69b0dc09-3468-8321-a8ea-ac1238ebc8d4)
1. cp ~/.config/terminator/config ~/terminator_config_backup
2. cp ~/terminator_config_backup ~/.config/terminator/config
3. ![[Pasted image 20260321201720.png]]

### 桥接没有dns，查文档发现遗漏了一处，[[20251116-17,21]]

#### 260311，已经复制到“[[✨VMware~Ubuntu20.04Desktop~ROS]]”

### jlink接入ubuntu2204,stm32cubeprg，记录
![[Pasted image 20260311222256.png]]
### Gemini Code Assist ，已经登录（？）
1. https://developers.google.com/gemini-code-assist/auth/auth_success_gemini?hl=zh-cn

2. ![[Pasted image 20260311235156.png]]
#### 可能是网络问题，vscode中未登录

### Linux下，stm32f103c8t6+freertos+cmake+jlink点灯成功

### 虚拟机开启“3D图形化加速”，会出现一些不支持/不兼容现象
#### 比如cubemx，配置时钟那一行字符会空白，比如flclash会上下颠倒（在issue中可见），比如github图形缺失
issue https://github.com/chen08209/FlClash/issues/1830

#### 配置flclash时，出现如下
![[Pasted image 20260312005318.png]]

### salese logic安装
#### 官网下载
#### 提示如图，需要复制到命令行并插拔逻辑分析仪 
![[Pasted image 20260315164434.png]]

> [!NOTE]
> cat /tmp/.mount_Logic-ac4eCa/resources/linux-x64/99-SaleaeLogic.rules | sudo tee /etc/udev/rules.d/99-SaleaeLogic.rules > /dev/null && echo "finished installing /etc/udev/rules.d/99-SaleaeLogic.rules"
#### 结果如图
![[Pasted image 20260315164605.png]]
#### 成功显示
![[Pasted image 20260315164633.png]]
## 实时监控设备指令：

sudo dmesg -w

## Linux下可以实现savvycan收消息
---
[分支 · 分支 · 分支 · Linux部署开发环境](https://chatgpt.com/c/69b3ad93-be18-83a9-9240-c618109ac7f9)

---

从源码编译下载，不能走wgets（版本太低，且applmage包含库少）

> [!NOTE]
> # 结论（直接说最有效方案）
> 
> 不要再折腾 AppImage 了。
> 
> **直接编译 SavvyCAN 源码。**
> 
> 这是 Linux 用户最常用的方式。
> 
> ---
> 
> # 一、安装依赖
> 
> sudo apt update  
>   
> sudo apt install \  
> qtbase5-dev \  
> qtdeclarative5-dev \  
> qttools5-dev \  
> libqt5serialbus5-dev \  
> libqt5serialport5-dev \  
> build-essential
> 
> `libqt5serialbus5-dev` 是关键。
> 
> ---
> 
> # 二、下载源码
> 
> git clone https://github.com/collin80/SavvyCAN.git  
> cd SavvyCAN
> 
> ---
> 
> # 三、编译
> 
> qmake  
> make -j8
> 
> SavvyCAN 官方也是这样编译的。


1. 成功表现如图![[Pasted image 20260313172953.png]]
2. 设置细节![[Pasted image 20260313173028.png]]
3. 步骤![[Pasted image 20260313173933.png]]

> [!NOTE]
> ls /dev/ttyACM*
> 
> sudo slcand -o -c -s6 /dev/ttyACM can0
> sudo ip link set can0 up
> ip link show can0
4. 现在，这样启动![[Pasted image 20260313174646.png]]
### 实现can收发，（借由无线串口）
[[✨重写UartToCan项目]]
1. cansend can0 456#1122334455667788
2. 连接到![[Pasted image 20260313201344.png]]

### 实现外部串口信息返回，发送到can网络，（借由e34h27d远程串口跳频）
![[Pasted image 20260315154647.png]]

### 实现一个串口下发指令到网关，另一个mcu网关串口信息返回；验证了数据链路完整性
1. 结果图![[Pasted image 20260315154939.png]]
2. 现场留档
	1. 下端的mcu接着e34h27d，同时接入can网络；上端的mcu接入无线串口，同时接入can网络![[WIN_20260315_15_51_48_Pro.jpg]]
	2. 两块mcu+canable2.0同时在回路中![[WIN_20260315_15_51_51_Pro.jpg]]
	3. ![[WIN_20260315_15_51_55_Pro.jpg]]

### vscode无法下载gemini插件，手动下载找不到文件（已解决）
1. 关键是下载下来的文件后缀问题，导致vscode无法识别，通过
	1. mv ~/Downloads/Microsoft.VisualStudio.Services.VSIXPackage ~/Downloads/Microsoft.VisualStudio.Services.VSIXPackage.vsix
2. 再次vscode从vsix安装，即可实现
3. 留档![[Pasted image 20260315161500.png]]

## 下载ros2 humble
### gazebo出现问题，无法从命令行启动丨新旧程序共存问题
#### 起因是turble3，无法launch启动
https://chatgpt.com/c/69b7a4c6-a624-8321-b970-6df687c79d49
多次排查，解决问题
1. ![[Pasted image 20260316150953.png]]
2. 留档![[Pasted image 20260316151040.png]]![[Pasted image 20260316151015.png]]
#### 经排查发现：是新旧程序共存问题

> [!NOTE]
> 为什么你之前会遇到 /spawn_entity 错误
> 
> 从你整个日志看，真实原因其实只有一个：
> 
> Address already in use
> 
> 也就是：
> 
> 旧 gzserver 进程还在
> ↓
> 新的 Gazebo 启动失败
> ↓
> spawn_entity 服务不存在
> 
> 这在 ROS 仿真里 非常常见。
> 
> 以后如果遇到类似问题，直接：
> 
> killall gzserver gzclient
> 
> 再启动仿真即可。

### ros2上的turble3初体验
---
https://chatgpt.com/c/69b7add8-cda0-8321-b986-e6aec6c61573

---

1. 键盘控制运动![[Pasted image 20260316152219.png]]
2. 在搞ros2 launch turtlebot3_cartographer cartographer.launch.py
	1. 车翻了![[Pasted image 20260316154124.png]]
	2. 这次是正常测试![[Pasted image 20260316154831.png]]
## linux下的串口助手，gui版本

> [!NOTE]
> 有的，而且 **Linux 下串口工具其实比 Windows 还多**，只是分两类：
> 👉 **GUI 图形界面（类似串口助手）**
> 👉 **CLI 命令行（更工程化）**
> 
> 我给你按“像 Windows 串口助手程度”帮你分一下 👇
> 
> ---
> 
> # 🟢 一、最接近 Windows 串口助手（推荐你用）
> 
> 这些基本就是你要的👇
> 
> ### 1️⃣ moserial（强烈推荐）
> 
> * GNOME 系 GUI 串口工具
> * 支持 HEX / ASCII、日志、波特率配置
> * 界面简单，非常像 Windows 串口助手
> 
> 👉 安装：
> 
> ```bash
> sudo apt install moserial
> ```
> 
> 👉 特点：
> 
> * 支持 HEX 收发
> * 可保存配置
> * 操作简单 ([GNOME Wiki][1])
> 
> ---
> 
> ### 2️⃣ CuteCom
> 
> * Qt 写的 GUI 串口工具
> * 很经典，做嵌入式的人常用
> 
> 👉 安装：
> 
> ```bash
> sudo apt install cutecom
> ```
> 
> 👉 特点：
> 
> * 支持 HEX 输入输出
> * 可设置延时发送
> * 类似 Windows 的调试工具 ([CuteCom][2])
> 
> ---
> 
> ### 3️⃣ GtkTerm
> 
> * 更轻量的 GUI 串口工具
> 
> 👉 安装：
> 
> ```bash
> sudo apt install gtkterm
> ```
> 
> 👉 特点：
> 
> * 简单直接
> * 适合快速调试 ([AlternativeTo][3])
> 
> ---
> 
> # 🟡 二、进阶 / 工程向（你以后一定会用）
> 
> （你做 ROS + STM32，这类其实更适合你）
> 
> ### 4️⃣ minicom（强烈建议掌握）
> 
> ```bash
> sudo apt install minicom
> ```
> 
> 👉 启动：
> 
> ```bash
> minicom -D /dev/ttyUSB0 -b 115200
> ```
> 
> 👉 特点：
> 
> * CLI 工具（无 GUI）
> * 稳定、功能强
> * Linux 老牌神器 ([AlternativeTo][3])
> 
> ---
> 
> ### 5️⃣ picocom（极简）
> 
> ```bash
> sudo apt install picocom
> ```
> 
> 👉 启动：
> 
> ```bash
> picocom /dev/ttyUSB0 -b 115200
> ```
> 
> 👉 特点：
> 
> * 超轻量
> * 比 minicom 简单
> 
> ---
> 
> ### 6️⃣ screen（隐藏王者）
> 
> ```bash
> screen /dev/ttyUSB0 115200
> ```
> 
> 👉 特点：
> 
> * 系统自带
> * 远程调试神器
> 
> ---
> 
> # 🔴 三、给你一个建议（很重要）
> 
> 结合你现在的情况（ROS + STM32 + CAN）👇
> 
> 👉 推荐组合：
> 
> * 日常调试 👉 **moserial / CuteCom**
> * 自动化 / 脚本 👉 **python + pyserial**
> * 工程开发 👉 **minicom**
> 
> ---
> 
> # ⚡ 四、你可能踩的坑（提前告诉你）
> 
> ### 1️⃣ 串口权限问题
> 
> ```bash
> sudo usermod -aG dialout $USER
> ```
> 
> 然后重启！
> 
> ---
> 
> ### 2️⃣ 串口名
> 
> 常见：
> 
> ```bash
> /dev/ttyUSB0
> /dev/ttyACM0
> ```
> 
> ---
> 
> # 🚀 一句话总结
> 
> 👉 想要“像 Windows 串口助手”：
> ✔ 用 **moserial / CuteCom**
> 
> 👉 想要“工程能力”：
> ✔ 学 **minicom**
> 
> ---
> 
> 如果你愿意，我可以帮你：
> 👉 直接给你一套“ROS2 + 串口通信调试方案”（包括 Python 节点 + 串口工具组合）
> 这个对你现在做底盘控制会非常关键 👍
> 
> [1]: https://wiki.gnome.org/Apps/Moserial?utm_source=chatgpt.com "Apps/Moserial – GNOME Wiki Archive"
> [2]: https://cutecom.sourceforge.net/?utm_source=chatgpt.com "CuteCom"
> [3]: https://alternativeto.net/software/gtkterm/?platform=linux&utm_source=chatgpt.com "GtkTerm Alternatives for Linux: Top 12 Terminal Emulators & Similar Apps | AlternativeTo"

---

> [!NOTE]
> 很好，这一步说明你已经**成功安装 moserial 了 ✅**，没有任何问题 👍
> 
> 接下来你只差最后一步：**怎么用它**
> 
> ---
> 
> # 🚀 一、启动 moserial
> 
> 在终端输入：
> 
> ```bash
> moserial
> ```
> 
> 如果打不开（VM 有时会这样），可以试：
> 
> ```bash
> /usr/bin/moserial
> ```
> 
> 或者在 Ubuntu 应用菜单里搜索：
> 👉 `moserial`
> 
> ---
> 
> # 🧭 二、基本使用（重点）
> 
> 打开之后，你只需要设置 3 个核心参数：
> 
> ### 1️⃣ 串口设备
> 
> 一般是：
> 
> ```bash
> /dev/ttyUSB0
> 或
> /dev/ttyACM0
> ```
> 
> 👉 不确定的话先查：
> 
> ```bash
> ls /dev/tty*
> ```
> 
> 或者插上设备前后对比：
> 
> ```bash
> dmesg | grep tty
> ```
> 
> ---
> 
> ### 2️⃣ 波特率（Baud Rate）
> 
> 比如你 STM32 用的是：
> 
> ```bash
> 115200
> ```
> 
> ---
> 
> ### 3️⃣ 数据格式
> 
> 一般默认即可：
> 
> * 8N1（8位数据，无校验，1停止位）
> 
> ---
> 
> # 🔧 三、连接流程（很关键）
> 
> 在 moserial 里：
> 
> 1. 点击 **Port Setup**
> 2. 设置：
> 
>    * Port → `/dev/ttyUSB0`
>    * Baud → `115200`
> 3. 点击 **Open**
> 
> 👉 成功的话，状态栏会变成：
> 
> ```
> Connected
> ```
> 
> ---
> 
> # 📡 四、收发测试
> 
> ### 发数据：
> 
> 直接在输入框输入，比如：
> 
> ```
> hello
> ```
> 
> 点击 **Send**
> 
> ---
> 
> ### 收数据：
> 
> * 串口有数据就会显示在窗口里
> 
> ---
> 
> # ⚠️ 五、你大概率会遇到的问题（提前帮你踩坑）
> 
> ## ❗1. Permission denied（最常见）
> 
> 解决：
> 
> ```bash
> sudo usermod -aG dialout $USER
> ```
> 
> 然后：
> 
> ```bash
> reboot
> ```
> 
> ---
> 
> ## ❗2. 虚拟机识别不到串口（你现在这个环境很可能遇到）
> 
> 你是：
> 👉 VMware + Ubuntu
> 
> 需要做：
> 
> 👉 在 VMware 菜单：
> 
> ```
> VM → Removable Devices → USB → 连接你的串口设备
> ```
> 
> 否则 Linux 根本看不到串口！
> 
> ---
> 
> ## ❗3. 设备名变化
> 
> 有时候：
> 
> ```
> /dev/ttyUSB0 → /dev/ttyUSB1
> ```
> 
> 👉 插拔后一定要重新确认
> 
> ---
> 
> # ⚡ 六、给你一个工程级建议（很重要）
> 
> 你现在在做：
> 
> 👉 STM32 + 串口 + ROS2
> 
> 建议你这样分层：
> 
> | 用途    | 工具                |
> | ----- | ----------------- |
> | 手动调试  | moserial          |
> | 自动通信  | Python + pyserial |
> | ROS接口 | ros2 node         |
> 
> 👉 **moserial只是调试工具，不要作为系统一部分**
> 
> ---
> 
> # 🧠 七、下一步我建议你做这个（非常关键）
> 
> 你现在已经具备：
> 
> * ✅ STM32 串口发送
> * ✅ Linux 串口工具
> 
> 👉 下一步应该做：
> 
> 👉 **写一个 ROS2 串口节点（桥接）**
> 
> 结构：
> 
> ```
> STM32 ←→ 串口 ←→ ROS2节点 ←→ 话题
> ```
> 
>---
> 
> 如果你愿意，我可以直接帮你写：
> 
> ✅ ROS2 串口节点（Python版）
> ✅ 支持你现在的“字符串调速协议”
> ✅ 可直接接入你底盘控制
> 
> 这个会直接把你项目推进一大步 🚀

## 260429，出现启动节点后，缺少tf的问题，
https://chatgpt.com/c/69f17a6e-4eb8-83e8-80c9-6d78bd09b421
进行了tf的补全，rviz2~gazebo能够正常联动，
但是，在取消tf发布后，仍然能够作用。
问过ai，回复是nav控制器退化，仅由odom作用，导致地图无法闭环

1. 确实是无法闭环，现在出现了远离世界原点，出现偏移的情况，如图![[Pasted image 20260429120555.png]]
2. ![[Pasted image 20260429120727.png]]



