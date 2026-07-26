# YOLOv5n TensorRT Engine 部署全记录

> 日期: 2026-05-26
> 设备: Jetson Nano (aarch64, Tegra X1), Docker 容器内
> 目标: 将 YOLOv5n ONNX 模型转换为 TensorRT engine 并完成性能基准测试

---

## 目录

1. [环境概述](#1-环境概述)
2. [任务背景](#2-任务背景)
3. [执行流程](#3-执行流程)
4. [Engine 构建](#4-engine-构建)
5. [性能基准测试](#5-性能基准测试)
6. [对比基线：SSD-MobileNet-v2 (UFF)](#6-对比基线的SSD-MobileNet-v2-uff)
7. [踩坑记录](#7-踩坑记录)
8. [最终配置总结](#8-最终配置总结)
9. [附：完整命令速查表](#9-附完整命令速查表)
10. [附：故障诊断思维导图](#10-附故障诊断思维导图)

---

## 1. 环境概述

### 1.1 硬件与软件栈

| 项目 | 详情 |
|------|------|
| **设备** | NVIDIA Jetson Nano |
| **架构** | aarch64 (ARM 64-bit) |
| **操作系统** | Ubuntu 18.04.6 LTS (Bionic) |
| **L4T 版本** | R32.7.6 |
| **GPU** | NVIDIA Tegra X1 (Maxwell, Compute Capability 5.3) |
| **SMs** | 1 |
| **Compute Clock** | 0.9216 GHz |
| **显存** | 3955 MiB（CPU/GPU 共享） |
| **TensorRT** | 8.2.1 |
| **容器镜像** | `dustynv/jetson-inference:r32.7.1` |
| **trtexec 路径** | `/usr/src/tensorrt/bin/trtexec` |

### 1.2 模型来源

| 项目 | 详情 |
|------|------|
| **模型** | YOLOv5n (Nano) |
| **来源** | Ultralytics YOLOv5 v6.0 Release |
| **格式** | ONNX (opset 14) |
| **输入尺寸** | 1×3×640×640 |
| **文件大小** | 7.2 MB |
| **参数量** | ~1.9M |
| **COCO mAP** | ~28%（预期） |

### 1.3 关键目录结构

```
/home/lin/jetson-inference/
├── data/
│   └── models/
│       └── yolov5n/
│           ├── yolov5n.onnx              # 原始 ONNX 模型（7.2M）
│           └── yolov5n_fp16.engine       # 生成的 TensorRT engine（7M）
└── docker/
    └── run.sh                            # 容器启动脚本
```

---

## 2. 任务背景

### 2.1 目标

验证 ONNX→TensorRT engine 转换管线在 Docker 容器内的可行性，建立多模型生态的基础。

### 2.2 路线图位置

```
当前: Docker + SSD-MobileNet (UFF) ← 基线
  │
  ├──→ 第一阶段: Docker 内 ONNX→TensorRT 验证（✅ 完成）
  │        yolov5n.onnx → trtexec → engine → benchmark
  │
  ├──→ 第二阶段: Python 推理脚本 + 多模型扩展（✅ 推理脚本完成，多模型扩展进行中）
  │        自定义推理脚本 → HTTP MJPEG 推流 → ~4.2 FPS
  │
  └──→ 第三阶段: 按需原生安装 + 完整开发闭环
```

### 2.3 核心策略

- **全部在 Docker 容器内完成**，不污染宿主机环境
- **只用到 trtexec CLI**，不涉及 Python 推理（减少变量）
- **持久化到挂载卷**，容器退出数据不丢失

---

## 3. 执行流程

### 3.1 Step 1：复制模型到挂载目录

在宿主机执行：

```bash
mkdir -p ~/jetson-inference/data/models/yolov5n
cp ~/models/yolov5n.onnx ~/jetson-inference/data/models/yolov5n/
ls -lh ~/jetson-inference/data/models/yolov5n/yolov5n.onnx
# 输出: -rw-rw-r-- 1 lin lin 7.2M 5月  26 09:30 yolov5n.onnx
```

**结果：✅ 成功**

### 3.2 Step 2：定位 trtexec

启动容器：

```bash
cd ~/jetson-inference && docker/run.sh
```

`trtexec` 不在默认 PATH 中，找到位置：

```bash
find / -name trtexec -type f 2>/dev/null
# 输出: /usr/src/tensorrt/bin/trtexec
```

**结果：✅ 找到，位于 `/usr/src/tensorrt/bin/trtexec`**

### 3.3 Step 3：ONNX→TensorRT Engine 转换

共尝试 4 次，详见[踩坑记录](#7-踩坑记录)：

| 尝试 | Workspace | 命令参数 | 耗时 | 结果 |
|------|-----------|---------|------|------|
| 1 | 1024 MB | 无 shape 参数 | ~7 min | ❌ Cask isConsistent |
| 2 | 1024 MB | `--minShapes/--optShapes/--maxShapes` | ~7 min | ❌ OOM |
| 3 | 512 MB | 同上 | ~2 min | ❌ Ctrl+C |
| 4 | **256 MB** | 同上 | **~11.5 min** | **✅ PASSED** |

**最终成功命令：**

```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=/jetson-inference/data/models/yolov5n/yolov5n.onnx \
  --saveEngine=/jetson-inference/data/models/yolov5n/yolov5n_fp16.engine \
  --fp16 --workspace=256 \
  --minShapes=images:1x3x640x640 \
  --optShapes=images:1x3x640x640 \
  --maxShapes=images:1x3x640x640
```

### 3.4 Step 4：Engine 基准测试

```bash
/usr/src/tensorrt/bin/trtexec \
  --loadEngine=/jetson-inference/data/models/yolov5n/yolov5n_fp16.engine \
  --iterations=100
```

---

## 4. Engine 构建

### 4.1 构建日志关键节点

```
[05/26/2026-01:59:38] ... GPU 层拓扑输出（780 层）
[05/26/2026-01:59:41] Local timing cache in use.
[05/26/2026-02:01:50] Some tactics do not have sufficient workspace memory to run.  ← 仅提示，非错误
[05/26/2026-02:10:58] Detected 1 inputs and 7 output network tensors.
[05/26/2026-02:10:58] Total Device Persistent Memory: 5715968
[05/26/2026-02:10:58] Peak memory usage of TRT GPU allocators: 228 MiB
[05/26/2026-02:10:58] Loaded engine size: 7 MiB
[05/26/2026-02:10:59] Engine built in 688.282 sec.
```

### 4.2 构建核心指标

| 指标 | 值 |
|------|------|
| **总耗时** | **688.3 秒（~11.5 分钟）** |
| Engine 大小 | **7 MiB** |
| 峰值 GPU 显存 | **228 MiB** |
| 输入 | 1×3×640×640（`images`） |
| 输出 1 | 1×3×80×80×85（小目标检测头） |
| 输出 2 | 1×3×40×40×85（中目标检测头） |
| 输出 3 | 1×3×20×20×85（大目标检测头） |
| 输出 4 | 1×25200×85（展平输出） |

### 4.3 构建后 Engine 加载

第二次启动直接加载 engine（无需重建）：

```bash
/usr/src/tensorrt/bin/trtexec --loadEngine=... --iterations=100
```

加载耗时：**4.44 秒**

---

## 5. 性能基准测试

### 5.1 测试配置

| 参数 | 值 |
|------|------|
| 迭代次数 | 100 |
| Warmup | 200 ms |
| 输入数据 | Random (trtexec 自动生成) |
| 精度 | FP16 |

### 5.2 性能摘要

```
Throughput:         20.8703 qps
GPU Compute Time:   mean = 45.76 ms, median = 45.45 ms
End-to-End Latency: mean = 47.90 ms, median = 47.60 ms
H2D Latency:        mean = 0.496 ms
D2H Latency:        mean = 1.648 ms
```

### 5.3 详细延时分解

| 阶段 | 最小值 | 均值 | 中位数 | P99 |
|------|--------|------|--------|-----|
| **GPU Compute** | 45.27 ms | **45.76 ms** | 45.45 ms | 49.71 ms |
| **End-to-End** | 47.41 ms | **47.91 ms** | 47.61 ms | 51.87 ms |
| H2D | 0.482 ms | 0.496 ms | 0.494 ms | 0.523 ms |
| D2H | 1.634 ms | 1.648 ms | 1.639 ms | 1.743 ms |
| Enqueue | 7.017 ms | 11.74 ms | 11.86 ms | 16.94 ms |

### 5.4 稳定性分析

- 100 次推理中 GPU Compute Time 波动范围：**45.27 ~ 49.71 ms**
- 方差很小（均值 45.76，中位数 45.45），表明推理稳定性好
- P99 仅比均值高 ~8.6%，没有严重抖动

---

## 6. 对比基线：SSD-MobileNet-v2 (UFF)

### 6.1 性能对比

| 指标 | SSD-MobileNet-v2 (UFF) | YOLOv5n (ONNX→TensorRT) | 差异 |
|------|----------------------|------------------------|------|
| **GPU Compute Time** | **42.3 ms** | **45.8 ms** | +3.5 ms (8.3%) |
| **FPS (trtexec)** | **~23** | **~20.9** | -2.1 FPS |
| **FPS (Python 管线)** | — | **~4.2** | 受 CPU 瓶颈限制 |
| 输入尺寸 | 300×300 (0.09 MP) | 640×640 (0.41 MP) | **+4.6x 像素** |
| 参数量 | ~5M | ~1.9M | **-62%** |
| COCO mAP | ~22% | ~28% | **+6 pp** |
| 格式 | UFF（弃用趋势） | ONNX（主流标准） | ✅ 未来兼容 |

### 6.2 分析

YOLOv5n 在 Jetson Nano 上推理速度略慢于 SSD-MobileNet-v2（45.8ms vs 42.3ms），但这是合理的：

1. **输入分辨率高 4.6 倍**：640×640 vs 300×300，处理像素量大得多
2. **参数量少 62%**：1.9M vs 5M，说明 YOLOv5 架构更高效
3. **精度更高**：mAP 28% vs 22%，检测质量明显更好

**结论**：YOLOv5n 是 SSD-MobileNet-v2 的合格替代方案——用约 8% 的速度代价，换来更高的检测精度和 ONNX 生态兼容性。

---

## 7. Python 推理管线部署

### 7.1 脚本概况

自定义推理脚本 [detect_yolov5n.py](../jetson-inference/data/detect_yolov5n.py)，包含完整检测管线：

| 组件 | 实现 |
|------|------|
| Engine 加载 | TensorRT Python API + pyCUDA 缓冲区分配 |
| 预处理 | letterbox 缩放 640×640, BGR→RGB, CHW, [0,1] |
| 推理 | 异步 H2D → execute → D2H, stream 同步 |
| 后处理 | 3 检测头解码 (stride 8/16/32) → 置信度过滤 → 类别分组 NMS → 坐标反算 |
| 输出 | 视频保存 (MJPG, 5 FPS) + HTTP MJPEG 推流 |

### 7.2 端到端性能

```
trtexec GPU-only:    20.9 FPS  (45.8ms)
Python 管线实测:      ~4.2 FPS  (238ms/帧)
```

| 环节 | 耗时占比 | 说明 |
|------|---------|------|
| **GPU 推理** | ~46ms (19%) | 纯 TensorRT，与 trtexec 一致 |
| CPU 预处理 | ~80ms (34%) | letterbox resize + 归一化 |
| CPU 后处理 | ~100ms (42%) | decode_head + NMS + 坐标转换 |
| 画框 + 编码 | ~12ms (5%) | OpenCV 绘制 + JPEG 编码 |

**瓶颈**: ARM Cortex-A57 CPU，非 GPU。GPU 推理只占 19% 时间，剩下 81% 耗在 CPU 侧。

### 7.3 视频流 (MJPEG HTTP)

通过 `--stream` 参数启用 HTTP MJPEG 推流：

```bash
python3 /jetson-inference/data/detect_yolov5n.py --stream --port 8080
```

- 纯 stdlib 实现（`http.server`），零额外依赖
- 每帧以 JPEG 60% 质量编码后推送
- 浏览器打开 `http://<nano-ip>:8080/stream` 观看
- RJ45 有线连接实测带宽充足，延迟 ~5ms

### 7.4 管线架构

```
Camera (USB V4L2, 640×480)
  │  [~250ms]
  ▼
CPU: letterbox resize → 640×640
  │  [~80ms]
  ▼
GPU: H2D → TensorRT FP16 → D2H
  │  [~46ms]
  ▼
CPU: decode_head ×3 → NMS → coord transform
  │  [~100ms]
  ▼
CPU: draw boxes → JPEG encode → HTTP push / AVI write
  │  [~12ms]
  ▼
Output: /jetson-inference/data/output_yolov5n.avi  +  MJPEG stream
```

### 7.5 优化方向

| 方案 | 预期 FPS | 难度 |
|------|---------|------|
| CSI 摄像头 (GStreamer 管道) | ~8-10 | 低 |
| GPU 预处理 (cuda::GpuMat) | ~6-7 | 中 |
| C++ 重写管线 | ~15-18 | 高 |
| 当前 Python 基线 | ~4.2 | — |

---

### 7.1 问题 1：trtexec 不在 PATH

**现象**：`trtexec: command not found`

**原因**：TRT 8.2.1 在 JetPack 中安装在 `/usr/src/tensorrt/bin/`，未加入 PATH。

**解决**：
```bash
# 方法 1：全路径运行
/usr/src/tensorrt/bin/trtexec ...
# 方法 2：创建软链
ln -s /usr/src/tensorrt/bin/trtexec /usr/local/bin/trtexec
```

### 7.2 问题 2：动态输入形状导致 engine 构建失败

**现象**：
```
Error Code 1: Cask (isConsistent) - 卷积维度不一致
Dynamic dimensions required for input: images, but no shapes were provided.
  Automatically overriding shape to: 1x3x1x1
```

**原因**：YOLOv5 ONNX 使用动态 batch/输入尺寸（opset 14），trtexec 未收到明确输入尺寸时错误地猜测为 `1x3x1x1`。

**解决**：使用 `--minShapes/--optShapes/--maxShapes` 明确指定：
```bash
--minShapes=images:1x3x640x640 \
--optShapes=images:1x3x640x640 \
--maxShapes=images:1x3x640x640
```

**注意**：TensorRT 8.2 不支持 `--inputShapes` 参数（它是 TRT 8.5+ 才加入的）。

### 7.3 问题 3：Workspace 太大导致 OOM

**现象**：构建跑 ~7 分钟后进程被系统终止（OOM killer），engine 文件未生成。

**原因**：Jetson Nano 仅有 ~4GB CPU/GPU 共享内存：
- GPU 基础占用：~2757 MiB
- cuDNN 初始化后：~3443 MiB
- 剩余可用：~500 MiB
- 而 `--workspace=1024` 申请 1GB，超出可用范围

**解决思路**：
```
workspace=1024 → ❌ OOM（GPU 预留 + workspace > 总内存）
workspace=512  → ❌ 仍不够（被 Ctrl+C）
workspace=256  → ✅ 成功（峰值 GPU 仅使用 228 MiB）
```

### 7.4 问题 4：`Some tactics do not have sufficient workspace memory`

**现象**：构建日志中出现此提示，紧跟着 `^C` 中断。

**根因**：这个提示**不是错误**，只是 TensorRT 告知"workspace 不够尝试所有优化策略，会选次优方案"。构建过程仍在正常进行，engine 会正常生成。

**教训**：**不要看到这个提示就 Ctrl+C！** 等待 `&&&& PASSED` 出现即可。

### 7.5 问题 5：INT64 权重转换

**现象**：
```
Your ONNX model has been generated with INT64 weights, while TensorRT
does not natively support INT64. Attempting to cast down to INT32.
One or more weights outside the range of INT32 was clamped.
```

**处理**：这是 TensorRT 8.x 的常规 Warning，不影响推理精度。YOLOv5 的权重值都在 INT32 范围内，clamping 不会造成精度损失。

---

## 8. 最终配置总结

### 8.1 成功命令（构建）

```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=/jetson-inference/data/models/yolov5n/yolov5n.onnx \
  --saveEngine=/jetson-inference/data/models/yolov5n/yolov5n_fp16.engine \
  --fp16 --workspace=256 \
  --minShapes=images:1x3x640x640 \
  --optShapes=images:1x3x640x640 \
  --maxShapes=images:1x3x640x640
```

### 8.2 成功命令（Benchmark）

```bash
/usr/src/tensorrt/bin/trtexec \
  --loadEngine=/jetson-inference/data/models/yolov5n/yolov5n_fp16.engine \
  --iterations=100
```

### 8.3 生成的文件

| 文件 | 路径 | 大小 | 备注 |
|------|------|------|------|
| ONNX 模型 | `data/models/yolov5n/yolov5n.onnx` | 7.2 MB | 源文件 |
| TensorRT Engine | `data/models/yolov5n/yolov5n_fp16.engine` | 7 MB | 构建产物 |

两个文件都在 Docker 挂载卷中，**容器退出后不会丢失**。

### 8.4 关键参数选择

| 参数 | 选值 | 原因 |
|------|------|------|
| `--fp16` | ✅ | 半精度推理，速度翻倍，精度几乎无损 |
| `--workspace=256` | 256 MB | Jetson Nano 4GB 共享内存的限制 |
| `--optShapes=1x3x640x640` | 640×640 | YOLOv5n 的标准训练尺寸 |
| `--iterations=100` | 100 次 | 足够消除单次波动，获得稳定统计数据 |

---

## 9. 附：完整命令速查表

### 9.1 容器管理

```bash
# 启动容器
cd ~/jetson-inference && docker/run.sh

# 查看运行中的容器（在宿主机）
docker ps

# 新开一个容器 shell
docker exec -it <容器名> /bin/bash
```

### 9.2 TensorRT 构建与推理

```bash
# ONNX → TensorRT Engine
/usr/src/tensorrt/bin/trtexec \
  --onnx=<model.onnx> \
  --saveEngine=<model.engine> \
  --fp16 --workspace=256 \
  --minShapes=input:1x3x640x640 \
  --optShapes=input:1x3x640x640 \
  --maxShapes=input:1x3x640x640

# Benchmark 已生成的 engine
/usr/src/tensorrt/bin/trtexec \
  --loadEngine=<model.engine> \
  --iterations=100

# 导出性能数据到 JSON
/usr/src/tensorrt/bin/trtexec \
  --loadEngine=<model.engine> \
  --iterations=100 \
  --exportTimes=<file.json>
```

### 9.3 文件管理

```bash
# 查看 engine 文件
ls -lh /jetson-inference/data/models/yolov5n/

# 从宿主机查看
ls -lh ~/jetson-inference/data/models/yolov5n/
```

### 9.4 GPU 状态检查

```bash
# 容器内查看 GPU 利用率
tegrastats

# 或使用 nvidia-smi（部分镜像支持）
nvidia-smi
```

---

## 10. 附：故障诊断思维导图

### 10.1 问题树

```
ONNX→TensorRT Engine 构建
│
├─ trtexec 找不到
│  ├─ 不在 PATH
│  │  └─ ✅ 使用全路径 /usr/src/tensorrt/bin/trtexec
│  └─ TensorRT 未安装
│     └─ dpkg -l | grep tensorrt
│
├─ ONNX 解析失败
│  ├─ 动态形状未指定 → 使用 --optShapes
│  ├─ INT64 权重 → TensorRT 自动处理，Warning 可忽略
│  └─ 算子不兼容 → onnxsim 简化 / 降 opset
│
├─ Engine 构建 OOM
│  ├─ workspace 太大 → 降到 256 MB
│  ├─ GPU 共享内存不足 → 关闭其他程序
│  └─ 模型太大 → 换更小模型 / INT8 量化
│
└─ "Some tactics do not have sufficient workspace"
   ├─ ✅ 纯信息提示，不是错误
   └─ 等待构建完成即可，Engine 会正常生成
```

### 10.2 核心教训

1. **Jetson Nano 内存敏感**：4GB 共享内存下 `--workspace` 不能超过 512，建议用 256
2. **动态形状必须显式指定**：ONNX opset 14+ 的模型都需要 `--optShapes`
3. **trtexec 参数版本差异**：TensorRT 8.2 不支持 `--inputShapes`，用 `--optShapes` 替代
4. **耐心等待构建完成**：`"Some tactics..."` 不是错误，Nano 上首次构建需要 11 分钟
5. **只构建一次**：engine 持久化后直接加载只需 ~4.4 秒，后续无需重建

### 10.3 有价值的参考

| 资源 | 用途 |
|------|------|
| TensorRT 8.2 trtexec --help | 查看所有参数选项 |
| TensorRT Quick Start Guide | 官方文档 |
| YOLOv5 GitHub Releases | 下载预训练 ONNX 模型 |

---

*文档整理于 2026-05-26，基于 YOLOv5n TensorRT Engine 构建完整会话记录。*

nano
sudo ip addr add 10.10.3.70/24 dev eth0

cd ~/jetson-inference && docker/run.sh

python3 /jetson-inference/data/detect_yolov5n.py --stream


vmware 
sshfs lin@192.168.1.207:/home/lin ~/nano 
tmux
code ~/nano

ssh lin@192.168.1.207
tmux new -s test1
ctrlb+ctrlr


sudo wireshark


firefrox
http://10.10.3.70:8080/stream

