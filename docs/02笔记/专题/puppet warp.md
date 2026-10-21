---
createdDate: 2026-10-21
tags:
  - 壁纸引擎
  - puppet-warp
  - 骨骼动画
  - 动画制作
description: "记录了在 Wallpaper Engine 中用 puppet warp 做头发轻微摆动动画的学习过程，包括导入图片、创建几何图形、添加骨骼、设置权重、循环动画，以及遇到的刘海动画影响脸部的问题。"
slug: wallpaper-engine-puppet-warp
---
> 写于 2026-10-21
> [官方文档](https://docs.wallpaperengine.io/en/scene/puppet-warp/introduction.html)

遇到的问题：wallpaper engine 里面的基础 effect 无法满足我的需求——头发自然地轻微摆动。claude 建议学习这个。

在 wallpaper engine 中，一个图片可以理解为：最下面是一个画框，然后把照片放在画框上面。默认一个图片是有四个支点。puppet warp 则是允许用户自由添加支点，通过支点来控制画面，从而达到想要的物理效果。

## 导入图片
---
puppet warp 要求：图片必须是单一的，没有背景，这样子才能方便系统识别图片。


## 创建几何图形（geometry）
---
点击按钮之后，图片上会呈现出很多个点以及它们构成的三角形。

通过调节**细分**的数值，可以增加或者减少点的个数。

通过调节**填充**的数值，可以扩大或者收缩三角形覆盖的区域。这个功能有什么作用？如果后续要在这张图片上添加基础 effect ，那些 effect 只能添加在几何图形填充到的区域。

## 添加 bone skeleton（骨骼）
---
点击图片的任意位置，可以生成一个 root bone 。再次点击其他的地方，就会生成一个 sub bone 。root bone 的变化是可以引起 sub bone 的变化的。

puppet warp 就是通过改变 **bone skeleton 所控制的区域**的物理变化来实现运动效果。

在添加 bone skeleton 的时候，尽量和现实世界保持一致。

## 确定 limb（ bone skeleton 所控制的区域）
---
在“权重”页面，一点进去就可以看见花花绿绿的一片。engine 是通过颜色来区分每一块 bone skeleton 控制的区域。选中某一块骨骼，再点击“绘制权重”，就可以按照自己的想法来确定每个骨骼控制的区域。

## 添加循环动画
---
为什么用循环？因为只要第一帧和最后一帧的画面一样，就可以达成无限动的效果。

## 新的问题
---
当我在为刘海制作动画的时候，我做的动画是平移+旋转。但是总是会影响到脸。

问题抽象：
1.如何合理地放置支点？
2.头发的运动应该是什么样子的