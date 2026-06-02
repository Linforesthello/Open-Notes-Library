
# UniLab 强化学习框架部署与四足机器人训练实验记录

**实验日期：** 2026-06-02
**实验平台：** 云端 RTX4090 Linux 环境
**实验目标：**

* 部署 UniLab 强化学习框架
* 配置 Motrix 仿真环境
* 完成 Go2 四足机器人训练
* 验证 CUDA 训练能力
* 导出 ONNX 策略模型
* 生成仿真视频
* 运行官方 Demo

---

# 一、实验环境

## 硬件资源

| 项目     | 配置             |
| ------ | -------------- |
| GPU    | NVIDIA RTX4090 |
| CPU    | 14 Core        |
| Memory | 50GB           |
| OS     | Linux          |

运行确认：

```bash
nvidia-smi
```

---

## Python环境

初期尝试：

```bash
conda create -n rl python=3.10 -y
conda activate rl
```

后续发现：

UniLab 官方已经完全采用：

```text
uv
```

管理环境。

因此最终使用：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装 uv。

验证：

```bash
uv --version
```

结果：

```text
uv 0.11.18
```

---

# 二、获取 UniLab 源码

创建工作目录：

```bash
mkdir -p /root/gpufree-data/robot_rl/repos
```

进入目录：

```bash
cd /root/gpufree-data/robot_rl/repos
```

克隆仓库：

```bash
git clone https://github.com/unilabsim/UniLab.git
```

进入项目：

```bash
cd UniLab
```

---

# 三、分析项目依赖

查看 Python 版本要求：

```bash
grep requires-python pyproject.toml
```

结果：

```text
requires-python = ">=3.10,<3.14"
```

说明：

支持：

```text
Python 3.10
Python 3.11
Python 3.12
Python 3.13
```

---

查看 PyTorch 要求：

```bash
grep -n "torch" pyproject.toml
```

结果：

```text
torch==2.7.0
```

同时发现：

```text
CUDA 12.8
```

官方仓库：

```text
https://download.pytorch.org/whl/cu128
```

---

# 四、安装 Motrix 版本环境

确认 Make 工具：

```bash
make --version
```

执行：

```bash
make setup-motrix
```

实际执行内容：

```bash
uv sync --extra motrix
```

---

## 安装结果

自动创建：

```text
.venv
```

虚拟环境。

共安装：

```text
185 Packages
```

主要组件包括：

### 深度学习

```text
torch 2.7.0+cu128
triton
tensorboard
```

### 强化学习

```text
rsl_rl
tensordict
gymnasium
```

### 仿真

```text
motrixsim-core
mujoco-uni
```

### ONNX

```text
onnx
onnxruntime
onnxscript
```

### HuggingFace

```text
huggingface-hub
```

---

# 五、验证环境

激活环境：

```bash
source .venv/bin/activate
```

检查 Python：

```bash
which python
```

结果：

```text
/root/.../UniLab/.venv/bin/python
```

说明：

已经进入 UniLab 专属环境。

---

验证 PyTorch：

```bash
python -c "import torch;print(torch.__version__)"
```

输出：

```text
2.7.0+cu128
```

---

验证 CUDA：

```bash
python -c "
import torch
print(torch.cuda.get_device_name(0))
"
```

结果：

```text
NVIDIA GeForce RTX 4090
```

说明：

GPU 已正确接入。

---

# 六、探索任务配置

查看可用任务：

```bash
find conf -type f | grep go2
```

查看：

```bash
find conf/task -type f | less
```

确认存在：

```text
go2_joystick_flat
```

任务。

---

# 七、首次强化学习训练

执行：

```bash
uv run train \
  --algo appo \
  --task go2_joystick_flat \
  --sim motrix
```

---

## 实际训练结果

训练输出：

```text
APPO | Go2JoystickFlat
```

---

训练环境：

```text
Envs = 512
```

---

训练轮数：

```text
180 Iterations
```

---

环境步数：

```text
2,283,520 Steps
```

---

总耗时：

```text
18 Seconds
```

---

最终奖励：

```text
Mean Reward ≈ 40.9
Peak Reward ≈ 41.8
```

---

训练结束自动保存：

```text
model_180.pt
```

位置：

```text
logs/appo/Go2JoystickFlat/...
```

---

# 八、ONNX 导出验证

训练结束后自动执行：

```text
Exported actor ONNX
```

生成：

```text
policy.onnx
```

---

一致性检查：

```text
max_diff = 9.54e-07
mean_diff = 2.01e-07
```

结果：

```text
ONNX export verified OK
```

说明：

导出成功。

推理结果与 PyTorch 基本一致。

---

# 九、首次可视化问题

训练完成后自动进入：

```text
interactive visualization
```

出现：

```text
XDG_RUNTIME_DIR not set
```

原因：

云服务器无桌面环境。

Motrix Renderer 无法弹出窗口。

---

随后程序停留在：

```text
Rendering playback frames...
```

等待用户关闭窗口。

最终：

```bash
Ctrl + C
```

退出。

---

# 十、问题分析

并非：

```text
训练失败
```

而是：

```text
图形界面无法显示
```

训练本身已经全部完成。

模型也已经保存。

---

# 十一、使用录像模式评估

执行：

```bash
uv run eval \
  --algo appo \
  --task go2_joystick_flat \
  --sim motrix \
  --load-run -1 \
  --render-mode record
```

---

含义：

```text
--load-run -1
```

加载最新训练结果。

---

```text
--render-mode record
```

不显示窗口。

直接生成视频。

---

# 十二、生成仿真视频

输出：

```text
Rendering video...
```

---

保存：

```text
play_video.mp4
```

位置：

```text
logs/appo/Go2JoystickFlat/.../
```

---

成功输出：

```text
Done.
```

说明：

录像生成成功。

---

# 十三、验证训练效果

下载视频后观察：

现象：

```text
Go2 四足机器人
```

能够：

* 保持站立
* 执行运动控制
* 按策略行走

说明：

训练结果有效。

---

# 十四、运行官方 Demo

执行：

```bash
uv run demo dance
```

---

首次运行时卡住：

原因：

需要下载资源。

下载内容：

```text
model_0.pt
```

约：

```text
6.7 MB
```

---

随后自动下载：

```text
dance1_subject2_part.npz
```

运动捕捉数据。

来源：

```text
HuggingFace
```

---

下载完成后：

```text
Loading latest model
```

成功。

---

# 十五、Dance Demo 网络机制分析

首次运行：

```text
需要联网
```

原因：

自动从云端获取：

* 策略模型
* Motion 数据
* 预训练权重

---

缓存位置：

```text
src/unilab/assets/
```

---

后续再次运行：

```text
无需重复下载
```

直接读取缓存。

---

# 十六、实验中遇到的主要问题

---

## 问题1

### 现象

```text
uv 不存在
```

### 解决

安装：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 问题2

### 现象

```text
图形界面打不开
```

### 原因

云服务器无 GUI。

### 解决

使用：

```bash
--render-mode record
```

生成视频。

---

## 问题3

### 现象

```text
demo dance 卡住
```

### 原因

下载模型。

### 解决

等待 HuggingFace 下载完成。

---

# 十七、实验成果

成功完成：

* UniLab 部署
* uv 环境管理
* CUDA验证
* APPO训练
* Go2任务训练
* ONNX导出
* ONNX验证
* Playback评估
* 视频生成
* Demo运行
* HuggingFace资源下载

---

# 十八、下一阶段规划

建议按以下顺序推进：

## 第一阶段

理解任务结构

```bash
conf/task/go2_joystick_flat.yaml
```

研究：

* Observation
* Action
* Reward

---

## 第二阶段

修改奖励函数：

```python
reward_tracking_lin_vel
reward_tracking_ang_vel
reward_action_rate
```

观察训练变化。

---

## 第三阶段

训练新策略：

```text
前进
后退
转向
高速跑步
```

---

## 第四阶段

学习 RL 工程体系

* PPO
* APPO
* SAC
* DDPG
* Dreamer

---

## 第五阶段

结合你的机器人系统路线

```text
STM32
 ↓
CAN
 ↓
ROS2
 ↓
状态估计
 ↓
MPC
 ↓
RL Policy
 ↓
四足机器人
```

形成从底层控制到强化学习控制的完整技术链路。
