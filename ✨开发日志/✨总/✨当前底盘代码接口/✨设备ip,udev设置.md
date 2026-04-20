192.168.1.200，windows，desktop
192.168.1.199，raspi4，ubuntu22.04，ros2humble
	astrapro
192.168.1.202，radxa，已废弃
192.168.1.204

192.168.1.？，raspi5，ubuntu24.04，docker-ros2humble
	astrapro

# 三个jlink设置了udev别名，根据是serial来的(唯一性)
ls -l /dev/ttyJLINK*

sudo udevadm control --reload-rules
sudo udevadm trigger

ls -l /dev/serial/by-id/