# ADR-0001：去掉 MkDocs，用自己的渲染层生成读者网站

2026-10-26，状态：已采纳（5.0.0）。

5.0.0 要把文档站改成单栏个人博客（见 [requirements.md](../requirements.md) M4）。MkDocs 自 2024-08 起没有发布，Material 已停止功能开发、关键修复只到 2027-05-05；改成博客布局要覆盖它大部分模板。Quartz 等 Obsidian 发布工具能处理双链，但链接坏了不会让构建失败，也不支持本项目的 slug 网址。所以保留自研的 `tools/obsidian_compat` 转换和检查层，去掉 MkDocs 和 Material，用 Python-Markdown + Jinja2 写一个只生成首页、全部文章、文章页和跳转页的渲染层。

代价：代码复制按钮、标题目录、公式加载这些 Material 自带的功能要自己实现；站内搜索不再有（需求本来就把它列为非目标）。以后如果想换回某个框架，转换层的输出仍是标准 Markdown，可以直接交给别的生成器。

候选对比见 [reuse-research.md](../reuse-research.md)，设计见 [architecture.md](../architecture.md)。
