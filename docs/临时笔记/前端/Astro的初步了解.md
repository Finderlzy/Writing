## 概述

Astro是一个前端框架，与Vue类似。Astro最大的特点是快速，因为它只把需要交互的部分打包为js，剩下的部分全都渲染为静态的html和css。

## 如何判断哪些是需要的交互的部分？

如果你在 Astro 里嵌入一个 React/Vue 组件（比如一个计数器按钮），默认只会渲染成静态 HTML，不会有任何 JS 运行——按钮点了没反应，因为你忘了加 client 指令。

必须显式加上 `client:*` 才会给它打包 JS 并"注水"（hydrate）：

```astro
<Counter />                 <!-- ❌ 静态 HTML，点击没反应 -->
<Counter client:load />     <!-- ✅ 页面一加载就注水 -->
<Counter client:idle />     <!-- ✅ 浏览器空闲时才注水，优先级更低 -->
<Counter client:visible />  <!-- ✅ 滚动到可见区域才注水，适合首屏外的组件 -->
```

也就是说：==Astro看见了“client”才打包==。

[[Astro的进一步了解]]
