是的，而且你实际上已经完成了**两个不同层次的 RL 例子**。

---

# 1 你第一次看到的是 Go2 四足机器人

运行命令：

```bash
uv run train \
  --algo appo \
  --task go2_joystick_flat \
  --sim motrix
```

这里：

```text
task = go2_joystick_flat
```

就是：

```text
Unitree Go2
四足机器人
速度跟踪任务
```

相当于：

```text
输入：
vx
vy
yaw_rate

↓

RL策略网络

↓

12个关节动作

↓

四足步态
```

目标是让机器人跟踪给定速度。([unilabsim.github.io][1])

---

从训练日志可以看出来：

```text
Reward
tracking lin vel
tracking ang vel
swing feet z
contact
base height
```

这些都是典型的四足 locomotion（运动控制）奖励项：

| 奖励项              | 含义    |
| ---------------- | ----- |
| tracking lin vel | 跟踪线速度 |
| tracking ang vel | 跟踪角速度 |
| swing feet z     | 摆腿高度  |
| contact          | 足端接触  |
| base height      | 身体高度  |

这就是经典：

```text
Legged Gym
Isaac Gym
RSL-RL
Unitree RL

这一脉
```

的奖励设计。

---

# 2 为什么18秒就训练完了？

你这里看到：

```text
Iterations: 180
Total env steps: 2,283,520

Total time: 18s
```

很多人第一次看到都会懵：

```text
卧槽
RL 18秒？
```

实际上：

```text
这是 Demo 配置
```

不是论文训练配置。

---

日志里：

```text
Envs 512
```

说明：

```text
512个Go2同时训练
```

类似：

```python
for i in range(512):
    simulate_go2()
```

并行执行。

---

你的环境：

```text
CPU:
14 Core

GPU:
RTX4090
```

而 UniLab 的核心思想正是：

```text
CPU负责仿真

GPU负责训练
```

即：

```text
CPU Sim
   ↓
Shared Memory
   ↓
GPU Learn
```

这正是他们论文宣传的异构架构。([unilabsim.github.io][2])

---

# 3 后面为什么突然弹出了四足机器人画面？

训练结束后：

```text
Training complete
```

接着：

```text
Loading model
Exported actor ONNX
ONNX export verified OK
```

然后：

```text
Starting interactive visualization
```

实际上程序自动执行了：

```text
训练
↓
保存模型
↓
加载模型
↓
播放训练结果
```

所以你看到的是：

```text
已经训练好的Go2策略
```

而不是训练过程。

---

# 4 为什么后来卡住了？

这里：

```text
Close the render window to exit.
```

UniLab等你关闭窗口。

但是你是在：

```text
云服务器
```

上跑的。

所以：

```text
没有真正桌面环境
```

导致：

```text
XDG_RUNTIME_DIR not set
```

然后：

```text
Ctrl+C
```

强行退出。

这不是训练失败。

实际上：

```text
训练已经结束
模型已经保存
```

---

# 5 后来你运行的 dance 是什么？

你执行：

```bash
uv run demo dance
```

这就不是四足了。

---

从日志：

```text
motions/g1/dance1_subject2_part.npz
```

可以直接看出：

```text
g1
```

即：

Unitree G1

人形机器人。

---

而且网络输出：

```text
29 actions
```

明显不可能是 Go2。

Go2：

```text
12 DOF
```

每条腿：

```text
hip
thigh
calf
```

3自由度。

总共：

```text
12关节
```

---

G1则是：

```text
双腿
腰部
双臂
躯干
```

大量关节。

所以：

```text
29动作维度
```

很正常。

---

# 6 dance 本质是什么？

你下载了：

```text
dance1_subject2_part.npz
```

这不是普通 RL。

而是：

```text
Motion Tracking
```

动作模仿。

即：

```text
人体动作捕捉
      ↓
动作轨迹
      ↓
RL学习
      ↓
机器人模仿
```

类似：

* DeepMimic
* ASE
* AMP
* HOVER
* H1/G1 Motion Tracking

这一类技术。

([unilabsim.github.io][1])

---

# 7 你现在已经实际接触了什么？

虽然只是几条命令，但实际上已经碰到了机器人 RL 的核心路线。

## 第一类

Go2

```text
Locomotion
```

运动控制

任务：

```text
速度跟踪
行走
跑步
越障
```

---

## 第二类

G1 Dance

```text
Motion Tracking
```

动作模仿

任务：

```text
跳舞
翻跟头
攀爬
跑酷
```

---

## 第三类

README里还有：

```text
Sharpa Inhand
Allegro Inhand
```

灵巧手。

任务：

```text
手内重定位
抓取
旋转物体
```

---

## 第四类

README里还有：

```text
Go2 Arm Manip Loco
```

移动操作。

即：

```text
四足机器人
+
机械臂
```

边走边操作。

---

# 结合你的背景

你已经有：

* ROS2
* STM32
* CAN
* Jetson
* LiDAR
* IMU
* 运动学

基础。

所以接下来最值得研究的不是：

```text
如何运行UniLab
```

而是：

```text
Go2JoystickFlat
到底观察量是什么

obs有哪些

action是什么

reward如何设计

如何导出ONNX

如何部署到真实Go2
```

因为这些内容和你未来做：

```text
MPC
RL控制
轮式机器人
四足机器人
移动操作
```

是直接相关的。

从你目前的进展看，你已经成功完成了：

```text
云端4090
↓
UniLab安装
↓
APPO训练
↓
Go2 locomotion
↓
G1 dance demo
↓
ONNX导出
```

这一整条机器人强化学习链路的第一次跑通。

[1]: https://unilabsim.github.io/?utm_source=chatgpt.com "UniLab — A Heterogeneous Training Framework for Embodied Reinforcement Learning"
[2]: https://unilabsim.github.io/paper/?utm_source=chatgpt.com "UniLab: A Heterogeneous Architecture for Robot RL Beyond GPU-Dominant Paradigms"
