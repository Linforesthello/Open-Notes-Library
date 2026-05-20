 
### 可以把函数封装，在封装内带锁，这样在文件内使用更方便

## 涉及到semaphores,初始值为0(Depleted)
### 具体见“fix_UartToDma.md”，claude“UartToDma_fix”

## 下层电机控制器写入每隔50ms发送当前电机状态（四个实测共80帧/s），网关转发常占线，导致mutex长期持有，无法接受上层串口指令，已修复
见“# Fix3：UART↔CAN 网关 UART TX 阻塞问题 — 排查全记录”
ai-session——==降序==
	“解决 | 问题在canrx占线导致mutex长期持有，没有检查机制”
	“合并UTC data flow和Now_all.md”
	“Debug code after modifications”
	“一直有这样的消息在发送“[14:13:36] RX: CAN RX | ID: 0x324 | DLC: 8 00 00 00 00 00 00 00 00 [14:13:36] RX: CAN: 0x325 | DLC: 8 | Data: 00 000 00 00 00 [14:13:36] RX: CAN RX | ID: 0x326 | DLC: 8 | Data: 00 00 000 0…”
	“检查“无法下发”问题，可能是uart tx互斥锁竞争”

![[Pasted image 20260519151756.png]]

![[Pasted image 20260519154823.png]]