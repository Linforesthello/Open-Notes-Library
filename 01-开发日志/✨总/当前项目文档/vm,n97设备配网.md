## 优先保证电脑端侧路由器有效，手机热点功率不够等等问题太多

### 路由失效（欠费）下，更换手机热点操作
n97需要图形化更改连接到的wifi，改自动ipv4为手动，192.168.43.xx，同时禁用ipv6

vmware需要手动选择另一个之前自己添加的配置
![[Pasted image 20260731144803.png]]

260731

### 当前n97 ip a
```
lin@lin-Default-string:~$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: enp1s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether e4:3a:6e:86:7e:42 brd ff:ff:ff:ff:ff:ff
    inet 10.10.3.20/24 brd 10.10.3.255 scope global noprefixroute enp1s0
       valid_lft forever preferred_lft forever
3: wlp2s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether 00:db:df:d6:a9:f2 brd ff:ff:ff:ff:ff:ff
    inet 192.168.43.210/24 brd 192.168.43.255 scope global noprefixroute wlp2s0
       valid_lft forever preferred_lft forever
    inet6 240a:4288:401:1703:2970:39d1:b790:1926/64 scope global temporary dynamic 
       valid_lft 3260sec preferred_lft 3260sec
    inet6 240a:4288:401:1703:70fe:c471:2093:bc33/64 scope global dynamic mngtmpaddr noprefixroute 
       valid_lft 3260sec preferred_lft 3260sec
    inet6 fe80::3435:7fa7:1905:977b/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever
4: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default 
    link/ether 1a:a9:a0:61:fd:04 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
5: Meta: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 9000 qdisc fq_codel state UNKNOWN group default qlen 500
    link/none 
    inet 198.18.0.1/30 brd 198.18.0.3 scope global Meta
       valid_lft forever preferred_lft forever
    inet6 fe80::7913:1cce:2afd:a92a/64 scope link stable-privacy 
       valid_lft forever preferred_lft forever
lin@lin-Default-string:~$ 

```

### 当前vmware ip a
```
lin@lin-virtual-machine:~$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:0c:29:81:2e:e5 brd ff:ff:ff:ff:ff:ff
    altname enp2s1
    inet 192.168.43.204/24 brd 192.168.43.255 scope global noprefixroute ens33
       valid_lft forever preferred_lft forever
    inet6 240a:4288:401:1703:9fe5:4d57:a453:9cd5/64 scope global temporary dynamic 
       valid_lft 3505sec preferred_lft 3505sec
    inet6 240a:4288:401:1703:13d7:e5e6:3f55:9632/64 scope global dynamic mngtmpaddr noprefixroute 
       valid_lft 3505sec preferred_lft 3505sec
    inet6 fe80::50fe:7f:a663:52f2/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever
3: ens37: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:0c:29:81:2e:ef brd ff:ff:ff:ff:ff:ff
    altname enp2s5
    inet 10.10.3.30/24 brd 10.10.3.255 scope global noprefixroute ens37
       valid_lft forever preferred_lft forever
    inet6 fe80::a621:c88c:2835:3adf/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever
lin@lin-virtual-machine:~$ 


```

260731