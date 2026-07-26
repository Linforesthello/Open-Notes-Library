下面把这次完整过程再扩成一份“实验复盘版”，尽量把**命令、输出、现象、错误、修复、结果**都写出来。你后面无论是复现 UniLab，还是把自己的 12 自由度四足接进去，这份记录都能直接当作操作手册和排错日志。

---

# 1. 初始目标与机器条件

你的目标不是“装一个软件”，而是要把一台云主机变成可用的四足强化学习训练节点。你拿到的是一台通过 SSH 访问的 Ubuntu 22.04 云主机，核心配置是：

* RTX 4090 / 24GB
* CPU 14 核
* 内存 50GB
* 系统盘 30GB
* 数据盘 50GB

这类配置对传统深度学习是够用的，但对机器人 RL 更关键的是：**GPU 是否可用、磁盘是否够放依赖、网络是否能稳定拉取大包、以及安装流程是否尽量自动化**。UniLab 官方仓库明确把 Linux CUDA 路线的推荐安装方式写成 `uv` + `make setup-motrix`，并且把训练、评估、demo 都统一在 `uv run train / eval / demo` 这一套命令下。仓库 README 还说明了 Linux CUDA 或 macOS 推荐 `make setup-motrix`，并给出了 `uv run train --algo appo --task go2_joystick_flat --sim motrix`、`uv run eval ... --render-mode record`、`uv run demo dance` 等标准入口。([GitHub][1])

---

# 2. 第一阶段：确认云主机和系统环境

最开始你先执行了这些命令：

```bash
nvidia-smi
python3 --version
conda --version
df -h
uname -a
```

得到的关键信息是：

1. `nvidia-smi` 正常，4090 被识别；
2. 系统默认 Python 是 3.13.9；
3. Conda 可用；
4. 系统盘只有 30GB，这一点非常危险；
5. 数据盘在 `/root/gpufree-data`，适合放大文件，但释放实例时不保存。

这一步的目的不是“看一眼配置”，而是判断后面会不会碰到以下常见问题：

* 依赖装到一半系统盘爆掉；
* GPU 不可用；
* Python 版本太高导致一堆库不兼容；
* 下载大 wheel 时网络抖动严重。

你一开始就意识到不能直接用系统 Python 3.13 来做机器人 RL，所以后面切到了 Conda 的 Python 3.10，这一步非常关键。

---

# 3. 第二阶段：第一次尝试手工装 Torch，发现不适合继续硬顶

你先尝试了比较直觉的路线：

```bash
conda create -n rl python=3.10 -y
conda activate rl
pip install torch torchvision torchaudio
```

这个阶段暴露了两个现实问题。

## 问题 A：Torch 相关 wheel 体积非常大

你在安装时看到了：

* `torch` 主包几百 MB；
* `nvidia-cublas` 几百 MB；
* `nvidia-cudnn` 几百 MB；
* 其他 CUDA 相关依赖继续往下拉。

这意味着如果完全靠自己手工 `pip install`，不仅慢，而且很容易把 30GB 系统盘缓存塞满。你的网络速度又不稳定，所以这一套并不是最优解。

## 问题 B：手工装依赖容易和项目锁定版本冲突

后来你看 UniLab 的 `pyproject.toml`，发现它明确锁定了：

* `requires-python = ">=3.10,<3.14"`
* `torch==2.7.0`
* Linux 下使用 `pytorch-cu128`

也就是说，自己先装一个 Torch，再去让 UniLab 接管，不如干脆按照项目官方锁定的版本走。这样更稳定，也更少踩兼容性坑。

---

# 4. 第三阶段：GitHub 拉仓库时出现 TLS 错误，改 Git 传输模式解决

你第一次 `git clone` UniLab 的时候失败过，报的是典型的 TLS 中断错误：

```text
GnuTLS recv error (-110): The TLS connection was non-properly terminated
```

你并没有直接放弃，而是先验证网络本身：

```bash
ping github.com -c 4
curl -I https://github.com
git ls-remote https://github.com/unilabsim/UniLab.git
```

结果说明：

* GitHub 是能 ping 通的；
* HTTPS 也不是完全不可达；
* 只是 `git clone` 的 TLS/传输阶段有问题。

然后你做了两个关键配置：

```bash
git config --global http.version HTTP/1.1
git config --global http.postBuffer 524288000
```

这一步把 Git 从更容易出问题的传输方式切回更稳的 HTTP/1.1，也扩大了 postBuffer。之后重新执行：

```bash
cd /root/gpufree-data/robot_rl/repos
git clone https://github.com/unilabsim/UniLab.git
```

终于成功，仓库完整拉下来了。这个经验很重要：**不是 GitHub 不能用，而是 Git 的传输方式和云主机网络环境不太兼容**。

---

# 5. 第四阶段：不再手工拼依赖，改走 UniLab 官方安装方式

你随后查看了 UniLab 仓库的 README 和 `pyproject.toml`，确认了几件核心事情。README 里明确写着：

* 推荐使用 `uv`；
* Linux CUDA 路线用 `make setup-motrix`；
* `uv run train`、`uv run eval`、`uv run demo` 是统一入口；
* 中国大陆用户如果 `huggingface.co` 不可达，可以先设置 `HF_ENDPOINT=https://hf-mirror.com`。 ([GitHub][1])

于是你先安装了 `uv`：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv --version
```

确认 `uv 0.11.18` 可用之后，开始正式安装 UniLab 依赖：

```bash
cd /root/gpufree-data/robot_rl/repos/UniLab
make setup-motrix
```

这一步是整个过程中的核心转折。

它自动完成了：

* 创建项目 `.venv`
* 解析依赖
* 安装 185 个包
* 安装 `torch==2.7.0+cu128`
* 安装 `mujoco-uni`
* 安装 `motrixsim-core`
* 安装 `rsl-rl-lib`
* 安装各种训练和可视化依赖
* 给 bash 装上 shell completion

从结果上看，**你已经不再是“装框架失败的用户”，而是已经有一个真正可用的 UniLab 训练环境了**。

---

# 6. 第五阶段：验证虚拟环境和 GPU 真正可用

安装完成后，你检查了环境：

```bash
source .venv/bin/activate
which python
python -c "import torch;print(torch.__version__)"
python -c "import torch;print(torch.cuda.get_device_name(0))"
```

得到的结果是：

* Python 指向 `.venv/bin/python`
* Torch 版本为 `2.7.0+cu128`
* GPU 名称显示为 `NVIDIA GeForce RTX 4090`

这意味着：

1. 没有混用系统 Python；
2. UniLab 安装所用的 Torch 版本和 CUDA 版本是匹配的；
3. 4090 被 PyTorch 正常识别；
4. 训练端基础环境已经完全成立。

---

# 7. 第六阶段：第一次真训练，Go2 任务跑通

你开始运行官方推荐的四足训练任务：

```bash
uv run train \
  --algo appo \
  --task go2_joystick_flat \
  --sim motrix
```

这条命令是 UniLab README 里明确给出的训练示例。它对应的任务是：

* 机器人：Go2
* 任务：平地速度跟踪
* 算法：APPO
* 仿真：Motrix

README 里还写明，UniLab 的设计是 CPU 负责仿真、GPU 负责策略训练，支持 `PPO / SAC / TD3` 等算法，且 `go2_joystick_flat/motrix` 是标准训练路径。([GitHub][1])

训练日志里你看到了非常重要的结果：

* `Envs 512`
* `Iterations: 180/180`
* `Total env steps: 2,283,520`
* `Total time: 18s`
* 最后生成了 `model_180.pt`

这说明：

1. 512 个环境并行工作；
2. 总共采样了 228 万步；
3. 训练不是卡住，而是成功完成；
4. 4090 对这类配置的 RL 训练确实够快。

日志中的 reward 项也很有信息量，比如：

* `tracking lin vel`
* `tracking ang vel`
* `swing feet z`
* `contact`
* `base height`

这些就是典型四足 locomotion 奖励项，说明你已经碰到了实际的四足运动控制 reward 设计，而不是停留在安装层面。

---

# 8. 第七阶段：第一次回放失败，问题在图形环境，不在训练本身

训练结束后，UniLab 自动进入交互回放阶段：

```text
Starting interactive visualization (motrix native renderer)...
Close the render window to exit.
```

然后报了：

```text
XDG_RUNTIME_DIR not set in the environment.
```

这个错误很典型，它不是训练错误，而是**你在纯 SSH 云主机上没有图形桌面环境**。程序试图打开窗口播放，但系统里没有真正可用的 GUI 会话，于是进入等待状态。你按 `Ctrl+C` 之后，进程被中断。

这一步的结论很明确：

* 训练已经成功；
* 模型已经保存；
* 失败的是“实时窗口渲染”，不是 RL；
* 在 SSH 服务器上不应该直接期待弹窗，而应该用录制模式或导出视频。

---

# 9. 第八阶段：改用 record 模式，成功导出视频

于是你换成了：

```bash
uv run eval \
  --algo appo \
  --task go2_joystick_flat \
  --sim motrix \
  --load-run -1 \
  --render-mode record
```

这次没有去开实时窗口，而是直接把回放录成视频。日志显示：

* 成功加载 `model_180.pt`
* 成功导出 `policy.onnx`
* `ONNX vs PyTorch` 的数值差很小，验证通过
* 最后保存出了 `play_video.mp4`

这意味着：

1. checkpoint 可以正常读；
2. ONNX 导出没问题；
3. 评估流程没问题；
4. 视频生成没问题；
5. 你的训练产物已经可以进一步用于部署。

这一步非常重要，因为它说明整个训练链路不只是“跑完”，而是**真的有可用输出**。

---

# 10. 第九阶段：`demo dance` 暴露 HuggingFace 下载问题

接着你又尝试了：

```bash
uv run demo dance
```

这次你先遇到的是下载预训练资源的问题。UniLab README 本来就说明了，`uv run demo dance` 会在第一次运行时从 HuggingFace 拉取 checkpoint；如果 `huggingface.co` 不可达，可以设置：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

README 也明确写了这条给中国大陆用户的镜像建议。([GitHub][1])

你在实际执行中确实看到：

* `model_0.pt` 被下载；
* 然后开始拉 `motions/g1/dance1_subject2_part.npz`；
* 请求走到了 `hf-mirror.com`；
* 下载完成后开始读取 motion 资源。

这说明镜像配置开始起作用，demo 确实在抓资源。

---

# 11. 第十阶段：理解 `dance` 和 `go2_joystick_flat` 是两条不同机器人路线

从日志里你又发现一个很重要的事实：`dance` 不是 Go2，而是 **G1**。理由很直观：

* 下载的 motion 路径里有 `g1`
* 进入模型后输出了 `29` 维 action
* 这明显不是 Go2 的 12 个关节动作空间

所以你实际上碰到了两类任务：

## A. Go2JoystickFlat

典型四足 locomotion：

* 输入：速度指令
* 输出：关节动作
* 目标：稳定行走、跟踪速度
* 适合你这种四足控制背景

## B. G1 Dance / Motion Tracking

典型动作模仿：

* 输入：动作序列或 motion capture
* 输出：机器人关节动作
* 目标：模仿舞蹈、翻滚、复杂动作
* 更偏人形机器人动作跟踪

你看到这两条路线，实际上就已经把机器人 RL 中“运动控制”和“动作模仿”两大主流任务区分开了。

---

# 12. 整个过程中遇到的主要问题与对应解决方法

## 问题 1：系统 Python 太新，生态不稳

**现象**：系统 Python 是 3.13.9。
**解决**：用 Conda 创建 Python 3.10 环境。
**结果**：后续 UniLab 依赖能正常安装。

## 问题 2：手工 `pip install torch` 太慢且容易炸盘

**现象**：CUDA 相关 wheel 很大，下载慢。
**解决**：改走 UniLab 官方 `uv + make setup-motrix`。
**结果**：依赖统一安装，版本锁定，Torch 也自动对上。

## 问题 3：GitHub clone 时 TLS 中断

**现象**：`GnuTLS recv error (-110)`。
**解决**：`git config --global http.version HTTP/1.1`。
**结果**：仓库成功克隆。

## 问题 4：SSH 服务器没有 GUI

**现象**：`XDG_RUNTIME_DIR not set`。
**解决**：用 `--render-mode record` 输出视频。
**结果**：成功生成 `play_video.mp4`。

## 问题 5：HuggingFace 资源下载慢/卡

**现象**：`demo dance` 要下载 checkpoint 和 motion。
**解决**：设置 `HF_ENDPOINT=https://hf-mirror.com`。
**结果**：资源下载可以通过镜像完成。README 也明确建议大陆用户这么做。([GitHub][1])

---

# 13. 最终结果：你已经跑通了一个完整的机器人 RL 闭环

从工程角度看，你这次不只是“装了一个库”，而是真的打通了以下链条：

```text
4090云主机
→ Ubuntu 22.04
→ Conda / Python 3.10
→ uv
→ UniLab 源码
→ make setup-motrix
→ Torch 2.7.0 + cu128
→ Go2JoystickFlat 训练
→ checkpoint 保存
→ ONNX 导出
→ 视频回放
→ HuggingFace 镜像下载
→ G1 dance demo 资源拉取
```

这条链路的意义很大，因为它已经覆盖了机器人强化学习最关键的几个阶段：

1. 环境部署；
2. 仿真训练；
3. checkpoint / ONNX 导出；
4. 评估回放；
5. 资源下载与镜像处理；
6. 任务区分（locomotion vs motion tracking）。

---

# 14. 对你后续最重要的下一步

你现在最值得做的，不是继续装东西，而是开始把这次跑通的经验迁移到自己的 12 自由度四足上。路线应该是：

1. 找到 Go2 的 task 配置；
2. 理解 observation、action、reward；
3. 看关节命名和动作空间；
4. 做你自己的 URDF；
5. 先做站立任务；
6. 再做速度跟踪；
7. 再考虑 ROS2、STM32、CAN 的实机部署。

你现在已经具备一个非常关键的起点：**你不是在研究“RL 是什么”，而是在研究“怎么把 RL 真正接进机器人系统”**。这是两个完全不同的层次。

如果你下一步要，我可以继续把这份总结整理成一版更正式的 Markdown 实验记录，按“环境准备 / 安装过程 / 训练过程 / 回放过程 / 错误处理 / 最终结论”分段排版，直接适合你以后归档。

[1]: https://github.com/unilabsim/UniLab?utm_source=chatgpt.com "UniLab: A Heterogeneous Architecture for Robot RL ..."
