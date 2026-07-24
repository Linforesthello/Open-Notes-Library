这是上层的控制器下发指令端
“
#!/usr/bin/env python3
import serial
import curses
import time
import glob
import threading

# 串口设置
BAUD_RATE = 115200

def select_port():
    ports = sorted(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))
    if not ports:
        print("未找到可用串口，使用默认 /dev/ttyACM0")
        return '/dev/ttyACM0'
    print("可用串口：")
    for i, p in enumerate(ports):
        print(f"  {i}: {p}")
    while True:
        try:
            idx = int(input(f"请输入串口编号 (0-{len(ports)-1}): "))
            if 0 <= idx < len(ports):
                return ports[idx]
        except ValueError:
            pass
        print("输入无效，请重试")

SERIAL_PORT = select_port()
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print(f"已连接: {SERIAL_PORT}")

def refresh_log(log_lines, log_win, lock):
    """刷新日志子窗口（线程安全）"""
    with lock:
        log_win.erase()
        h, w = log_win.getmaxyx()
        visible = log_lines[-(h - 2):]
        for i, line in enumerate(visible):
            try:
                log_win.addstr(i, 0, line[:w - 1])
            except curses.error:
                pass
        log_win.refresh()

def send_command(command_str, log_lines, log_win, lock):
    """通过串口发送命令（命令是十六进制字节流），并在日志窗口显示"""
    command_bytes = bytes.fromhex(command_str.replace(' ', ''))  # 转换为字节流
    ser.write(command_bytes)

    # 记录发送日志
    timestamp = time.strftime('%H:%M:%S')
    log_lines.append(f"[{timestamp}] TX: {command_str.upper()}")
    refresh_log(log_lines, log_win, lock)

def rx_reader(log_lines, log_win, lock, stop_event):
    """后台线程：持续读取串口回调数据并显示到日志窗口"""
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                timestamp = time.strftime('%H:%M:%S')
                text = data.decode('ascii', errors='replace').strip()
                log_lines.append(f"[{timestamp}] RX: {text}")
                refresh_log(log_lines, log_win, lock)
        except serial.SerialException:
            break
        time.sleep(0.05)  # 50ms 轮询一次

def main(stdscr):
    """主程序，处理键盘输入控制"""
    curses.curs_set(0)  # 隐藏光标
    stdscr.nodelay(1)   # 设置为非阻塞模式
    stdscr.timeout(100)  # 设置输入超时

    # 存储每个按键对应的十六进制命令
    # 命令结构: AA 01 <ID> 01 00 00 02 11 <DATA>
    # DATA: 4B (开), 00 (关)
    # 4B = 75 (十六进制)，表示前进/转动；00 表示停止
    commands = {
        # --- 全局命令 ---
        # 0x101: 全体停止
        ord('s'): 'AA 01 01 01 00 00 02 11 00',  # 全体停止
        # 0x102: 转向电机控制
        ord('a'): 'AA 01 02 01 00 00 02 11 4B',  # 转向全体前进
        ord('z'): 'AA 01 02 01 00 00 02 11 00',  # 转向全体停
        # 0x103: 动力电机控制
        ord('d'): 'AA 01 03 01 00 00 02 11 4B',  # 动力全体前进
        ord('x'): 'AA 01 03 01 00 00 02 11 00',  # 动力全体停

        # --- 转向控制 (方向) ---
        # 0x123: 左前方向
        ord('f'): 'AA 01 23 01 00 00 02 11 4B',  # 左前轮-左转
        ord('g'): 'AA 01 23 01 00 00 02 11 00',  # 左前轮-方向停
        # 0x125: 右后方向
        ord('j'): 'AA 01 25 01 00 00 02 11 4B',  # 右后轮-方向控制
        ord('h'): 'AA 01 25 01 00 00 02 11 00',  # 右后轮-方向停
        # (缺少: 左后、右前转向控制)

        # --- 动力控制 ---
        # 0x124: 左前动力
        ord('c'): 'AA 01 24 01 00 00 02 11 4B',  # 左前轮-前进
        ord('v'): 'AA 01 24 01 00 00 02 11 00',  # 左前轮-动力停
        # 0x126: 右后动力
        ord('n'): 'AA 01 26 01 00 00 02 11 4B',  # 右后轮-前进
        ord('b'): 'AA 01 26 01 00 00 02 11 00',  # 右后轮-动力停
        # (缺少: 左后、右前动力控制)

        # 反馈测试
        ord('t'): 'AA 01 23 02 00 00 01 01',
        ord('y'): 'AA 01 24 02 00 00 01 01',
        ord('u'): 'AA 01 25 02 00 00 01 01',
        ord('i'): 'AA 01 26 02 00 00 01 01',
    }

    # 按键说明文字
    help_text = [
        "=== 电机控制 | 按 q 退出 ===",
        " s: 全体停止    a/z: 转向前进/停    d/x: 动力前进/停",
        " f/g: 左前转向  j/h: 右后转向",
        " c/v: 左前动力  n/b: 右后动力",
        "-" * 50,
        "  收发日志 (TX=发送 / RX=回调):",
    ]

    total_rows, total_cols = stdscr.getmaxyx()
    help_rows = len(help_text)

    # 绘制顶部说明区
    for i, line in enumerate(help_text):
        try:
            stdscr.addstr(i, 0, line[:total_cols - 1])
        except curses.error:
            pass
    stdscr.refresh()

    # 创建日志子窗口（剩余区域）
    log_rows = total_rows - help_rows
    log_win = curses.newwin(log_rows, total_cols, help_rows, 0)
    log_lines = []
    lock = threading.Lock()

    # 启动 RX 后台线程
    stop_event = threading.Event()
    rx_thread = threading.Thread(target=rx_reader, args=(log_lines, log_win, lock, stop_event), daemon=True)
    rx_thread.start()

    try:
        while True:
            key = stdscr.getch()  # 获取按键, 由于 stdscr.timeout(100) 此处为非阻塞，超时返回-1

            if key == ord('q'):  # 按 'q' 退出程序
                break

            # 当检测到有效按键时，发送一次对应命令
            # 这种模式适用于发送"开始"和"停止"类型的指令
            # 如果按住一个键，系统会自动重复发送该键，从而实现连续控制
            if key in commands:
                send_command(commands[key], log_lines, log_win, lock)
    finally:
        stop_event.set()
        rx_thread.join(timeout=1)

if __name__ == "__main__":
    curses.wrapper(main)

“

这是当前反馈
“
[11:35:44] TX: AA 01 02 01 00 00 02 11 00
[11:35:44] RX: UART->CAN | RX_MSG | ID: 0x102, DLC: 2. Sending...
[11:35:44] TX: AA 01 02 01 00 00 02 11 4B
[11:35:44] RX: UART->CAN | RX_MSG | ID: 0x10
[11:35:44] RX: 2, DLC: 2. Sending...
[11:35:45] TX: AA 01 02 01 00 00 02 11 00
[11:35:45] TX: AA 01 02 01 00 00 02 11 4B
[11:35:45] RX: 2, DLC: 2. Sending...
[11:35:46] TX: AA 01 02 01 00 00 02 11 4B
[11:35:46] RX: UART->CAN | RX_MSG | ID: 0x102, DLC: 2. Sending...
[11:35:47] TX: AA 01 02 01 00 00 02 11 00
[11:35:47] RX: UART->CAN | RX_MSG | ID: 0x10
[11:35:47] RX: 2, DLC: 2. Sending...
[11:35:47] TX: AA 01 02 01 00 00 02 11 4B
[11:35:47] RX: UART->CAN | RX_MSG | ID: 0x10
[11:35:47] RX: 2, DLC: 2. Sending...
[11:35:49] TX: AA 01 02 01 00 00 02 11 00
[11:35:50] RX: UART->CAN | RX_MSG | ID: 0x10
[11:35:50] RX: 2, DLC: 2. Sending...
[11:35:50] TX: AA 01 03 01 00 00 02 11 00
[11:35:50] RX: UART->CAN | RX_MSG | ID: 0x10
[11:35:50] RX: 3, DLC: 2. Sending...
[11:35:50] TX: AA 01 02 01 00 00 02 11 4B
[11:35:50] RX: UART->CAN | RX_MSG | ID: 0x10
[11:35:50] RX: 2, DLC: 2. Sending...
[11:35:52] TX: AA 01 01 01 00 00 02 11 00
[11:35:52] RX: UART->CAN | RX_MSG | ID: 0x10
[11:35:52] RX: 1, DLC: 2. Sending...

”

