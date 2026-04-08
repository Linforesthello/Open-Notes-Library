## 成功通讯！
### 波特率只支持4M波特率，这个坑我踩了
参照Lain的推荐，买了华杰的usb转rs485/422模块，
买了达妙的转接模块
#### 成功通讯！

![[Pasted image 20260329211742.png]]

### 成功控制电机运行linux下的示例代码
[unitreerobotics/unitree_actuator_sdk --- unitreerobotics/unitree_actuator_sdk](https://github.com/unitreerobotics/unitree_actuator_sdk/tree/main)

[unitree_actuator_sdk/motor_tools at main · unitreerobotics/unitree_actuator_sdk](https://github.com/unitreerobotics/unitree_actuator_sdk/tree/main/motor_tools)

sudo chmod 777 /dev/ttyACM0

sudo ./swboot /dev/ttyACM0
./swmotor /dev/ttyACM0

lin@lin-virtual-machine:~/unitree_actuator_sdk/build$ sudo ./example_goM8010_6_motor
![[Pasted image 20260329215507.png]]
![[Pasted image 20260329215523.png]]

### 仿照示例代码，尝试不同的控制模式

#### 官方代码示例解析

> [!NOTE]
> example_goM8010_6_motor.cpp
> 解读当前代码，这是官方的示例历程，
> Let me read the file first.
> 
> Read example_goM8010_6_motor.cpp
> 这是宇树科技 GO-M8010-6 电机的官方控制示例，逻辑很简单：
> 
> 初始化
> 
> 打开串口 /dev/ttyACM0（USB转串口设备）
> 创建命令结构体 MotorCmd 和数据结构体 MotorData
> 控制循环（每 200μs 一次）
> 
> 字段	值	含义
> motorType	GO_M8010_6	指定电机型号
> mode	FOC	磁场定向控制模式
> id	0	电机 ID（总线上第0号）
> kp	0.0	位置增益（关闭位置控制）
> kd	0.01	阻尼增益（微小阻尼）
> q	0.0	目标位置（rad）
> dq	-6.28 × 减速比	目标转速（-1 转/秒，折算到输出轴）
> tau	0.0	前馈力矩
> 控制律本质：
> 
> 
> 输出力矩 = kp*(q_target - q_actual) + kd*(dq_target - dq_actual) + tau
>          = 0 + 0.01*(-6.28*ratio - dq_actual) + 0
> 即纯速度跟踪，让电机以 -1 rad/s（输出轴） 匀速旋转，kd 提供阻尼。
> 
> 反馈读取：每帧打印位置 q、温度 temp、实际转速 dq、错误码 merror。
> 
> 关键点：dq 命令值乘了 queryGearRatio() 是因为 SDK 内部期望的是电机端转速，而非输出轴转速，减速比将输出轴速度换算回电机端。

#### 按照Linux下视频，编写了电机停止控制"./StopMode_8010t1"

#### 位置控制
##### 位置模式触发保护，电机状态灯频闪，重新上电可脱离
##### 13:00左右给宇树发送了工单，等反馈

> [!NOTE]
> 问题描述: 在电机模式下，空载，运行LocationMode_8010t1.cpp后，电机瞬间高转速，且立即停止，并且状态灯频闪不停。 
> 监测电流发现瞬时2.78A左右，而电机运行例程速度控制空载为0.05A左右， 供电电池为75C,1450mah,6s航模电池（24V左右）。 
> 1、请问是什么情况，是触发了什么保护吗？ 
> 2、如何从下发控制指令脱离当前情况？我发送"./swboot""./swmotor"均没有反应，物理上的断电再续才可返回电机模式

![[Pasted image 20260330130107.png]]

#### 暂时总结
##### 可执行代码：[[unitree_sdk]]

> [!NOTE]
> # GO-M8010-6 位置控制调试记录
> 
> ## 控制律
> 
> ```
> 力矩 = kp*(q_target - q_actual) + kd*(dq_target - dq_actual) + tau
> ```
> 
> ## 踩坑记录
> 
> ### Bug 1：字段赋值错误（原始代码）
> ```cpp
> cmd.kp  = 0;        // 位置增益为 0，位置环失效
> cmd.q   = 0.0;      // 目标位置固定为 0
> cmd.dq  = cmdPos;   // 位置值塞进了速度字段
> ```
> **现象**：电机持续高速旋转。
> **修复**：`cmd.q = cmdPos`，`cmd.dq = 0.0`，`cmd.kp = 非零值`。
> 
> ### Bug 2：启动时突然高速反转
> **原因**：`cmdPos` 初始为 0，但电机实际位置在 -123 rad，启动瞬间误差巨大，电机被命令"回到0"。
> **修复**：循环前先读一次 `data.q`，`cmdPos` 从实际位置出发。
> ```cpp
> cmd.kp = 0; cmd.kd = 0; cmd.q = 0; cmd.dq = 0; cmd.tau = 0;
> serial.sendRecv(&cmd, &data);
> float cmdPos = data.q;
> ```
> 
> ### Bug 3：过流保护（merror: 3）
> **原因**：`kp=0.1`，目标 -124.8 rad，初始力矩 = `0.1 × 124.8 = 12.48 N·m`，超额定值。
> **修复**：降低 kp，或缩小初始目标。
> 
> ## 参数调整过程
> 
> | kp | stepSize | 现象 |
> |----|----------|------|
> | 0.1 | 0.01 | merror:3，过流保护 |
> | 0.02 | 0.01 | 正常，但静差 ~2.4 rad |
> | 0.1 | 0.05 | 当前版本 |
> 
> ## 关键参数
> 
> | 参数 | 值 | 说明 |
> |------|----|------|
> | 减速比 | 6.33 | 官方文档值 |
> | `gearRatio` | `-6.33 × 6.33 ≈ -40.07` | 含方向符号 |
> | `targetPos` | `3.14 × gearRatio ≈ -125.8 rad` | 电机轴目标，对应输出轴 3.14 rad |
> 
> ## merror 错误码
> 
> | 值 | 含义 |
> |----|------|
> | 0 | 正常 |
> | 3 | 过流保护 |
> 
> ## 最终状态输出示例（到位）
> ```
> motor.q: -127.98       # 实际位置（电机轴 rad），有静差
> motor.temp: 29         # 温度正常
> motor.dq: 0.098175     # 接近静止
> motor.merror: 0        # 无错误
> ```
> 
> ## 静差说明
> kp 越小，稳态力矩越小，摩擦力导致静差越大。增大 kp 可减小静差，但过大会触发过流。


