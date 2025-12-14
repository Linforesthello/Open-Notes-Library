原稿“20251209-1210-”
# 6_OMF_Feedback
#FreeRTOS  #控制/车体控制 #优化/代码组成  #长期项目/OMF_Feedback及其合理化衍生 
[电机正转故障分析](https://chatgpt.com/c/6937fd37-aecc-8321-b0c6-53f54de114fd)
1. 之前，用tb6612对无刷电机进行控制（实际为错误操作），发现当前板载tb6612模块A口无法正常工作；
	1. 于是，更换了B口，最后经由mcu对无刷电机形成直接控制
2. 对电机控制频率进行了调整，由1khz改到20khz![[Pasted image 20251210171751.png]]![[Pasted image 20251210171811.png]]
3. 准备优化电机控制代码，实现“运动控制固件”![[Pasted image 20251210172333.png]]
=======
# 优化OMF_UARTback代码库
 #长期项目/OMF_Feedback及其合理化衍生 
[代码解析与优化建议](https://chatgpt.com/c/6938406e-a8e0-8325-83b6-6fee1182f23d)
[代码评价与优化建议_1211](https://chatgpt.com/c/693aa487-c104-8321-87a7-093a91e97f47)
1. #待做 加入pid控制，使得测速task能够作用于control task
2. #待做/已实现 freertos.c代码各部分解耦合
    1. task_motor.c
    2. motor.c
    3. ...
3. #待做/正在进行 考虑上位机合作项目与朱，
    1. 决定介入esp32，作为mqtt网关，进行“串口～网络层”的数据交换
4. 问题 #解决问题/电机控制/频率  
	1. 事发：为了调控无刷电机，提高了电机控制频率到20khz，但是到直流电机上并不适用
	2. 具体表现为：![[Pasted image 20251211184703.png]]
	3. 换回1khz，问题解决；去查，发现可能是如下：![[Pasted image 20251211184751.png]]![[Pasted image 20251211184800.png]]
5. 优化代码 #优化/代码组成 
	1. command.c![[Pasted image 20251211191831.png]]![[Pasted image 20251211191848.png]]![[Pasted image 20251211192509.png]]
	2. uart_app.c![[Pasted image 20251211192706.png]]![[Pasted image 20251211192732.png]]
6. #优化/代码架构 [代码评价与优化建议_1211](https://chatgpt.com/c/693aa487-c104-8321-87a7-093a91e97f47)
	1. motor.c,motor_task.c![[Pasted image 20251211210137.png]]
	2. encoder_task.c  如图[encoder_task.c代码评价与优化建议_1211](https://chatgpt.com/c/693ac529-cce4-8321-ac32-655a5747ff24)![[Pasted image 20251211214916.png]]![[Pasted image 20251211214935.png]]
	3. logger_task.c  [encoder_task.c代码评价与优化建议_1211](https://chatgpt.com/c/693ac529-cce4-8321-ac32-655a5747ff24)
		1. ![[Pasted image 20251212110023.png]]![[Pasted image 20251212110046.png]]![[Pasted image 20251212110533.png]]![[Pasted image 20251212111012.png]]
	4. 优化freertos.c，查验覆盖问题
			1. ![[Pasted image 20251212114138.png]]
			2. 确实如此![[Pasted image 20251212114207.png]]
			3. freertos入口函数/入口转发函数参数问题 #C语言/基本语法 ![[Pasted image 20251212120157.png]]
			4. freertos对于自写的转发函数，未预定义问题![[Pasted image 20251212120130.png]]![[Pasted image 20251212120746.png]]![[Pasted image 20251212120905.png]]
	5. 优化main.c
			1. ![[Pasted image 20251212122704.png]]![[Pasted image 20251212130519.png]]
	6. 至此，基本迁移完毕；见github上/stm32/ONL两个仓库
		1. #存在问题 当前输入的映射仅有-50~0~50，并不是-1000~0~1000
		2. #存在问题 当前各部分基础代码（或者叫做驱动代码），仍然不够优化
		3. #存在问题 当前代码仍然是一个黑箱，串口输入命令后，并无串口反馈
		4. #存在问题 当前并无统一的数据栈，用于反馈上位机读取/调用
	7. 优化command.c/command.h  [细化每一份.c/.h代码-encoder_task.c代码评价与优化建议_1211](https://chatgpt.com/c/693ba457-e854-8323-a091-a21558a36d8e)
		1. ![[Pasted image 20251212170651.png]]
		2. ![[Pasted image 20251212171107.png]]
		3. ![[Pasted image 20251212172758.png]]
	8. logger.c
		1. ![[Pasted image 20251212182328.png]]
		2. 没看明白， #存在问题  ，**==有大量待优化部分==**![[Pasted image 20251212182553.png]]
	9. 电机映射确认![[Pasted image 20251214183325.png]]
		1. 这个是根据arr走的，比如50-1：“-50~0~50”;100-1"-100~0~100"
	10. command_task.c  #优化/代码组成/反馈设计 
		1. [main.c 优化建议](https://chatgpt.com/c/693c064e-5580-8324-b8eb-7f0b7836a96f)
		2. ![[Pasted image 20251214182800.png]]
		3. ![[Pasted image 20251214182817.png]]
		4. 出问题了
			1. ![[Pasted image 20251214192900.png]]
			2. ![[Pasted image 20251214193137.png]]![[Pasted image 20251214193155.png]]
			3. #FreeRTOS/Queue ![[Pasted image 20251214194102.png]]
			4. 修改了cubemx中的设置，可能是把usart1的dma删掉了![[Pasted image 20251214201251.png]]