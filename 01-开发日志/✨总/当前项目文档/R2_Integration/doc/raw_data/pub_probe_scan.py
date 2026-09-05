#!/usr/bin/env python3
"""判别轮 synthetic scan：0° 1.0m 单障碍（08-25 验证形态），5Hz BEST_EFFORT frame=velodyne"""
import math, rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import LaserScan
import time
rclpy.init()
n = Node('vm_probe_scan')
qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST,
                 depth=5, durability=DurabilityPolicy.VOLATILE)
pub = n.create_publisher(LaserScan, '/scan', qos)
def mk(t):
    msg = LaserScan()
    msg.header.stamp = t
    msg.header.frame_id = 'velodyne'
    msg.angle_min, msg.angle_max, msg.angle_increment = -math.pi, math.pi, math.pi/450.0
    msg.range_min, msg.range_max = 0.1, 30.0
    msg.ranges = [float('inf')] * 900
    # 0°(idx450)=1.0m 障碍 + 附近
    for k, az in enumerate([-0.02, -0.01, 0.0, 0.01, 0.02]):
        idx = int(round((az - msg.angle_min) / msg.angle_increment))
        msg.ranges[idx] = 1.0
    return msg
end = time.time() + 30
while time.time() < end:
    pub.publish(mk(n.get_clock().now().to_msg()))
    time.sleep(0.2)
