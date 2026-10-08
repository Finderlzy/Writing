# Writing

个人文章网站，收录各种各样的想法、学习笔记、技术知识、随笔、兴趣记录和仍在整理中的内容。

内容使用 Obsidian 编写，网站由 [MkDocs](https://www.mkdocs.org/) 和 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 生成，并发布到 [GitHub Pages](https://finderlzy.github.io/Writing/)。仓库内置 Obsidian → MkDocs 兼容层，可以在不修改原始笔记的前提下转换双链、Callout、高亮、LaTeX 数学公式等语法。

## 工作原理

```text
docs/ 原始 Obsidian 笔记
        ↓ 扫描、转换和链接检查
.cache/converted-docs/ 标准 Markdown
        ↓ MkDocs 构建
site/ 最终 HTML
        ↓ 页面、附件和锚点复检
GitHub Pages
```

每次构建都会重新生成缓存和站点。`docs/` 始终是内容源，`theme/extra.css` 是站点样式源；构建入口会把它注入 `.cache/converted-docs/stylesheets/` 后再交给 MkDocs。构建过程会检查 `docs/` 前后摘要，避免转换意外修改原始笔记。

## 支持的 Obsidian 语法

| Obsidian 写法 | 作用 |
| --- | --- |
| `[[页面]]`、`[[页面\|别名]]` | 页面双链 |
| `[[页面#标题]]` | 跳转到目标页面标题 |
| `[[页面#^block-id]]` | 跳转到 Obsidian 块 ID |
| `[[#标题]]`、`[[#^block-id\|别名]]` | 跳转到当前页面标题或块 ID |
| `![[图片.png]]` | 嵌入本地图片 |
| `![[图片.png\|300]]`、`![[图片.png\|300x200]]` | 指定图片宽度（及高度） |
| 表格中的 `[[页面\\\|别名]]` | 表格内带别名的双链（`\|` 需转义，Obsidian 会自动生成） |
| `==重点==` | 文字高亮 |
| `> [!note]` | Callout；支持 Obsidian 内置类型及别名（`tip`、`important`、`info`、`danger` 等） |
| `$x$`、`$$...$$` | LaTeX 数学公式（基于 MathJax 3 渲染） |

转换器会避开 YAML front matter、代码围栏、公式块和行内代码。它也会修正常见的宽松列表格式与紧贴正文的公式块，避免其被 MkDocs 当成普通段落或被换行规则打断。

当前不支持页面嵌入、Callout 折叠标记和自定义 Callout 类型。PDF 等非图片附件请暂时使用普通 Markdown 链接。页面内存在重复标题时，建议不要链接到重复项。

空目标、空锚点和无效路径会产生明确诊断、阻止构建，并保留原始双链或嵌入文本，方便定位和修改。合法的 `../` 相对路径、中文文件名和包含空格的路径仍按普通引用处理。


## 目录结构

```text
docs/                   # 原始 Obsidian 笔记与附件
├── 00收集/             # 尚未归类、等待处理的新笔记
├── 01系统/             # 笔记系统说明与规范
├── 02学习/             # 持续学习和探索的问题
├── 03学习方法论/       # 对学习方法、课程与实习规划的思考
├── 04技术/             # 技术实践与操作记录
├── 05二次元/           # 番剧评价与观后感
├── 06读书/             # 读书笔记
├── 07自己/             # 对自我的思考（不部署到网站）
├── 08作品/             # 已完成或正在整理的创作
├── 09归档/             # 暂时归档的学习和技术资料
├── 09附件/             # 图片、PDF 等本地附件
├── javascripts/         # 站点脚本：访问统计、MathJax 配置
└── index.md             # 站点首页
tools/
├── build_site.py        # 转换、构建和验收入口
└── obsidian_compat/     # 索引、解析、转换及 HTML 检查
tests/                   # 单元测试与仓库级验收测试
theme/
└── extra.css            # 站点样式源；由构建入口注入转换缓存
overrides/
└── partials/comments.html  # Material 主题覆盖：Giscus 评论区
开发文档/               # 设计文档与开发日志（版本记录）
mkdocs.yml               # 站点与主题配置
requirements.txt         # 固定版本的 Python 依赖
```

一级分类由 MkDocs 和转换器动态扫描，可以按需要新增，不需要修改构建程序。`00收集`、`09附件`、`docs` 和 `site` 是构建与编辑器约定的特殊路径；调整它们时必须同步检查 `mkdocs.yml`、`docs/.obsidian/app.json`、`.gitignore` 和自动验收测试。

`tools/build_site.py` 中的 `UNPUBLISHED_PATHS` 列出只在本地 Obsidian 保留、不部署到网站的一级目录或根目录文件（目前为 `07自己` 和 `AGENTS.md`）。这些页面仍参与双链检查；公开页面指向它们的双链会渲染为纯文字，只被它们嵌入的附件也不会复制到网站。注意它们仍会随 Git 推送到 GitHub 仓库。

## 评论区

除首页外的页面底部显示 [Giscus](https://giscus.app/zh-CN) 评论区，留言存放在本仓库的 GitHub Discussions，读者需登录 GitHub 才能留言。参数位于 `mkdocs.yml` 的 `extra.giscus`；`category_id` 为空时不渲染评论区。页面与讨论帖按 URL 路径对应，移动或重命名笔记后，旧留言不会跟到新页面。

## 仓库与社交链接

顶栏右侧链接到本仓库（`mkdocs.yml` 的 `repo_url`），页脚图标链接到个人主页（`extra.social`）。新增社交媒体时在 `extra.social` 下追加一项 `icon`、`link`、`name`，图标名可在 [Material 图标库](https://squidfunk.github.io/mkdocs-material/reference/icons-emojis/#search) 查询，例如 `fontawesome/brands/bilibili`、`fontawesome/brands/zhihu`。

## Obsidian 链接设置

在“文件与链接”中，将“内部链接类型”设为“基于仓库根目录的绝对路径”（`newLinkFormat: "absolute"`），附件目录保持 `09附件`，并开启“始终更新内部链接”。其他设备使用此仓库时也应保持这些设置。

中央附件使用 `![[09附件/图片.png]]`，不要使用 `![[../../09附件/图片.png]]` 这类依赖笔记目录深度的嵌入。这里的绝对路径以 Obsidian 仓库根目录（`docs/`）为起点，不是电脑上的磁盘路径。转换器会在生成网站时输出对应的相对 URL；普通笔记已有的合法相对链接仍然受支持。

修改链接设置只影响之后生成的链接，不会自动迁移历史引用。旧的中央附件相对引用需单独修正；仓库验收测试会汇总违规位置和建议路径。构建过程不会自动改写源笔记。
