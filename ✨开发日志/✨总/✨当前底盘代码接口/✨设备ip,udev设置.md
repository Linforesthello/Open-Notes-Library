192.168.1.200，windows，desktop

192.168.1.199，raspi4，ubuntu22.04，ros2humble
	astrapro

192.168.1.202，radxa，已废弃

192.168.1.204 vmware主机
	eth 10.10.3.30
192.168.1.？，raspi5，ubuntu24.04，docker-ros2humble
	astrapro
	
192.168.1.207 jetson nano
	eth 10.10.3.70

192.168.1.210 minipc n97

云主机

# 三个jlink设置了udev别名，根据是serial来的(唯一性)
ls -l /dev/ttyJLINK*

sudo udevadm control --reload-rules
sudo udevadm trigger

ls -l /dev/serial/by-id/