
# 方案：色域采样点网格密度聚类检测

  

## Context

  

当前检测依赖 `findContours → minEnclosingCircle` 获取球心。

对黄蓝双色球，掩码常有缺口（两色之间的暗带），导致：

- 轮廓断裂 → `contourArea` 偏小，半径校验失败

- `minEnclosingCircle` 对残缺轮廓偏大 → 已换成面积等效半径，但根源未解决

  

**新思路**：对掩码前景像素做网格密度统计，取密度最高的格子中心作为球心。

密度法天然对缺口鲁棒（整体像素分布仍集中在球体区域），且纯 NumPy 实现 <1ms。

  

---

  

## 改动文件

  

`/home/lin/Lin_workspace/vision/gpt_CommandLine.py`

  

---

  

## 实施步骤

  

### Step 1 — `__init__` 新增参数（ball_pub 之前）

  

```python

# ── 网格密度聚类参数 ─────────────────────────────────

self.grid_size = 16 # 格子边长（像素，基于 img_scale=0.5 后分辨率）

self.show_heatmap = True # 是否叠加密度热力图

self.density_min_pixels = 20 # 峰值格子最低有效像素数

```

  

---

  

### Step 2 — 新增私有方法 `_detect_by_density`（camera_info_callback 之前）

  

```python

def _detect_by_density(self, mask, grid_size):

"""

网格密度图聚类。替代 findContours + minEnclosingCircle。

Returns: (found, center_x, center_y, radius, draw_radius, norm_density)

"""

h, w = mask.shape[:2]

yx = np.where(mask > 0)

if yx[0].size < self.density_min_pixels:

empty = np.zeros((h // grid_size + 1, w // grid_size + 1), dtype=np.float32)

return False, 0, 0, 0.0, 0.0, empty

  

y_coords = yx[0].astype(np.float32)

x_coords = yx[1].astype(np.float32)

  

x_bins = np.arange(0, w + grid_size, grid_size)

y_bins = np.arange(0, h + grid_size, grid_size)

hist, x_edges, y_edges = np.histogram2d(x_coords, y_coords, bins=[x_bins, y_bins])

density_map = hist.T # (n_rows, n_cols) 与图像方向对齐

  

peak_flat_idx = np.argmax(density_map)

peak_row, peak_col = np.unravel_index(peak_flat_idx, density_map.shape)

peak_val = density_map[peak_row, peak_col]

  

if peak_val < self.density_min_pixels:

return False, 0, 0, 0.0, 0.0, np.zeros_like(density_map, dtype=np.float32)

  

center_x = int((x_edges[peak_col] + x_edges[peak_col + 1]) / 2.0)

center_y = int((y_edges[peak_row] + y_edges[peak_row + 1]) / 2.0)

  

# 密度等效半径：统计密度 ≥ 峰值25% 的格子内前景像素总数

density_threshold = peak_val * 0.25

valid_pixels = float(np.sum(density_map[density_map >= density_threshold]))

radius = float(np.sqrt(valid_pixels / np.pi))

draw_radius = radius

  

# 归一化密度图供热力图使用

norm_density = density_map.astype(np.float32)

max_val = norm_density.max()

if max_val > 0:

norm_density /= max_val

  

return True, center_x, center_y, radius, draw_radius, norm_density

```

  

---

  

### Step 3 — `image_callback` 替换：步骤3（原 L138–L231 整块替换）

  

**删除**：

```python

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours:

largest_contour = max(contours, key=cv2.contourArea)

((x, y), draw_radius) = cv2.minEnclosingCircle(largest_contour)

area = cv2.contourArea(largest_contour)

radius = np.sqrt(area / np.pi)

if draw_radius > 10:

center_x, center_y = int(x), int(y)

# … 整个 if contours 块内部

```

  

**替换为**：

  

```python

# 3. 网格密度图聚类检测

found, center_x, center_y, radius, draw_radius, norm_density = \

self._detect_by_density(mask, self.grid_size)

  

# 热力图叠加（show_heatmap=True 时）

if self.show_heatmap and norm_density.size > 0:

h_img, w_img = color_image.shape[:2]

heatmap_u8 = (norm_density * 255).astype(np.uint8)

heatmap_u8 = cv2.resize(heatmap_u8, (w_img, h_img),

interpolation=cv2.INTER_NEAREST)

heatmap_color = cv2.applyColorMap(heatmap_u8, cv2.COLORMAP_JET)

color_image = cv2.addWeighted(color_image, 0.65, heatmap_color, 0.35, 0)

  

if found and draw_radius > 5:

# 十字准星

cs = 12

cv2.line(color_image, (center_x-cs, center_y), (center_x+cs, center_y), (0,255,0), 2)

cv2.line(color_image, (center_x, center_y-cs), (center_x, center_y+cs), (0,255,0), 2)

  

# 5~7. 深度采样 / 3D计算 / 距离过滤 / 半径校验 / 发布（与原代码完全相同）

try:

h_img, w_img = depth_image.shape[:2]

r_patch = 5

y0_p = max(0, center_y - r_patch)

y1_p = min(h_img, center_y + r_patch + 1)

x0_p = max(0, center_x - r_patch)

x1_p = min(w_img, center_x + r_patch + 1)

patch = depth_image[y0_p:y1_p, x0_p:x1_p].flatten()

valid = patch[patch > 0]

if valid.size == 0:

self.get_logger().info(

f"球心({center_x},{center_y})邻域内无有效深度，"

f"邻域大小={patch.size}，跳过本帧。")

depth = int(np.median(valid)) if valid.size > 0 else 0

if depth > 0:

z_meters = float(depth) / 1000.0

x_meters = (center_x - cx) * z_meters / fx

y_meters = (center_y - cy) * z_meters / fy

  

if not (self.dist_min_m <= z_meters <= self.dist_max_m):

self.get_logger().debug(

f"距离 {z_meters:.2f}m 超出有效范围 "

f"[{self.dist_min_m}, {self.dist_max_m}]m，丢弃。")

else:

expected_radius_px = fx * self.ball_radius_m / z_meters

lo = expected_radius_px * (1.0 - self.radius_tolerance)

hi = expected_radius_px * (1.0 + self.radius_tolerance)

if not (lo <= radius <= hi):

self.get_logger().debug(

f"密度等效半径 {radius:.1f}px"

f" 不在期望范围 [{lo:.1f}, {hi:.1f}]px"

f"（期望={expected_radius_px:.1f}px，距离={z_meters:.2f}m），丢弃。")

else:

point_msg = PointStamped()

point_msg.header = color_msg.header

point_msg.point.x = x_meters

point_msg.point.y = y_meters

point_msg.point.z = z_meters

self.ball_pub.publish(point_msg)

  

self.get_logger().info(

f"检测到目标：3D坐标 = ({x_meters:.2f}, {y_meters:.2f}, {z_meters:.2f})m")

  

cv2.circle(color_image, (center_x, center_y), int(draw_radius), (0,255,255), 2)

cv2.circle(color_image, (center_x, center_y), 5, (0,0,255), -1)

  

timestamp_sec = self.get_clock().now().nanoseconds * 1e-9

self.trajectory_points.append(

(timestamp_sec, x_meters, y_meters, z_meters, center_x, center_y))

  

except IndexError:

self.get_logger().warn(f"球心坐标 ({center_x}, {center_y}) 超出深度图像边界。")

```

  

---

  

## 改动汇总

  

| 位置 | 操作 |

|------|------|

| `__init__` ball_pub 之前 | 新增 3 个参数 |

| `camera_info_callback` 之前 | 新增方法 `_detect_by_density` |

| `image_callback` 原 L138–L231 | 整块替换（findContours 块 → 密度聚类块） |

  

**不改动**：`_display_loop`、`camera_info_callback`、ROS 通信、`main()`

  

---

  

## 验证方法

  

1. 启动节点，观察窗口是否显示 JET 热力图叠加

2. 将球放在 1~3m 处，确认绿色十字准星落在球体中心

3. 观察日志，确认 `检测到目标` 频率 ≥ 10Hz

4. 遮挡球体一半（模拟掩码缺口），验证准星是否仍然稳定

5. 将 `show_heatmap=False` 重启，确认热力图消失、其余功能正常

  

---

  

## 参数调优速查

  

| 参数 | 默认 | 调大 | 调小 |

|------|------|------|------|

| `grid_size` | 16 | 抗噪↑，精度↓ | 精度↑，噪声敏感↑ |

| `density_min_pixels` | 20 | 漏检↑，误检↓ | 漏检↓，误检↑ |

| `density_threshold_ratio`（方法内） | 0.25 | 半径缩小 | 半径偏大 |

| `heatmap_alpha`（方法内） | 0.35 | 热力图更显眼 | 原图更清晰 |