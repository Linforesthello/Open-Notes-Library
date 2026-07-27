# R1 底盘树莓派控制 — 操作手顺

## 环境信息

| 项目 | 值 |
|------|----|
| 树莓派 IP | `192.168.1.199` |
| CAN 适配器 | CANable2 (1Mbps) |
| 无线串口 | E34-2G4H27D (2.4GHz) |
| PC 端 | `lin@lin-virtual-machine` (192.168.1.204) |
| 底盘构型 | 四舵轮 (4 steering + 4 drive) |

## 一、上电 → CAN 就绪

### 1. SSH 登录

```bash
ssh lin@192.168.1.199
# 密码: (用户密码)
```

### 2. 启动 CAN

```bash
cd ~/r1_control
sudo ./can_up.sh
```

验证：

```bash
ip -details link show can0
candump can0
# 应看到 0x321~0x328 状态帧（50ms 周期）
```

### 3. 启用 Python 环境

```bash
source venv/bin/activate
export PYTHONPATH=/home/lin/r1_control:$PYTHONPATH
```

---

## 二、底盘标定

### 测 ticks/圈（4 个单元）

```bash
python3 measure_steering_ticks.py --unit 1  # 每次测一圈，Ctrl+C 停
python3 measure_steering_ticks.py --unit 2
python3 measure_steering_ticks.py --unit 3
python3 measure_steering_ticks.py --unit 4
```

**当前实测值（2026-07-14）：**

| 单元 | CAN ID | 物理位置 | TICKS_PER_REV |
|:----:|:------:|:--------:|:-------------:|
| UNIT1 | 0x121/0x122 | 右后 | 9218 |
| UNIT2 | 0x123/0x124 | 右前 | 9196 |
| UNIT3 | 0x125/0x126 | 左前 | 7844 |
| UNIT4 | 0x127/0x128 | 左后 | 9395 |

---

## 三、整车控制

### 启动控制程序

```bash
python3 pi_chassis_control.py
```

启动后应看到 4/4 单元在线。

### 安全测试序列

```python
# Step 1: 排除坏单元（如 UNIT4 转向已烧）
disable 4

# Step 2: 掰正所有轮子，归零
cal

# Step 3: 转向测试（不动驱动轮）
steer 30       # 左转 30°，看方向
steer -30      # 右转 30°
steer 0        # 回正

# Step 4: 前进
0.2 0 0
# 观察: 🔴 等待舵向就绪 → 到位后 🟢 可驱动 → 动力输出
stop

# Step 5: 侧移
0 0.2 0
stop

# Step 6: 自转
0 0 0.2
stop
```

### 控制命令

| 命令 | 说明 |
|:----|:------|
| `0.3 0 0` | 前进 0.3 m/s |
| `0 0.2 0` | 左移 0.2 m/s |
| `0 -0.2 0` | 右移 0.2 m/s |
| `0 0 0.3` | 左转 0.3 rad/s |
| `0 0 -0.3` | 右转 0.3 rad/s |
| `stop` | 全车停止 |
| `cal` | 当前位置归零 |
| `s` | 显示状态 |
| `steer <角度>` | 全部转向到指定角度（不动驱动） |
| `remote` | 切换遥控模式 |
| `disable <N>` | 禁用某单元 |
| `enable <N>` | 启用某单元 |
| `reset` | 重置堵转保护 |
| `q` | 退出 |

---

## 四、遥控模式

### 接线

```
PC (USB) → E34-2G4H27D 模块 ←→ 无线 ←→ E34-2G4H27D 模块 → 树莓派 UART
```

树莓派端：E34 模块 TX → GPIO15 (RXD), GND → GND

或直接用 USB 转 TTL：

```
E34 模块 → USB转TTL(CH340) → 树莓派 USB → /dev/ttyUSB0
```

### 配置

编辑 `pi_chassis_control.py` 顶部：

```python
SERIAL_PORT = "/dev/ttyUSB0"     # 无线模块对应的串口
SERIAL_BAUD = 115200             # 波特率
```

### 启动遥控

```python
# 1. 启动控制程序
python3 pi_chassis_control.py

# 2. 归零
cal

# 3. 切遥控
remote

# 4. PC 端通过串口发 "vx vy omega" 文本行
echo "0.3 0 0" > /dev/ttyUSB0    # 前进
echo "0 0.2 0" > /dev/ttyUSB0    # 左移
echo "0 0 0"    > /dev/ttyUSB0    # 停止
```

串口数据格式（文本，`\n` 结尾）：

```
0.3 0 0
0 0.2 0
0 0 0.3
```

### 超时保护

遥控模式下超过 **1 秒** 未收到串口数据 → 自动全车急停。

---

## 五、PID 参数

| 参数 | 值 | 说明 |
|:----|:---|:------|
| KP_ANGLE | 1.0 | 比例增益 |
| KI_ANGLE | 0.03 | 积分增益（消除静差） |
| DEAD_ZONE_DEG | 0.5° | 转向死区 |
| STEER_READY_DEG | 5.0° | 舵向就绪阈值 |
| MAX_STEER_SPEED | 60 | 最大转向速度 |
| STEER_RAMP_RATE | 8 | 转向速度变化率限制 |

---

## 六、CAN 协议速查

### CAN ID 映射

| 单元 | 物理 | 转向 CMD | 驱动 CMD | 转向状态 | 驱动状态 |
|:----:|:----:|:--------:|:--------:|:--------:|:--------:|
| UNIT1 | 右后 | 0x121 | 0x122 | 0x321 | 0x322 |
| UNIT2 | 右前 | 0x123 | 0x124 | 0x323 | 0x324 |
| UNIT3 | 左前 | 0x125 | 0x126 | 0x325 | 0x326 |
| UNIT4 | 左后 | 0x127 | 0x128 | 0x327 | 0x328 |

### 状态帧格式

```
[0-1] current_logic_speed (int16 LE)
[2-3] accumulated_ticks   (uint16 LE)
[4-5] pwm_output          (int16 LE)
[6]   target_logic_speed  (int8)
[7]   flags               (uint8)
```

flags: `0x01`=堵转, `0x02`=PWM饱和, `0x80`=角度模式

### 命令帧格式

```
data[0] = 0x11              # CMD_SET_SPEED
data[1] = speed (-100~100)  # int8
data[2~7] = 0               # 填充
```

---

## 七、文件清单（树莓派 ~/r1_control/）

| 文件 | 说明 |
|:----|:------|
| `can_up.sh` | CAN 一键启动脚本 |
| `pi_chassis_control.py` | 底盘控制主程序（自包含） |
| `steering_control.py` | 单单元转向测试 |
| `measure_steering_ticks.py` | ticks/圈 测量 |
| `serial_monitor.py` | 串口监视器 |
| `serial_quality.py` | 串口通信质量测试 |
| `mclm_can.py` | CAN 协议封装库（依赖用） |
| `venv/` | Python 虚拟环境 |

---

## 八、常见问题

**Q: can0 找不到**
```bash
sudo ./can_up.sh
```

**Q: Permission denied on serial**
```bash
sudo usermod -a -G dialout $USER
# 退出重新 SSH
```

**Q: 转向抖动/过冲**
检查 TICKS_PER_REV 是否准确，重新测量

**Q: 堵转保护触发**
```python
reset     # 确认无机械卡死后解除保护
```

**Q: 方向反了**  
检查 `inv_kinematics` 中的 `-atan2` 取反。如果 `steer 30` 往右转 → 去掉负号

---

## 九、运动学

```
V_ix = vx - omega * y
V_iy = vy + omega * x
steer = -atan2(V_iy, V_ix)    # 取反与电机方向对齐
drive = hypot(V_ix, V_iy)
```

WHEEL_POS (x⁺=前, y⁺=左)：

```python
WHEEL_POS = [
    (-0.25, -0.30),   # UNIT1: 右后
    ( 0.25, -0.30),   # UNIT2: 右前
    ( 0.25,  0.30),   # UNIT3: 左前
    (-0.25,  0.30),   # UNIT4: 左后
]
```
