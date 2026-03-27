
## CLI 命令化（Command-line tool / CLI tool）
https://chatgpt.com/c/69bb9ebf-18b4-8321-8e49-4a0677eb2403

| 你做的方式           | 专业名称                         |
| --------------- | ---------------------------- |
| alias           | **命令别名（alias）**              |
| shebang + chmod | **可执行脚本（executable script）** |
| PATH / bin      | **命令搜索路径机制（PATH lookup）**    |
| ln -s           | **符号链接命令（symlink command）**  |

---

### 创建软连接

> [!NOTE]
> 你刚刚已经执行了：
> 
> ln -s ~/Lin_workspace/control/motor_control.py ~/.local/bin/SimpleMotorControl
> 
> 👉 这一步本质是创建了一个符号链接（软链接）
> 👉 相当于 Linux 里的“高级快捷方式”
> 
> 🚀 一、先验证你是否成功
> 
> 执行：
> 
> ls -l ~/.local/bin/
> 
> 你应该能看到类似：
> 
> SimpleMotorControl -> /home/lin/Lin_workspace/control/motor_control.py
> 
> 👉 这个 -> 很关键，说明链接成功了
> 
> ⚠️ 二、你现在还差一个关键步骤（很多人会漏）
> 👉 给原文件执行权限
> chmod +x ~/Lin_workspace/control/motor_control.py
> 👉 并确保第一行是：
> #!/usr/bin/env python3
> 
> 👉 否则你直接运行会报错
> 👉 因为 symlink 只是“指针”，真正执行的是原文件
> 
> 🚀 三、直接运行试试
> SimpleMotorControl
> 
> 如果成功 👉 🎉 你已经进入 Linux 工程流了

### 第一次成功

![[Pasted image 20260327122813.png]]