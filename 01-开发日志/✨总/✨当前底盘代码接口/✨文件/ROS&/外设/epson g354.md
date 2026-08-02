/home/lin/Lin_workspace/g354_test


## 观测imu数据
### rqt_plot 
```bash
ros2 run rqt_plot rqt_plot /imu/data/orientation/x /imu/data/orientation/y /imu/data/orientation/z
```

![[Pasted image 20260730182506.png]]

### plotjuggler

ros2 run plotjuggler plotjuggler

敲击

![[Pasted image 20260730183820.png]]


### 静置稳定性

```bash
ros2 topic echo /imu/data --field angular_velocity
```


![[Pasted image 20260730184014.png]]

![[Pasted image 20260730185732.png]]


