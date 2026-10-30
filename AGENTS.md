# AGENTS.md

这是个人文章网站 `https://finderlzy.github.io/writing/` 的仓库：`docs/` 是 Obsidian 笔记库，`tools/` 把它构建成静态站点。

## 内容分类

- 写的东西沿两条线走：想法 → 思考 → 博客，灵感 → 初稿 → 作品；两条线的起点都是 `00收集`，私人生活进 `07自己`。
- 分类的唯一依据是 `docs/01系统/分类标准.md`，不确定就按它判断。

## 发布范围

- 只有 `02思考`、`03初稿`、`04博客`、`05作品` 和 `docs/index.md` 发布；`00收集`、`01系统`、`07自己` 不发布，但仍随 Git 推送到公开仓库。
- 不发布的页面同样参与双链检查：公开页面指向它们的双链渲染成纯文字，只被它们引用的附件不复制。
- 「这篇发不发布」只由 `tools/content.py` 的 `LAYOUT` 和 `is_published` 决定，不要在别处另写一套；新增阶段或一级文件夹要在 `LAYOUT` 登记，网址前缀同样写在那里。

## 对外契约

线上网址动不得，改之前先看这几条：

- slug 只能用小写字母、数字和单个连字符，同一栏目内唯一。不写 slug 的页面按源文件路径生成 8 位短 ID，文件移动或改名后 ID 会变——要分享的文章手写 slug。
- `04博客` 的子文件夹各是一个系列，要在 `content.SERIES` 登记入口篇（`04博客` 根目录那篇）。系列内顺序：入口篇在前（入口篇固定在系列开头，不按链接数排，所以系列里其它篇都不链回它，别按「多链一链」的建议去加），其余按组内链接最多的页面排序。新增系列或加篇后跑构建，确认没报 `E_SERIES_*`。
- **订阅教程旧链接**：`04博客/如何订阅claude（纯操作版）.md` 原来在 `/tech/subscribe-claude-quick/`，这个地址在视频里公开过。旧网址由 `tools/build_site.py` 的 `REDIRECTS` 跳转到 `/blog/subscribe-claude-quick/`，改文件名或 slug 时同步改 `REDIRECTS`，构建会检查跳转目标是否存在。

## Obsidian 写法

支持的写法见 `tools/obsidian_compat/` 的解析器，不要往 README 或本文件补语法表。

- 不支持的写法（页面嵌入、Callout 折叠标记、自定义 Callout 类型）会报错并阻止构建，不会降级渲染。
- 双链目标缺失、歧义、锚点不存在或语法未闭合时，构建给出文件和行号并停止，不会跳过。
- 嵌入附件写 `![[09附件/图片.png]]`，不要写依赖目录深度的 `../` 相对路径。

## 提交与部署

- 直接在 `main` 上提交并推送，不建分支、不开 PR。提交信息用中文，一句话说清改了什么，如「需求 R-UI-3：……」。
- 推送即触发部署。开工前和提交前看一眼 `git log -3`：作者的 Obsidian 开着 Obsidian Git 自动备份，会定时把整个仓库的未提交改动一起提交（信息是 `vault backup: …`）并推送。改代码时尽快提交；发现自己的改动已被自动备份带走时，在交付记录里写明对应的提交号。不要改 `docs/.obsidian/` 里的插件配置来关掉它。

## 工作区

- `python` 指向哪个解释器不确定，直接调用 `.venv/bin/python`。
- 验证、诊断码语义、字体缓存见 [构建与验证](06-构建与验证.md)：**交付前跑单测和构建、构建失败或 `.cache/fonts/` 缺失时读它**。
- 设计文档、ADR、开发日志和 Agent 约定放 `开发文档/`，不要放进 `docs/`——那是 Obsidian 仓库，多出一级文件夹会让构建报错。模板和站点样式放 `theme/`，构建代码放 `tools/`。

## matt 流程与文档

- 研发流程用 `.claude/skills/` 里的 matt 套件，命令清单和各步用法见总库 `~/Workspace/Tools/Skills/dev/README.md`。
- 技能里写的 `docs/agents/` 在本仓库对应 `开发文档/agents/`（`docs/` 是 Obsidian 仓库）。
- 跑 `/arch` 时读写 `开发文档/agents/developer.md`：该文件尚未创建，按技能要求现场创建，别读 `docs/agents/developer.md`。
- 本地 issue tracker 计划放根目录 `.scratch/`，随 git 提交，但**目前还没创建**；首次执行需要它的流程前，先读 `开发文档/agents/issue-tracker.md` 按其约定建目录。别把这个文件追加上 Git 让本地状态进入公开仓库。
- single-context：术语表是根目录 `CONTEXT.md`（不另建 `GLOSSARY.md`），ADR 在 `开发文档/adr/`；`开发文档/agents/domain.md` 的模板写的是 `GLOSSARY.md` 和 `docs/adr/`，以本节为准。

## 编辑 README

README 的章节取舍由作者决定。曾经加进去、之后被作者删除的内容（分类表、Obsidian 语法表、本地构建步骤等）不要再加回去；需要补充的项目知识写进本节。

## 现状说明

通用约定（沟通、执行、测试、工具）同步自作者的全局规则 `~/Workspace/Tools/AGENTS.md`，那边已加载，本文件不复制；项目事实、历史决策和对外契约以本文件及 `开发文档/` 为准。
