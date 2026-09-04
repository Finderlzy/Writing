# Writing

个人文章网站，收录各种各样的想法、学习笔记、技术知识、随笔、兴趣记录和仍在整理中的内容。

内容使用 Obsidian 编写，网站由 [MkDocs](https://www.mkdocs.org/) 和 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 生成，并发布到 [GitHub Pages](https://finderlzy.github.io/Writing/)。仓库内置 Obsidian → MkDocs 兼容层，可以在不修改原始笔记的前提下转换双链、Callout、高亮等语法。

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
| `==重点==` | 文字高亮 |
| `> [!note]` | Callout；支持 `note`、`question`、`warning`、`example` |

转换器会避开 YAML front matter、代码围栏和行内代码。它也会修正常见的宽松列表格式，避免列表被 MkDocs 当成普通段落。

当前不支持页面嵌入、Callout 折叠标记和附件尺寸选项。PDF 等非图片附件请暂时使用普通 Markdown 链接。页面内存在重复标题时，建议不要链接到重复项。

空目标、空锚点和无效路径会产生明确诊断、阻止构建，并保留原始双链或嵌入文本，方便定位和修改。合法的 `../` 相对路径、中文文件名和包含空格的路径仍按普通引用处理。


## 目录结构

```text
docs/                   # 原始 Obsidian 笔记与附件
├── 00收集/             # 尚未归类、等待处理的新笔记
├── 01系统/             # 笔记系统说明与规范
├── 02学习/             # 持续学习和探索的问题
├── 03思考/             # 对自我、学习和兴趣的思考
├── 04项目/             # 围绕明确成果展开的工作
├── 05作品/             # 已完成或正在整理的创作
├── 08归档/             # 暂时归档的学习和技术资料
├── 09附件/             # 图片、PDF 等本地附件
└── index.md             # 站点首页
tools/
├── build_site.py        # 转换、构建和验收入口
└── obsidian_compat/     # 索引、解析、转换及 HTML 检查
tests/                   # 单元测试与仓库级验收测试
theme/
└── extra.css            # 站点样式源；由构建入口注入转换缓存
开发文档/               # 设计文档
mkdocs.yml               # 站点与主题配置
requirements.txt         # 固定版本的 Python 依赖
```

一级分类由 MkDocs 和转换器动态扫描，可以按需要新增，不需要修改构建程序。`00收集`、`09附件`、`docs` 和 `site` 是构建与编辑器约定的特殊路径；调整它们时必须同步检查 `mkdocs.yml`、`docs/.obsidian/app.json`、`.gitignore` 和自动验收测试。
