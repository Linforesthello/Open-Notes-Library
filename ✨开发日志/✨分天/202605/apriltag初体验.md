
![[Pasted image 20260520211418.png]]


ros2 run apriltag_ros apriltag_node \
--ros-args \
-r image_rect:=/camera/color/image_raw \
-r camera_info:=/camera/color/camera_info

ros2 topic echo /tf

