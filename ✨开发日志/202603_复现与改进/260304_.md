
## 第一次使用原配的cmakelist.txt进行修改
5_UartToCan_test
1. ![[Pasted image 20260304160311.png]]
### 触发了头文件循环依赖
1. ![[Pasted image 20260304160545.png]]

### 规范化了app_task.h的功能，分化给app_global.h（5_UaToCan和3_MCLM均如此）

### 发现并修复了上一次jlink一键下载的漏洞，并留档
#Tools/git/修改上一次的commit 
[Git回退单个文件](https://chatgpt.com/c/69a67c05-7220-8320-9e34-488b993a6ac9)
1. ![[Pasted image 20260304174142.png]]
2. 已经提交修改，下一步强推；
3. 完成，可见图片，路线正常![[Pasted image 20260304174314.png]]
