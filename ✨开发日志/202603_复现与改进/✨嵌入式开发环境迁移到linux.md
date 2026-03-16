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
	3. 