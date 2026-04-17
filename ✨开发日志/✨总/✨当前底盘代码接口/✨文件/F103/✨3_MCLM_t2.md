
## 修复问题，具体见claude.md，result.md

### 当下问题
#### 电机空载编码器输出实测最大tick

![[Pasted image 20260414125520.png]]
#### 当前pid控制率修改过，失效了，后续再测算
### f411ceu6,f401均没有can,大失败。最便宜的还是f446re,30元两个can,资源还可以

### cubemx自动更改引脚，
#### 电机反馈失效，是cubemx机制问题。为了不报错，cubemx会自动更换引脚，基本都有一组默认+一组复用引脚

![[Pasted image 20260416114301.png]]

#### 解决方法就是多关注cubemx右边那个图，以及给引脚加锁
#### 不同版本cubemx也不一致

## 开始第二电机升级
### cubemx
1.  修改arr"100-1"->"1000-1"
2. pwm->tim1,ch1,ch2
3. encoder->tim3
4. encoder-t1 and t2->tim2,tim3
5. 
