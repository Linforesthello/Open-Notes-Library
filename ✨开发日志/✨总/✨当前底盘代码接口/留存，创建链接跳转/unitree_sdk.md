## 260330
### Q1
> [!NOTE]
> LocationMode_8010t1.cpp
> 我把gearRatio的-6.28改到了-6.33,这是官方文档提到的减速比。后来“motor.q: -123.725
> motor.temp: 30
> motor.dq: -0.294525
> motor.merror: 0
> ”。1、解析。2、现在下发命令后，电机会突然高速反转，然后才是缓慢的接近目标，为什么？我一窍不通
#### A1
> [!NOTE]
> 1. 数据解析
> 
> 目标位置：3.14 × (-6.33 × 6.33) ≈ -125.6 rad（电机轴）
> 当前位置：-123.725 rad，还差约 1.9 rad，即将到位，正常。
> 
> 2. 为什么启动时突然高速反转？
> 
> 原因是 cmdPos 从 0 开始，但电机实际位置不在 0。
> 
> 
> 电机实际位置：-123 rad（上次运行留下的）
> cmdPos 初始值：0.0f（程序重启后从 0 开始爬）
> 程序启动瞬间，cmd.q = 0，而电机在 -123 rad，误差 = 123 rad，控制律：
> 
> 
> 力矩 = kp × (0 - (-123)) = 0.02 × 123 = 2.46 N·m  → 正方向猛冲
> 电机被命令"回到0"，所以高速反转。等 cmdPos 缓慢爬到 -124 rad 附近，方向才反过来朝目标走。
> 
> 根本原因：程序启动时没有读取电机当前位置作为 cmdPos 的初始值。
> 
> 正确做法是启动时先发一帧读取 data.q，然后 cmdPos = data.q，再开始缓变：
> 
> 
> // 先读一次当前位置
> serial.sendRecv(&cmd, &data);
> float cmdPos = data.q;  // 从实际位置出发，不从 0 出发
#### source
```
#include <unistd.h>
#include <cmath>
#include "serialPort/SerialPort.h"
#include "unitreeMotor/unitreeMotor.h"

int main() {

  SerialPort  serial("/dev/ttyACM0");
  MotorCmd    cmd;
  MotorData   data;

  const float gearRatio  = -6.33*queryGearRatio(MotorType::GO_M8010_6);
  const float targetPos  = 3.14f * gearRatio;  // 输出端 3.14 rad -> 电机轴
  const float stepSize   = 0.01f;             // 每次最大步进（rad，电机轴），安全缓变
  float       cmdPos     = 0.0f;               // 当前指令位置，从 0 开始缓慢逼近目标

  while(true)
  {
    // 缓慢逼近目标，避免瞬间大力矩
    if (std::fabs(targetPos - cmdPos) > stepSize)
      cmdPos += (targetPos > cmdPos) ? stepSize : -stepSize;
    else
      cmdPos = targetPos;

    cmd.motorType = MotorType::GO_M8010_6;
    data.motorType = MotorType::GO_M8010_6;
    cmd.mode = queryMotorMode(MotorType::GO_M8010_6,MotorMode::FOC);
    cmd.id   = 0;
    cmd.kp   = 0.02;
    cmd.kd   = 0.01;
    cmd.q    = cmdPos;  
    cmd.dq   = 0.0;
    cmd.tau  = 0.0;
    serial.sendRecv(&cmd, &data);

    std::cout <<  std::endl;
    std::cout << "motor.q: "      << data.q      << std::endl;
    std::cout << "motor.temp: "   << data.temp   << std::endl;
    std::cout << "motor.dq: "     << data.dq     << std::endl;
    std::cout << "motor.merror: " << data.merror << std::endl;
    std::cout <<  std::endl;

    usleep(200);  // 2ms 周期，配合缓变步进
  }

}
```
## 当前可执行版本
速度尚可，但是不稳定
1. 静差
2. 到达固定点位后不固定，手能搓动电机输出盘
### source
```
#include <unistd.h>
#include <cmath>
#include "serialPort/SerialPort.h"
#include "unitreeMotor/unitreeMotor.h"

int main() {

  SerialPort  serial("/dev/ttyACM0");
  MotorCmd    cmd;
  MotorData   data;

  const float gearRatio  = -6.33*queryGearRatio(MotorType::GO_M8010_6);
  const float targetPos  = 3.14f * gearRatio;  // 输出端 3.14 rad -> 电机轴
  const float stepSize   = 0.05f;             // 每次最大步进（rad，电机轴），安全缓变

  // 先读一次当前位置，避免启动时从 0 出发导致突然反转
  cmd.motorType = MotorType::GO_M8010_6;
  data.motorType = MotorType::GO_M8010_6;
  cmd.mode = queryMotorMode(MotorType::GO_M8010_6, MotorMode::FOC);
  cmd.id = 0; cmd.kp = 0; cmd.kd = 0; cmd.q = 0; cmd.dq = 0; cmd.tau = 0;
  serial.sendRecv(&cmd, &data);
  float cmdPos = data.q;  // 从实际位置出发

  while(true)
  {
    // 缓慢逼近目标，避免瞬间大力矩
    if (std::fabs(targetPos - cmdPos) > stepSize)
      cmdPos += (targetPos > cmdPos) ? stepSize : -stepSize;
    else
      cmdPos = targetPos;

    cmd.motorType = MotorType::GO_M8010_6;
    data.motorType = MotorType::GO_M8010_6;
    cmd.mode = queryMotorMode(MotorType::GO_M8010_6,MotorMode::FOC);
    cmd.id   = 0;
    cmd.kp   = 0.1;
    cmd.kd   = 0.01;
    cmd.q    = cmdPos;  
    cmd.dq   = 0.0;
    cmd.tau  = 0.0;
    serial.sendRecv(&cmd, &data);

    std::cout <<  std::endl;
    std::cout << "motor.q: "      << data.q      << std::endl;
    std::cout << "motor.temp: "   << data.temp   << std::endl;
    std::cout << "motor.dq: "     << data.dq     << std::endl;
    std::cout << "motor.merror: " << data.merror << std::endl;
    std::cout <<  std::endl;

    usleep(200);  // 200ms 周期，配合缓变步进
  }

}
```