底盘控制器，为新项目替代

### stm32工程复制与迁移
1. 直接复制整个文件夹，改名，
2. 改动.ioc名称，若不进行配置，进入后会出现cmake无法刷新
3. 除了自己创建的/app, .ioc，其他全部删掉
4. 返回cubemx开启，确认名称是否正确
5. 由.ioc生成架构与代码，注意cmakelist对应，![[Pasted image 20260507161956.png]]
6. 至此，迁移成功，等待实机测试
## 因为要适配多个控制器，所以引入了条件编译

这是第二次使用条件编译
第一次也是电机控制器代码，第一代的

## 系统内，局部ai审查局部代码容易在系统层次失效、冲突

详见
"A1_dp_t1.md"
claude"Assess task importance and modification risk"

## 开始笔记新方式，进行文件夹->工程化
### now_all.md,deepseek_t1.md,A1_dp文档更新

## done遇到问题，dp去查hal源码发现回调写错，stm32f1不调用Tx,调用的是txmail
stm32f1xx_hal_can.c->1719~1724
