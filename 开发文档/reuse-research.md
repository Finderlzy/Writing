# 复用调研：5.0.0 读者网站

> 检索日期：2026-10-26。对应需求见 [requirements.md](requirements.md)，术语见 [CONTEXT.md](../CONTEXT.md)。
> 核查程度：下列候选都只读过 README、官方文档、LICENSE 和发布记录（“文档/源码核查”），没有克隆或运行任何一个。

## 要解决的问题

5.0.0 要把文档风格的站点改成单栏个人博客：首页、全部文章（阶段 + 标签筛选）、文章页（目录、上下篇、系列、评论）。内容约 110 篇公开文章，大量使用 Obsidian 写法：398 处双链（含 `#标题`、`#^block-id`、别名、表格转义）、33 处 Callout、带尺寸的图片嵌入、高亮和公式。需求要求链接坏了时构建报文件和行号并停止（第 6 节），并且托管方式不变（GitHub Actions → GitHub Pages）。

现状 4.1.0：自研的 `tools/obsidian_compat` 把 Obsidian 写法转成标准 Markdown 并做严格检查，再交给 MkDocs 1.6.1 + Material 9.7.7 生成网站。

## 检索词

`obsidian static site generator`、`obsidian publish github pages`、`obsidian wikilinks markdown export`、`personal blog static site generator python`、`mkdocs material maintenance`、`zensical mkdocs compatibility`、`Obsidian 发布 博客`。

## 候选对比

| 候选 | 许可证 | 维护状态 | 覆盖 | 缺口 | 判断 |
| --- | --- | --- | --- | --- | --- |
| [MkDocs](https://github.com/mkdocs/mkdocs) 1.6.1 + [Material](https://github.com/squidfunk/mkdocs-material) 9.x（现状） | BSD-2 / MIT | MkDocs 自 2024-08 起没有发布；Material 已停止功能开发，只修关键问题到 2027-05-05（[官方公告](https://squidfunk.github.io/mkdocs-material/blog/2025/11/05/zensical/)），后续版本把 mkdocs 限制在 `<2` | Markdown 渲染、目录、代码复制、搜索 | 文档站布局：侧边导航树、顶栏 tabs；改成单栏博客要覆盖大部分模板，等于在一个停止开发的主题上写新主题 | 不再作为站点框架；只保留它底下的 Python-Markdown 和 pymdown-extensions |
| [Zensical](https://github.com/zensical/zensical) v0.0.72 | MIT | 活跃，但仍是 0.0.x | 读 `mkdocs.yml`，延续 Material 外观 | 仍是文档站；[兼容性文档](https://zensical.org/docs/compatibility/mkdocs/)没有承诺支持自定义 MkDocs 插件，现有 `PageUrlPlugin` 无法确认能迁过去 | 仅作参考，不采用 |
| [Quartz](https://github.com/jackyzha0/quartz) v5.0.0（2026-03） | MIT | 活跃，13k star | 原生支持双链、块引用、Callout、带尺寸嵌入、公式、标签页、Giscus 评论、别名跳转 | 链接坏了只给 `<a>` 加 `broken` 样式类（[CrawlLinks 文档](https://github.com/jackyzha0/quartz/blob/v5/docs/plugins/CrawlLinks.md)），做不到“报文件和行号并停止”；网址按文件路径生成并转小写，和现有 slug 规则不同；插件在构建时从 `github:quartz-community/*` 拉取；默认是数字花园布局（左右栏、图谱），要大量改布局；引入 Node 22 工具链 | 仅作参考（它的系列阅读、标签页做法可借鉴），不采用 |
| [obsidian-export](https://github.com/zoni/obsidian-export) v25.3.0 | BSD-2-Clause-Patent 类（LICENSE 文件，GitHub 未识别 SPDX） | 维护中，最近发布 2025-03 | 把仓库导出成普通 Markdown，能处理双链和嵌入 | 输出仍要另找生成器；不处理 Callout 转换和本项目的 slug 网址；Rust 二进制要进 CI | 不采用：现有转换层已覆盖它的能力，而且带行号诊断 |
| [obsidian-digital-garden](https://github.com/oleeskild/obsidian-digital-garden) 2.102.0 | MIT | 活跃 | Obsidian 插件 + Eleventy 模板，按笔记属性发布 | 发布动作在 Obsidian 里点，绑定 Vercel/Netlify 模板；与“推送 main 自动发布”和严格检查都不合 | 不采用 |

## 推荐方向

保留自研的 `obsidian_compat` 转换和检查层，去掉 MkDocs 和 Material，换成一个只服务这三类页面的小型渲染层：Python-Markdown + pymdown-extensions 渲染正文，Jinja2 模板出页面。理由：

- 需求里最难的部分（Obsidian 写法的严格转换、行号诊断、slug 网址）已经有经过测试的实现，所有候选都做不到同等的严格程度。
- MkDocs 栈已经停止发展，改成博客布局反而要和它的文档站模型对抗。
- 新渲染层要做的事很少：三种页面模板、链接改写、跳转页。Jinja2、Markdown、PyYAML 都已经是现在的依赖，不新增第三方服务。

具体设计见 [architecture.md](architecture.md)，决策记录见 [adr/0001-drop-mkdocs.md](adr/0001-drop-mkdocs.md)。

## 缺口

- 没有找到能直接复用的“单栏中文个人博客”Jinja2 模板，前端模板和样式自己写，参考刘未鹏博客的版式。
- 没有验证 Zensical 对自定义插件的实际支持；它不在采用路线上，不再追查。
