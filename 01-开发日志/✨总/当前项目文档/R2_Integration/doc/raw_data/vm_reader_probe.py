#!/usr/bin/env python3
"""判别 reader：raw + master 双路值直方，不再预判 -2/254"""
import rclpy, json, math
from rclpy.node import Node
from collections import Counter
from nav2_msgs.msg import Costmap
from nav_msgs.msg import OccupancyGrid
class R(Node):
    def __init__(self):
        super().__init__('vm_probe_reader')
        self.create_subscription(Costmap, '/costmap/costmap_raw', self.cb_raw, 10)
        self.create_subscription(OccupancyGrid, '/costmap/costmap', self.cb_master, 10)
        self.raw_cnt = self.master_cnt = 0
    def cb_raw(self, msg):
        meta = msg.metadata
        w, h, res = meta.size_x, meta.size_y, meta.resolution
        ox, oy = meta.origin.position.x, meta.origin.position.y
        c = Counter(msg.data)
        top = {k: v for k, v in c.most_common(8) if k != 0}
        lethal = []
        for i, v in enumerate(msg.data):
            if v == 254 or v == -2:
                lethal.append([round(ox + (i % w + 0.5) * res, 2), round(oy + (i // w + 0.5) * res, 2)])
        self.raw_cnt += 1
        if self.raw_cnt <= 3 or (lethal and self.raw_cnt % 5 == 1):
            print(f"[raw] 帧{self.raw_cnt} 非零值: {top} lethal格: {lethal[:8]}{'...' if len(lethal) > 8 else ''}", flush=True)
    def cb_master(self, msg):
        w, h, res = msg.info.width, msg.info.height, msg.info.resolution
        ox, oy = msg.info.origin.position.x, msg.info.origin.position.y
        c = Counter(msg.data)
        top = {k: v for k, v in c.most_common(8) if k != 0}
        lethal = []
        for i, v in enumerate(msg.data):
            if v == 100:
                lethal.append([round(ox + (i % w + 0.5) * res, 2), round(oy + (i // w + 0.5) * res, 2)])
        self.master_cnt += 1
        if self.master_cnt <= 3 or (lethal and self.master_cnt % 5 == 1):
            print(f"[master] 帧{self.master_cnt} 非零值: {top} lethal100格: {lethal[:8]}{'...' if len(lethal) > 8 else ''}", flush=True)
rclpy.init()
r = R()
rclpy.spin(r)
