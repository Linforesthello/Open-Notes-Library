# Jetson Nano B01 + SSD-MobileNet 检测部署（jetson-inference）

> **硬件**：Jetson Nano B01 (4GB)  
> **系统**：JetPack r32.7.1 (Ubuntu 18.04 aarch64)  
> **加速**：CUDA 10.2 + TensorRT 8.2.1  
> **Python**：3.6.9  
> **摄像头**：USB 2.0 Camera (MJPEG 1280x720)  
> **路线**：NVIDIA 官方 jetson-inference (Hello AI World)

---

## 目录

- [一、环境准备](#一环境准备)
- [二、编译 jetson-inference](#二编译-jetson-inference)
- [三、安装](#三安装)
- [四、下载模型](#四下载模型)
- [五、运行检测](#五运行检测)
- [六、踩坑记录](#六踩坑记录)
- [七、检测结果](#七检测结果)
- [八、附录](#八附录)

---

## 一、环境准备

设备通过 SSHFS 挂载连接：桌面 PC → `lin@192.168.1.207:/home/lin` → `~/nano`

### 确认系统信息

```bash
uname -m                    # → aarch64
cat /etc/nv_tegra_release   # → JetPack r32.7.1
nvcc --version              # → CUDA 10.2
python3 --version           # → 3.6.9
```

### 项目初始状态

```
~/jetson-inference/                               # 已 git clone
~/jetson-inference/build/                         # 空目录
~/torch-1.11.0a0+17540c5+nv22.01-cp36-cp36m-linux_aarch64.whl
~/torch-1.10.0-cp36-cp36m-linux_aarch64.whl
~/PyTorch-Jetson-Nano/
~/pane.log                                         # tmux 日志
~/detect_headless.py                               # 检测脚本（后创建）
```

---

## 二、编译 jetson-inference

### 2.1 初始化 submodule

```bash
cd ~/jetson-inference
git submodule update --init
```

> **必须执行**，否则 cmake 报 `FATAL_ERROR`

### 2.2 CMake 配置

```bash
mkdir -p build && cd build
cmake ..
```

cmake 自动阶段：

| 阶段 | 说明 |
|---|---|
| 系统检测 | Ubuntu 18.04 bionic, aarch64 ✅ |
| CUDA 检测 | **10.2** → 启用 **SM_53 / SM_62 / SM_72** |
| OpenCV 检测 | **4.1.1** ✅ → 启用 |
| 依赖安装 | CMakePreBuild.sh → 需 sudo 密码 |
| PyTorch 交互 | **选 Skip**（内置 1.6.0 太旧） |
| 模型选择 | 勾选 ssd-mobilenet-v2 |

成功标志：

```
-- Configuring done
-- Generating done
-- Build files have been written to: /home/lin/jetson-inference/build
```

### 2.3 编译

```bash
make -j$(nproc)
```

> Nano 编译约 **20-40 分钟**

编译产物：

| 目标 | 路径 |
|---|---|
| 核心库 | `build/aarch64/lib/libjetson-inference.so` |
| C++ 检测工具 | `build/aarch64/bin/detectnet` |
| Python 3.6 绑定 | `build/aarch64/lib/python/3.6/jetson_inference_python.so` |
| Python 2.7 绑定 | `build/aarch64/lib/python/2.7/jetson_inference_python.so` |

---

## 三、安装

```bash
cd ~/jetson-inference/build
sudo make install
sudo ldconfig
```

### 验证安装

```bash
detectnet --help
python3 -c "from jetson_inference import detectNet; print('OK')"
```

### 安装路径

| 内容 | 路径 |
|---|---|
| C++ 头文件 | `/usr/local/include/jetson-inference/` |
| C++ 库 | `/usr/local/lib/libjetson-inference.so` |
| Python 3.6 包 | `/usr/lib/python3.6/dist-packages/jetson_inference/` |
| 可执行文件 | `/usr/local/bin/detectnet` |
| 模型目录 | `/usr/local/bin/networks/`（→ `~/jetson-inference/data/networks/` 符号链接） |

---

## 四、下载模型

### 问题

启动时自动从 `nvidia.box.com` 下载 SSD-Mobilenet-v2（~60MB）。  
box.com 在国内网络不稳定，多次下载失败。

### 解决：桌面 PC 下载 → SSHFS

```bash
# 在桌面 PC 执行
cd ~/nano/jetson-inference/data/networks
wget https://nvidia.box.com/shared/static/jcdewxep8vamzm71zajcovza938lygre.gz \
  -O SSD-Mobilenet-v2.tar.gz
tar -xzvf SSD-Mobilenet-v2.tar.gz
```

解压后：

```
SSD-Mobilenet-v2/
├── ssd_coco_labels.txt              # 91 类 COCO 标签
└── ssd_mobilenet_v2_coco.uff        # TensorRT UFF 模型 (65MB)
```

> `/usr/local/bin/networks/` 是符号链接，解压后自动生效，无需额外复制

---

## 五、运行检测

### 5.1 无头实时检测脚本

创建 `~/detect_headless.py`：

```python
#!/usr/bin/env python3
import sys
import signal
from jetson_inference import detectNet
from jetson_utils import videoSource

signal.signal(signal.SIGINT, signal.SIG_DFL)

net = detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = videoSource("/dev/video0")   # USB 摄像头，CSI 用 csi://0

frame_count = 0
while True:
    img = camera.Capture()
    if img is None:
        continue
    detections = net.Detect(img)
    frame_count += 1
    print(f"\r帧 {frame_count} | 检测到 {len(detections)} 个物体:", end="")
    for d in detections:
        cls = net.GetClassDesc(d.ClassID)
        conf = d.Confidence * 100
        print(f" [{cls} {conf:.0f}%]", end="")
    sys.stdout.flush()
```

运行：

```bash
python3 ~/detect_headless.py
```

### 5.2 首次启动：TensorRT 自动调优（关键！）

第一次加载模型耗时 **5-20 分钟**。TensorRT 逐层测试 GPU 内核策略：

```
[TRT] Autotuning format combination: Float(...) -> Float(...)
[TRT] Timing Runner: FeatureExtractor/MobilenetV2/... (CudnnConvolution)
[TRT] Fastest Tactic: 7144526460361122478 Time: 9.99
[TRT] >>>>>>>>>>>>>>> Chose Runner Type: CudaDepthwiseConvolution
```

> **不要 Ctrl+C**，耐心等跑完。调优结果缓存到 `.engine` 文件，后续秒开。

成功启动流程：

```
TensorRT 8.2.1 → 解析 UFF → 自动调优 → 缓存 engine → 打开摄像头 → 实时检测
```

### 5.3 C++ 命令行

```bash
# 摄像头实时
detectnet --network=ssd-mobilenet-v2 /dev/video0

# 图片处理
detectnet --network=ssd-mobilenet-v2 input.jpg output.jpg

# 无头保存视频
detectnet --network=ssd-mobilenet-v2 --headless /dev/video0 output.mp4
```

---

## 六、踩坑记录

### 坑 1：submodule 未初始化

**现象**：cmake 报 `FATAL_ERROR`  
**解决**：`git submodule update --init`

---

### 坑 2：Python 绑定链接失败 `cannot find -lnpymath`

**现象**：make 到 95% 报错，C++ 库全成功，仅 Python `.so` 失败

```
/usr/bin/ld: cannot find -lnpymath
collect2: error: ld returned 1 exit status
```

**原因**：Ubuntu 18.04 NumPy 1.13.3 有 `libnpymath.a` 但链接器找不到  
**解决**：

```bash
# 找到位置
find /usr -name "libnpymath*"
# → /usr/lib/python3/dist-packages/numpy/core/lib/libnpymath.a

# 创建软链接
sudo ln -s /usr/lib/python3/dist-packages/numpy/core/lib/libnpymath.a \
           /usr/lib/aarch64-linux-gnu/libnpymath.so

# 重新 make（几十秒）
cd ~/jetson-inference/build && make -j$(nproc)
```

> `sudo apt install python3-numpy-dev` 无效

---

### 坑 3：模型下载失败

**现象**：`nvidia.box.com` 连不上，反复重试  
**解决**：桌面 PC 下载后 SSHFS 传过去（见第四章）

---

### 坑 4：OpenGL 报错

**现象**：SSH 下 `failed to open X11 server connection`  
**原因**：无桌面环境  
**解决**：用 Python 脚本做终端输出，无需 GUI

---

### 坑 5：FlattenConcat_TRT 注册警告

```
[TRT] Could not register plugin creator - ::FlattenConcat_TRT version 1
```

**无害**，插件已注册跳过重复，不影响功能。

---

### 坑 6：频繁 Ctrl+C

**问题**：中断 TensorRT 调优，导致每次从头开始  
**解决**：第一次运行完整跑完，不要中断

---

## 七、检测结果

### 成功输出

```text
帧 2866 | 检测到 1 个物体: [laptop 94%] [keyboard 56%]
帧 2897 | 检测到 3 个物体: [laptop 99%] [keyboard 59%] [chair 57%]
帧 3328 | 检测到 13 个物体: [person 87%] [dining table 81%] [laptop 62%] [chair 86%] [wine glass 68%]
帧 3337 | 检测到 12 个物体: [chair 56%] [cup 53%] [person 87%] [laptop 92%]
```

### 支持的 91 类 COCO

person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, traffic light, fire hydrant, stop sign, parking meter, bench, bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket, bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant, bed, dining table, toilet, tv, laptop, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors, teddy bear, hair drier, toothbrush

---

## 八、附录

### 8.1 可用检测模型对比

| 模型 | 速度 | 精度 | 推荐场景 |
|---|---|---|---|
| ssd-mobilenet-v1 | ⚡最快 | 较低 | 极致性能 |
| **ssd-mobilenet-v2** | **⚡快** | **中等** | **Nano 首选** |
| ssd-inception-v2 | 中等 | 较高 | 精度优先 |
| peoplenet | 快 | 高 | 行人检测 |
| facedetect | 快 | 高 | 人脸检测 |

### 8.2 安装 PyTorch（可选）

jetson-inference 本身不需要 PyTorch（仅训练需要）：

```bash
pip3 install ~/torch-1.11.0a0+17540c5+nv22.01-cp36-cp36m-linux_aarch64.whl

git clone --branch v0.12.0 https://github.com/pytorch/vision ~/torchvision
cd ~/torchvision
export BUILD_VERSION=0.12.0
python3 setup.py install --user
```

### 8.3 tmux 日志查看

```bash
tmux list-windows                              # 列出窗口
tmux capture-pane -p -S - > ~/pane.log         # 捕获当前窗格
tmux capture-pane -p -S - -t 2 > ~/pane2.log   # 捕获指定窗格
```

### 8.4 关键文件

| 用途 | 路径 |
|---|---|
| 项目源码 | `~/jetson-inference/` |
| 编译目录 | `~/jetson-inference/build/` |
| UFF 模型 | `~/jetson-inference/data/networks/SSD-Mobilenet-v2/ssd_mobilenet_v2_coco.uff` |
| COCO 标签 | `~/jetson-inference/data/networks/SSD-Mobilenet-v2/ssd_coco_labels.txt` |
| 检测脚本 | `~/detect_headless.py` |
| 操作日志 | `~/pane.log` |
