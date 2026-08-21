## 解决什么问题
在前端中，导航栏是非常常见的东西，几乎每一个页面都有导航栏。另外，很多页面的 `<head>` 部分是相同的。如果每一次写新的页面都写一遍导航栏和 `<head>` ，不仅开发的时候很繁琐，未来维护也很困难（每次都要修改很多地方）。

## 是什么
Layout = 把「页面外壳」抽出来做成的一个[[组件]]。它负责所有页面**相同**的部分：`<html>`、`<head>`、导航、主题按钮、主区容器。它在最外层，把页面整个包住。

==本质上是复用的思想==

## 为什么要用Layout
开发和维护方便

## 在astro中如何使用layout
### 建立layout文件
首先在 `src\layouts` 里面新建一个文件夹，用来放一个最基本的页面外壳，比如我的个人网站的 `HeaderLayout`（导航栏在顶部的页面外壳）、`SidebarLayout`（导航栏在左侧的页面外壳）。

然后就在里面定义页面的外壳：

```astro
// one_layout.astro

<html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>The Layout</title>
    </head>

    <body>
        <a href = "/"> 首页 </a>
        <a href = "/about"> 关于 </a>
        <a href = "/tag"> 标签</a>
        
        <slot></slot> // 插槽
        
    </body>
</html>
```
其中，`slot` **插槽**是用来放页面其他东西的。什么叫做“页面其他东西”？layout只是一个外壳，一个页面肯定还要有内容什么的，`slot` 就是放那些的。**类似于相框和相片的关系**。
### `import`

在要使用这个外壳的页面中，import你所写的layout文件。

```astro
// index.astro

// layout文件名字是上面那个
---
import LayoutAstroComponent from "./one_Layout.astro";
---
```

然后是使用组件，并自己写一下页面内容。

```astro
// index.astro

// layout文件名字是上面那个
---
import LayoutAstroComponent from "./one_Layout.astro";
---

<LayoutAstroComponent>
    这是首页
</LayoutAstroComponent>
```
使用组件的时候，就把页面外壳都搭好了，新写的东向会放在 `<slot>` 里面。
