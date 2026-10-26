# 实施计划：5.0.0

> 写于 2026-10-26。依据：[requirements.md](requirements.md)、[architecture.md](architecture.md)（第 13 节是实施前评审和过渡方案）、[CONTEXT.md](../CONTEXT.md)。
> 不使用 GitHub Issues，任务状态记在本文的“状态”一栏。一个里程碑一个任务，任务内的步骤按顺序做，每步结束时测试和旧构建都要保持通过。
> 下面列出的命令都是计划中的验收方式，没有执行过。

## 首个可开工任务

**T1 新流水线骨架**，建议档位：强。新开会话，用 `task-implement` 执行“开发文档/implementation-plan.md 的 T1”。

## 任务一览

| ID | 任务 | 需求 | 依赖 | 档位 | 线上网站 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 新流水线骨架：预览构建生成文章页 | R-PUB-1～3、R-PUB-5 | 可立即开工 | 强 | 不变 | 待开始 |
| T2 | 读者页面：首页、全部文章、完整文章页、系列、跳转、版式 | R-UI-1～6、R-PUB-4 | T1 | 标准 | 不变 | 待开始 |
| T3 | 切换上线：清理、迁移、换流水线、删旧代码、验收 | R-STR-1～5、R-CLN-1～3、第 7 节全部 | T2 | 强 | 切换 | 待开始 |

三个任务严格串行。T1、T2 只往仓库里加新模块，线上仍由 4.1.0 的 `build_site.py` 构建；T3 才动内容和线上网站。

检查点：T1 结束时作者打开一次预览站点确认方向；T2 结束时作者在手机和桌面上过一遍全部页面，再开始 T3。

## T1 新流水线骨架：预览构建生成文章页

**目标**：新流水线的第一个端到端切片。用真实内容（旧文件夹布局）在临时目录里构建出新版文章页：站内双链能点、锚点正确、图片显示，只有四个阶段的文章出现。线上网站不变。对应 R-PUB-1、R-PUB-2、R-PUB-3、R-PUB-5。

**涉及范围**：`tools/content.py`（新）、`tools/render.py`（新）、`tools/preview_v5.py`（新，T3 删除）、`tools/obsidian_compat/converter.py`、`tools/obsidian_compat/urls.py`、`tools/site_nav.py`、`tools/build_site.py`（只改调用方式）、`theme/templates/base.html`、`theme/templates/article.html`、`theme/assets/site.css`（新）、`site.toml`（新）、`requirements.txt`、`tests/test_content.py`（新）、`tests/test_render.py`（新）、`tests/test_compat.py`、`tests/test_urls.py`、`tests/test_site_nav.py`。

**依赖**：可立即开工

**建议档位**：强 — 首个端到端骨架，定下 `Catalog` 和 `write_site` 两个跨模块接口。

**步骤**：

1. **先重构，输出不变。** 新建 `tools/content.py`，放 `Stage`、`Layout`、`LAYOUT`、`is_published`、`read_meta`（接口见 [architecture.md §4.1](architecture.md)）。
   - `Converter.__init__(index, unpublished_paths)` 和 `is_unpublished`（`converter.py:127-132`，唯一使用处在 `converter.py:541`）改为 `Converter(index, is_published: Callable[[Path], bool] = lambda path: True)`；`test_compat.py:72` 用 `("私密",)` 的地方改成对应的函数。
   - `plan_page_urls(docs, pages, is_unpublished, sections)`（`urls.py:48`）改为 `plan_page_urls(docs, pages, is_published, prefix_of: Callable[[Path], str | None])`，`prefix_of` 返回 `None` 时照旧报 `E_URL_SECTION_MISSING`。
   - `front_matter_slug` 改为用 `content.read_meta` 取值，只自己扫描行号；删除 `site_nav.read_meta`，调用方改用 `content.read_meta`。
   - `build_site.py` 按 4.1.0 的规则（`UNPUBLISHED_PATHS`、`SECTION_SLUGS`）传入判断函数。
   - 边界用例：`slug: abc # note` 读成 `abc`；front matter 未闭合时读不到 slug（有意的行为变化，靠“输出不变”确认真实内容不受影响）；`Layout` 里同时有 `03思考` 和 `03思考/初稿` 时，`03思考/初稿/a.md` 属于后者；`index.md` 恒为公开。
2. **内容目录。** `Catalog.load` 读出全部文章（标题、阶段、日期、标签、简介），按 `createdDate` 从新到旧，缺日期的排最后并给出 `W_POST_DATE_MISSING`。日期和标签的解析搬用 `site_nav._as_date`、`_as_tags`。
3. **渲染和预览入口。** `render.write_site` 把每篇文章渲染成 `<阶段前缀>/<slug>/index.html`，站内 `.md` 链接改写成相对网址并保留锚点，只复制公开文章引用到的附件到 `assets/`。模板先只有最简单的 `base.html`、`article.html` 和一份基础样式。`tools/preview_v5.py <输出目录>` 用旧布局构建真实内容并跑 `check_site`，有诊断时以非零退出。
   - 旧布局：`Stage("03思考", "思考", "thoughts")`、`Stage("03思考/初稿", "初稿", "drafts")`、`Stage("04技术", "博客", "blog")`、`Stage("05作品", "作品", "opus")`，`series` 先留空。
   - `write_site` 的 `urls` 用 `plan_page_urls` 的结果（键是源路径的 POSIX 字符串）；改成 `Path` 键时同步改架构文档。
   - Markdown 扩展照搬 `mkdocs.yml` 的 `markdown_extensions`，另加 `toc`、`tables`、`fenced_code`。
   - `requirements.txt` 显式加入 `Jinja2==3.1.6`、`PyYAML==6.0.3`。
   - 边界用例：公开文章链接到不公开页面时显示纯文字；本页标题链接 `[[#标题]]`；附件文件名含空格和中文；`docs/index.md` 不生成文章页。

**验收**：
- [ ] 测试：`.venv/bin/python -m unittest discover -s tests`
- [ ] 旧构建输出不变：第 1 步前后各跑一次 `.venv/bin/python tools/build_site.py`，把 `site/` 分别复制到临时目录，`diff -r` 没有差异
- [ ] 预览构建：`.venv/bin/python tools/preview_v5.py <临时目录>` 退出码 0
- [ ] 手工验证：`.venv/bin/python -m http.server -d <临时目录> 8000`，打开《CLANNAD》→ 双链能点、目标正确，图片显示；临时目录里没有 `00收集`、`01系统`、`02笔记`、`07自己`、`09归档` 任何一篇的页面
- [ ] 验收后删除临时目录和 `site/`

## T2 读者页面

**目标**：在预览站点里做完读者能看到的全部页面，线上仍不变。对应 R-UI-1～R-UI-6 和 R-PUB-4 的跳转机制。开工前按 T1 落地的代码补全参照。

**涉及范围**：`tools/content.py`、`tools/render.py`、`tools/preview_v5.py`、`tools/build_site.py`（只加 `REDIRECTS`，旧构建暂不使用）、`theme/templates/`、`theme/assets/`、`site.toml`、`tests/test_content.py`、`tests/test_render.py`、`tests/test_urls.py`。

**依赖**：依赖 T1

**建议档位**：标准 — 接口已在 T1 定下，各页面按架构文档的规则填充，没有新的跨模块接缝。

**步骤**：

1. **首页与顶部栏**（R-UI-2、R-UI-3）：`home.html`；顶部栏只有站名、“首页”“全部文章”；`Catalog.home()`；作者的话来自 `docs/index.md`；末尾“全部文章”入口。
2. **全部文章页**（R-UI-4）：`/posts/`、`posts.html`；`site.js` 按阶段和标签筛选，读写 `stage`、`tag` 查询参数，空结果时提示；没有 JS 时列表全部可见。
3. **文章页**（R-UI-5）：日期、阶段、标签；二、三级标题合计 ≥ 3 时显示目录；同阶段按日期的上一篇 / 下一篇；Giscus（参数从 `mkdocs.yml` 的 `extra.giscus` 搬到 `site.toml`）；代码复制按钮；只在有公式的页面加载 MathJax `3.2.2`。
4. **系列博客**（R-UI-6，架构 §6）：`Layout.series`（预览用 `04技术/原理版`、`04技术/操作版`）；`E_SERIES_UNCONFIGURED`、`E_SERIES_ENTRY_MISSING`、`E_STAGE_SUBFOLDER`；阅读顺序沿用 `site_nav._reading_order`；文章页的系列导航；全部文章页标出系列名；首页排除系列子文件夹里的文章。
5. **跳转页与 404**（R-PUB-4，架构 §5）：`REDIRECTS` 解析目标网址；`E_REDIRECT_TARGET_MISSING`、`E_REDIRECT_CONFLICT`；`404.html`。
6. **版式**（R-UI-1、第 6 节手机优先）：参考刘未鹏博客的单栏版式；375px 下三种页面无横向滚动，表格、公式、代码块在容器内滚动；`prefers-color-scheme` 深色。

**验收**：
- [ ] 测试：`.venv/bin/python -m unittest discover -s tests`
- [ ] 构建：`.venv/bin/python tools/preview_v5.py <临时目录>` 退出码 0；`.venv/bin/python tools/build_site.py` 仍然成功
- [ ] 手工验证：在预览站点上逐行走需求第 7 节 R-UI-1～R-UI-6 的验收；访问 `/tech/subscribe-claude-quick/` → 跳到 `/blog/subscribe-claude-quick/`；浏览器在 375px 和桌面宽度下检查首页、全部文章页、文章页
- [ ] 作者检查点：作者在手机和桌面上看过预览站点并同意进入 T3
- [ ] 验收后删除临时目录和 `site/`

## T3 切换上线

**目标**：内容迁移到新文件夹，线上换成新网站，删除旧流水线，完成 5.0.0 的验收和记录。对应 R-STR-1～R-STR-5、R-CLN-1～R-CLN-3、R-PUB-1、R-PUB-2、R-PUB-4，以及需求第 7 节全部验收。开工前按 T2 落地的代码补全参照。

**涉及范围**：`docs/`（移动、删除、改链接，不改正文）、`docs/01系统/分类标准.md`、`scripts/setup.sh`（删除）、`tools/`、`theme/`、`tests/test_repository.py`、`mkdocs.yml`、`overrides/`、`docs/javascripts/`、`requirements.txt`、`AGENTS.md`、`开发文档/DEVELOPMENT.md`。

**依赖**：依赖 T2

**建议档位**：强 — 内容迁移和删除，涉及线上切换。

**开始前**：请作者关掉 Obsidian 或暂停 Obsidian Git，确认 `main` 已同步；每次推送后请作者在 Obsidian 里拉取。

**步骤**：

1. **清理**（R-CLN-1～R-CLN-3），可以单独推送：删除 `docs/02笔记`、`docs/09归档`、只被它们引用的附件和 `scripts/setup.sh`；其他页面指向被删页面的双链改成纯文字，保留显示文字；`build_site.py` 去掉 `NAV_NOTES` 和这两个文件夹的前缀；`AGENTS.md` 去掉 `setup.sh` 的说明。删除前把附件清单和改写的双链清单写进提交说明。推送后线上的笔记随之消失，其余不变。
2. **迁移并切换**（R-STR-1～R-STR-5、R-PUB-1、R-PUB-2、R-PUB-4），必须是一次提交：`git mv` 迁移到新文件夹并合并 `00收集/灵感`；改写双链；重写 `docs/01系统/分类标准.md`；`build_site.py` 改用 `content.LAYOUT`、`SERIES` 改成 `04博客/…` 和新渲染层；`tests/test_repository.py` 加结构检查（架构 §10）；更新 `AGENTS.md` 的“项目说明”。
3. **删除旧流水线**（架构 §8）：`mkdocs.yml`、`overrides/`、`theme/extra.css`、`docs/javascripts/`、`tools/site_nav.py`、`tools/preview_v5.py`、`PageUrlPlugin`、`renamed_folder_redirects`、`requirements.txt` 里的 `mkdocs` 和 `mkdocs-material`，以及对应的测试。
4. **记录**：`开发文档/DEVELOPMENT.md` 写 5.0.0 条目（不兼容：文件夹、网址、前端）；把 README 过时段落的清单（架构 §12）交给作者。

**验收**：
- [ ] 测试：`.venv/bin/python -m unittest discover -s tests`
- [ ] 构建：`.venv/bin/python tools/build_site.py` 输出 `build succeeded: …`，没有双链目标缺失
- [ ] 内容不丢：对比迁移前后除 `02笔记`、`09归档` 以外的 `.md` 文件，数量相同，内容只在链接处有变化
- [ ] 线上验收：推送后等 GitHub Actions 部署完成，在线上逐行走需求第 7 节全部验收，包括访问 `/tech/subscribe-claude-quick/`
- [ ] 删除本次的临时目录和 `site/`
