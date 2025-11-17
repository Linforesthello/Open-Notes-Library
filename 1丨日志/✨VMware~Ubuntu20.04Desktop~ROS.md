
#VMware_Ubuntu20-04ROS配置流程  #VMware 
# 初始化配置

### 常用配置：
- 全屏vmware；切换Ctrl+G~Ctrl+Alt~Alt+Tab
- 重启vmtools服务：sudo systemctl restart open-vm-tools
- 挂载共享文件夹：sudo vmhgfs-fuse .host:/virtual /mnt/hgfs -o allow_other
### 一般步骤：
1. 配置NAT，处理器，硬盘，
2. 进入系统后配置
	1. **系统更新**，防止后续意外错误
		1. sudo apt update
		2. sudo apt upgrade
	2. **安装vmware-tools**；得以启用复制粘贴、共享文件夹等等
		1. sudo apt update
		2. sudo apt install open-vm-tools open-vm-tools-desktop -y
		3. sudo reboot
		4. 验证：
			1. systemctl status open-vm-tools
			2. Active: active (running)![[Pasted image 20251019111428.png]]
	3. **设置共享文件夹**
			1. 若走平台，会遇到问题（[Ubuntu与Windows文件共享](https://chatgpt.com/c/68f4531a-00ec-8324-b3b0-92af21b6af73)）![[Pasted image 20251019113420.png]]
			2. 设置了文件夹自动挂载([Google Gemini](https://gemini.google.com/app/8fd881de1d9a764e?hl=zh-cn&pli=1))![[Pasted image 20251019194657.png]]
			3. VMware与Ubuntu均需要设置，vmware只是对接接口，并无使能
			4. 共享的文件夹名称是”virtual“
				1. ==sudo vmhgfs-fuse .host:/virtual /mnt/hgfs -o allow_other==
	4. **检查vmware-ubuntu网络，至少保证本地网络-桥接-畅通**
		1. ubuntu系统本地设置代理端口，（别export，也别bashrc；；出问题不好找）[Linux 网络代理推荐](https://chatgpt.com/c/68f45015-e254-8322-a24c-da4d88404947)![[Pasted image 20251019171121.png]]![[Pasted image 20251019181657.png]]
		2. 需要本机关闭防火墙，
			1. **当设置网络为”内部网络“时，可以仅放开内部网络用的防火墙；而外部保持开启**
			2. **引来注意事项：保持内部网络链条整洁**![[Pasted image 20251019181610.png]]
	5. 安装输入法——fcitx(4)
		1. fcitx配置界面：
			1. 需要注意，“拼音”需要另外下载，
			2. 拼音选择在”键盘-英语（美国）“之下，保证英语为默认输入语言，避免来回切换（且拼音shift到英文偶尔消失）![[Pasted image 20251019181804.png]]
			3. 遗漏了一点，设置输入法![[Pasted image 20251019182741.png]]
			4. 个人习惯，左shift用于切换输入法![[Pasted image 20251019182148.png]]
		3. 系统语言选项
			1. ”添加“，简体中文；（上次配置时，遇到有些字符【比如”桥“等等】，仍为繁体）
			2. ”添加“后，中文选项默认在最后，且为灰色，不可点击；需要长按拖动，使其变为黑色，得以使能
			3. 注意，更改后，需要”apply“到系统，才算完成设置![[Pasted image 20251019182226.png]]
			4. 设置时间显示的国区形式，具体如图；注意apply![[Pasted image 20251019182629.png]]
	6. 安装常用工具链
	 - [**Ubuntu 20.04 下基于 ROS 的完整开发环境与工具链配置指南**——Ubuntu与Windows文件共享](https://chatgpt.com/c/68f4531a-00ec-8324-b3b0-92af21b6af73)
		1. 软件：
			1. edge
			2. vscode
			3. clion
		2. tools：
			1. ![[Pasted image 20251019183122.png]]
			2. 