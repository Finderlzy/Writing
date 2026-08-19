---
aliases:
  - Sprite sheet
  - Animator
  - Clean up
  - Flip character
---

## 7.Sprite sheet

这一节让人物有动画小人，而不是那个黄球。

==动画载入——碰撞体积修改==

---
### 精灵表的下载与插入

- 去unity的资源商店下载
	点击“在unity中打开”即可

- 去找PNG图片也可以
	直接拖进去
### 精灵表的裁剪

1. 设置为multiple
2. sprite sheet
3. slice
### 创建子对象animator

创建子对象animator方便处理单独动画
添加组件“sprite render“
再把裁剪好的精灵图片拖到”sprite“选项里面
### 重新设置碰撞体积

由于玩家从球变成了人，碰撞体积也需要调整。
删去player对象的”circle collider“组件，新增为”capsule collider"（胶囊型）组件。
==注意，子对象animator只用来处理动画的问题，其他问题还是用父对象player来处理==
### 冻结z轴

现在人物的动画处理好了，但是发现走的时候它会倒，冻结z轴就好了
“interpolate——interpolate”让动画更流畅



## 8.Animator

这一节使人物拥有静止动画与奔跑动画，但没有处理转向问题。

==制作动画——动画切换（脚本书写）==

---

### 新增窗口animation和animator

animation用于制作动画
animator用于处理动画与动画的播放关系，例如，由静止动画变为运动动画就是用animator处理的

### 创建animator controller

在项目中创建，并拖动到player-animation当中

### 建立动画

在animation窗口中“create”，然后把对应的几帧的精灵拖进里面即可
调整采样率可以改变动画播放的速度

### 制作动画切换

在animator窗口中，右键“playeridle”，点击“make transition”，并点击“player Move”。
此时创建了，由静止转换到运动的路径。

以同样的方式制作从运动到静止的路径。

现在要建立转换的条件。

![[Pasted image 20260304155206.png]]

	点击那个+号，再点击bool，新建一个“isMoving”的条件
## 9.Clean up

这一节主要是把之前写的代码给模块化，方便维护

---

没啥好说的了，养成一下这种习惯吧——写完一个模块后，把代码给封装一下。



## 10.Flip character

这一节让玩家可以左右转向

---
### 有关转向的参数

- int facingDir
- bool facingRight
	`不知道为什么用了两个参数
### Flip()（翻转函数）

实现的功能：
1. 改变角色面向——transform内置函数
2. 改变转向参数
![[Pasted image 20260309221817.png]]
### FlipController() （判断何时翻转函数）

这个很简单了，右边有速度但是面朝的不是右边就转向。
左边同理。
![[Pasted image 20260309222034.png]]