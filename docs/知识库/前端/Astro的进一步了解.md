## .astro文件

这个文件就是体现Astro框架的东西。

==每一个.astro文件都有2个部分组成——**frontmatter**和**template**==。
- frontmatter写在两个`---`之间，负责导入组件、接收 props、请求数据、做计算，只会在构建时跑一次
- template就是除了frontmatter的部分，写在`---`之外。本质就是html，但是可以通过{}插入js

例子：
```例子
// Frontmatter：JS/TS 代码，只在服务器端/构建时跑一次
---
import '../styles/global.css';
const pagetitle = "首页";
---

// Template
<html lang="zh-cn">

  <head>
    ......
  </head>

  <body>
    ......
  </body>
</html>
```

## 文件路由

简单来说就是==写在`src/pages/` 下的每个 `.astro` 文件自动会有一个网址==。这就是路由，虽然我还不懂是什么意思。

`index.astro`对应的网址是`/`,其他的文件对应的网址是`/其他的文件`

没有文件，但是搜索那个网址则会404

## `define:vars` 和 `var()`

css有一套自己的语法，它是识别不了js语法的。但是.astro文件会在frontmatter部分会定义一些变量，有的是给css用的。这个时候就需要把js变量转化为css自定义属性。

==`define:vars={{ skillColor }}`：Astro 指令，把 frontmatter 里的 JS 变量"搬运"成 CSS 自定义属性（`--skillColor`）==，挂在元素上，作为 frontmatter 和 CSS 之间的桥梁

css变量是不能直接使用自定义属性的值，需要通过一个函数——**`var(--skillColor)`**：CSS 函数，用来**读取**这个自定义属性的值

关系：`define:vars` 负责"生产"变量，`var()` 负责"消费"变量

例子：
```
font-weight: var(--fontWeight);

// font-weight（变量） = --fontWeight（css自定义属性）
```
