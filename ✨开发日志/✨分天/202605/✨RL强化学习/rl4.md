这是一次**成功、质量不错的完整训练**，不是“勉强跑通”。UniLab 官方把 FastSAC、G1、MuJoCoUni / MotrixSim 都列为支持对象，并且公开页给出的代表性结果里，G1 Walk Flat 在 RTX 4090 基线下是 18.3 分钟、对应 8.4× 的 wall-clock 加速；你这次 5000/5000、总计 10,240,000 env steps、14m12s 完成，整体已经落在官方宣称的高吞吐范围内，甚至在这个单次运行上看起来更快。 ([unilabsim.github.io][1])

算法层面，这个结果是健康的。SAC 本来就是 off-policy 的最大熵 actor-critic：actor 既要追求回报，也要保留熵，所以 `Actor Loss` 为负、`Alpha` 很小、`Action Std` 仍在 0.29 左右，并不奇怪；`Qf Loss = 2.615` 也没有发散迹象，说明 critic 还在稳定地拟合目标 Q。([arXiv][2])

奖励结构也很清楚：`Reward Mean 291.732 / Peak 296.207` 已经是很高的水平；`alive +10` 稳定拿满，`tracking lin vel +1.7054` 和 `tracking ang vel +0.8459` 说明速度跟踪已经成了主信号，`feet +4.8049` 也表明落脚/步态相关项在起作用。换句话说，这个策略已经不是“随机乱走”，而是进入了比较成形的行走策略阶段。这个结论来自你日志里的数值本身，不是猜测。

系统层面，瓶颈不在 GPU，而在采样和仿真流水线：`Envs = 2048`、`Env Step = 95.4ms`、`Replay = 3.1ms`、`Weight Sync = 1.0ms` 说明主要成本仍然是 MuJoCo + collector 的环境步进与同步。`Timeout Rate 100…` 和 `Terminated 0.0%` 这一组如果按常见语义理解，说明 episode 大多是到时间上限结束，而不是因为摔倒或提前终止；这在平地行走任务里通常是好现象。不过你贴出来的这一栏被截断了，所以我不会把那个“100”精确解读成某个固定百分比。

那些 `gymnasium.spaces.Box` 的 `overflow encountered in cast` 警告，属于**低严重度但值得清理**的问题。Gymnasium 的 `Box` 用来定义观测/动作空间，官方文档和 release notes 都提到：当 `low/high` 超出 dtype 范围、或使用过大的边界值时，可能出现这类 cast/边界边缘情况。它通常不会直接阻断训练，但会暗示你的 space bounds 里有 `inf`、过大数值，或者 dtype 设计不够干净。([Gymnasium][3])

最后看部署链路：`model_5000.pt` 成功保存，`policy.onnx` 成功导出，而且 `ONNX vs PyTorch` 的 `max_diff = 4.77e-07`、`mean_diff = 1.05e-07` 非常小，说明导出几乎是数值等价的；`play_video.mp4` 也成功渲染完成，这表示训练、导出、回放三段链路都闭环了。

一句话评价：**这是一个可用、可复现、结构正确的训练结果**。下一步最有价值的是先看 `play_video.mp4`，再做 2–3 个不同 seed 的重复跑，确认这个 reward 和步态不是偶然收敛。

[1]: https://unilabsim.github.io/ "UniLab — A Heterogeneous Training Framework for Embodied Reinforcement Learning"
[2]: https://arxiv.org/abs/1801.01290?utm_source=chatgpt.com "Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor"
[3]: https://gymnasium.farama.org/_modules/gymnasium/spaces/box/?utm_source=chatgpt.com "Source code for gymnasium.spaces.box"


下面是一版完整复盘，按“环境搭建 → 训练跑通 → 结果解读 → 你现在的位置 → 下一步”整理。

## 1) 先把环境打通了

你这台云主机配置已经够用：

* RTX 4090 24GB
* 14 核 CPU
* 50 GB 内存
* 系统盘 30 GB
* 数据盘 50 GB

真正要注意的是：**代码、仓库、日志、checkpoint、视频都放数据盘**，系统盘只放少量系统和必要配置。后来你把工作目录放到 `/root/gpufree-data/robot_rl` 这一点是对的。

---

## 2) 解决了 GitHub 连接问题

你最开始 `git clone` UniLab 时出现过：

* TLS 连接非正常终止
* clone 失败

后来通过：

```bash
git config --global http.version HTTP/1.1
git config --global http.postBuffer 524288000
```

再 clone，成功了。
这一步很关键，因为它说明问题不是“彻底连不上 GitHub”，而是 HTTPS/TLS 兼容性或连接稳定性问题。

---

## 3) UniLab 环境安装成功

你完成了这些关键动作：

* 安装 `uv`
* 进入 UniLab 仓库
* `make setup-motrix`
* `uv sync --extra motrix`
* 自动创建 `.venv`
* 安装完成约 185 个包
* 最终得到：

  * `torch==2.7.0+cu128`
  * `mujoco-uni`
  * `motrixsim-core`
  * `rsl-rl-lib`
  * 以及一整套训练依赖

这意味着：

**UniLab 的运行环境已经完整建立。**

另外你也确认了：

```bash
which python
```

指向的是 UniLab 的 `.venv`，这说明你后面跑训练时已经不是系统 Python 了，而是在项目自己的隔离环境里执行。

---

## 4) 第一条训练链路已经跑通：Go2 + Motrix + APPO

你先跑通的是：

```bash
uv run train --algo appo --task go2_joystick_flat --sim motrix
```

这一步的结果非常好，训练日志显示：

* `iter 180/180`
* `Total env steps: 2,283,520`
* `Total time: 18s`
* 最后生成：

  * `model_180.pt`
  * `policy.onnx`

并且：

* ONNX 导出成功
* ONNX vs PyTorch 的差异很小
* 说明策略网络导出是正确的

这一步的意义是：

**训练、保存、导出、回放整个闭环第一次打通了。**

你后来用 `--render-mode record` 把视频导出来，得到 `play_video.mp4`，这说明：

* 训练已完成
* 回放已完成
* 离线视频导出已完成

SSH 没图形界面，所以交互式窗口会卡在渲染等待上；但改成 record 模式后就能正常生成视频，这是正确处理方式。

---

## 5) 第二条训练链路也跑通了：G1WalkFlat + MuJoCo + FastSAC

你后来跑的是：

```bash
uv run train --algo sac --task g1_walk_flat --sim mujoco
```

这次训练日志显示：

* `FastSAC | G1WalkFlat`
* `iter 5000/5000`
* `Total time: 14m12s`
* `Total env steps: 10,240,000`
* 最后 checkpoint：

  * `model_5000.pt`

并且同样完成了：

* ONNX 导出
* ONNX 与 PyTorch 比对
* 视频回放导出 `play_video.mp4`

这说明：

**MuJoCo 路线也完全跑通了。**

---

## 6) 这次训练结果本身质量不错

你最后这次 G1WalkFlat 的指标很值得肯定：

* `Reward Mean 291.732 / Peak 296.207`
* `alive +10.0000`
* `feet +4.8049`
* `tracking +1.7054`
* `tracking +0.8459`
* `Qf Loss 2.615`
* `Action Std 0.2910`
* `Alpha 0.0041`

从工程角度看，这意味着：

* 策略已经不是乱走
* 存活奖励稳定拿满
* 速度跟踪项已经学起来了
* critic 没有明显发散
* policy 也没有崩掉

这是一份**可用的、已经成形的 locomotion 策略**，不是“勉强训练完”的状态。

---

## 7) 那些 warning 是什么

你在 MuJoCo 路线里看到的：

```text
gymnasium.spaces.box.py: overflow encountered in cast
```

这类 warning 的本质是：

* Gymnasium 在构造 `Box` 空间时
* 有些 `low/high` 或 dtype 相关的边界值触发了 cast 溢出警告

它通常是：

* 空间定义不够干净
* 使用了过大的边界值
* 或者有 `inf / -inf` 一类设定

但从你的训练结果看，这**不是致命错误**，因为训练仍然完整执行到了 5000/5000，并且导出和回放都成功了。

---

## 8) 为什么 MuJoCo 这条看起来比前面的更慢

你后来已经观察到：

* `Env Step` 约 95 ms
* `Envs = 2048`
* `Replay` 和 `Sync Coordinator` 也有不小开销

所以慢的主要原因不是 GPU，而是：

1. **MuJoCo 的 CPU 物理仿真开销**
2. **2048 并行环境的同步代价**
3. **SAC / FastSAC 的 replay 与 critic 计算**
4. **任务本身更复杂**

所以你体感“慢”，其实是正常的研究级并行训练开销，不是程序卡死。

---

## 9) 你已经理解了很多关键名词

这一轮你已经把下面这些东西真正串起来了：

* `FR / FL / RR / RL`：四条腿的命名
* `rpy`：URDF 中的姿态旋转写法
* `Box space overflow`：空间边界警告
* `ETA`：根据当前吞吐估计的剩余训练时间
* `Actor Loss / Qf Loss / Alpha / Action Std`：SAC 的核心监控量
* `Env Step / Replay / Sync Coordinator`：采样管线的瓶颈拆分
* `model_5000.pt` / `policy.onnx` / `play_video.mp4`：训练到部署的输出链路

---

## 10) 你现在所处的位置

现在你的状态已经不是“在学怎么装环境”，而是：

**你已经有一个能在 4090 云主机上训练、导出、回放的 RL 四足流程了。**

这点很重要，因为接下来就不是抽象概念，而是开始做你的**真实 12DOF 串联四足**了。

---

## 11) 下一步最该做什么

按优先级，应该是：

1. **先看这两个视频**

   * `Go2JoystickFlat` 的回放
   * `G1WalkFlat` 的回放
     这样你会直观看到策略到底学成了什么样。

2. **把 G1WalkFlat 的配置文件、reward、observation、action 结构找出来**
   这是后面迁移到你自己的 12DOF 机器人的关键模板。

3. **开始准备你自己的 URDF**
   你的四足是：

   * 单腿 3DOF
   * 4 腿共 12DOF
   * 关节顺序明确
   * 非常适合照着现成任务改

4. **把自己的机器人接入 UniLab 的 task / reward / action 配置**
   这一步会从“跑官方任务”进入“跑自己的机器人”。

---

## 12) 最后一句总评价

这一轮不是“试运行成功”，而是：

**你已经把一条完整的四足强化学习链路真正跑通了：**
从安装、依赖、GPU识别、训练、保存、导出 ONNX，到视频回放，全都闭环了。

如果把这次工作压缩成一句话，就是：

**UniLab 环境已建立，4090 训练正常，Go2 与 G1 两条官方任务都已跑通，下一步可以正式转入你自己的 12DOF 四足建模与迁移。**
