# Writing

个人文章网站，收录各种各样的想法、学习笔记、技术知识、随笔、兴趣记录和仍在整理中的临时笔记。

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

每次构建都会重新生成缓存和站点。`docs/` 始终是内容源，构建过程会检查其前后摘要，避免转换意外修改原始笔记。

## 支持的 Obsidian 语法

| Obsidian 写法 | 作用 |
| --- | --- |
| `[[页面]]`、`[[页面\|别名]]` | 页面双链 |
| `[[页面#标题]]` | 跳转到目标页面标题 |
| `[[页面#^block-id]]` | 跳转到 Obsidian 块 ID |
| `![[图片.png]]` | 嵌入本地图片 |
| `==重点==` | 文字高亮 |
| `> [!note]` | Callout；支持 `note`、`question`、`warning`、`example` |

转换器会避开 YAML front matter、代码围栏和行内代码。它也会修正常见的宽松列表格式，避免列表被 MkDocs 当成普通段落。

当前不支持页面嵌入、Callout 折叠标记和附件尺寸选项。PDF 等非图片附件请暂时使用普通 Markdown 链接。页面内存在重复标题时，建议不要链接到重复项。


## 目录结构

```text
docs/                   # 原始 Obsidian 笔记与附件
├── 知识库/             # 编程与其他领域的学习笔记
├── 碎碎念/             # 随笔、个人思考与兴趣记录
├── 临时笔记/           # 尚在整理中的资料与想法
├── 附件/               # 图片、PDF 等本地附件
└── index.md             # 站点首页
tools/
├── build_site.py        # 转换、构建和验收入口
└── obsidian_compat/     # 索引、解析、转换及 HTML 检查
tests/                   # 单元测试与仓库级验收测试
开发文档/               # 设计文档
mkdocs.yml               # 站点与主题配置
requirements.txt         # 固定版本的 Python 依赖
```
