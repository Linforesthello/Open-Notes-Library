
## 回顾并启用之前的can收发测试代码

1. 5_TecCAN_CmakeTest_SLAVE，从端
	1. 接收外部输入“0x123”帧头消息，并翻转led；
	2. 自身在收到外部消息后，发送“0x456”帧头消息，
2. 5_TecCAN_CmakeTest，主端
	1. 接收到外部“0x456”帧头消息后，翻转led
	2. 并原样发送接收到的内容到can网络中
3. 复现成功后验证的逻辑分析仪文件，保存于"C:\Users\86173\Desktop\ProjectRequirement\MCU_Now\Lin_STM32\STM32_F103C8T6\5_Tec_CAN\260309_success.sal"

## 完善5_UartToCan_test
