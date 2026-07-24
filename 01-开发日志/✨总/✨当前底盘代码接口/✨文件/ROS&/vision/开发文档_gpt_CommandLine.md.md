# gpt_CommandLine.py — 开发文档

  

> 深度相机球体追踪与落点预测节点（ROS2）

  

---

  

## 一、项目概述

  

| 项目 | 说明 |

|------|------|

| 节点名 | `ball_detector_node` |

| 目标球体 | 黄蓝相间，直径 **24 cm** |

| 有效识别距离 | **0.2 m ～ 7.0 m** |

| 核心功能 | 颜色检测 → 3D 定位 → 轨迹记录 → **落点预测** |

| 输入话题 | `/camera/color/image_raw`、`/camera/depth/image_raw`、`/camera/color/camera_info` |

| 输出话题 | `/detected_ball`（当前位置）、`/predicted_landing`（落点，待实现） |

  

---

  

## 二、已完成修改记录

  

### ✅ 修改 1 — 黄蓝双色检测（替换原橙色单色）

  

**位置：** `__init__` 参数定义 + `image_callback` 掩码生成

  

**改动前：**

```python

self.hsv_lower = np.array([10, 100, 100]) # 橙色

self.hsv_upper = np.array([25, 255, 255])

...

mask = cv2.inRange(hsv_image, self.hsv_lower, self.hsv_upper)

```

  

**改动后：**

```python

# 黄色范围

self.yellow_lower = np.array([20, 100, 100])

self.yellow_upper = np.array([35, 255, 255])

# 蓝色范围（S 下界由 100 → 50，覆盖阴影/边缘蓝色）

self.blue_lower = np.array([100, 50, 50])

self.blue_upper = np.array([130, 255, 255])

...

mask_yellow = cv2.inRange(hsv_image, self.yellow_lower, self.yellow_upper)

mask_blue = cv2.inRange(hsv_image, self.blue_lower, self.blue_upper)

# 各自单独形态学处理后传入密度聚类，不再提前合并

```

  

**取值依据：**

- 黄色 H=20~35：纯黄核心区，避开橙色(H<20)和绿色(H>40)

- 蓝色 H=100~130：标准深蓝/天蓝

- 蓝色 S≥50（原 100）：原阈值过高，球体边缘/阴影侧饱和度常落在 50~100，导致蓝色像素严重丢失

- 黄色 S≥100：黄色背景噪声多，保持较高阈值排除干扰

  

---

  

### ✅ 修改 2 — 距离范围过滤 + 像素半径合理性验证

  

**位置：** `__init__` 新增物理参数 + `image_callback` 3D坐标计算之后

  

#### 新增参数（`__init__`）

```python

self.ball_diameter_m = 0.24 # 球体直径 (m)

self.ball_radius_m = 0.12 # 球体半径 (m)

self.dist_min_m = 0.2 # 最小有效距离 (m)

self.dist_max_m = 7.0 # 最大有效距离 (m)

self.radius_tolerance = 0.7 # 像素半径容差 ±70%（黄蓝掩码有缺口，±50% 过窄）

```

  

#### 新增三道过滤（`image_callback`）

  

**过滤 ①：距离范围**

```python

if not (self.dist_min_m <= z_meters <= self.dist_max_m):

# 仅跳过发布，不 return，确保图像始终送达显示线程

pass

```

  

**过滤 ②：像素半径合理性（面积等效半径，非外接圆半径）**

  

> ⚠️ `minEnclosingCircle` 对残缺/不规则轮廓会显著偏大，改用 `√(面积/π)` 作为校验值，外接圆半径仅保留用于绘图。

  

```python

# 轮廓面积等效半径（校验用）

area = cv2.contourArea(largest_contour)

radius = np.sqrt(area / np.pi)

  

# minEnclosingCircle 半径（仅绘图）

((x, y), draw_radius) = cv2.minEnclosingCircle(largest_contour)

  

# 期望像素半径 = fx_scaled × R_ball / Z

expected_radius_px = fx * self.ball_radius_m / z_meters

lo = expected_radius_px * (1.0 - self.radius_tolerance)

hi = expected_radius_px * (1.0 + self.radius_tolerance)

if not (lo <= radius <= hi):

pass # 像素大小与距离不匹配，排除同色背景误检

```

  

**过滤 ③（新）：11×11 邻域中位数深度（替换原单像素采样）**

  

> ⚠️ 单像素深度因球面反光/边缘噪声极易返回 0，导致整帧静默丢弃，是 ~1m 处丢追踪的主因。

  

```python

r_patch = 5 # 邻域半径（像素），对应 11×11 区域，可调

y0_p = max(0, center_y - r_patch)

y1_p = min(h_img, center_y + r_patch + 1)

x0_p = max(0, center_x - r_patch)

x1_p = min(w_img, center_x + r_patch + 1)

patch = depth_image[y0_p:y1_p, x0_p:x1_p].flatten()

valid = patch[patch > 0] # 去掉无效值（0）

if valid.size == 0:

# INFO 日志：邻域内无有效深度，跳过本帧

...

depth = int(np.median(valid)) if valid.size > 0 else 0

```

  

---

  

## 三、待实现功能

  

### ✅ 修改 3 — 轨迹历史加时间戳 + 滑动窗口

  

**目标：** 将 `trajectory_points` 从旧的 `(px, py, x_m, y_m, z_m)` 5元组改为带时间戳结构，支持滑动窗口（保留最近 30 帧）。

  

**新数据结构（`__init__`）：**

```python

# 每条记录格式：(timestamp_sec, x_m, y_m, z_m, px, py)

# px/py 为像素坐标，用于图像可视化

# deque(maxlen=30) 自动弹出最旧帧，O(1) 无需手动 pop

self.trajectory_points = deque(maxlen=30)

```

  

**追加逻辑（`image_callback`）：**

```python

timestamp_sec = self.get_clock().now().nanoseconds * 1e-9

self.trajectory_points.append(

(timestamp_sec, x_meters, y_meters, z_meters, center_x, center_y)

)

# deque 超出 maxlen 自动弹出，无需手动 pop(0)

```

  

**轨迹绘制（当前已注释，需要时取消注释）：**

```python

# if len(self.trajectory_points) > 1:

# pts = list(self.trajectory_points)

# for i in range(1, len(pts)):

# cv2.line(color_image,

# (pts[i-1][4], pts[i-1][5]),

# (pts[i][4], pts[i][5]),

# (255, 0, 0), 2)

```

  

---

  

### ✅ 修改 3.5 — 性能优化（消除卡顿）

  

**问题根因：**

  

| # | 位置 | 问题 | 严重程度 |

|---|------|------|----------|

| 1 | `image_callback` 末尾 | `cv2.waitKey(1)` 阻塞 ROS 回调线程，消息队列持续积压 | 🔴 最严重 |

| 2 | `trajectory_points.pop(0)` | `list.pop(0)` 每帧 O(n) 内存移位（已被修改3一并解决） | 🔴 高频 |

| 3 | 全局 | 无分辨率缩放，全分辨率跑所有 CV 算子 | 🟡 中等 |

| 4 | 距离/半径过滤处 | 过滤不合格时 `return`，跳过 `imshow` 导致画面冻结 | 🟡 中等 |

  

**改动 1：独立显示线程（解耦 waitKey 阻塞）**

```python

import threading

  

# __init__ 中：

self._display_image = None

self._display_lock = threading.Lock()

self._display_thread = threading.Thread(target=self._display_loop, daemon=True)

self._display_thread.start()

  

# 新增方法：

def _display_loop(self):

cv2.namedWindow("Ball Detection and Trajectory", cv2.WINDOW_NORMAL)

while True:

with self._display_lock:

frame = self._display_image

if frame is not None:

cv2.imshow("Ball Detection and Trajectory", frame)

cv2.waitKey(33) # ~30fps，阻塞只在此线程，不影响任何 ROS 回调

  

# image_callback 末尾（替代原 imshow）：

with self._display_lock:

self._display_image = color_image

```

  

**改动 2：图像降采样 50%（处理像素量减少 75%）**

```python

self.img_scale = 0.5 # __init__ 中定义

  

# image_callback 中，imgmsg_to_cv2 之后立即缩放：

s = self.img_scale

color_image = cv2.resize(color_image, (0, 0), fx=s, fy=s)

depth_image = cv2.resize(depth_image, (0, 0), fx=s, fy=s,

interpolation=cv2.INTER_NEAREST) # 深度用 NEAREST 避免伪深度值

# 内参等比缩放为局部变量（不修改 self.fx 等，避免累积误差）：

fx, fy, cx, cy = self.fx * s, self.fy * s, self.cx * s, self.cy * s

```

  

**改动 3：过滤逻辑去掉中途 return**

  

原代码距离/半径过滤不合格时直接 `return`，导致回调提前退出，`_display_image` 不更新，画面冻结。改为 `if/else` 结构，过滤仅跳过发布，图像始终推送给显示线程。

  

---

  

**算法思路：**

1. 用历史轨迹点做最小二乘拟合，估算当前 3D 速度 `(vx, vy, vz)`

2. 在相机坐标系中建立抛体方程（Y轴向下为重力方向）：

  

```

x(t) = x0 + vx * t

y(t) = y0 + vy * t + 0.5 * g * t²

z(t) = z0 + vz * t

```

  

3. 求解 `y(t) = Y_ground`（地面平面）时的 `t`，代入得 `(x, z)` 落点

4. 可选：再求解 `y(t) = Y_horizontal_plane`（水平接球面）

  

**输出：**

- 命令行：`落点预测(抛体) 地面: (x=?, z=?)m | 水平面: (x=?, z=?)m`

- Topic：`/predicted_landing` 发布 `PointStamped`

  

---

  

### 🔲 修改 5 — 线性外推落点预测

  

**算法思路：**

  

用最近 3~5 帧的位移差分求平均速度，不考虑重力：

  

```

t_land = (Y_target - y0) / vy

x_land = x0 + vx * t_land

z_land = z0 + vz * t_land

```

  

适合近距离（<2m）快速球判断，作为抛体模型的对比输出。

  

---

  

### 🔲 修改 6 — 落点 ROS2 Topic 发布

  

**计划：**

```python

# __init__ 中

self.landing_pub = self.create_publisher(PointStamped, '/predicted_landing', 10)

  

# 发布格式：

# point.x = 落点 X（相机坐标系）

# point.y = 目标平面高度（地面=相机安装高度，水平面=设定高度）

# point.z = 落点 Z（深度方向）

```

  

---

  

### 🔲 修改 7 — 图像可视化（落点和预测轨迹）

  

**计划：**

- 将预测的抛物线轨迹反投影回图像平面，绘制曲线

- 在预测落点处绘制大圆圈 + 文字标注坐标

- 区分颜色：历史轨迹蓝色、预测轨迹绿色、落点红色大圆

  

---

  

## 四、参数速查表

  

| 参数名 | 当前值 | 说明 |

|--------|--------|------|

| `yellow_lower` | `[20, 100, 100]` | 黄色 HSV 下界 |

| `yellow_upper` | `[35, 255, 255]` | 黄色 HSV 上界 |

| `blue_lower` | `[100, 50, 50]` | 蓝色 HSV 下界 |

| `blue_upper` | `[130, 255, 255]` | 蓝色 HSV 上界 |

| `ball_diameter_m` | `0.24` | 球体直径 (m) |

| `ball_radius_m` | `0.12` | 球体半径 (m) |

| `dist_min_m` | `0.2` | 最小有效识别距离 (m) |

| `dist_max_m` | `7.0` | 最大有效识别距离 (m) |

| `r_patch` | `5` | 深度邻域半径（像素），取 11×11 中位数深度，防单像素无效值丢帧 |

| `radius_tolerance` | `0.7` | 像素半径容差（±70%），黄蓝掩码有缺口，±50% 过窄 |

| `img_scale` | `0.5` | 图像处理缩放比例（降采样 50%） |

| `trajectory_points` | `deque(maxlen=30)` | 轨迹滑动窗口，自动维护最近 30 帧 |

| `camera_height_m` | 待设定 | 相机安装高度，用于水平面落点计算 |

  

---

  

## 六、已知问题与修复记录

  

### 🐛 Bug 1 — 蓝色区域不被识别（已修复）

  

**现象：** 节点运行时画面只追踪黄色半球，蓝色半球无法贡献定位。

  

**根因（两层叠加）：**

  

| 层 | 位置 | 问题 |

|----|------|------|

| 1（主因） | `blue_lower` S=100 | 球体边缘/阴影侧蓝色像素饱和度 S 常落在 50~100，阈值过高导致大量蓝色前景像素丢失 |

| 2（放大） | `_detect_by_density` 原为合并掩码 | 单峰算法下黄色像素数远多于蓝色时，密度峰值始终落在黄色区，蓝色贡献被完全压制 |

  

**修复：**

  

1. **放宽蓝色 S 下界**：`[100, 100, 50]` → `[100, 50, 50]`

  

2. **密度法改为双通道分峰**：黄蓝掩码分别建密度图、各自找峰值，以各自总像素数加权平均得到最终球心：

  

```python

# image_callback：各色掩码单独形态学处理（不提前合并）

mask_yellow = cv2.erode/dilate(mask_yellow, ...)

mask_blue = cv2.erode/dilate(mask_blue, ...)

  

# _detect_by_density 内部：

cx_final = (cx_yellow * n_yellow + cx_blue * n_blue) / (n_yellow + n_blue)

cy_final = (cy_yellow * n_yellow + cy_blue * n_blue) / (n_yellow + n_blue)

```

  

**效果：** 两种颜色均有效参与定位；当球体转动使一侧朝向相机时，优势颜色权重自动提升，定位更鲁棒。

  

---

  

## 五、话题总览

  

| 话题 | 类型 | 方向 | 说明 |

|------|------|------|------|

| `/camera/color/image_raw` | `sensor_msgs/Image` | 订阅 | 彩色图 |

| `/camera/depth/image_raw` | `sensor_msgs/Image` | 订阅 | 深度图 |

| `/camera/color/camera_info` | `sensor_msgs/CameraInfo` | 订阅 | 相机内参 |

| `/detected_ball` | `geometry_msgs/PointStamped` | 发布 | 当前球体 3D 坐标 |

| `/predicted_landing` | `geometry_msgs/PointStamped` | 发布（待实现） | 预测落点 3D 坐标 |