# 先验目标选择（Prior-based Target Selection）

  

> 在追踪开始前，通过人工确认锁定唯一目标球体，消除同色干扰物的误追踪。

  

---

  

## 一、整体流程

  

```

启动节点

│

▼

【先验采集阶段】取前 N 帧，检测所有候选色块

│ 每个候选输出：编号 | 颜色 | 像素坐标(u,v) | 深度距离(m)

▼

终端打印候选列表 → 人类输入编号选择目标

│

▼

【锁定目标阶段】只追踪选中目标（颜色 + 位置先验门限双约束）

│

▼

正常追踪 + 落点预测（现有逻辑不变）

```

  

---

  

## 二、状态机设计

  

在 `__init__` 中新增：

  

```python

# ── 先验选择状态机 ──────────────────────────────────────────

self.prior_state = 'collecting' # 'collecting' → 'waiting_input' → 'tracking'

self.prior_frames = 3 # 取前 N 帧做候选检测（多帧提升深度稳定性）

self.prior_count = 0 # 已采集帧数

self.candidates = {} # {key: {px, py, z_m, color, area}}

self.prior_menu = {} # {编号: 候选}（打印给用户后暂存）

self.target_prior = None # 锁定后的先验：{px, py, z_m, color}

self.target_color = None # 'yellow' | 'blue'（锁定后只检测此颜色）

self.prior_gate_px = 80 # 追踪阶段先验位置门（缩放后坐标系，像素）

```

  

**状态转移：**

  

| 状态 | 触发条件 | 行为 |

|------|---------|------|

| `collecting` | 节点启动 | 每帧检测所有候选，累积 N 帧后打印列表 |

| `waiting_input` | 采集满 N 帧 | 暂停追踪，等待用户在终端输入编号 |

| `tracking` | 用户输入有效编号 | 按先验颜色+位置门限追踪唯一目标 |

  

---

  

## 三、各阶段实现

  

### 3.1 候选检测（先验采集阶段）

  

```python

def _collect_candidates(self, mask_yellow, mask_blue, depth_image, fx, cx, cy, color_image):

candidates = []

h_img, w_img = depth_image.shape

  

for color_label, mask in [('yellow', mask_yellow), ('blue', mask_blue)]:

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:

area = cv2.contourArea(cnt)

if area < 80: # 过滤噪声小块（缩放后坐标系）

continue

M = cv2.moments(cnt)

if M['m00'] == 0:

continue

px = int(M['m10'] / M['m00'])

py = int(M['m01'] / M['m00'])

  

# 11×11 邻域中位数深度（复用现有方案，防单像素无效值）

r = 5

patch = depth_image[max(0,py-r):min(h_img,py+r+1),

max(0,px-r):min(w_img,px+r+1)].flatten()

valid = patch[patch > 0]

if valid.size == 0:

continue

z_m = int(np.median(valid)) * 0.001

  

if not (self.dist_min_m <= z_m <= self.dist_max_m):

continue

  

candidates.append({'px': px, 'py': py, 'z_m': z_m,

'color': color_label, 'area': area})

return candidates

```

  

### 3.2 多帧聚合 + 终端打印

  

```python

def _aggregate_and_print(self):

# 像素距离 < prior_gate_px 且同色 → 合并为同一候选（取均值）

merged = []

for c in self.candidates.values():

matched = False

for m in merged:

if (c['color'] == m['color'] and

np.hypot(c['px']-m['px'], c['py']-m['py']) < self.prior_gate_px):

m['px'] = int((m['px'] + c['px']) / 2)

m['py'] = int((m['py'] + c['py']) / 2)

m['z_m'] = (m['z_m'] + c['z_m']) / 2

matched = True

break

if not matched:

merged.append(dict(c))

  

print('\n' + '='*55)

print(' [先验选择] 检测到以下候选目标，请选择要追踪的球：')

print(f' {"编号":4s} {"颜色":8s} {"像素(u,v)":14s} {"深度(m)":8s}')

print('-'*55)

self.prior_menu = {}

for i, m in enumerate(merged):

print(f' [{i}] {m["color"]:8s} ({m["px"]:4d},{m["py"]:4d}) {m["z_m"]:.2f} m')

self.prior_menu[i] = m

print('='*55)

  

import threading

threading.Thread(target=self._wait_user_input, daemon=True).start()

self.prior_state = 'waiting_input'

```

  

### 3.3 非阻塞用户输入线程

  

```python

def _wait_user_input(self):

while True:

try:

idx = int(input(' 请输入编号（数字）: ').strip())

if idx not in self.prior_menu:

print(f' ⚠ 无效编号，请输入 0~{len(self.prior_menu)-1}')

continue

except ValueError:

print(' ⚠ 请输入纯数字')

continue

  

chosen = self.prior_menu[idx]

self.target_prior = {'px': chosen['px'], 'py': chosen['py'],

'z_m': chosen['z_m'], 'color': chosen['color']}

self.target_color = chosen['color']

print(f'\n ✅ 已锁定目标 [{idx}]：{chosen["color"]}，'

f'像素({chosen["px"]},{chosen["py"]})，深度 {chosen["z_m"]:.2f} m')

print(' 开始追踪...\n')

self.prior_state = 'tracking'

break

```

  

> ⚠️ 必须用独立线程执行 `input()`，否则阻塞 ROS 回调线程，导致消息队列积压。

  

### 3.4 追踪阶段先验门限（接入 `image_callback`）

  

```python

# ── image_callback 中，得到 center_x/center_y/z_meters 之后 ──

  

if self.prior_state == 'tracking' and self.target_prior is not None:

dist_px = np.hypot(center_x - self.target_prior['px'],

center_y - self.target_prior['py'])

depth_diff = abs(z_meters - self.target_prior['z_m'])

  

# 位置 AND 深度双双超出预期 → 极可能是干扰目标，跳过本帧发布

if dist_px > self.prior_gate_px * 3 and depth_diff > 1.5:

pass # 不发布、不更新先验

else:

# EMA 滚动更新先验（低通跟随球体运动）

alpha = 0.3

self.target_prior['px'] = int(alpha * center_x + (1-alpha) * self.target_prior['px'])

self.target_prior['py'] = int(alpha * center_y + (1-alpha) * self.target_prior['py'])

self.target_prior['z_m'] = alpha * z_meters + (1-alpha) * self.target_prior['z_m']

# ... 正常发布 /detected_ball ...

```

  

### 3.5 `image_callback` 顶层状态分发

  

```python

def image_callback(self, color_msg, depth_msg):

# ... 图像解码、缩放、HSV掩码生成 ...

  

if self.prior_state == 'collecting':

cands = self._collect_candidates(mask_yellow, mask_blue, depth_image, fx, cx, cy, color_image)

for c in cands:

key = f"{c['color']}_{c['px']}_{c['py']}"

self.candidates[key] = c

self.prior_count += 1

# 屏幕叠加提示

cv2.putText(color_image, f"Prior collecting {self.prior_count}/{self.prior_frames}",

(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

if self.prior_count >= self.prior_frames:

self._aggregate_and_print()

# 更新显示后直接返回，不进入追踪逻辑

with self._display_lock:

self._display_image = color_image

return

  

elif self.prior_state == 'waiting_input':

cv2.putText(color_image, "Waiting for target selection...",

(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

with self._display_lock:

self._display_image = color_image

return

  

elif self.prior_state == 'tracking':

# 按选定颜色过滤掩码，减少干扰

if self.target_color == 'yellow':

active_mask = mask_yellow

elif self.target_color == 'blue':

active_mask = mask_blue

else:

active_mask = cv2.bitwise_or(mask_yellow, mask_blue)

# ... 原有追踪逻辑（使用 active_mask）...

```

  

---

  

## 四、终端交互示例

  

```

启动节点后约 3 帧（~0.1 s）输出：

  

=======================================================

[先验选择] 检测到以下候选目标，请选择要追踪的球：

编号 颜色 像素(u,v) 深度(m)

-------------------------------------------------------

[0] yellow ( 320, 240) 1.83 m

[1] blue ( 318, 244) 1.85 m ← 同一球的蓝色半边

[2] yellow ( 510, 190) 4.20 m ← 背景干扰物

=======================================================

请输入编号（数字）: 0

  

✅ 已锁定目标 [0]：yellow，像素(320,240)，深度 1.83 m

开始追踪...

```

  

---

  

## 五、关键参数

  

| 参数 | 默认值 | 说明 |

|------|--------|------|

| `prior_frames` | `3` | 采集帧数（多帧提升深度稳定性，过多延迟启动） |

| `prior_gate_px` | `80` | 候选合并距离 & 追踪门限基准（缩放后像素） |

| `alpha`（EMA） | `0.3` | 先验滚动更新速率（越大跟随越快，越小越稳定） |

| 追踪门限倍数 | `3×` | 超出 `prior_gate_px * 3` 且深度差 > 1.5 m 才拒绝 |

  

---

  

## 六、设计决策说明

  

| 问题 | 选择 | 原因 |

|------|------|------|

| 先验帧数 | 3 帧 | 单帧深度易无效；3 帧 ≈ 0.1 s，启动延迟可接受 |

| 候选合并策略 | 像素距离 + 同色双条件 | 黄蓝分峰，避免将球的黄色半边和蓝色半边误合并为两个目标 |

| 用户输入方式 | 独立守护线程 `input()` | 不阻塞 ROS 回调线程，显示画面持续刷新 |

| 追踪门限 | 位置 AND 深度双阈值 | 单像素门限在球飞行时会误拒；双阈值 AND 才能有效排除干扰 |

| 先验滚动更新 | EMA α=0.3 | 低通跟随球体运动，防止先验漂离；纯静态先验在球大幅移动后会持续拒绝正确检测 |

| 锁定颜色后过滤掩码 | 只保留选定颜色的掩码 | 减少另一种颜色背景噪声的干扰，提升追踪专一性 |