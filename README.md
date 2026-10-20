# Writing

个人文章网站：<https://finderlzy.github.io/Writing/>

这里放我的思考、学习笔记、技术教程和文学作品。所有内容在 Obsidian 里写，用 [MkDocs](https://www.mkdocs.org/) + [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 生成网站，推送到 GitHub 后自动发布到 GitHub Pages。

当前版本：**4.1.0**，版本记录见 [开发文档/DEVELOPMENT.md](开发文档/DEVELOPMENT.md)。

## 日常写作流程

```text
在 Obsidian 的 docs/00收集/ 写新文章
        ↓ 按 01系统/分类标准.md 移到对应文件夹（Inbox Filer 插件或 Claude 代劳）
推送到 GitHub 的 main 分支（Obsidian Git 自动备份也会推送）
        ↓ GitHub Actions：跑测试 → 转换并构建 → 检查页面和链接
发布到 GitHub Pages
```

`docs/` 就是 Obsidian 仓库本身。构建只读取它，不会改动原始笔记。

## 内容分类

写的东西沿两条线往前走：想法 → 思考 → 技术，灵感 → 初稿 → 作品；只有私人生活放进 `07自己`。每个文件夹的判断标准和例子都写在 [docs/01系统/分类标准.md](docs/01系统/分类标准.md)，那篇是唯一的权威说明，Inbox Filer 插件也把它作为分类依据。

| 文件夹 | 放什么 | 网址前缀 | 公开 |
| --- | --- | --- | --- |
| `00收集/` | 还没分类的新文章；`灵感/` 放灵感片段 | — | 否 |
| `01系统/` | 笔记库、写作和发布的规则 | `system` | 是 |
| `02笔记/` | 写给自己的学习记录：`课程/`、`概念/`、`专题/` | `notes` | 是 |
| `03思考/` | 我自己的观点、心得、番评、书评和计划（平铺，主题写在 `tags`）；`初稿/` 放还没润色的文学初稿 | `thoughts` | 是 |
| `04技术/` | Agent 帮忙梳理后、面向读者的文章和教程 | `tech` | 是 |
| `05作品/` | Agent 润色后发布的文学作品 | `opus` | 是 |
| `07自己/` | 私人生活：出现真实人名，或剖析自己的内心和缺点 | — | 否 |
| `09归档/` | 不再维护的旧资料 | `archive` | 是 |
| `09附件/` | 图片、PDF 等附件 | — | 随引用的页面 |

不公开的内容由 `tools/build_site.py` 的 `UNPUBLISHED_PATHS` 控制（目前是 `00收集`、`07自己` 和 `docs/AGENTS.md`）。这些页面仍然参与双链检查。公开页面指向它们的双链会显示成纯文字，只被它们引用的附件也不会复制到网站。**注意：它们仍然会随 Git 推送到公开的 GitHub 仓库。**

## 导航与思考列表

导航由构建生成，配置在 `tools/build_site.py` 的 `NAV_POSTS`、`NAV_NOTES`，顺序是：

| 导航 | 内容 | 排序 |
| --- | --- | --- |
| 首页 | `docs/index.md`，末尾自动加上“最近的思考”（最新 8 篇）和“全部思考”链接 | — |
| 思考 | 列表页 `/thoughts/`，加上 `03思考` 的全部文章，`初稿/` 折叠成一组 | `createdDate` 从新到旧 |
| 技术 | `04技术` | `createdDate` 从新到旧 |
| 作品 | `05作品` | `createdDate` 从新到旧 |
| 笔记 | `02笔记`，保留子文件夹结构 | 按文件名 |

- `01系统` 和 `09归档` 不进导航，但页面照常发布，原网址不变。
- 思考列表页按时间列出 `03思考` 的所有文章（包括初稿），顶部有按 `tags` 筛选的按钮（`docs/javascripts/post-filter.js`）。它只在构建时生成，`docs/03思考/` 里不能有 `index.md`，否则构建报 `E_GENERATED_PAGE_CONFLICT`。
- 在 front matter 写 `description: 一两句话简介`，列表页会在标题下面用灰色小字显示它；首页的“最近的思考”不显示。
- 日期取 front matter 的 `createdDate`（写成 `2026-10-14`）。文章缺日期时会排在最后，构建给出 `W_POST_DATE_MISSING` 提示，但不会失败。

## 页面网址

页面网址的格式是 `/<网址前缀>/<slug>/`，Obsidian 里的中文文件名和目录不受影响。

- 网址前缀由一级文件夹决定，对照表是 `tools/build_site.py` 的 `SECTION_SLUGS`。新增一级文件夹时必须在这里补上，否则构建会报 `E_URL_SECTION_MISSING`。
- 在 front matter 写 `slug: vless-reality`，网址就是 `…/tech/vless-reality/`。slug 只能用小写字母、数字和单个连字符，同一栏目内不能重复，否则构建报 `E_SLUG_INVALID` 或 `E_SLUG_DUPLICATE`。
- 没写 slug 的页面会按源文件路径生成 8 位短 ID，例如 `/notes/c319381c/`。文件移动或改名后 ID 也会变，所以**要分享的文章请手写 slug**。
- 每个页面的中文路径都会生成一个跳转页，自动跳到新网址。跳转页只按页面现在的位置生成，文件移走后，旧位置的跳转页就没有了。
- 一级文件夹改名后，`build_site.py` 的 `RENAMED_SECTIONS` 让旧网址继续可用：目前把原 `03文章` 的 `/articles/<id>/` 和 `/articles/` 跳到 `/thoughts/` 下对应的页面。只覆盖文件夹根目录下的页面，不覆盖子文件夹。
- **不能动的链接**：`04技术/如何订阅claude（纯操作版）.md`（`/tech/subscribe-claude-quick/`）已经在视频里公开。不要移动或改名这篇文章，不要改它的 slug，也不要改 `04技术 → tech` 这个对应关系。`scripts/setup.sh` 同理，它是转发到独立仓库 [reality-setup](https://github.com/Finderlzy/reality-setup) 的壳，用来保证视频里的旧命令继续可用，不要删除或改名。

## 支持的 Obsidian 语法

| Obsidian 写法 | 作用 |
| --- | --- |
| `[[页面]]`、`[[页面\|别名]]` | 页面双链 |
| `[[页面#标题]]`、`[[页面#^block-id]]` | 跳到目标页面的标题或块 |
| `[[#标题]]`、`[[#^block-id\|别名]]` | 跳到当前页面的标题或块 |
| `![[图片.png]]`、`![[图片.png\|300]]`、`![[图片.png\|300x200]]` | 嵌入本地图片，可指定宽高 |
| 表格中的 `[[页面\\\|别名]]` | 表格里带别名的双链（Obsidian 会自动转义 `\|`） |
| `==重点==` | 高亮 |
| `> [!note]` | Callout，支持 Obsidian 内置类型及别名（`tip`、`important`、`info`、`danger` 等） |
| `$x$`、`$$...$$` | LaTeX 数学公式（MathJax 3） |

暂不支持：页面嵌入、Callout 折叠标记、自定义 Callout 类型。PDF 等非图片附件请用普通 Markdown 链接。

双链目标为空、锚点为空或路径无效时，构建会给出明确的诊断并停止，方便定位修改。

## Obsidian 设置

在“文件与链接”中：

- “内部链接类型”设为“基于仓库根目录的绝对路径”（`newLinkFormat: "absolute"`）；
- 附件目录保持 `09附件`；
- 开启“始终更新内部链接”，这样在 Obsidian 里移动文件时，双链会自动跟着更新。

嵌入附件请写 `![[09附件/图片.png]]`，不要写 `![[../../09附件/图片.png]]` 这种依赖目录深度的相对路径；仓库测试会列出违规位置和建议写法。

## 本地构建

需要 Python 3.13 以上版本。

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python -m unittest discover -s tests
```

```bash
.venv/bin/python tools/build_site.py
```

构建成功会输出 `build succeeded: N pages published, M unpublished`，生成的网站在 `site/`。想在本地预览，可以运行：

```bash
.venv/bin/python -m http.server -d site 8000
```

然后打开 <http://localhost:8000/>。

构建流程：

```text
docs/ 原始笔记
   ↓ 扫描、转换 Obsidian 语法、检查双链
.cache/converted-docs/ 标准 Markdown（注入 theme/extra.css）
   ↓ MkDocs 构建、按 SECTION_SLUGS 分配网址、生成中文路径跳转页
site/ 网站
   ↓ 检查页面、附件和锚点
```

构建前后会比对 `docs/` 的摘要，确保转换过程没有改动原始笔记。

## 评论区与外链

- 评论区：除首页外，每个页面底部都有 [Giscus](https://giscus.app/zh-CN) 评论区，留言存放在本仓库的 GitHub Discussions，读者需要登录 GitHub。配置在 `mkdocs.yml` 的 `extra.giscus`，`category_id` 为空时不显示评论区。评论按网址对应，页面网址变了，旧留言不会跟过去。
- 顶栏链接到本仓库（`repo_url`），页脚是社交媒体图标（`extra.social`）。新增时追加一项 `icon`、`link`、`name`，图标名在 [Material 图标库](https://squidfunk.github.io/mkdocs-material/reference/icons-emojis/#search) 查询。

## 仓库结构

```text
docs/                    # Obsidian 仓库：笔记、附件、首页（分类见上文）
├── javascripts/         # 站点脚本：访问统计、MathJax 配置、文章列表的标签筛选
└── index.md             # 网站首页
tools/
├── build_site.py        # 构建入口：转换、构建、检查；SECTION_SLUGS、UNPUBLISHED_PATHS、导航配置在这里
├── site_nav.py          # 生成导航、文章列表页和首页的最近文章
└── obsidian_compat/     # 索引、解析、转换、网址分配、HTML 检查
tests/                   # 单元测试与仓库级验收测试
theme/extra.css          # 站点样式
overrides/               # Material 主题覆盖（Giscus 评论区）
scripts/setup.sh         # 旧命令转发壳，不要删除或改名
开发文档/                # 设计文档、开发日志（版本记录）、交付记录
.github/workflows/       # 推送 main 后自动测试、构建、部署
mkdocs.yml               # 站点与主题配置
requirements.txt         # 固定版本的 Python 依赖
```

`docs/`、`00收集`、`09附件` 和 `site` 是构建和编辑器共同约定的路径。调整它们时，必须同步修改 `mkdocs.yml`、`docs/.obsidian/app.json`、`.gitignore` 和自动验收测试。
