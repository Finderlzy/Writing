# 实施计划

## 5.1.0 视觉改版

> 写于 2026-10-26，V0 已于同日完成。依据：[requirements.md §9](requirements.md)（R-VIS-1～7）、[architecture.md §7.1](architecture.md) 和 §14 的实施前评审、样稿 [设计样稿/5.1.0-首页与文章页.html](设计样稿/5.1.0-首页与文章页.html)。
> 沿用 5.0.0 的做法：不使用 GitHub Issues，任务状态记在本表；每个任务的正文按 Issue 模板写，需要时可以直接贴成 Issue。下面的命令都是计划中的验收方式，没有执行过。
> 推送 `main` 即部署。V1 推送后全站就换成新视觉，标题区先是简化版，V2～V4 逐页补齐；中间状态可以正常阅读，不需要长期分支。

### 首个可开工任务

**V1 全站视觉基础**，建议档位：强。V0 已完成（2026-10-26），字体方案和源字体存放方式已定稿，结论写在 [architecture.md §7.1](architecture.md) 的“字体”一段。开工前请作者看一眼 §7.1 里的“存放方式”，特别是本地构建要先跑一次 `fetch_fonts.py` 这一点。

### 任务一览

| ID | 任务 | 需求 | 依赖 | 档位 | 状态 |
| --- | --- | --- | --- | --- | --- |
| V0 | 验证：字体子集化的体积、构建时间和源字体存放方式 | R-VIS-5 | 可立即开工 | 强 | 已完成（结论见 architecture.md §7.1） |
| V1 | 全站视觉基础：配色、字体流水线、顶部栏和页脚、涂鸦、正文排版 | R-VIS-1、R-VIS-5～7 | V0 | 强 | 已完成（ab9fdfb） |
| V2 | 文章页标题区和文末 | R-VIS-3 | V1 | 标准 | 待细化 |
| V3 | 首页：气泡、大字、篇数、两条线、按月分组 | R-VIS-2 | V1 | 标准 | 待细化 |
| V4 | 全部文章和 404 | R-VIS-4 | V1 | 标准 | 待细化 |
| V5 | 整体验收与交付记录 | §9 验收表全部 | V2、V3、V4 | 标准 | 待细化 |

V2、V3、V4 都改 `site.css`、`render.py` 和模板，建议按 V2 → V3 → V4 串行；要并行就各用一个 worktree，按这个顺序合并。

检查点：V1 推送后作者在手机和桌面上看一眼新配色和字体；V2 做完再看一次文章页，确认后再做首页。

### V0 验证：字体子集化（已完成，2026-10-26）

**目标**：确定 R-VIS-5 的做法能不能成立。用真实内容验证四款字体按用到的字子集化成 woff2 后的体积、构建多花的时间，以及源字体放进仓库还是 CI 下载。结果写回 [architecture.md §7.1](architecture.md) 的“字体”一段，决定 V1 怎么做。这是验证任务，不改线上网站。

**涉及范围**：只在临时目录里试验；产物是 `开发文档/architecture.md` §7.1 的修改，以及（如果决定提交源字体）一份记录字体来源和许可的说明。不改 `tools/`、`theme/`、`requirements.txt`。

**依赖**：可立即开工

**建议档位**：强 — 未定的设计取舍：字体体积、源文件存放和依赖选择会决定 V1 的实现。

**结果摘要**（细节和表都在 [architecture.md §7.1](architecture.md) 的“字体”一段）：

- **体积**：四款字体五个 woff2 合计 **81.4 KB**（83,336 B），预算 300 KB，余量 223.8 KB。head（Noto Sans SC 固定到 wght=900）50,336 B，cute 2,512 B，slab 600/700 各 14.7/14.5 KB，hand 1,276 B。
- **耗时**：五个文件子集化单独计时 **0.62 秒**（含读源文件、写 woff2；三次重跑 0.97～1.00 秒，含解释器启动），远低于 10 秒线。
- **字形**：和在线字体一致。首页差 8.4% 的像素、文章页差 3.5%，差异主要在正文（正文不加载网络字体，机器上装的中文字体不同）；标题、大字、数字这些用到字体的地方，形状和在线字体一致。成功标准全部达到，不需要“head 只收首字 + 系统粗体”这条退路。
- **依赖**：`fonttools==4.67.0`、`brotli==1.2.1`（Python 3.14.4 全新虚拟环境实测）。
- **源字体**：google/fonts 提交 `e7db6ca603fd4862010383ff17ffd6cc4ffac1c0`，四个角色的文件名和仓库里的路径一致（`NotoSansSC[wght].ttf`、`ZCOOLKuaiLe-Regular.ttf`、`ZillaSlab-SemiBold.ttf`、`ZillaSlab-Bold.ttf`、`GochiHand-Regular.ttf`），五个文件的 SHA-256 已记在 §7.1 的表里。
- **存放方式（推荐）**：源字体不提交进仓库（提交要多 18.95 MB 且永久留在 git 历史里），改为 CI 按提交号固定的网址下载并校验 SHA-256；本地构建先跑一次 `tools/fetch_fonts.py`（下载到 `.cache/fonts/`）；下载或校验失败时构建 job 失败，线上维持上一版。
- **推翻的设想**：`FontSpec` 要支持一个角色多个文件（`weight`、`family`）和固定字（`text`）；head 必须“先子集化可变字体、再实例化到 900”，反过来慢 20 倍以上；子集化选项要写死（`name_IDs`、`layout_features`），否则 head 会多出 3～15 KB。

**验收**（2026-10-26 全部通过）：
- [x] `开发文档/architecture.md` §7.1 的“字体”一段写明：依赖及版本、源字体来源与 SHA-256、存放方式、实测体积和耗时
- [x] 试验用的临时目录已删除：虚拟环境、源字体、截图、本地 http.server 和 Chrome 临时配置都在仓库外的试验目录里，做完即删
- [x] 仓库里没有 `site/`、`.cache/` 或其他新产物，本次只提交两份文档

### V1 全站视觉基础

**目标**：把样稿的配色、字体、描边、涂鸦和正文排版铺到全站所有页面，标题区先用简化版（标题、日期、阶段、标签照现在的结构，只换样式）。推送后线上整站换成新视觉，内容和网址不变。对应 R-VIS-1、R-VIS-5、R-VIS-6、R-VIS-7。

**涉及范围**：`theme/assets/site.css`（整份重写）、`theme/templates/base.html`、`theme/templates/article.html`、`theme/templates/home.html`、`theme/templates/posts.html`、`theme/templates/404.html`（这几个只加 `data-font` 和类名，不改结构）、`tools/fonts.py`（新）、`tools/fetch_fonts.py`（新，按 V0 的结论）、`tools/render.py`（`build_pages` 调用 `subset_fonts`）、`requirements.txt`、`.github/workflows/deploy.yml`（加下载源字体和校验 SHA-256 的步骤）、`theme/fonts/OFL.txt` 与 `theme/fonts/README.md`（许可原文和来源记录，源字体本身不进仓库）、`tests/test_fonts.py`（新）、`tests/test_render.py`。

**依赖**：依赖 V0

**建议档位**：强 — 首个端到端切片，新增字体流水线这个跨模块接口（渲染层 → 字体模块 → 站点产物）。

**参照**：
- 视觉取值：样稿 `<style>` 里 `:root` 的变量、`.site-head`、`.brand`、`.site-nav`、`.chip`、`.neigh`、`.window`、`.foot` 和 `<svg>` 里的五个 `<symbol>`，直接搬，深色变量照抄。
- 接口：[architecture.md §7.1](architecture.md) 的 `FontSpec`、`collect_chars`、`subset_one`、`subset_fonts`，已按 V0 的实测改过：`FontSpec` 带 `text`、`weight`、`optional`、`family` 四个字段；head 先子集化可变字体、再实例化到 wght=900；子集化选项按 §7.1 “V0 改掉的三处设想”第 3 条写死。
- 现有结构：`base.html` 的顶部栏两项和页脚社交链接保持不变；`test_render.py` 第 186～223 行对首页顺序、顶部栏链接、资源路径的断言必须继续通过。
- 构建顺序：`render.build_pages` 里 `write_site` 之后、`check_site` 之前调用 `subset_fonts`。

**步骤**：

1. **字体流水线**（先做，独立可测）：`requirements.txt` 加 `fonttools==4.67.0`、`brotli==1.2.1`；写 `tools/fetch_fonts.py`（从提交号固定的地址下载五个源文件和四份 OFL.txt 到 `.cache/fonts/`，逐个校验 SHA-256）和 `tools/fonts.py`。`collect_chars` 用 `html.parser` 扫 `site/**/*.html`，收集带 `data-font` 属性的元素（含子元素）的文字；每个角色的固定字用 `FontSpec.text` 补上（数字 0～9、slab 的 ASCII、`docs/index.md` 第一段和导航文字）。边界用例：同一字出现在多个角色里各收一份；属性值不认识时报 `E_FONT_ROLE_UNKNOWN`；没有任何元素用到某角色时仍生成只含 `text` 字的文件，CSS 引用不会 404；源字体缺失报 `E_FONT_SOURCE_MISSING`；需要的字在源字体里没有时报 `W_FONT_GLYPH_MISSING`（交给字体栈兜底）；合计超过 300 KB 报 `W_FONT_BUDGET`。测试不联网，用安装包里 `fontTools` 自带的小字体文件（`fontTools.ttLib.TTFont` 能打开的那种）或仓库里放一个几十字的测试字体。
2. **样式和模板**：重写 `site.css`，`@font-face` 指向 `../fonts/<output>.woff2`（相对 `assets/theme/site.css`），`font-display: swap`，每个角色都有系统字体兜底。家族名要和 `:root` 里 CSS 变量引用的名字完全一致（V0 踩过：写成 `"Noto Sans SC Lzy"` 而变量写 `"Noto Sans SC"`，浏览器直接回退，截图看不出错）；两个 Zilla Slab 用同一个家族名加 `font-weight: 600/700`，名字和 `OS/2.usWeightClass` 由 `FontSpec.family`、`FontSpec.weight` 统一。`base.html` 加涂鸦 `<symbol>` 和站名旁的星星；各模板给标题、站名、日期、按钮等加 `data-font`。正文里的 `h2`～`h4`、代码块和复制按钮、表格、提示块（`.admonition`）、引用、图片、`mark`、目录、系列提示行都要有新样式；表格、代码块、公式各自横向滚动。
3. **深色和动效**：深色只改变量；`prefers-reduced-motion` 时关掉卡片悬停位移。

**验收**：
- [x] 测试：`.venv/bin/python -m unittest discover -s tests` 通过（97 个），含新的 `tests/test_fonts.py`（收字、子集化后的字体包含所需字形、缺源字体的诊断、超预算的提示）
- [x] 构建：先 `.venv/bin/python -m tools.fetch_fonts`，再 `.venv/bin/python tools/build_site.py`，输出 `build succeeded: 109 pages published, 20 unpublished`，`site/assets/fonts/` 下有 5 个 woff2（head 49,836 B、cute 2,112 B、slab-600 14,908 B、slab-700 14,480 B、hand 1,256 B），合计 82,592 B，预算 300 KB
- [x] 手工验证：桌面和 375/320/414px 下打开首页、全部文章、《黑框眼镜》、《三、把服务器变成节点》 → 配色、字体、描边与样稿一致；五个 woff2 都从本站加载（状态 200），页面里没有任何 Google Fonts 链接；教程的代码块能复制（按钮变“已复制”）、表格在容器内横向滚动；三档宽度下 `scrollWidth` 都等于视口宽，无横向滚动；关掉 JS 后四页正文和列表照常可读
- [x] 手工验证：模拟深色 → 上面四页没有看不清的文字或消失的边框（正文、标题、日期对比度 4.67～6.91，描边和投影都有颜色）

**做完后记**（2026-10-26，提交 `ab9fdfb`）：

- 验收里的“4 个 woff2”是笔误：本条验收线自己写的是 5 个，V0 实测也是四款字体五个文件（slab 600/700 各一个）。按 5 个交付，`tests/test_fonts.py` 里也断言了这五个文件名。
- `check_site` 在现有代码里并不存在（正文检查是 `write_site` 内部的逐页 `check_body`），所以子集化放在 `write_site` 返回之后。
- 源字体缺失时 `build_site.py` 会提示先跑 `python -m tools.fetch_fonts`；只想看页面可以用 `--skip-fonts`，标题退回系统字体，CI 不用这个开关。
- `.cache/fonts/` 里的源字体要在收尾时删掉，下次构建前重跑一次 `fetch_fonts`。
- `test_render.py` 没有改任何断言，只改了搭测试环境的那几行：`Workspace.build()` 改成调本类新加的 `build_pages()` 并传 `font_specs=None`，三处直接调 `build_pages` 的地方也补了这个参数。原因是 `build_pages` 默认会去 `.cache/fonts/` 找源字体，收尾删掉 `.cache/` 后这 17 个渲染测试会全部因 `E_FONT_SOURCE_MISSING` 失败。这些测试考的是模板、网址和诊断，不该依赖要联网下载的字体文件；字体子集化本身由 `test_fonts.py` 覆盖，它在源字体不在时整类跳过并说明怎么装（本机 97 个测试全过；删掉 `.cache/` 后 88 个通过、1 个跳过）。
- `site.js` 只删了 `pre` 上行的 `has-copy` 类（新 CSS 不再用它）。
- 模板只加了 `data-font` 和 `data-stage`/`data-stage-chip` 属性和类名，结构没动；深色只改 `:root` 变量。

### V2 文章页标题区和文末（待细化）

**目标**：做出样稿文章页的完整标题区和文末：淡色大字、读完时间黑圈、“讲了什么”对话框、阶段英文前缀、改于日期、跳过正文开头的日期引用块、文末涂鸦和“完”。对应 R-VIS-3。

**涉及范围**：`tools/content.py`（`Article.updated`）、`tools/render.py`（`giant_chars`、`strip_date_notes`、`reading_minutes`、`Page` 新字段）、`theme/templates/article.html`、`theme/assets/site.css`、`tests/test_content.py`、`tests/test_render.py`。

**依赖**：依赖 V1

**建议档位**：标准 — 接口已在 architecture.md §7.1 定好，照样稿实现。

**已知边界用例**（细化时补参照）：“黑框眼镜（作品）”→ 黑、眼镜；“CLANNAD~AFTER STORY~” → C、无第二个；“《棋王 树王 孩子王》” → 棋、子王；《CLANNAD》开头的 `>写于 2026-08-20` 没有空格、同一引用块里还有星级和“下一季”链接；操作版入口篇的引用块在日期行之后还有说明文字；没有 description 的文章。

**验收**：需求 §9 验收表里 R-VIS-3 的三行。

### V3 首页（待细化）

**目标**：做出样稿首页：气泡标题取 `docs/index.md` 第一段，右侧“想法”“灵感”大字，黑圈总数，两条线的卡片（阶段名链接到 `posts/?stage=…`），博客和作品按月分组。对应 R-VIS-2，R-UI-3 的内容规则不变。

**涉及范围**：`tools/content.py`（`stage_counts`）、`tools/render.py`（`split_home_intro`、首页按月分组的数据）、`theme/templates/home.html`、`theme/assets/site.css`、`tests/test_content.py`、`tests/test_render.py`。

**依赖**：依赖 V1（建议在 V2 之后）

**建议档位**：标准 — 照样稿和已定接口实现。

**验收**：需求 §9 验收表里 R-VIS-2 那一行；`test_render.py` 原有的首页断言继续通过。

### V4 全部文章和 404（待细化）

**目标**：全部文章页按月分组、筛选按钮按阶段着色；404 页有大号淡色“404”和两个入口。对应 R-VIS-4，筛选行为不变。

**涉及范围**：`theme/templates/posts.html`、`theme/templates/404.html`、`theme/assets/site.css`，按月分组如需数据则改 `tools/render.py`；`tests/test_render.py`。

**依赖**：依赖 V1（建议在 V3 之后，复用首页的按月分组）

**建议档位**：标准 — 复用 V3 的分组和 V1 的组件样式。

**验收**：需求 §9 验收表里 R-VIS-4 那一行；`test_render.py` 里筛选相关断言继续通过。

### V5 整体验收与交付记录（待细化）

**目标**：按需求 §9 的验收表逐条在桌面、375px、深色下验收全部页面，记录到 `开发文档/delivery.md`，在 `开发文档/DEVELOPMENT.md` 写 5.1.0 的开发日志。用 `project-delivery` 执行。

**依赖**：依赖 V2、V3、V4

**建议档位**：标准 — 按验收表逐条检查。

---

## 5.0.0 按阶段管理内容（已完成）

> 写于 2026-10-26。依据：[requirements.md](requirements.md)、[architecture.md](architecture.md)（第 13 节是实施前评审和过渡方案）、[CONTEXT.md](../CONTEXT.md)。
> 不使用 GitHub Issues，任务状态记在本文的“状态”一栏。一个里程碑一个任务，任务内的步骤按顺序做，每步结束时测试和旧构建都要保持通过。
> 下面列出的命令都是计划中的验收方式，没有执行过。

### 首个可开工任务

**T1 新流水线骨架**，建议档位：强。新开会话，用 `task-implement` 执行“开发文档/implementation-plan.md 的 T1”。

### 任务一览

| ID | 任务 | 需求 | 依赖 | 档位 | 线上网站 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 新流水线骨架：预览构建生成文章页 | R-PUB-1～3、R-PUB-5 | 可立即开工 | 强 | 不变 | 已完成（`f860518`） |
| T2 | 读者页面：首页、全部文章、完整文章页、系列、跳转、版式 | R-UI-1～6、R-PUB-4 | T1 | 标准 | 不变 | 已完成 |
| T3 | 切换上线：清理、迁移、换流水线、删旧代码、验收 | R-STR-1～5、R-CLN-1～3、第 7 节全部 | T2 | 强 | 切换 | 已完成（`b2b8c63`、`6657f31`、`a57b8db`、`6ecae6e`） |

三个任务严格串行。T1、T2 只往仓库里加新模块，线上仍由 4.1.0 的 `build_site.py` 构建；T3 才动内容和线上网站。

检查点：T1 结束时作者打开一次预览站点确认方向；T2 结束时作者在手机和桌面上过一遍全部页面，再开始 T3。

### T1 新流水线骨架：预览构建生成文章页

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

**验收**（2026-10-26 全部通过）：
- [x] 测试：`.venv/bin/python -m unittest discover -s tests`，79 个测试通过
- [x] 旧构建输出不变：第 1 步前后各跑一次 `.venv/bin/python tools/build_site.py`，两次都是 `269 pages published, 14 unpublished`，`site/` 各 775 个文件，`diff -r` 无差异
- [x] 预览构建：`.venv/bin/python tools/preview_v5.py <临时目录>` 退出码 0，生成 108 个文章页（博客 66、思考 35、初稿 2、作品 5）和 116 个资源文件
- [x] 手工验证：用 `python -m http.server` 打开《CLANNAD》：双链 `../606b2865/`、`../9713cd15/` 都返回 200 且指向对应文章，页内 `#_1` 等锚点存在，图片 `assets/09附件/DM_20260821120227_001.webp` 返回 200 `image/webp`；临时目录里没有 `00收集`、`01系统`、`02笔记`、`07自己`、`09归档` 任何目录
- [x] 验收后删除临时目录和 `site/`

### T2 读者页面

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

**验收**（2026-10-26 全部通过，提交 `167d55a`）：
- [x] 测试：`.venv/bin/python -m unittest discover -s tests`，92 个测试通过
- [x] 构建：`.venv/bin/python tools/preview_v5.py <临时目录>` 退出码 0，111 个页面（108 篇文章 + 首页 + 全部文章 + 跳转页）；`.venv/bin/python tools/build_site.py` 仍是 `269 pages published, 14 unpublished`
- [x] 手工验证：浏览器逐行走过需求第 7 节 R-UI-1～R-UI-6 共 14 条，全部符合；筛选“思考”+“二次元”剩 15 篇且都是思考，换成没有结果的组合显示提示；长文有 34 项目录、代码块复制把内容真的写进剪贴板、Giscus 以 `pathname` 加载；从入口篇顺着“下一篇”走完 19 篇系列，最后一篇给出回目录的链接
- [x] 跳转：`/tech/subscribe-claude-quick/` 跳到 `/blog/subscribe-claude-quick/`，查询参数和锚点保留
- [x] 版式：375px 和 1280px 下首页、全部文章页、文章页都是单栏、无左侧导航树、`scrollWidth == clientWidth`；抽查 40 篇文章（含 11 张宽表格）在 375px 下无横向滚动；深色跟随系统
- [ ] 作者检查点：作者在手机和桌面上看过预览站点并同意进入 T3
- [ ] 验收后删除临时目录和 `site/`

**作者检查预览的方法**（仓库里执行）：

```
.venv/bin/python tools/preview_v5.py preview-t2
.venv/bin/python -m http.server -d preview-t2 8765
```

然后打开 `http://127.0.0.1:8765/`。手机在同一局域网里访问 `http://<电脑的局域网地址>:8765/`。
要看的页面：`/`（首页）、`/posts/`（全部文章，点“思考”和“二次元”看筛选）、`/blog/subscribe-claude/`（长文：目录、上下篇、复制按钮、评论）、`/thoughts/05af6b0e/`（从首页或全部文章点进去的代表作）、`/tech/subscribe-claude-quick/`（应跳到 `/blog/subscribe-claude-quick/`）；随便打开一个不存在的地址看 404 页。
`preview-t2/` 已在 `.gitignore` 里，看完直接删掉即可。

### T3 切换上线

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
- [x] 测试：`.venv/bin/python -m unittest discover -s tests` —— 82 个测试通过
- [x] 构建：`.venv/bin/python tools/build_site.py` 输出 `build succeeded: …`，没有双链目标缺失 —— `build succeeded: 109 pages published, 20 unpublished`，只有 `W_MATHJAX_UNUSED` 一条提示（公开发布的页面里没有公式）
- [x] 内容不丢：对比迁移前后除 `02笔记`、`09归档` 以外的 `.md` 文件，数量相同，内容只在链接处有变化 —— 122 个文件对 95 个完全一致、24 个只改链接，3 个另有改动且都是第 1 步把指向已删页面的双链改成纯文字造成的
- [x] 线上验收：推送后等 GitHub Actions 部署完成，在线上逐行走需求第 7 节全部验收，包括访问 `/tech/subscribe-claude-quick/` —— 部署 run `40286735629` 成功，第 7 节逐条通过
- [x] 删除本次的临时目录和 `site/`