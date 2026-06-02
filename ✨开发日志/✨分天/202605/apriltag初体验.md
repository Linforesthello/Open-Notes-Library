
![[Pasted image 20260520211418.png]]


ros2 run apriltag_ros apriltag_node \
--ros-args \
-r image_rect:=/camera/color/image_raw \
-r camera_info:=/camera/color/camera_info

ros2 topic echo /tf


## orbbec tornado d2测试。感谢大船




---

## 二、 普通 RGB 摄像头测试工具 (GUI 图形界面)

如果只想快速测试 Astra 的 **RGB 彩色画面（UVC部分）**，或者普通的免驱 USB 摄像头、笔记本自带摄像头，以下 GUI 工具开箱即用：

### 1. Cheese (茄子) —— 简单直观

Ubuntu 社区最常用的自带/推荐相机测试软件，基于 GStreamer。

* **特点**：界面极其简单，支持拍照、录像、添加滤镜。
* **安装命令**：
```bash
sudo apt update
sudo apt install cheese

```


* **使用**：直接在应用菜单搜索 "Cheese" 或在终端输入 `cheese` 运行。如果有多路相机，可以在其“首选项”中切换设备。

### 2. Guvcview —— 开发者必备（功能最全）

相比 Cheese，**Guvcview 是专门为 UVC 摄像头调优和测试设计的**，功能更偏向底层控制。

* **特点**：可以非常详细地调节镜头的各项参数（曝光度、白平衡、亮度、对比度、增益、帧率、分辨率等），支持切换不同的视频格式（YUYV、MJPEG、H264）。
* **安装命令**：
```bash
sudo apt install guvcview

```



### 3. VLC Media Player —— 万能播放器测试法

VLC 不仅能看片，还能直接捕获硬件输入流。

* **使用方法**：打开 VLC -> `媒体 (Media)` -> `打开捕获设备 (Open Capture Device)` -> 捕获模式选择 `Video camera` -> 在 `视频设备名称` 中选择 `/dev/video0`（或video1/2），点击播放即可。

---

## 三、 终端与命令行测试工具 (高级/远程调试)

如果你使用的是 **Ubuntu Server（无桌面环境）**，或者通过 SSH 远程连接机器人，你需要使用命令行工具：

### 1. v4l2-ctl (Video4Linux2 工具)

这是 Linux 下排查摄像头问题**最核心、最底层的硬核工具**。

* **安装命令**：
```bash
sudo apt install v4l-utils

```


* **常用测试命令**：
* *查看当前连接了哪些摄像头设备*：
```bash
v4l2-ctl --list-devices

```


* *查看某个摄像头（如 /dev/video0）支持的分辨率、格式和帧率*：
```bash
v4l2-ctl -d /dev/video0 --list-formats-ext

```


* *查看当前相机的曝光、白平衡等控制参数设置*：
```bash
v4l2-ctl -d /dev/video0 --list-ctrls

```





### 2. FFmpeg / mplayer

可以使用命令行工具直接抓取一帧图片或一段视频，用来验证相机是否正常工作。

* **用 FFmpeg 截取一张相机照片**：
```bash
ffmpeg -f video4linux2 -i /dev/video0 -vframes 1 test.jpg

```


* **用 mplayer 播放实时画面（需要 X11 转发或有桌面）**：
```bash
sudo apt install mplayer
mplayer tv:// -tv driver=v4l2:device=/dev/video0

```



---

## 总结建议

* 如果是**刚插上 Astra 相机想看深度图和点云** $\rightarrow$ 优先用 **Orbbec Viewer** 或配置 **ROS + Rviz**。
* 如果只想**快速看一眼 RGB 画面亮不亮** $\rightarrow$ 直接终端输入 `cheese`。
* 如果发现**画面太暗、卡顿，想调分辨率或曝光参数** $\rightarrow$ 使用 `guvcview` 或命令行 `v4l2-ctl`。


