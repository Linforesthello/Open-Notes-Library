## 在当前代码中，加入记录当前程序启动次数，加入can0这个序号的按次递增（比如第一次是can0，第二次是can1.。。）

> [!NOTE]
> Let me read the current file first.
> 
> Read can_command.py
> Edit can_command.py
> Added 13 lines
> Now wire it into __main__:
> 
> Edit can_command.py
> Added 2 lines
> 现在：
> 
> 每次启动程序，计数从 .can_counter.json 读取并递增（持久化到磁盘）
> 第1次用 can0，第2次用 can1，以此类推
> 启动时打印 第 N 次启动，使用接口: canX

---
### 当前源代码
```

#!/usr/bin/env python3
import glob
import json
import os
import subprocess
import sys
import time

_COUNTER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".can_counter.json")

def _get_and_increment_count():
    count = 0
    if os.path.exists(_COUNTER_FILE):
        with open(_COUNTER_FILE) as f:
            count = json.load(f).get("count", 0)
    with open(_COUNTER_FILE, "w") as f:
        json.dump({"count": count + 1}, f)
    return count

def select_can_device():
    """
    扫描并允许用户从 /dev/ttyACM* 和 /dev/ttyUSB* 中选择一个CAN设备。
    """
    # 仿照 select_port 的逻辑，我们同时搜索 ttyACM 和 ttyUSB 设备
    devices = sorted(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))
    
    if not devices:
        print("错误: 未找到可用设备，请检查设备连接。")
        sys.exit(1)

    print("可用设备：")
    for i, p in enumerate(devices):
        print(f"  {i}: {p}")
    
    while True:
        try:
            idx_input = input(f"请输入设备编号 (0-{len(devices)-1}): ")
            idx = int(idx_input)
            if 0 <= idx < len(devices):
                return devices[idx]
        except (ValueError, IndexError):
            pass
        print("输入无效，请重试。")

def setup_can_interface(device, can_interface_name="can0", baud_rate_symbol="s6"):
    """
    使用 slcand 和 ip link 命令设置CAN接口。
    :param device: 设备路径, 例如 /dev/ttyACM0。
    :param can_interface_name: CAN接口的名称, 例如 can0。
    :param baud_rate_symbol: slcand 的波特率符号, 例如 s6 代表 500k。
    """
    print(f"\n正在为设备 {device} 设置 CAN 接口 {can_interface_name}...")

    # 命令 1: sudo slcand -o -c -s6 /dev/ttyACMx can0
    # slcand 是一个守护进程，-o 选项会在后台启动它
    slcand_command = f"sudo slcand -o -c -{baud_rate_symbol} {device} {can_interface_name}"
    print(f"  > {slcand_command}")
    
    result = subprocess.run(slcand_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  错误: 启动 slcand 失败。")
        print(f"  {result.stderr.strip()}")
        sys.exit(1)
    
    # 等待一会，给 slcand 初始化接口的时间
    print(f"  slcand 已启动，等待接口就绪...")
    time.sleep(1)

    # 命令 2: sudo ip link set can0 up
    set_link_up_command = f"sudo ip link set {can_interface_name} up"
    print(f"  > {set_link_up_command}")
    result = subprocess.run(set_link_up_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  错误: 无法 'up' {can_interface_name} 接口。")
        print(f"  {result.stderr.strip()}")
        print(f"  清理提示: 或许需要手动执行 'sudo pkill -f slcand' 来终止 slcand 进程。")
        sys.exit(1)
    
    print(f"  接口 {can_interface_name} 已成功 'up'。")

    # 命令 3: ip link show can0
    show_link_command = f"ip link show {can_interface_name}"
    print(f"  > {show_link_command}")
    result = subprocess.run(show_link_command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\n--- {can_interface_name} 状态 ---")
        print(result.stdout.strip())
        print("--------------------")
    else:
        print(f"  警告: 无法获取 {can_interface_name} 的状态。")

    print(f"\nCAN 接口 {can_interface_name} 在设备 {device} 上设置成功。")
    print("现在您可以使用 can-utils (例如 candump, cansend) 与该接口交互。")

def launch_savvycan():
    """启动 SavvyCAN 应用程序。"""
    print("\n正在启动 SavvyCAN...")
    subprocess.Popen(["./SavvyCAN"], cwd="/home/lin/SavvyCAN")
    print("SavvyCAN 已启动。")

if __name__ == "__main__":
    run_count = _get_and_increment_count()
    can_interface = f"can{run_count}"
    print(f"第 {run_count + 1} 次启动，使用接口: {can_interface}")
    selected_device = select_can_device()
    setup_can_interface(selected_device, can_interface_name=can_interface, baud_rate_symbol="s6")
    launch_savvycan()

```

