# writing

个人文章网站：<https://finderlzy.github.io/writing/>

这里放我的思考、初稿、博客和文学作品。所有内容在 Obsidian 里写，用仓库里自带的 Python 脚本生成网站，推送到 GitHub 后自动发布到 GitHub Pages。

当前版本：**5.3.0**，版本记录见 [开发文档/DEVELOPMENT.md](开发文档/DEVELOPMENT.md)。

## 日常写作流程

```text
在 Obsidian 的 docs/00收集/ 记下念头
        ↓ 用自己的话写成思考、初稿，再整合成博客、润色成作品，各自新建在对应文件夹，原文留在原处
        ↓ 去哪个文件夹看 01系统/分类标准.md（Inbox Filer 插件或 Claude 代劳）
推送到 GitHub 的 main 分支（Obsidian Git 自动备份也会推送）
        ↓ GitHub Actions：跑测试 → 下载源字体 → 转换并构建 → 检查页面和链接
发布到 GitHub Pages
```

`docs/` 就是 Obsidian 仓库本身。构建只读取它，不会改动原始笔记。网站只发布 `02思考`、`03初稿`、`04博客`、`05作品` 和首页；`00收集`、`01系统`、`07自己` 只在 Obsidian 里看，网站上打不开，但它们仍在这个公开仓库里。

## 网站页面

| 页面 | 内容 |
| --- | --- |
| 首页 | 对话气泡里是 `docs/index.md` 正文的第一段，下面是其余的话；两张卡片画出“想法 → 思考 → 博客”和“灵感 → 初稿 → 作品”两条线和各阶段篇数；最后是博客和作品，按 `createdDate` 从新到旧、按月分组 |
| 全部文章 `/posts/` | 所有公开文章，按月分组，可以按阶段（思考、初稿、博客、作品）和标签筛选 |
| 文章页 | 标题、日期、阶段、标签、读完大约几分钟、简介、目录、正文、上一篇和下一篇，最后是评论区 |

- `04博客` 下的子文件夹是一组系列博客，比如订阅教程的 `原理版/`、`操作版/`。首页只放 `04博客` 根目录里代表系列的那篇，系列里的各篇在全部文章里，文章页能顺着系列往下读。新建系列时要在 `tools/content.py` 的 `SERIES` 里登记入口篇，否则构建报错。
- 在 front matter 写 `description: 一两句话简介`，首页和全部文章会在标题下面显示它，文章页把它放进“讲了什么”的对话框。
- 标题取 front matter 的 `title`，没写就用文件名；文件名末尾和阶段同名的注释不显示，比如 `05作品/黑框眼镜（作品）.md` 显示为“黑框眼镜”。正文第一行和标题重复的 `# 标题`、开头只写“写于 / 更新于”日期的引用行，网页上都不再重复显示，原文不受影响。
- 日期取 front matter 的 `createdDate`（写成 `2026-10-14`）。文章缺日期时会排在最后，构建给出 `W_POST_DATE_MISSING` 提示，但不会失败。

## 外观

明亮的轻小说封面风格：白底，标题后面垫着大号的淡色字，粗黑体标题，一个红橙色强调色，卡片和窗口用粗描边，空白处有几个用代码画的星星、音符。深色模式默认跟随系统，也可以用顶栏右端的按钮在白天和黑夜之间切换。设计样稿和取舍记在 `开发文档/`。

标题、大字和数字用的字体（Noto Sans SC、ZCOOL KuaiLe、Zilla Slab、Gochi Hand，都是 OFL 授权）放在本站，构建时只保留页面上用到的字，全站约 84 KB；正文用读者系统自带的字体。网站不从 Google Fonts 等境外服务加载任何东西。源字体约 19 MB，不放进仓库，构建前从 google/fonts 的固定版本下载并校验，来源记在 `theme/fonts/README.md`。

## 页面网址

页面网址的格式是 `/<网址前缀>/<slug>/`，Obsidian 里的中文文件名和目录不受影响。

- 网址前缀由文件夹决定：`02思考` 是 `thoughts`，`03初稿` 是 `drafts`，`04博客` 是 `blog`，`05作品` 是 `opus`，配置在 `tools/content.py` 的 `LAYOUT`。
- 在 front matter 写 `slug: vless-reality`，网址就是 `…/blog/vless-reality/`。slug 只能用小写字母、数字和单个连字符，同一栏目内不能重复，否则构建报 `E_SLUG_INVALID` 或 `E_SLUG_DUPLICATE`。
- 没写 slug 的页面会按源文件路径生成 8 位短 ID，例如 `/thoughts/92de090c/`。文件移动或改名后 ID 也会变，所以**要分享的文章请手写 slug**。
- **旧链接**：视频里公开过的 `/tech/subscribe-claude-quick/` 会跳到《如何订阅claude（纯操作版）》的新地址 `/blog/subscribe-claude-quick/`，配置在 `tools/build_site.py` 的 `REDIRECTS`。改这篇文章的文件名或 slug 时要同步改 `REDIRECTS`，构建会检查跳转目标是否存在。

## Obsidian 设置

在“文件与链接”中：

- “内部链接类型”设为“基于仓库根目录的绝对路径”（`newLinkFormat: "absolute"`）；
- 附件目录保持 `09附件`；
- 开启“始终更新内部链接”，这样在 Obsidian 里移动文件时，双链会自动跟着更新。

嵌入附件请写 `![[09附件/图片.png]]`，不要写 `![[../../09附件/图片.png]]` 这种依赖目录深度的相对路径；仓库测试会列出违规位置和建议写法。

## 评论区与外链

- 评论区：每篇文章底部都有 [Giscus](https://giscus.app/zh-CN) 评论区，留言存放在本仓库的 GitHub Discussions，读者需要登录 GitHub。配置在 `site.toml` 的 `[giscus]`，`category_id` 为空时不显示评论区。评论按网址对应，页面网址变了，旧留言不会跟过去。
- 页脚是社交媒体链接，配置在 `site.toml` 的 `[[social]]`。新增时追加一项，写上 `name` 和 `link`。

## 仓库结构

```text
docs/                    # Obsidian 仓库：笔记、附件、首页（分类见 01系统/分类标准.md）
└── index.md             # 网站首页上我想说的话
tools/
├── build_site.py        # 构建入口：转换、生成网站、检查；旧链接跳转 REDIRECTS 在这里
├── content.py           # 哪些文件夹发布、网址前缀、系列（LAYOUT、SERIES）
├── render.py            # 把文章渲染成网页
├── fonts.py             # 按页面用到的字裁剪字体
├── fetch_fonts.py       # 下载并校验源字体
└── obsidian_compat/     # Obsidian 写法的索引、转换、网址分配、HTML 检查
theme/
├── templates/           # 首页、全部文章、文章页、404 的页面模板
├── assets/              # 样式 site.css 和脚本 site.js
└── fonts/               # 字体来源说明和授权文件（字体本身不进仓库）
tests/                   # 单元测试与仓库级验收测试
开发文档/                # 需求、架构、开发日志（版本记录）、交付记录、设计样稿
.github/workflows/       # 推送 main 后自动测试、构建、部署
site.toml                # 站点名称、网址、页脚链接、评论区配置
requirements.txt         # 固定版本的 Python 依赖
```

`docs/`、`00收集`、`09附件` 和 `site` 是构建和编辑器共同约定的路径。调整它们时，必须同步修改 `tools/content.py`、`docs/.obsidian/app.json`、`.gitignore` 和自动验收测试。
