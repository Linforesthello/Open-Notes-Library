# 🚀 第一步：安装 Tilix（替代 Terminator）

在 Ubuntu / Linux 里直接：

sudo apt update  
sudo apt install tilix

👉 就这么简单，一条命令搞定

---

# 🧩 第二步：设为默认终端（关键）

否则很多地方还是会打开旧终端：

sudo update-alternatives --config x-terminal-emulator

选择：

/usr/bin/tilix

## ✔ 推荐架构（工程级）

Tilix（UI）  
   ↓  
zsh（日常交互）  
   ↓  
bash（脚本执行）

---

## ✔ 为什么这样最好？

### 🟢 zsh 负责：

- 日常命令
- 调试
- ROS 操作
- 提升效率

---

### 🔵 bash 负责：

- `.sh` 脚本
- ROS launch / build
- 自动化部署

---

👉 两者**不是竞争关系，是分工关系**

---

# ⚠️ 五、什么时候必须用 bash？

你必须记住这几点👇

---

## ❗1. 写脚本

#!/bin/bash

👉 永远用 bash（最兼容）

---

## ❗2. ROS 官方脚本

例如：

setup.bash

👉 不要乱改

---

## ❗3. 远程设备（树莓派/服务器）

👉 很多环境默认只有 bash

---

# 🧠 六、什么时候用 zsh（你的主战场）

👉 日常开发：

- ROS 调试
- git 操作
- 多终端管理
- 命令探索

👉 你现在所有操作：

ros2 topic list  
colcon build  
git status

👉 都应该在 zsh 里完成

---

# 🧨 七、很多人犯的错误（你要避免）

## ❌ 错误1：全切 zsh

👉 导致：

- 脚本兼容性问题
- ROS奇怪bug

---

## ❌ 错误2：完全不用 zsh

👉 导致：

- 效率低
- 手动输入多
- 容易出错