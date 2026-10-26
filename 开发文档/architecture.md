# 架构：5.0.0 读者网站

> 写于 2026-10-26，状态：**定稿，待实施**。需求见 [requirements.md](requirements.md)，术语见 [CONTEXT.md](../CONTEXT.md)，复用调研见 [reuse-research.md](reuse-research.md)，关键决策见 [adr/0001-drop-mkdocs.md](adr/0001-drop-mkdocs.md)。
>
> 标注沿用需求文档：【选定】是需求授权后由架构阶段选定的方案，可以推翻。凡写“计划”的文件、函数和命令目前还不存在；现状是 4.1.0。

## 1. 总体方案

构建仍是一条 Python 流水线，在 GitHub Actions 里跑，产物发布到 GitHub Pages，托管方式不变。变化在后半段：MkDocs 和 Material 主题整体去掉，换成项目自己的渲染层，只生成首页、全部文章、文章页和跳转页四种页面。【选定，理由见 ADR-0001】

```mermaid
flowchart LR
  D[docs/ 只读] --> IX[VaultIndex 扫描]
  IX --> CV[Converter 转换与检查]
  IX --> CT[Catalog 文章目录]
  CT --> U[plan_page_urls 网址]
  CV --> R[Renderer 渲染 HTML]
  CT --> R
  U --> R
  R --> S[site/]
  S --> HC[check_site 链接检查]
```

## 2. 技术栈与运行

| 项 | 选择 | 说明 |
| --- | --- | --- |
| 语言 | Python ≥ 3.13（CI 固定 3.13.15，本地 `.venv` 是 3.14） | 沿用 |
| Markdown | Python-Markdown 3.10 + pymdown-extensions 11 | 沿用；扩展：`toc`、`admonition`、`attr_list`、`nl2br`、`sane_lists`、`tables`、`fenced_code`、`pymdownx.arithmatex`（generic） |
| 模板 | Jinja2 3.1 | 现在是 MkDocs 的间接依赖，改为直接写进 `requirements.txt` |
| front matter | PyYAML 6 | 同上，改为直接依赖 |
| 公式 | MathJax 3，固定版本（计划 `mathjax@3.2.2`），只在含公式的文章页加载 | 现在是不带版本号的 unpkg 链接 |
| 评论 | Giscus，`data-mapping="pathname"` | 沿用参数；只在文章页出现 |
| 部署 | `.github/workflows/deploy.yml`：测试 → 构建 → 上传 `site/` → Pages | 工作流不用改，变的只是 `requirements.txt` |

去掉的依赖：`mkdocs`、`mkdocs-material`。不引入 Node、打包工具或 CSS 框架；样式一个 CSS 文件，脚本一个原生 JS 文件。

## 3. 复用决策

- **复用自己的转换层**：`tools/obsidian_compat` 的扫描、转换、行号诊断、网址分配、HTML 检查全部保留，这是需求第 6 节“构建失败要说清楚”和 R-PUB-3 的基础。上游版本即本仓库 4.1.0。
- **复用库**：Python-Markdown（含 `toc` 的标题锚点规则，`slug.py` 已与之对齐，订阅教程里的中文锚点不会变）、pymdown-extensions、Jinja2、PyYAML。
- **不复用框架**：Quartz、Zensical、obsidian-export 都只作参考，原因见调研记录。
- **自己写的部分**：内容目录 `Catalog`、渲染层 `Renderer`、四个模板、样式和脚本。

## 4. 模块

按依赖方向从下到上。每个模块只列调用方需要知道的接口。

### 4.1 发布范围与内容目录 `tools/content.py`（计划，取代 `tools/site_nav.py`）

一个深模块，回答“哪些是文章、它们是什么、怎么排”。其他模块不再自己判断是否公开，也不再自己读 front matter。4.1.0 里“是否公开”在转换器、发布计数、附件规则和测试里各写了一遍，slug 用正则读、其他元数据用 YAML 读，两者对同一份 front matter 会给出不同结果，这一版都收进这个模块。

```python
@dataclass(frozen=True)
class Stage:
    folder: str             # 文件夹路径前缀，如 "02思考"；按最长前缀匹配，所以也可以是 "03思考/初稿"
    name: str               # 思考 / 初稿 / 博客 / 作品
    prefix: str             # 网址前缀 thoughts / drafts / blog / opus

@dataclass(frozen=True)
class Layout:               # 文件夹与阶段的对应，加上系列配置
    stages: tuple[Stage, ...]
    series: dict[str, str]  # 系列子文件夹 → 入口篇，见 §6

LAYOUT: Layout              # 5.0.0 的正式对应：02思考、03初稿、04博客、05作品
HOME_PAGE = Path("index.md")

def is_published(path: Path, layout: Layout = LAYOUT) -> bool   # 唯一的“是否公开”判断：属于某个阶段的 .md，或首页
def read_meta(text: str) -> dict          # 唯一的 front matter 解析（YAML）；坏 front matter 返回 {}

@dataclass(frozen=True)
class Article:
    source_path: Path
    stage: Stage
    title: str              # front matter 的 title，没写就用文件名
    date: date | None       # createdDate
    tags: tuple[str, ...]
    description: str
    series: str | None      # 所属系列名（入口篇标题）；入口篇自己也属于系列
    url: str = ""           # 站内网址，由渲染层按 urls 填好再交给模板（T2 加）

class Catalog:
    @classmethod
    def load(cls, docs: Path, pages: Iterable[Path], layout: Layout = LAYOUT) -> tuple["Catalog", list[Diagnostic]]
    articles: tuple[Article, ...]           # 全部文章，createdDate 从新到旧，无日期的排最后（W_POST_DATE_MISSING）
    def home(self) -> tuple[Article, ...]   # 不在系列子文件夹里的博客 + 全部作品，同样排序（R-UI-3、R-UI-6）
    def neighbours(self, a: Article) -> tuple[Article | None, Article | None]   # 上一篇、下一篇
    def series(self, a: Article) -> tuple[Article, ...]                        # a 所在系列的阅读顺序，不在系列里时为空
    def entry_of(self, folder: str) -> Article | None                          # 系列的入口篇
    def article(self, source_path: Path) -> Article | None

def series_diagnostics(docs: Path, pages: Iterable[Path], layout: Layout = LAYOUT) -> list[Diagnostic]
    # E_STAGE_SUBFOLDER / E_SERIES_ENTRY_MISSING / E_SERIES_UNCONFIGURED，见 §6
```

规则：

- **阶段**只由一级文件夹决定（R-STR-1）。`stage` 是 `Article` 的必填字段，模板直接用 `stage.name` 显示。
- **上一篇 / 下一篇**：系列里的文章按系列阅读顺序；其他文章在同一阶段内按 `createdDate`，“上一篇”是更早的一篇。【选定】
- **系列**：见 §6。
- **坏 front matter**：`_read_article` 里再解析一次 YAML（`_strict_meta`），解析不了报 `E_FRONT_MATTER_INVALID` 并停止；`read_meta` 本身仍对坏数据返回 `{}`，供只需要容错的调用方（转换层取 slug）使用。
- **阶段按最长前缀匹配，诊断里也一样**：`E_STAGE_SUBFOLDER` 只对“最具体的那个阶段”的页面报警，否则预览用旧布局时 `03思考/初稿` 下的两篇初稿会被算成“思考的子文件夹”。`E_SERIES_ENTRY_MISSING` 只要求入口篇在它**所属阶段的根目录**（正式布局 `04博客/`，预览的旧布局 `04技术/`），不要求它在系列文件夹里。`E_SERIES_UNCONFIGURED` 对每个真实的顶层子文件夹只报一次。
- **`W_` 开头的诊断只提示**：`build_pages` 遇到警告照常写完站点，只有错误才提前返回。`W_POST_DATE_MISSING` 让缺日期的文章排在最后（R-UI-4）；`W_MATHJAX_UNUSED` 是一篇带公式的公开文章都没有时的自检提示。
- **系列文件夹里可能还有一份作者手写的目录页**（如 `04技术/原理版/如何订阅claude.md`），它也是系列成员，但系列顺序从 `Layout.series` 登记的入口篇开始。`series()` 按源路径去重，`_reading_order` 以入口篇为起点沿双链展开，没被链到的按文件名排最后。
- **`home()` 的口径**：属于某个阶段、且不在任何系列文件夹里的文章；`series()` 返回空元组表示不在系列里，模板用 `series[0].url` 指到入口篇。
- **标签按钮顺序**：`_tag_counts` 按篇数从多到少、同数按字典序，避免每次构建按钮顺序抖动。
- **配置**：`site.toml` 的 `[giscus]` 里 `repo`、`repo_id`、`category_id` 三项齐全时 `GiscusConfig.enabled` 为真，文章页才输出评论区脚本；`[[social]]` 每项 `name` + `url`，渲染在页脚。

### 4.2 Obsidian 转换层 `tools/obsidian_compat/`（已有，小改）

| 文件 | 接口 | 5.0.0 的变化 |
| --- | --- | --- |
| `index.py` | `VaultIndex.scan(docs)` → 页面、附件、标题锚点、块 ID | 不变 |
| `converter.py` | `Converter(index, is_published).convert(path, text)` → `ConversionResult(text, references, diagnostics)` | 构造参数从 `unpublished_paths` 改为 `content.is_published`；页面链接仍输出为指向目标 `.md` 的相对路径加锚点，由渲染层改写成网址 |
| `urls.py` | `plan_page_urls(docs, pages, is_published, prefixes)`；`write_redirects(site, redirects, site_url)`；`legacy_redirects(site, pairs, site_url)`（T2 加） | 删除 `PageUrlPlugin`、`renamed_folder_redirects` 和逐页中文路径跳转（不再保留旧网址）；`front_matter_slug` 改用 `content.read_meta` 取值，只额外定位行号 |
| `html_check.py` | `check_site(site, site_url)`；`check_body(site, page_url, body)` | 新增 `check_body`：只检查单页正文的链接、锚点和残留标记。T1 只生成文章页，模板里的站名和样式表指向尚未生成的页面，整站检查会在 T2 补齐页面后才用 |
| `parser.py`、`slug.py`、`models.py`、`diagnostics.py` | — | 不变 |

### 4.3 渲染层 `tools/render.py`

一个深模块：输入转换好的 Markdown 和目录，输出整个 `site/`。入口是 `write_site`，
扫描和转换在 `build_pages` 里完成后再交给它：

```python
def write_site(
    site: Path,
    catalog: Catalog,
    converted: Mapping[str, str],   # 公开页面的源路径（POSIX 字符串）→ 转换后的 Markdown
    urls: Mapping[str, str],        # 源路径（POSIX 字符串）→ 站内网址，如 "blog/subscribe-claude-quick/"
    attachments: Iterable[Path],    # 要复制的附件（只含公开文章引用的）
    config: SiteConfig,
    docs: Path,                     # 复制附件时读源文件
    index: VaultIndex,              # 查目标页面的标题锚点
    references: Mapping[str, list], # 源路径 → ConversionResult.references
    diagnostics: list[Diagnostic] | None = None,
    legacy: Iterable[tuple[str, str]] = (),   # 旧地址 → 现地址，交给 urls.legacy_redirects（T2 加）
) -> list[Diagnostic]

def build_pages(
    docs: Path,
    destination: Path,
    config: SiteConfig,
    layout: Layout = LAYOUT,
    legacy: Iterable[tuple[str, str]] = (),
) -> list[Diagnostic]
```

`write_site` 用 `urls.legacy_redirects(site, [(旧, 新)], site_url)` 写跳转页：地址先规整成 `/a/b/`，目标页面不存在报 `E_REDIRECT_TARGET_MISSING`，与已有页面冲突由 `write_redirects` 报 `E_REDIRECT_CONFLICT`。`Page` 带 `url`、`articles`、`previous`、`following`、`series`、`toc`、`tags`、`rows`、`comments`、`highlight_nav` 这些模板字段；`_context` 另给 `root`（到站点根目录的相对路径）、`mathjax`、`unit_separator`（列表项 `data-tags` 的分隔符，用不可见的 U+0001，因为主题标签里可能出现逗号）。所有页面都加载 `site.js`；MathJax 只在 `page.has_math` 的页面加载，判定依据是转换后 Markdown 里的 `$…# 架构：5.0.0 读者网站

> 写于 2026-10-26，状态：**定稿，待实施**。需求见 [requirements.md](requirements.md)，术语见 [CONTEXT.md](../CONTEXT.md)，复用调研见 [reuse-research.md](reuse-research.md)，关键决策见 [adr/0001-drop-mkdocs.md](adr/0001-drop-mkdocs.md)。
>
> 标注沿用需求文档：【选定】是需求授权后由架构阶段选定的方案，可以推翻。凡写“计划”的文件、函数和命令目前还不存在；现状是 4.1.0。

## 1. 总体方案

构建仍是一条 Python 流水线，在 GitHub Actions 里跑，产物发布到 GitHub Pages，托管方式不变。变化在后半段：MkDocs 和 Material 主题整体去掉，换成项目自己的渲染层，只生成首页、全部文章、文章页和跳转页四种页面。【选定，理由见 ADR-0001】

```mermaid
flowchart LR
  D[docs/ 只读] --> IX[VaultIndex 扫描]
  IX --> CV[Converter 转换与检查]
  IX --> CT[Catalog 文章目录]
  CT --> U[plan_page_urls 网址]
  CV --> R[Renderer 渲染 HTML]
  CT --> R
  U --> R
  R --> S[site/]
  S --> HC[check_site 链接检查]
```

## 2. 技术栈与运行

| 项 | 选择 | 说明 |
| --- | --- | --- |
| 语言 | Python ≥ 3.13（CI 固定 3.13.15，本地 `.venv` 是 3.14） | 沿用 |
| Markdown | Python-Markdown 3.10 + pymdown-extensions 11 | 沿用；扩展：`toc`、`admonition`、`attr_list`、`nl2br`、`sane_lists`、`tables`、`fenced_code`、`pymdownx.arithmatex`（generic） |
| 模板 | Jinja2 3.1 | 现在是 MkDocs 的间接依赖，改为直接写进 `requirements.txt` |
| front matter | PyYAML 6 | 同上，改为直接依赖 |
| 公式 | MathJax 3，固定版本（计划 `mathjax@3.2.2`），只在含公式的文章页加载 | 现在是不带版本号的 unpkg 链接 |
| 评论 | Giscus，`data-mapping="pathname"` | 沿用参数；只在文章页出现 |
| 部署 | `.github/workflows/deploy.yml`：测试 → 构建 → 上传 `site/` → Pages | 工作流不用改，变的只是 `requirements.txt` |

去掉的依赖：`mkdocs`、`mkdocs-material`。不引入 Node、打包工具或 CSS 框架；样式一个 CSS 文件，脚本一个原生 JS 文件。

## 3. 复用决策

- **复用自己的转换层**：`tools/obsidian_compat` 的扫描、转换、行号诊断、网址分配、HTML 检查全部保留，这是需求第 6 节“构建失败要说清楚”和 R-PUB-3 的基础。上游版本即本仓库 4.1.0。
- **复用库**：Python-Markdown（含 `toc` 的标题锚点规则，`slug.py` 已与之对齐，订阅教程里的中文锚点不会变）、pymdown-extensions、Jinja2、PyYAML。
- **不复用框架**：Quartz、Zensical、obsidian-export 都只作参考，原因见调研记录。
- **自己写的部分**：内容目录 `Catalog`、渲染层 `Renderer`、四个模板、样式和脚本。

## 4. 模块

按依赖方向从下到上。每个模块只列调用方需要知道的接口。

### 4.1 发布范围与内容目录 `tools/content.py`（计划，取代 `tools/site_nav.py`）

一个深模块，回答“哪些是文章、它们是什么、怎么排”。其他模块不再自己判断是否公开，也不再自己读 front matter。4.1.0 里“是否公开”在转换器、发布计数、附件规则和测试里各写了一遍，slug 用正则读、其他元数据用 YAML 读，两者对同一份 front matter 会给出不同结果，这一版都收进这个模块。

```python
@dataclass(frozen=True)
class Stage:
    folder: str             # 文件夹路径前缀，如 "02思考"；按最长前缀匹配，所以也可以是 "03思考/初稿"
    name: str               # 思考 / 初稿 / 博客 / 作品
    prefix: str             # 网址前缀 thoughts / drafts / blog / opus

@dataclass(frozen=True)
class Layout:               # 文件夹与阶段的对应，加上系列配置
    stages: tuple[Stage, ...]
    series: dict[str, str]  # 系列子文件夹 → 入口篇，见 §6

LAYOUT: Layout              # 5.0.0 的正式对应：02思考、03初稿、04博客、05作品
HOME_PAGE = Path("index.md")

def is_published(path: Path, layout: Layout = LAYOUT) -> bool   # 唯一的“是否公开”判断：属于某个阶段的 .md，或首页
def read_meta(text: str) -> dict          # 唯一的 front matter 解析（YAML）；坏 front matter 返回 {}

@dataclass(frozen=True)
class Article:
    source_path: Path
    stage: Stage
    title: str              # front matter 的 title，没写就用文件名
    date: date | None       # createdDate
    tags: tuple[str, ...]
    description: str
    series: str | None      # 所属系列名（入口篇标题）；入口篇自己也属于系列
    url: str = ""           # 站内网址，由渲染层按 urls 填好再交给模板（T2 加）

class Catalog:
    @classmethod
    def load(cls, docs: Path, pages: Iterable[Path], layout: Layout = LAYOUT) -> tuple["Catalog", list[Diagnostic]]
    articles: tuple[Article, ...]           # 全部文章，createdDate 从新到旧，无日期的排最后（W_POST_DATE_MISSING）
    def home(self) -> tuple[Article, ...]   # 不在系列子文件夹里的博客 + 全部作品，同样排序（R-UI-3、R-UI-6）
    def neighbours(self, a: Article) -> tuple[Article | None, Article | None]   # 上一篇、下一篇
    def series(self, a: Article) -> tuple[Article, ...]                        # a 所在系列的阅读顺序，不在系列里时为空
    def entry_of(self, folder: str) -> Article | None                          # 系列的入口篇
    def article(self, source_path: Path) -> Article | None

def series_diagnostics(docs: Path, pages: Iterable[Path], layout: Layout = LAYOUT) -> list[Diagnostic]
    # E_STAGE_SUBFOLDER / E_SERIES_ENTRY_MISSING / E_SERIES_UNCONFIGURED，见 §6
```

规则：

- **阶段**只由一级文件夹决定（R-STR-1）。`stage` 是 `Article` 的必填字段，模板直接用 `stage.name` 显示。
- **上一篇 / 下一篇**：系列里的文章按系列阅读顺序；其他文章在同一阶段内按 `createdDate`，“上一篇”是更早的一篇。【选定】
- **系列**：见 §6。
- **坏 front matter**：`_read_article` 里再解析一次 YAML（`_strict_meta`），解析不了报 `E_FRONT_MATTER_INVALID` 并停止；`read_meta` 本身仍对坏数据返回 `{}`，供只需要容错的调用方（转换层取 slug）使用。
- **阶段按最长前缀匹配，诊断里也一样**：`E_STAGE_SUBFOLDER` 只对“最具体的那个阶段”的页面报警，否则预览用旧布局时 `03思考/初稿` 下的两篇初稿会被算成“思考的子文件夹”。`E_SERIES_ENTRY_MISSING` 只要求入口篇在它**所属阶段的根目录**（正式布局 `04博客/`，预览的旧布局 `04技术/`），不要求它在系列文件夹里。`E_SERIES_UNCONFIGURED` 对每个真实的顶层子文件夹只报一次。
- **`W_` 开头的诊断只提示**：`build_pages` 遇到警告照常写完站点，只有错误才提前返回。`W_POST_DATE_MISSING` 让缺日期的文章排在最后（R-UI-4）；`W_MATHJAX_UNUSED` 是一篇带公式的公开文章都没有时的自检提示。
- **系列文件夹里可能还有一份作者手写的目录页**（如 `04技术/原理版/如何订阅claude.md`），它也是系列成员，但系列顺序从 `Layout.series` 登记的入口篇开始。`series()` 按源路径去重，`_reading_order` 以入口篇为起点沿双链展开，没被链到的按文件名排最后。
- **`home()` 的口径**：属于某个阶段、且不在任何系列文件夹里的文章；`series()` 返回空元组表示不在系列里，模板用 `series[0].url` 指到入口篇。
- **标签按钮顺序**：`_tag_counts` 按篇数从多到少、同数按字典序，避免每次构建按钮顺序抖动。
- **配置**：`site.toml` 的 `[giscus]` 里 `repo`、`repo_id`、`category_id` 三项齐全时 `GiscusConfig.enabled` 为真，文章页才输出评论区脚本；`[[social]]` 每项 `name` + `url`，渲染在页脚。

### 4.2 Obsidian 转换层 `tools/obsidian_compat/`（已有，小改）

| 文件 | 接口 | 5.0.0 的变化 |
| --- | --- | --- |
| `index.py` | `VaultIndex.scan(docs)` → 页面、附件、标题锚点、块 ID | 不变 |
| `converter.py` | `Converter(index, is_published).convert(path, text)` → `ConversionResult(text, references, diagnostics)` | 构造参数从 `unpublished_paths` 改为 `content.is_published`；页面链接仍输出为指向目标 `.md` 的相对路径加锚点，由渲染层改写成网址 |
| `urls.py` | `plan_page_urls(docs, pages, is_published, prefixes)`；`write_redirects(site, redirects, site_url)` | 删除 `PageUrlPlugin`、`renamed_folder_redirects` 和逐页中文路径跳转（不再保留旧网址）；`front_matter_slug` 改用 `content.read_meta` 取值，只额外定位行号 |
| `html_check.py` | `check_site(site, site_url)`；`check_body(site, page_url, body)` | 新增 `check_body`：只检查单页正文的链接、锚点和残留标记。T1 只生成文章页，模板里的站名和样式表指向尚未生成的页面，整站检查会在 T2 补齐页面后才用 |
| `parser.py`、`slug.py`、`models.py`、`diagnostics.py` | — | 不变 |

### 4.3 渲染层 `tools/render.py`

一个深模块：输入转换好的 Markdown 和目录，输出整个 `site/`。入口是 `write_site`，
扫描和转换在 `build_pages` 里完成后再交给它：

```python
def write_site(
    site: Path,
    catalog: Catalog,
    converted: Mapping[str, str],   # 公开页面的源路径（POSIX 字符串）→ 转换后的 Markdown
    urls: Mapping[str, str],        # 源路径（POSIX 字符串）→ 站内网址，如 "blog/subscribe-claude-quick/"
    attachments: Iterable[Path],    # 要复制的附件（只含公开文章引用的）
    config: SiteConfig,
    docs: Path,                     # 复制附件时读源文件
    index: VaultIndex,              # 查目标页面的标题锚点
    references: Mapping[str, list], # 源路径 → ConversionResult.references
 / `$…$`。

`build_pages` 负责 `VaultIndex.scan` → `Converter.convert`（全部公开页面）→ `plan_page_urls`
→ `Catalog.load`，收集要复制的附件后调用 `write_site`。预览入口和单元测试都走 `build_pages`。

内部负责：

- Markdown → HTML。先剥掉 front matter（4.1.0 由 MkDocs 的 `meta` 扩展做），再交给 Python-Markdown。指向 `.md` 的链接按 `ConversionResult.references` 里已解析的目标改写成相对网址并保留锚点；目标不在 `urls` 里（不公开或不存在）时只留文字。标题锚点用转换层同一套 slug 规则，标题没有 ASCII 字符时是 `_1`、`_2`。
- 嵌入的附件复制到 `assets/<原目录>/<原名>`，地址按当前页面深度写成相对路径，文件名含空格和中文时按百分号编码。
- 每篇文章用 `toc` 扩展产出的标题列表决定是否显示目录：二级和三级标题合计 ≥ 3 个时显示。【选定】
- 套模板写出 `index.html`、`posts/index.html`、每篇文章的 `<网址>/index.html`、`404.html`，复制 `theme/assets/` 和附件。
- 所有站内链接都写相对路径，站点在 `/Writing/` 子路径下和本地 `http.server` 下都能用。

`SiteConfig` 从根目录 `site.toml`（取代 `mkdocs.yml`）读取：站名、`site_url`、`theme` 目录。T1 只需这三项，社交链接、Giscus 参数和站点验证 meta 在 T2 加。T1 用 Jinja2 渲染模板，`requirements.txt` 已固定 `Jinja2==3.1.6`、`PyYAML==6.0.3`。

### 4.4 构建编排 `tools/build_site.py`（已有，重写后半段）

保留：清理 `.cache/` 与 `site/`、构建前后对 `docs/` 做哈希比对（`E_SOURCE_MUTATED`）、诊断统一输出、退出码（0 成功 / 1 内容问题 / 2 工具问题）、成功时打印 `build succeeded: N pages published, M unpublished`。

顺序：`VaultIndex.scan` → `Catalog.load` → 逐页 `Converter.convert`（全部页面都转换以检查双链，只保留公开页面的结果）→ `plan_page_urls` → 有诊断就停止 → `write_site` → 写跳转页 → `check_site`。

配置常量留在这个文件里：`REDIRECTS`（§5）；网址前缀由 `content.LAYOUT` 的各阶段给出，`plan_page_urls` 改为按阶段取前缀，不再用 `SECTION_SLUGS`。`UNPUBLISHED_PATHS`、`NAV_POSTS`、`NAV_NOTES`、`ARTICLES_INDEX`、`HOME_RECENT_POSTS`、`RENAMED_SECTIONS` 删除。

## 5. 网址与跳转

| 页面 | 网址 |
| --- | --- |
| 首页 | `/` |
| 全部文章 | `/posts/`；筛选状态写在查询参数里，如 `/posts/?stage=思考&tag=二次元`，可以分享 |
| 文章 | `/<阶段前缀>/<slug 或 8 位短 ID>/`，前缀：思考 `thoughts`、初稿 `drafts`、博客 `blog`、作品 `opus` |

- slug 规则和短 ID 算法沿用 4.1.0（R-PUB-5）。短 ID 由源文件路径算出，所以迁移后的文章网址会变，这是需求允许的。
- 系列子文件夹不进网址：`04博客/操作版/x.md` 是 `/blog/<slug>/`，slug 在整个阶段内唯一。
- **跳转页**只有一处配置：

  ```python
  REDIRECTS = {"tech/subscribe-claude-quick/": Path("04博客/如何订阅claude（纯操作版）.md")}
  ```

  构建时查出目标的新网址并写跳转页（沿用 `redirect_html`：`meta refresh` + `location.replace`，保留查询串和锚点）。目标不存在或未公开时报 `E_REDIRECT_TARGET_MISSING` 并停止；跳转地址与已有页面冲突时报 `E_REDIRECT_CONFLICT`（R-PUB-4）。这篇文章已有 `slug: subscribe-claude-quick`，新地址是 `/blog/subscribe-claude-quick/`。
  T2 的实现：`REDIRECTS` 声明在 `tools/build_site.py`（`{"tech/subscribe-claude-quick": "blog/subscribe-claude-quick"}`，不带首尾斜杠），4.1.0 的构建不读它，线上网址一字不变；`tools/preview_v5.py` 把它转成 `(旧, 新)` 列表传给 `build_pages`。T3 换流水线时 `build_site.py` 直接把这个字典交给 `write_site` 的 `legacy` 参数。

## 6. 系列博客

`04博客` 的子文件夹各是一个系列（R-STR-1、R-UI-6）。入口篇无法从链接可靠推断（例如《方案一断连后》链到原理版的篇数比入口篇还多），所以显式配置：【选定】

```python
SERIES = {
    "04博客/原理版": "04博客/如何订阅claude.md",
    "04博客/操作版": "04博客/如何订阅claude（纯操作版）.md",
}
```

- 系列名是入口篇的标题。入口篇在 `04博客` 根目录，出现在首页；子文件夹里的各篇只出现在全部文章页，并标出系列名。
- 阅读顺序：入口篇在前，然后是子文件夹里的文章，沿用 4.1.0 导航的排序规则（组内链接最多的页面在前，其余按它链接过去的顺序，没被链到的按文件名排在最后）。
- `04博客` 下出现没配置的子文件夹，或配置的入口篇不存在时，报 `E_SERIES_UNCONFIGURED` / `E_SERIES_ENTRY_MISSING` 并停止。其他阶段文件夹出现子文件夹时报 `E_STAGE_SUBFOLDER`。

## 7. 前端

单栏，正文最大宽度约 40em，字号和行距以中文长文阅读为准，装饰只有分隔线和灰色辅助文字，参考刘未鹏博客（R-UI-1）。颜色用 CSS 变量，`prefers-color-scheme: dark` 时切换深色（需求待决策项的默认值）。375px 下所有页面不出现横向滚动：表格、公式和代码块各自在容器内横向滚动。

| 模板（`theme/templates/`，计划） | 内容 |
| --- | --- |
| `base.html` | 顶部栏：站名（回首页）、“首页”“全部文章”两项（R-UI-2）；页脚：社交链接 |
| `home.html` | `docs/index.md` 渲染的作者的话；`Catalog.home()` 列表，每项标题、日期、阶段、简介；末尾“全部文章”入口；不放评论和筛选（R-UI-3） |
| `posts.html` | 全部文章列表，每项标题、日期、阶段、系列名、简介；阶段按钮和标签按钮两组筛选；结果为空时的提示（R-UI-4） |
| `article.html` | 标题、日期、阶段、标签、目录（条件显示）、正文、系列导航（所属系列与系列内下一篇）、上一篇 / 下一篇、Giscus（R-UI-5、R-UI-6） |
| `404.html` | “页面不存在”加回首页、全部文章的入口（R-PUB-4） |

脚本 `theme/assets/site.js`（计划）只做两件事，没有 JS 时页面照常可读：

- 全部文章页的筛选：读写 `stage`、`tag` 查询参数，两个条件同时满足才显示，空结果时显示提示。每项的阶段和标签由构建写在 `data-` 属性里。
- 代码块的复制按钮（`navigator.clipboard` 为主，`execCommand` 兜底）。

实现要点（T2）：筛选按钮和筛选结果摘要默认 `hidden`，由 `site.js` 显示，所以没有 JS 时按钮不出现、列表全部可见；查询参数里的阶段或标签对不上任何按钮时按“没筛选”处理；筛选状态用 `history.replaceState` 写回地址，可以分享。样式集中在 `theme/assets/site.css` 一个文件里，颜色走 CSS 变量，`prefers-color-scheme: dark` 时整体切换；MathJax 的读屏辅助层 `mjx-assistive-mml` 挪出排版流（否则会撑出横向滚动），行内公式和行间公式各自在容器内横向滚动。

去掉的前端内容：Material 主题与 `overrides/`、左侧导航树、站内搜索、不蒜子访问统计（`counter.js`，属于非目标）。`docs/javascripts/` 里的三个脚本移出 Obsidian 仓库（MathJax 配置并入 `site.js`）。

## 8. 目录结构

```text
docs/                         # Obsidian 仓库，构建只读（已有；一级文件夹按 R-STR-1 迁移）
site.toml                     # 计划：站点配置，取代 mkdocs.yml
tools/
├── build_site.py             # 已有：构建编排、SECTION_PREFIXES、REDIRECTS
├── content.py                # 计划：发布范围、front matter、Catalog、SERIES；取代 site_nav.py
├── render.py                 # 计划：Markdown → HTML、模板、写 site/
└── obsidian_compat/          # 已有：扫描、转换、网址、HTML 检查
theme/
├── templates/                # 计划：base / home / posts / article / 404
└── assets/                   # 计划：site.css（取代 extra.css）、site.js
tests/                        # 已有：单元测试 + 仓库级检查，按新模块改写
开发文档/                     # 需求、架构、调研、ADR、开发日志、交付记录
.github/workflows/deploy.yml  # 已有
```

删除（计划）：`mkdocs.yml`、`overrides/`、`theme/extra.css`、`docs/javascripts/`、`tools/site_nav.py`、`scripts/setup.sh`（R-CLN-3）。

放置规则：新的构建代码放 `tools/`，Obsidian 专有的处理放 `tools/obsidian_compat/`；模板和静态资源放 `theme/`，不放进 `docs/`；测试按被测模块命名为 `tests/test_<模块>.py`；设计文档放 `开发文档/`（不能放 `docs/`，那是 Obsidian 仓库）。

## 9. 生成物与版本

- 转换副本：`.cache/converted-docs/`。渲染层直接用内存里的结果，这个目录只为排错时能看到转换后的 Markdown。
- 网站：`site/`，附件复制到 `site/assets/`，保持 `09附件` 下的相对路径。
- 两者都已在 `.gitignore` 中，不提交。
- 版本号来源不变：`开发文档/DEVELOPMENT.md` 的开发日志和 README 的“当前版本”。这一版是 5.0.0（文件夹、网址和前端都不兼容）。

## 10. 内容迁移（M1、M2）的工程做法

迁移和清理是一次性的内容操作，不做成仓库里的脚本：

- 用 `git mv` 移动文件，保留历史；双链按新路径批量改写（`newLinkFormat: absolute`，双链都以一级文件夹开头，可以按前缀替换），改完用构建的双链检查确认没有目标缺失。
- 删除 `02笔记`、`09归档` 前，先用 `VaultIndex` 算出“只被它们引用的附件”和“指向它们的双链”，列表随提交说明一起留档（R-CLN-1、R-CLN-2）。
- `tests/test_repository.py` 增加结构检查：一级文件夹集合等于 R-STR-1 的表、阶段文件夹（`04博客` 除外）没有子文件夹、`09附件` 里没有不被引用的文件、`docs/` 里没有站点脚本。
- `docs/01系统/分类标准.md`、项目 `AGENTS.md` 的“项目说明”随迁移同步改写（三级边界 Always）。`docs/.obsidian/` 里 Inbox Filer 的配置如果写死了旧文件夹名，需要先问作者（Ask first）。

## 11. 验证

| 需求 | 自动化 | 手工 |
| --- | --- | --- |
| R-STR-1、R-STR-5、R-CLN-1、R-CLN-3 | `test_repository.py` 的结构检查；构建无 `E_LINK_MISSING` | 对比迁移前后的 `.md` 文件清单 |
| R-PUB-1、R-PUB-2 | `test_content.py`：`is_published` 边界；构建后检查 `site/` 只含四个阶段的文章，且不含任何不公开页面的标题 | — |
| R-PUB-3 | `check_site` 检查站内链接和锚点；`test_render.py` 覆盖链接改写和图片 | 打开《CLANNAD》 |
| R-PUB-4 | `test_urls.py`：跳转目标解析和冲突；构建后检查 `site/tech/subscribe-claude-quick/index.html` | 浏览器访问旧地址 |
| R-PUB-5 | `test_urls.py`：增删其他文章不改变已有网址 | — |
| R-UI-1～R-UI-6 | `test_content.py`：首页列表、排序、上下篇、系列；`test_render.py`：顶部栏两项、首页无思考/初稿、目录显示条件 | 在 375px 和桌面宽度下用浏览器检查三种页面、筛选和空结果提示、复制按钮、公式、评论区 |

命令沿用：`.venv/bin/python -m unittest discover -s tests`，然后 `.venv/bin/python tools/build_site.py`；本地预览 `.venv/bin/python -m http.server -d site 8000`。

## 12. 待定与留给作者的事项

- **README 过时内容**（README 由作者维护，Ask first）：5.0.0 落地后，以下段落不再准确，需要作者决定怎么改：开头的“MkDocs + Material”和“学习笔记”；“日常写作流程”的“移到对应文件夹”；“导航与思考列表”整节；“页面网址”里的中文路径跳转、`RENAMED_SECTIONS`、“不能动的链接”；“评论区与外链”里的 `mkdocs.yml`、`repo_url`、Material 图标；“仓库结构”整节。
- **系列的阅读顺序**沿用 4.1.0 规则，如果实施时发现某个系列的顺序不对，再考虑在 `SERIES` 里改为显式列出顺序。
- **深色模式**按需求默认跟随系统，不做手动切换。

## 13. 实施前评审（2026-10-26）

范围：沿 S1～S3 三个场景，对照需求第 3～7 节检查本文 §1～§12。只做了文档评审，没有运行任何新代码。结论：**通过，有三处修正已写回本文**，没有阻塞项。

| 发现 | 影响 | 处理 |
| --- | --- | --- |
| 推送 `main` 即部署，而 Obsidian Git 每 10 分钟自动提交、开机自动拉取。如果先迁移内容、后换前端，线上会有一段时间是旧前端配新文件夹，`SECTION_SLUGS` 缺项会让构建直接失败；在长期分支上迁移又会和作者在 `main` 上的写作冲突 | 阻塞迁移的顺序，不阻塞开工 | 改为 expand–contract（见下方“过渡方案”），已据此把 §4.1 的阶段配置改成可传入的 `Layout` |
| §4.1 的 `STAGES` 写成固定常量，新流水线在迁移前无法用真实内容试跑，前端只能在切换当天第一次见到真实文章 | 验收风险集中到最后一步 | 同上：`Layout` 按文件夹前缀匹配阶段，预览构建可以用旧文件夹布局 |
| `plan_page_urls` 现在按一级文件夹查前缀，旧布局下 `03思考/初稿` 要映射到 `drafts`，一级文件夹不够 | 预览构建的网址会错 | §4.4 改为按阶段取前缀 |

核对过、无需修改的点：发布范围改成白名单符合 Never 边界；`docs/` 只读由构建前后的哈希比对保证；R-PUB-4 的跳转在切换的同一次部署里生效；Inbox Filer 没有写死文件夹名（`docs/.obsidian/plugins/inbox-filer` 没有 `data.json`），它读分类标准，迁移时不需要改插件配置。

### 过渡方案

1. **并存**：新模块 `content.py`、`render.py`、`theme/templates/`、`theme/assets/` 先加进仓库，只被单元测试和一个临时预览入口 `tools/preview_v5.py`（计划）使用。预览入口用旧文件夹布局的 `Layout`（`03思考`→思考、`03思考/初稿`→初稿、`04技术`→博客、`05作品`→作品）把真实内容构建到指定的临时目录。线上仍由 4.1.0 的 `build_site.py` 构建，每一步推送都不改变线上网站。
2. **切换**：一次提交里完成文件夹迁移、清理、分类标准改写和 `build_site.py` 改用新流水线。开始前请作者关掉 Obsidian 或暂停 Obsidian Git，推送后再在 Obsidian 里拉取。
3. **收缩**：删除预览入口、MkDocs 相关的代码、配置、模板和依赖。