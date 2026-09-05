#!/bin/bash
source /opt/ros/humble/setup.bash
PIDS=()
cleanup() { for p in "${PIDS[@]}"; do kill -9 "$p" 2>/dev/null; done; }
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_link >/tmp/tf1.log 2>&1 & PIDS+=($!)
ros2 run tf2_ros static_transform_publisher 0 0 0.655 0 0 0 base_link velodyne >/tmp/tf2.log 2>&1 & PIDS+=($!)
sleep 2
ros2 run nav2_costmap_2d nav2_costmap_2d --ros-args --params-file /tmp/costmap_vm_test_wall.yaml >/tmp/costmap_probe.log 2>&1 & PIDS+=($!)
sleep 3
timeout 15 ros2 lifecycle set /costmap/costmap configure >/dev/null 2>&1 || true
timeout 15 ros2 lifecycle set /costmap/costmap activate  >/dev/null 2>&1 || true
python3 /tmp/vm_reader_probe.py >/tmp/reader_probe.log 2>&1 & PIDS+=($!)
sleep 2
python3 /tmp/pub_probe_scan.py >/tmp/pub_probe.log 2>&1 & PIDS+=($!)
sleep 25
cleanup
echo DONE
