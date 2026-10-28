# AGENTS.md

## 沟通

- 叙述用简体中文；代码、命令和技术标识保持英文。
- 先说结论和影响，再说行动与待决策；简洁直接，不写套话和重复总结。

## 执行

- 用户当前指令优先于 Skill 和记忆；本文件在本仓库内覆盖全局规则。
- 接到任务就推进到完成；能自己做完的先做完，再拿可检查的结果找用户确认。
- 用户建议不适合目标时直说。不为假想风险加警告、免责声明或审批流程。

## 测试

- 只跑与改动相称的测试；通过后不再重复，除非有新改动或新失败。
- 不为可逆、低影响或只复述实现的改动写测试。
- 收尾删除本次产生的临时文件。

## 工具

- 搜索用 `rg`；网页控制台没有 CLI/API 时用已登录的 Chrome；飞书用 `lark-cli`。
- 只有真正独立的工作才委派子 Agent，结论由主 Agent 验证汇总。

## 项目说明

这是个人文章网站 `https://finderlzy.github.io/writing/` 的仓库。README 只保留作者本人维护的对外说明，不往里加下面的运维细节；这些内容以本节为准。

### 目录与发布

- `docs/` 是 Obsidian 仓库本身，构建只读不写，转换副本在 `.cache/converted-docs/`，网站在 `site/`。
- 一级文件夹只有 `00收集`、`01系统`、`02思考`、`03初稿`、`04博客`、`05作品`、`07自己`、`09附件`，除 `04博客` 的系列子文件夹外不再分子文件夹。写的东西沿两条线走：想法 → 思考 → 博客，灵感 → 初稿 → 作品；私人生活进 `07自己`。分类的唯一依据是 `docs/01系统/分类标准.md`。
- 发布范围只由 `tools/content.py` 的 `LAYOUT` 决定：`02思考`、`03初稿`、`04博客`、`05作品` 和 `docs/index.md`。`00收集`、`01系统`、`07自己` 和 `docs/AGENTS.md` 不发布，但仍参与双链检查；公开页面指向它们的双链渲染成纯文字，只被它们引用的附件不复制；它们仍随 Git 推送到公开仓库。判断发布与否只用 `content.is_published`，不要在别处另写一套。
- 网址前缀写在 `LAYOUT` 的 `Stage` 里（`thoughts`、`drafts`、`blog`、`opus`），新增阶段或一级文件夹必须在那里登记，否则报 `E_URL_SECTION_MISSING`。slug 只能用小写字母、数字和单个连字符，同一栏目内唯一；不写 slug 的页面按源文件路径生成 8 位短 ID，文件移动或改名后会变。
- `04博客` 的子文件夹各是一个系列，在 `content.SERIES` 里登记入口篇；出现没登记的子文件夹报 `E_SERIES_UNCONFIGURED`，入口篇不存在报 `E_SERIES_ENTRY_MISSING`。系列内顺序沿用 4.1.0 规则：入口篇在前，其余按组内链接最多的页面排序。
- **订阅教程旧链接**：`04博客/如何订阅claude（纯操作版）.md` 原来在 `/tech/subscribe-claude-quick/`，这个地址在视频里公开过。旧网址由 `tools/build_site.py` 的 `REDIRECTS` 跳转到 `/blog/subscribe-claude-quick/`，改文件名或 slug 时同步改 `REDIRECTS`，构建会检查跳转目标是否存在。
- 前端是自写的 Jinja2 模板（`theme/templates/`）加 `theme/assets/site.css`、`site.js`，站点配置在 `site.toml`。4.1.0 的 MkDocs + Material、`mkdocs.yml`、`overrides/`、`theme/extra.css`、`docs/javascripts/`、`tools/site_nav.py` 都已删除，不要再引入。
- 需求、技术方案和任务顺序见 `开发文档/`（术语在根目录 `CONTEXT.md`，决策记录在 `开发文档/adr/`）。设计文档、ADR、开发日志和 Agent 约定（`开发文档/agents/`）放 `开发文档/`，不要放进 `docs/`（那是 Obsidian 仓库，多出一级文件夹会让构建报错）；matt 流程的地图与任务放根目录 `.scratch/`；模板和站点脚本放 `theme/`，构建代码放 `tools/`，测试按模块命名为 `tests/test_<模块>.py`。

### 提交与合并

提交信息用中文，一句话说清改了什么，如“需求 R-UI-3：……”“同步订阅教程：……”。目前直接在 `main` 上提交并推送，推送即触发部署。

作者的 Obsidian 开着 Obsidian Git 自动备份，会定时把整个仓库的未提交改动一起提交（信息是 `vault backup: …`）并推送，推送即部署。改代码时尽快提交，别让改到一半的代码在工作区里停留太久；开工前和提交前都看一眼 `git log -3`，发现自己的改动已被自动备份带走时，在交付记录里写明对应的提交号。不要改 `docs/.obsidian/` 里的插件配置来关掉它。

### 写作语法

支持的 Obsidian 写法：页面双链和别名、`[[页面#标题]]` / `[[页面#^block-id]]` / `[[#标题]]`、表格里的转义双链 `[[目标\|别名]]`、图片嵌入及尺寸 `![[图片.png\|300x200]]`、`==高亮==`、内置 Callout 类型及别名、MathJax 公式。

暂不支持：页面嵌入、Callout 折叠标记、自定义 Callout 类型，遇到时报错并阻止构建。PDF 等非图片附件用普通 Markdown 链接。嵌入附件写 `![[09附件/图片.png]]`，不要写依赖目录深度的 `../` 相对路径。双链目标缺失、歧义、锚点不存在或语法未闭合时，构建给出文件和行号并停止。

### 构建与验证

- 需要 Python 3.13 以上，依赖见 `requirements.txt`（Jinja2、PyYAML 和 Markdown 转换用的库；仓库内 `.venv` 已就绪）。
- 验证命令：`.venv/bin/python -m unittest discover -s tests`，然后 `.venv/bin/python tools/build_site.py`；构建成功输出 `build succeeded: N pages published, M unpublished`，网站在 `site/`。诊断码以 `W_` 开头的只是提示，不影响退出码；`E_` 开头的会让构建失败。
- 本地预览用 `.venv/bin/python -m http.server -d site 8000`。工作区里的 `site/` 可能是旧构建，判断线上内容以 CI 产物为准，必要时重新构建。
- 不要在仓库里留下构建产物或临时副本：`site/`、`.cache/converted-docs/` 虽被忽略，但旧的 `site/` 会误导检查；需要试跑构建时复制到临时目录，跑完删除。`.cache/fonts/` 是下载好的源字体（约 19 MB），构建要用，不要删；缺了就运行 `.venv/bin/python -m tools.fetch_fonts` 重新下载。
- `python` 指向哪个解释器不确定，直接调用 `.venv/bin/python`。

### 编辑 README

README 的章节取舍由作者决定。曾经加进去、之后被作者删除的内容（分类表、Obsidian 语法表、本地构建步骤等）不要再加回去；需要补充的项目知识写进本节。

## Agent skills

研发流程用 matt 套件（`.claude/skills/`，setup-skills 安装，用法见总库 `dev/README.md`）：每个项目一次 `/wayfinder` 画地图，每个里程碑 `/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` ×N → `/closeout` → `/retro`；按需 `/arch`、`/research`、`/prototype`。技能里写的 `docs/agents/` 在本仓库对应 `开发文档/agents/`（`docs/` 是 Obsidian 仓库）。

### Issue tracker

本地 markdown，地图与任务都在 `.scratch/`，随 git 提交。见 `开发文档/agents/issue-tracker.md`。

### Domain docs

single-context：术语表是根目录 `CONTEXT.md`（不另建 `GLOSSARY.md`），ADR 在 `开发文档/adr/`。见 `开发文档/agents/domain.md`。

## 规则来源

- 同一层级只保留一个 `AGENTS.md`；`CLAUDE.md` 等只作入口，不复制正文，也不新建 `agent.md`、`AGENT.md`。
- 通用约定（上文沟通、执行、测试、工具）同步自作者的全局规则 `~/Workspace/Tools/AGENTS.md`；项目事实、历史决策和对外契约以本文件及 `开发文档/` 为准。
