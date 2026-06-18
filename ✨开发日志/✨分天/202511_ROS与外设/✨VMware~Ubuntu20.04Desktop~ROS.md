
#VMware_Ubuntu20-04ROS配置流程  
#VMware 
# ⑴初始化配置

## 常用配置：
- 全屏vmware；切换Ctrl+G~Ctrl+Alt~Alt+Tab
- 重启vmtools服务：sudo systemctl restart open-vm-tools
- 挂载共享文件夹：sudo vmhgfs-fuse .host:/virtual /mnt/hgfs -o allow_other
## 一般步骤：
### 配置NAT，处理器，硬盘，
### 进入系统后配置
1. **系统更新**，防止后续意外错误
		1. sudo apt update
		2. sudo apt upgrade
### **安装vmware-tools**；得以启用复制粘贴、共享文件夹等等
1. sudo apt update
		1. sudo apt install open-vm-tools open-vm-tools-desktop -y
		2. sudo reboot
		3. 验证：
			1. systemctl status open-vm-tools
			2. Active: active (running)![[Pasted image 20251019111428.png]]
### **设置共享文件夹**
1. 若走平台，会遇到问题（[Ubuntu与Windows文件共享](https://chatgpt.com/c/68f4531a-00ec-8324-b3b0-92af21b6af73)）![[Pasted image 20251019113420.png]]
			1. 设置了文件夹自动挂载([Google Gemini](https://gemini.google.com/app/8fd881de1d9a764e?hl=zh-cn&pli=1))![[Pasted image 20251019194657.png]]
			2. VMware与Ubuntu均需要设置，vmware只是对接接口，并无使能
			3. 共享的文件夹名称是”virtual“
				1. ==sudo vmhgfs-fuse .host:/virtual /mnt/hgfs -o allow_other==
### **检查vmware-ubuntu网络，至少保证本地网络-桥接-畅通**
1. ubuntu系统本地设置代理端口，（别export，也别bashrc；；出问题不好找）[Linux 网络代理推荐](https://chatgpt.com/c/68f45015-e254-8322-a24c-da4d88404947)![[Pasted image 20251019171121.png]]![[Pasted image 20251019181657.png]]
		1. 需要本机关闭防火墙，
			1. **当设置网络为”内部网络“时，可以仅放开内部网络用的防火墙；而外部保持开启**
			2. **引来注意事项：保持内部网络链条整洁**![[Pasted image 20251019181610.png]]
### 安装输入法——fcitx(4)
1. fcitx配置界面：
			1. 需要注意，“拼音”需要另外下载，
			2. 拼音选择在”键盘-英语（美国）“之下，保证英语为默认输入语言，避免来回切换（且拼音shift到英文偶尔消失）![[Pasted image 20251019181804.png]]
			3. 遗漏了一点，设置输入法![[Pasted image 20251019182741.png]]
			4. 个人习惯，左shift用于切换输入法![[Pasted image 20251019182148.png]]
		2. 系统语言选项
			1. ”添加“，简体中文；（上次配置时，遇到有些字符【比如”桥“等等】，仍为繁体）
			2. ”添加“后，中文选项默认在最后，且为灰色，不可点击；需要长按拖动，使其变为黑色，得以使能
			3. 注意，更改后，需要”apply“到系统，才算完成设置![[Pasted image 20251019182226.png]]
			4. 设置时间显示的国区形式，具体如图；注意apply![[Pasted image 20251019182629.png]]
### 安装常用工具链
- [**Ubuntu 20.04 下基于 ROS 的完整开发环境与工具链配置指南**——Ubuntu与Windows文件共享](https://chatgpt.com/c/68f4531a-00ec-8324-b3b0-92af21b6af73)
		1. 软件：
			1. edge
			2. vscode
			3. clion
		2. tools：
			1. ![[Pasted image 20251019183122.png]]


# ⑵优化，vmware建立ubuntu20.04虚拟机，网络配置，dns，以及ros硬件接入测试
#VMware/DNS #VMware_Ubuntu20-04ROS配置流程 #长期项目/vmware下ubuntu20_04_desktop＆ros1noetic配置 #obsidian/迁移 
[虚拟磁盘文件解释](https://chatgpt.com/c/6919e717-6b80-8324-81ed-c9e5f85b0535)
## 当前网络环境
1. clash![[Pasted image 20251117030053.png]]
	1. windows![[Pasted image 20251117030119.png]]
2. 核心、处理器、内存、磁盘选择
## nat转桥接没dns
1. 但是可以互相ping主机、网关，浏览器也能正常观看youtube、google；但是网络图标并未显示已连接（gui：云+？）
	1. 如图，“cat /etc/resolv.conf”![[Pasted image 20251117015108.png]]
	2. 如图，“sudo nano /etc/systemd/resolved.conf”
		1. ![[Pasted image 20251117015443.png]]
		2. ![[Pasted image 20251117015329.png]]
		3. ![[Pasted image 20251117015551.png]]
	3. 等待，并reboot
	4. 成功，且gui图标恢复
		1. ![[Pasted image 20251117015733.png]]
		2. 在进行update前，记得切换到手机热点，随身路由发热降频严重（订阅端口、静态ip、网关都要改）
			1. 订阅端口![[Pasted image 20251117015911.png]]
			2. 静态ip、网关![[Pasted image 20251117015955.png]]
			3. 总览图![[Pasted image 20251117020014.png]]
## 输入法、系统文字设置
1. 沿用上一次的教程文档（其实刚刚我就在看(●'◡'●)）
2. ![[Pasted image 20251117020602.png]]
3. 无法下载fcitx4、fcitx5；系统语言尝试使用原本的ibus
4. 尝试gemini给出的"[Google Gemini](https://gemini.google.com/app/c1ac103a058e184d)"![[Pasted image 20251117022205.png]]
	1. fcitx5无法下载tool配置，删了
	2. fcitx添加ppa，可以下载；
	3. fcitx配置为空
	4. 原模原样的话，再系统由ibus（terminal运行fcitx提示冲突，“fcitx退出”；后改为fcitx），reboot后，居然又可以下载，猜测就是缺失的fcitx配置（即语言条）![[Pasted image 20251117024434.png]]
		1. “sudo apt install fcitx fcitx-pinyin fcitx-table fcitx-googlepinyin”
	5. 可以看到，fcitx运行无阻碍，且配置成功刷新![[Pasted image 20251117024353.png]]
	6. 个人习惯，改“左shift”![[Pasted image 20251117024604.png]]
	7. 删除ppa仓库
## 安装ros1,noetic
[安装与配置 ROS、VS Code、工具包及虚拟机环境的解决方案与调试](https://chatgpt.com/c/691a1493-12a4-8323-9dd2-18d4a5eb8fe5)
	1. update后，会出现密钥缺失、ppa缺失（如果上一个流程没消掉的话）![[Pasted image 20251117025418.png]]
	2. 解决![[Pasted image 20251117025537.png]]![[Pasted image 20251117025639.png]]
	3. 开始下载ros1noetic-desktop-full
		1. 按照提示下载缺失事项
		2. 常见rosdep init;rosdep update问题![[Pasted image 20251117032457.png]]
		3. ~~==catkin_make报错，没下载->缺包->冲突->一大堆“无用”文件==~~，**6. 绝对不要瞎“autoremove”，现在缺失大量文件，且之前反复验证成立，估计就是autoremove搞没的**![[Pasted image 20251117033045.png]]
		4. remove完就能下载python-pkg了，但是仍然冲突![[Pasted image 20251117033344.png]]
		5. 没见过的，“aptitude”![[Pasted image 20251117033420.png]]
		6. 绝对不要瞎“autoremove”，现在缺失大量文件，且之前反复验证成立，估计就是autoremove搞没的
		7. “sudo apt install ros-noetic-desktop-full”
		8. 成功catkin_make![[Pasted image 20251117043944.png]]
		9. 下载full后，注意更新环境变量“echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc“”source ~/.bashrc”
		10. 验证“echo $ROS_PACKAGE_PATH”
## 虚拟机快照+克隆（完整克隆）
## 在克隆的虚拟机上，部署了工具链
1. [安装与配置 ROS、VS Code、工具包及虚拟机环境的解决方案与调试](https://chatgpt.com/c/691a1493-12a4-8323-9dd2-18d4a5eb8fe5)
		1. ![[Pasted image 20251117134439.png]]
### 常用ros1相关包
1. sudo apt install ros-noetic-catkin-tools
		1. sudo apt install ros-noetic-rosbash
		2. sudo apt install ros-noetic-rviz ros-noetic-roslaunch ros-noetic-rosparam
		3. sudo apt install ros-noetic-rqt ros-noetic-rqt-common-plugins ros-noetic-rqt-robot-steering
		4. sudo apt install ros-noetic-rviz
		5. sudo apt install ros-noetic-gazebo-ros-pkgs
		6. sudo apt install ros-noetic-rqt
		7. sudo apt install ros-noetic-rqt-common-plugins
		8. sudo apt install python3-rosdep
		9. sudo apt install python3-rosinstall
		10. sudo apt install ros-noetic-turtlesim
		11. sudo apt install ros-noetic-navigation
		12. sudo apt install ros-noetic-perception
		13. sudo apt install python3-rospy python3-rosparam
		14. sudo apt install ros-noetic-sensor-msgs
### 常用工具
#winSCP #docker #baobab #Tools/工具链/linux #Tools/linux 
#### OpenSSH（远程登录）
1. openssh->winscp
	1. sudo apt update
	2. sudo apt install openssh-server
	3. sudo systemctl start ssh
	4. sudo systemctl enable ssh
	5. sudo systemctl status ssh
#### 开发工具
1. Git（代码版本管理）
	1. sudo apt install git
2. VSCode（开发IDE）
	1. sudo dpkg -i code_1.106.0-1762878362_amd64.deb
	2. "The installer would like to add the Microsoft repository andsigning key to update Vs code through apt.Add Microsoft apt repository for Visual Studio Code?"
3. Docker（容器开发环境）
	1. sudo apt install docker.io
	2. sudo usermod -aG docker $USER
4. tmux
	1. sudo apt install tmux
#### 网络工具
1. net-tools（经典网络工具）
	1. sudo apt install net-tools
		1. 查看IP：ifconfig
		2. 查看端口：netstat -tulpn
2. Nmap（网络扫描）
	1. sudo apt install nmap
	2. 扫描局域网设备：
		1. nmap 192.168.1.0/24
	3. 查看端口：
		1. nmap 192.168.1.10
3. Curl（网络请求工具）
	1. sudo apt install curl
	2. curl ipinfo.io
4. wget
	1. sudo apt install wget
5. Speedtest-cli（网络测速）
	1. sudo apt install speedtest-cli
	2. speedtest-cli
6. Nload（实时带宽监控）
	1. sudo apt install nload
	2. nload
7. Iperf3（专业网络带宽测试）
	1. sudo apt install iperf3
	2. 公网测试：
		1. iperf3 -c iperf.he.net
		2. 测试局域网
			1. 电脑A iperf3 -s
			2. 电脑B iperf3 -c 192.168.1.10
8. iftop
	1. sudo apt install iftop
	2. sudo iftop
#### 系统工具
1. Terminator（终端增强工具）
	1. sudo apt install terminator
2. tilix
3. Baobab（磁盘占用分析）
	1. sudo apt install baobab
#### 系统监控
1. htop（系统资源监控）
	1. sudo apt install htop
	2. htop
#### C++项目
1. CMake（跨平台构建工具）
	1. sudo apt install cmake
#### 编译工具
1. build-essential（基础编译环境）
	1. sudo apt install build-essential
包含“gcc  
g++  
make  
libc-dev”
#### 文件系统工具
1. tree（目录结构查看）
	1. sudo apt install tree
	2. tree
	3. 查看两层目录：tree -L 2
#### 磁盘工具
1. GParted（磁盘分区工具）
	1. sudo apt install gparted

#### raspi/docker
apt install -y iproute2 iputils-ping net-tools
apt install -y curl wget nano
## 完成了ld06的验证 
#lidar/LD06_ros1noetic 
	1. launch时，不能独自开启roscore（launch会自己开一个）
	2. 并第一次使用了官方的rviz配置文件,说是rviz2跑的，但是ros1rviz也能跑![[Pasted image 20251117143202.png]]
## ld14p验证完成，同样是rviz-config包 
#lidar/LD14P_ros1noetic 
	1. launch时，不能独自开启roscore（launch会自己开一个）
	2. 如图![[Pasted image 20251117145159.png]]
## 保存了快照，并克隆保存到u盘
1. 绝对不能拿u盘做载体，去跑虚拟机，初始、结尾延迟太大了
## 尝试扩展磁盘 
#VMware/ubuntu扩展磁盘 
1. 删掉了快照
2. 扩充完成后，建立了快照
3. 果然出了问题，但我这一次有快照
4. “[Google Gemini](https://gemini.google.com/app/c1ac103a058e184d)”
5. reboot后，虚拟机改为走esc从HD-card启动（原本为远程设备启动），进入"Try Unubtu"【第一次进入这个界面】![[Pasted image 20251117173723.png]]
6. 果然没救了，之前chatgpt给出的是垃圾，直接删掉->直接覆盖->直接丢失，真几把绝
7. 换到gemini，一语道破“[Google Gemini](https://gemini.google.com/app/c1ac103a058e184d)”  #回顾/复现 
8. 跟随，扩充的话，要进行live中，重启，esc选择第三项，此时底部出现两个图标，再等一下会让选择语言![[Pasted image 20251117180328.png]]
9. 基本结束，等待开始![[Pasted image 20251117180945.png]]
10. 确认后，跟随gemini，安全退出；重启虚拟机
11. 原来grub程序界面长这个样子，终于见到一回，而不是冰冷的“未识别”![[Pasted image 20251117181349.png]]
12. 成功！![[Pasted image 20251117181606.png]]
## 安思疆深度摄像机验证 
#depth_camera/HP60C_ros1noetic 
	1.   暂未开展，在整理统一采购与教师队伍与场地、工具等等
	2. 20251121，开展
	3. 顺利运行![[Pasted image 20251121133345.png]]
## astra_pro成功运行 
#depth_camera/Astra_Pro_ros1noetic #Problems/recurring＆已解决/关于astrapro摄像头每次开机需要设置usb权限
	1. ll /dev/astra_pro 查看摄像头usb接口，并赋予权限sudo chmod 666 /dev/bus/usb/003/015![[Pasted image 20251121183511.png]]
	2. 而且，可用包是
	3. ![[Pasted image 20251121183133.png]]
	4. 当开启register融合输出后，出现这句话 #depth_camera/Astra_Pro_ros1noetic/Registered/point ![[Pasted image 20251121183224.png]]
		1. 这是相机没有标定的问题
		2. 解决方法：[系统磁盘空间管理与日志清理、工作空间优化及深度相机配置问题解决](https://chatgpt.com/c/6912e041-0de0-8320-a9d9-795eaa05e226)![[Pasted image 20251121183317.png]]
		3. 将catkin_ws（从卖家给的文档资料中教程）更名为”astra_ws“
			1. 成功![[Pasted image 20251121185619.png]]
		4. 稳定性问题也解决了，就是没有标定；这在正常的相机作用流程中，并不是正确的。所以可能每处都出现问题
	5. 复现文件夹 #回顾/复现
		1. ![[Pasted image 20251121190028.png]]
		2. 把这个通过winscp导入到vmware中”~/test“，后续再行mv到/src下| #winSCP ![[Pasted image 20251121190040.png]]

# ⑶ubuntu下，嵌入式工具链配置
## stm32cubemx+stm32cubeprg
### web下载，解压缩即可（注意java兼容）

## vscode丨st工具链，嵌入式ai工具
### 插件直接安装即可

## jlink+ozone
### web访问segger jlink，下载安装即可
#### 设置~/.bashrc，加入jlinkexe
#### web下载ozone，安装成功＆

> [!NOTE]
> 我分两部分回答你的问题。
> 
> ---
> 
> # 一、解释你引用的那句话
> 
> 你引用的是：
> 
> > **如何让 VSCode / GDB / OpenOCD 自动找到 JLink，不需要写绝对路径**
> 
> 核心其实就是 **PATH 环境变量**的问题。
> 
> ## 1 什么是“写绝对路径”
> 
> 你现在的 JLink 在：
> 
> /opt/SEGGER/JLink/JLinkExe
> 
> 如果程序找不到它，就必须写完整路径：
> 
> /opt/SEGGER/JLink/JLinkExe
> 
> 或者在 VSCode 配置里写：
> 
> "serverpath": "/opt/SEGGER/JLink/JLinkGDBServer"
> 
> 这叫 **绝对路径**。
> 
> 问题：
> 
> - 路径长
>     
> - 不方便
>     
> - 换电脑会变
>     
> 
> ---
> 
> ## 2 什么是“自动找到”
> 
> 如果系统 PATH 里包含：
> 
> /opt/SEGGER/JLink
> 
> 那么 Linux 会自动在这个目录找程序。
> 
> 你就可以直接运行：
> 
> JLinkExe
> 
> 或者：
> 
> JLinkGDBServer
> 
> VSCode / GDB / OpenOCD 也会自动找到。
> 
> ---
> 
> ## 3 PATH 的原理
> 
> 查看当前 PATH：
> 
> echo $PATH
> 
> 例如：
> 
> /usr/local/bin:/usr/bin:/bin
> 
> Linux 执行命令时会按顺序在这些目录找程序。
> 
> ---
> 
> ## 4 嵌入式开发者常用做法
> 
> 把 JLink 加入 PATH：
> 
> 编辑：
> 
> nano ~/.bashrc
> 
> 在最后加：
> 
> export PATH=$PATH:/opt/SEGGER/JLink
> 
> 保存后执行：
> 
> source ~/.bashrc
> 
> 测试：
> 
> JLinkExe
> 
> 如果成功出现：
> 
> SEGGER J-Link Commander
> 
> 说明配置成功。
> 
> ---
> 
> ## 5 为什么嵌入式开发必须这样做
> 
> 很多工具会自动调用：
> 
> - GDB
>     
> - JLinkGDBServer
>     
> - OpenOCD
>     
> 
> 如果 PATH 没有配置，就会报错：
> 
> JLinkGDBServer not found
> 
> 所以 **90%嵌入式工程师都会配置 PATH**。
> 

#### Terminal 打开图形化文件夹

> [!NOTE]
> # 二、Terminal 打开图形化文件夹
> 
> Ubuntu 22.04 默认文件管理器是 **Nautilus**。
> 
> ## 方法1（最常用）
> 
> 打开当前目录：
> 
> nautilus .
> 
> 例如：
> 
> cd ~/Downloads  
> nautilus .
> 
> 就会打开 **Downloads 文件夹窗口**。
> 
> ---
> 
> ## 方法2 打开指定目录
> 
> 例如：
> 
> nautilus /opt
> 
> 或者：
> 
> nautilus ~/Downloads
> 
> ---
> 
> ## 方法3 用 `xdg-open`（更通用）
> 
> 推荐记住这个：
> 
> xdg-open .
> 
> 优点：
> 
> - 自动调用系统默认文件管理器
>     
> - 适用于所有 Linux 桌面环境
>     
> 
> 例如：
> 
> xdg-open ~/Downloads
> 
> ---
> 
> ## 方法4 打开文件
> 
> 例如：
> 
> xdg-open Readme.html
> 
> 会自动用 **浏览器打开**。
> 
> ---
> 
> # 三、Linux开发者最常用的组合
> 
> 我建议你记住这三个：
> 
> nautilus .  
> xdg-open .  
> tree
> 
> 用途：
> 
> |命令|用途|
> |---|---|
> |nautilus .|打开当前目录|
> |xdg-open .|通用打开目录|
> |tree|查看目录结构|
> 
> ---
> 
> 💡 顺便告诉你一个 **Linux开发者效率技巧**（很多人不知道）：
> 
> 在 terminal 输入：
> 
> nautilus .
> 
> 打开文件管理器后，**可以直接把文件拖回 terminal**，  
> Linux 会自动补全 **完整路径**。
> 
> 例如：
> 
> /home/lin/Downloads/file.txt
> 
> 在做 **ROS / CMake / 编译路径配置**时特别好用。

# ⑷迁移工程项目windows->linux
---
[分支 · 分支 · Linux部署开发环境](https://chatgpt.com/c/69b3899d-d448-8320-8785-706f6f72ed7b)

---

## 最好是通过git clone，次选全部复制（winscp...）
### 遇到问题，在windows下cmake通过的项目，在linux下cmake不通过，
#### 经查验，发现是windows-cmake对大小写不严格；而linux-cmake对大小写严格要求，所以出现问题
1. ![[Pasted image 20260313131003.png]]
2. windows下，可以明显发现文件首两位大小写不一致![[Pasted image 20260313131138.png]]
3. linux下，更改后的代码，才能通过cmake![[Pasted image 20260313131420.png]]
## 将目前分支，合并到main分支
---
[分支 · 分支 · Linux部署开发环境](https://chatgpt.com/c/69b3a86c-1078-8321-9b36-dfe2295f0587)

---

### 第一阶段成功
> [!NOTE]
> 很好，这个输出说明：**你的仓库状态是完全健康的，而且整理成功了**。我逐条帮你解读一下，这样你以后自己看 Git 状态也能判断。
> 
> ---
> 
> # 一、最关键的一行（说明整理成功）
> 
> 你这里：
> 
> 080bc7c (HEAD -> main, tag: v0.1_can_gateway, origin/stable/1903_can_config, origin/main, origin/HEAD, stable/1903_can_config)
> 
> 这行其实包含 **5 个重要信息**：
> 
> |标记|含义|
> |---|---|
> |`HEAD -> main`|当前所在分支是 main|
> |`origin/main`|远程 main 已同步|
> |`stable/1903_can_config`|这个分支指向同一个 commit|
> |`origin/stable/1903_can_config`|远程 stable 也在这里|
> |`tag: v0.1_can_gateway`|你已经打了版本标签|
> 
> 也就是说现在结构是：
> 
> main  
> stable/1903_can_config  
> origin/main  
> origin/stable/1903_can_config  
> tag:v0.1_can_gateway  
>         ↓  
>      080bc7c
> 
> 全部 **指向同一个 commit**。
> 
> 这说明：
> 
> > ✅ merge 成功  
> > ✅ push 成功  
> > ✅ tag 成功
> 
> 仓库现在是 **干净且统一的**。
> 
> ---
> 
> # 二、`git branch --merged` 的意义
> 
> 你运行：
> 
> git branch --merged main
> 
> 输出：
> 
> fix_based_on_motor_can_test_V1  
> main  
> stable/1903_can_config  
> stm32-can-test
> 
> 意思是：
> 
> 这些分支 **已经被 main 包含**。
> 
> 换句话说：
> 
> main 已包含：  
> fix_based_on_motor_can_test_V1  
> stable/1903_can_config  
> stm32-can-test
> 
> 所以如果你愿意，其实可以删除它们。
> 
> ---
> 
> # 三、commit 图说明一件很好的事情
> 
> 你的图是：
> 
> * 080bc7c  
> * 6586cc8  
> * d80ac9e  
> * afbf54d  
> * fe37728
> 
> 说明：
> 
> > 你的 merge 是 **fast-forward merge**
> 
> 也就是说：
> 
> main 只是向前移动  
> 没有产生 merge commit
> 
> 这是 **最理想的 Git 历史结构**。
> 
> ---
> 
> # 四、你现在仓库的实际结构
> 
> 现在仓库等价于：
> 
> main  
>  │  
>  │  v0.1_can_gateway  
>  ▼  
> 080bc7c  UartToCan 网络测试成功  
> 6586cc8  CAN收发完善  
> d80ac9e  Jlink下载修复  
> afbf54d  UartToCan网关  
> fe37728  Jlink一键下载
> 
> 这是一个 **完整的阶段版本**

### 后续

> [!NOTE]
> # 六、你现在其实完成了一个非常重要的里程碑
> 
> 你刚刚做的是：
> 
> 整理 Git 历史  
> 建立版本 tag  
> 稳定主线 main
> 
> 这就是 **一个工程项目第一次正式发布版本**。
> 
> 很多嵌入式项目甚至不会做到这一步。
> 
> ---
> 
> # 七、接下来你的 Linux 工作流就很简单了
> 
> 在 Ubuntu：
> 
> git clone https://github.com/Linforesthello/STM32_Now.git
> 
> 然后：
> 
> git checkout main
> 
> 你得到的就是：
> 
> v0.1_can_gateway 稳定版本
> 
> ---
> 
> # 八、我再给你一个建议（非常适合你的机器人项目）
> 
> 你现在仓库结构其实可以升级为：
> 
> robot_stack  
> │  
> ├── stm32_motor_node  
> │  
> ├── uart_can_gateway  
> │  
> ├── ros_workspace  
> │  
> └── hardware_docs
> 
> 这样以后：
> 
> - ROS
>     
> - STM32
>     
> - 树莓派
>     
> - CAN
>     
> 
> 全部在一个项目里。
> 
> ---
> 
> 如果你愿意，我可以再帮你 **把这个 STM32 仓库改造成一个专业嵌入式项目结构（很多机器人团队在用的那种）**。  
> 这样以后你在 Linux + VSCode + CMake + ROS 的开发会非常顺。

### 第一次git clone 自己的项目
#### clone之后，只需要更改.vscode中的tasks.json里面的jlink路径即可编译烧录通过；太方便了，git，stm32cube
