ubuntu20.04.6
# 1. 串口通信
[路径梳理与发展](https://chatgpt.com/c/69578ce8-ce60-8323-8a9f-8cc8b7c60ba5)
1. 树莓派串口通信，原本的串口，是作为登录串口使用的，所以直接发送信息会乱码；
	1. ![[Pasted image 20260105151007.png]]
	2. 删除了串口部分
		1. cat /proc/cmdline
		2. sudo nano /boot/firmware/cmdline.txt
		3. ==注意，我并未禁用串口登录服务==
		4. ![[Pasted image 20260105151037.png]]
2. 成功
	1. ![[Pasted image 20260105151232.png]]
	2. ![[Pasted image 20260105151210.png]]

# 2. 树莓派部署键盘，键盘控制车体底盘运动（串口发送）
![[WIN_20260103_10_26_35_Pro.mp4]]![[WIN_20260103_10_24_16_Pro.jpg]]![[WIN_20260103_10_32_46_Pro.jpg]]