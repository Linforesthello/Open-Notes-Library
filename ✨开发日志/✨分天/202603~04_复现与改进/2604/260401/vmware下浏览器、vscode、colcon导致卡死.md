[虚拟机卡死原因分析](https://chatgpt.com/c/69cc9bf1-3d78-83e8-8a4d-5396a09c80e6)

## 

> [!NOTE]
> lin@lin-virtual-machine:~$ sudo fallocate -l 8G /swapfile
> [sudo] lin 的密码： 
> fallocate: fallocate 失败: 文本文件忙
> lin@lin-virtual-machine:~$ sudo fallocate -l 8G /swapfile
> fallocate: fallocate 失败: 文本文件忙
> lin@lin-virtual-machine:~$ swapon --show
> NAME      TYPE SIZE USED PRIO
> /swapfile file   2G   0B   -2
> lin@lin-virtual-machine:~$ sudo swapoff /swapfile
> lin@lin-virtual-machine:~$ sudo rm /swapfile
> lin@lin-virtual-machine:~$ sudo fallocate -l 8G /swapfile
> lin@lin-virtual-machine:~$ sudo chmod 600 /swapfile
> lin@lin-virtual-machine:~$ sudo mkswap /swapfile
> 正在设置交换空间版本 1，大小 = 8 GiB (8589930496  个字节)
> 无标签， UUID=5028cef9-dd4d-4f60-98e0-dfc515d09cc8
> lin@lin-virtual-machine:~$ sudo swapon /swapfile
> lin@lin-virtual-machine:~$ swapon --show
> NAME      TYPE SIZE USED PRIO
> /swapfile file   8G   0B   -2
> lin@lin-virtual-machine:~$ 
> 

### 成功
![[Pasted image 20260401123432.png]]
