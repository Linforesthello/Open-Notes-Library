#depth_camera/Astra_Pro_ros1noetic 
## launch后，rgb&ir的image正常，但是depth不正常；
插拔后正常；之间改过rviz的“Fixed Frame”

[视觉主导决策架构](https://chatgpt.com/c/699046aa-0af4-8323-9f1d-9cda84b94e2b)
rosrun computer_vision_tutorial simple_cv_node.py
## 识别红色，画出物体，标明物体中心点
在原有的程序上进行了改动
1. 文件地址/home/lin/workspaces/astra_vision_ws/src/computer_vision_tutorial/src/simple_cv_node.py
2. 结果图片![[Pasted image 20260220174700.png]]

## 识别被关注物体中心点像素位置，以及距离
1. ![[Pasted image 20260220182329.png]]
2. 问题是存在的，过近过远都无法识别到，跟光照有很大关系

## 在输出图像上中心点位置附加实时距离信息输出
1. ![[Pasted image 20260220185115.png]]
2. ![[Pasted image 20260220185356.png]]


> [!NOTE]
> 好的，我来为您解读这个更新后的 `/home/lin/workspaces/astra_vision_ws/src/computer_vision_tutorial/src/simple_cv_node.py` 文件。
> 
> 与之前的版本相比，这个脚本的功能得到了显著增强。它现在不仅能进行颜色识别，还能结合深度摄像头来测量被识别物体的距离。
> 
> ### 文件作用
> 
> 该脚本的核心作用是：
> 
> 1.  **初始化ROS节点**: 创建一个名为 `simple_cv_node` 的ROS节点。
> 2.  **订阅图像和深度数据**:
>     *   订阅RGB彩色图像话题 (`/camera/rgb/image_raw`)。
>     *   订阅与之对齐的深度图像话题 (`/camera/depth_registered/image_raw`)。
> 3.  **识别红色物体**: 在彩色图像中，通过颜色过滤（HSV色彩空间）来检测红色的物体。
> 4.  **定位物体中心**: 对检测到的最大的红色物体，计算其轮廓和质心（中心点）。
> 5.  **测量距离**: 利用物体在彩色图像中的中心点坐标，查询深度图像中对应点的深度值，从而得到摄像头到物体的直线距离。
> 6.  **可视化结果**:
>     *   在彩色图像上，用蓝色框标出物体轮廓，用绿色点标出物体中心。
>     *   在物体中心旁边显示测得的距离（单位：米）。
>     *   同时显示一个只包含红色物体的二值化 "mask" 图像，方便调试。
> 
> ### 实现方式
> 
> 代码通过 `SimpleCVNode` 类实现其功能，主要分为以下几个部分：
> 
> 1.  **`__init__(self)` (构造函数)**:
>     *   初始化ROS节点和 `CvBridge`。
>     *   创建了两个订阅者：
>         *   `self.image_sub` 订阅彩色图像，回调函数为 `self.image_callback`。
>         *   `self.depth_sub` 订阅深度图像，回调函数为 `self.depth_callback`。
>     *   `self.depth_image = None`: 初始化一个变量，用于存储最新接收到的深度图像。
> 
> 2.  **`depth_callback(self, msg)` (深度图像回调)**:
>     *   此函数在接收到新的深度图像时被调用。
>     *   它使用 `CvBridge` 将ROS深度图像消息转换为OpenCV格式。`desired_encoding="passthrough"` 确保了深度数据（通常是16位无符号整数或32位浮点数）在转换过程中保持其原始精度。
>     *   将转换后的深度图存放在 `self.depth_image` 中，以供RGB回调函数使用。
> 
> 3.  **`image_callback(self, msg)` (彩色图像回调)**:
>     *   这是最核心的函数，在接收到新的彩色图像时被调用。
>     *   **颜色检测**:
>         *   将图像从BGR色彩空间转换到HSV色彩空间，因为HSV对光照变化的鲁棒性更好，更适合颜色识别。
>         *   定义了两个红色的HSV阈值范围（因为红色在HSV色轮上跨越了0/180度的边界），并创建对应的 `mask`。
>         *   将两个 `mask` 合并，得到所有红色区域的二值图像。
>     *   **轮廓分析**:
>         *   `cv2.findContours`: 在 `mask` 上查找所有独立物体的轮廓。
>         *   `c = max(contours, key=cv2.contourArea)`: 如果找到了轮廓，就找出其中面积最大的一个，这通常就是我们感兴趣的主要目标。
>         *   `cv2.contourArea(c) > 500`: 通过面积阈值过滤掉过小的、可能是噪声的红色斑点。
>     *   **质心计算与深度测量**:
>         *   `M = cv2.moments(c)`: 计算最大轮廓的几何矩。
>         *   `cx = int(M["m10"] / M["m00"])`: 通过几何矩计算出轮廓的质心x, y坐标 (`cx`, `cy`)。
>         *   `if self.depth_image is not None`: 检查是否已经收到了深度图像。
>         *   `depth_value = self.depth_image[cy, cx]`: **关键步骤**。使用彩色图像中计算出的质心坐标 `(cx, cy)`，直接在深度图像 `self.depth_image` 的相同位置查找对应的深度值。因为深度图是与彩色图对齐过的，所以两个图像的坐标是对应的。
>         *   `rospy.loginfo_throttle(...)`: 将测得的距离打印到ROS的日志中，`throttle(1)`表示每秒最多打印一次，防止刷屏。
>     *   **结果可视化**:
>         *   `cv2.circle` 和 `cv2.drawContours`: 在原图上绘制质心和轮廓。
>         *   `cv2.putText`: 将测得的距离文本绘制在质心旁边。
>         *   `cv2.imshow`: 显示处理后的彩色图像和红色的 `mask` 图像。
> 
> 4.  **`run(self)` 和 `if __name__ == '__main__':`**:
>     *   这部分是标准的ROS Python节点启动代码，通过 `rospy.spin()` 使程序保持运行以持续接收消息，并在程序退出时通过 `cv2.destroyAllWindows()` 关闭所有OpenCV窗口。
> 
> **文件底部的注释代码**是被注释掉的旧版本，它们分别实现了“红色目标检测（无测距）”和“灰度图与固定中心圆绘制”的功能，可以作为学习和理解代码演进过程的参考。

## 下载yolo/ultralytics（pip3 install ultralytics）
![[Pasted image 20260220191201.png]]

## 得给小路由整一个散热了，太容易过热，过热后可能降速
#Tools/internet/随身wifi 
1. ![[WIN_20260220_21_40_28_Pro.jpg]]
2. ![[WIN_20260220_21_40_41_Pro.jpg]]