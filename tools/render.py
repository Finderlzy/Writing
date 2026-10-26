"""Render the site into a directory.

Pipeline: `VaultIndex` scans `docs/`, `Converter` rewrites Obsidian syntax,
`Catalog` decides what counts as an article, `plan_page_urls` assigns URLs, and
this module writes each article to `<stage prefix>/<slug>/index.html`. Only the
attachments referenced by published articles are copied to `assets/`.
"""

from __future__ import annotations

import posixpath
import re
import shutil
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from urllib.parse import quote, unquote

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .content import HOME_PAGE, LAYOUT, Article, Catalog, Layout, is_published, series_diagnostics
from .fonts import FontSpec, default_specs, subset_fonts
from .obsidian_compat.converter import Converter
from .obsidian_compat.index import VaultIndex
from .obsidian_compat.html_check import check_body
from .obsidian_compat.models import Diagnostic, SourceSpan
from .obsidian_compat.parser import residual_diagnostics
from .obsidian_compat.urls import legacy_redirects, plan_page_urls

MARKDOWN_EXTENSIONS = (
    "toc",
    "tables",
    "fenced_code",
    "attr_list",
    "admonition",
    "nl2br",
    "sane_lists",
    "pymdownx.arithmatex",
)
MARKDOWN_EXTENSION_CONFIGS = {"pymdownx.arithmatex": {"generic": True}}

ASSETS_DIR = "assets"
_THEME_ASSETS_DIR = "theme"
# 源文件里手写的普通 Markdown 链接指向的扩展名（双链已由 Converter 处理）
_PAGE_SUFFIXES = (".md", ".markdown")
_TOC_DEPTH = 3
_TOC_MIN_HEADINGS = 3
_MATH_RE = re.compile(r"\$[^$\n]+\$|\$\$")
_TAG_RE = re.compile(r"<[^>]*>")
_SPACE_RE = re.compile(r"\s+")
_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
# build_pages 的 font_specs 哨兵：没传时按 site/fonts.py 的四个角色子集化，
# 明确传 None 则跳过字体步骤（页面的标题退回系统字体，仍然可读）
_UNSET_FONT_SPECS: object = object()


@dataclass(frozen=True)
class SocialLink:
    """One entry of the footer: a name and where it goes."""

    name: str
    url: str


@dataclass(frozen=True)
class GiscusConfig:
    """The Giscus comment widget; `category_id` empty means no comments."""

    repo: str = ""
    repo_id: str = ""
    category: str = ""
    category_id: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.repo and self.repo_id and self.category_id)


@dataclass(frozen=True)
class SiteConfig:
    """What a build needs besides `docs/`: names, URLs, the theme folder and the widgets."""

    site_name: str = "Writing"
    site_url: str = "https://finderlzy.github.io/writing/"
    theme: Path = Path("theme")
    social: tuple[SocialLink, ...] = ()
    giscus: GiscusConfig = GiscusConfig()


@dataclass(frozen=True)
class Page:
    """One rendered HTML page."""

    url: str  # 输出目录内的相对网址目录，如 "blog/vless-reality/"
    title: str
    body: str = ""
    article: Article | None = None
    toc: tuple[dict, ...] = ()
    has_math: bool = False
    articles: tuple[Article, ...] = ()  # 首页和全部文章页的列表
    previous: Article | None = None
    following: Article | None = None
    series: tuple[Article, ...] = ()
    headings: bool = False  # 正文是否已经有标题
    highlight_nav: str = ""  # 顶部栏当前项："home" 或 "posts"
    comments: bool = False
    tags: tuple[str, ...] = ()  # 全部文章页的筛选按钮：全站出现过的主题标签，按篇数从多到少
    rows: tuple[dict, ...] = ()  # 全部文章页的列表项：每条文章和它的筛选数据
    giant: str = ""  # 标题后面垫的淡色大字，“黑”“C”；空串表示不画
    giant_second: str = ""  # 小一号的第二个大字，“眼镜”“子王”；空串表示没有
    minutes: int = 0  # 读完大约几分钟；0 表示没有正文（首页、全部文章页、404）
    headline: str = ""  # 首页气泡标题：docs/index.md 正文第一段
    stage_counts: dict[str, int] = field(default_factory=dict)  # 首页黑圈和两张卡片：阶段名 → 篇数
    total: int = 0  # 首页黑圈：公开文章总数，不是首页列表的条数
    months: tuple[tuple[int, int | None, tuple[Article, ...]], ...] = ()  # 列表的按月分组：首页是博客和作品，全部文章页是全部文章


def _toml_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_config(text: str) -> tuple[dict, list[SocialLink], GiscusConfig]:
    """A tiny TOML reader: `key = "value"` lines, `[[social]]` tables and a `[giscus]` table."""
    top: dict[str, str] = {}
    social: list[SocialLink] = []
    giscus: dict[str, str] = {}
    section = ""
    current: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[[") and line.endswith("]]"):
            if current.get("name") and current.get("link"):
                social.append(SocialLink(current["name"], current["link"]))
            current = {}
            section = line[2:-2].strip()
            continue
        if line.startswith("[") and line.endswith("]"):
            if section == "social" and current.get("name") and current.get("link"):
                social.append(SocialLink(current["name"], current["link"]))
                current = {}
            section = line[1:-1].strip()
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), _toml_value(value)
        if section == "social":
            current[key] = value
        elif section == "giscus":
            giscus[key] = value
        elif not section:
            top[key] = value
    if section == "social" and current.get("name") and current.get("link"):
        social.append(SocialLink(current["name"], current["link"]))
    widget = GiscusConfig(
        repo=giscus.get("repo", ""),
        repo_id=giscus.get("repo_id", ""),
        category=giscus.get("category", ""),
        category_id=giscus.get("category_id", ""),
    )
    return top, social, widget


def load_config(path: Path) -> SiteConfig:
    """Read `site.toml`: top-level `key = "value"` pairs, `[[social]]` tables and `[giscus]`."""
    top, social, giscus = _parse_config(path.read_text(encoding="utf-8"))
    return SiteConfig(
        site_name=top.get("site_name", SiteConfig.site_name),
        site_url=top.get("site_url", SiteConfig.site_url),
        theme=Path(top.get("theme", str(SiteConfig.theme))),
        social=tuple(social),
        giscus=giscus,
    )


def _markdown() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=list(MARKDOWN_EXTENSIONS),
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
    )


def _iter_tokens(tokens: Iterable[dict]) -> Iterable[dict]:
    for token in tokens:
        yield token
        yield from _iter_tokens(token.get("children") or [])


def _toc_tokens(tokens: Iterable[dict], depth: int = _TOC_DEPTH) -> tuple[dict, ...]:
    result: list[dict] = []
    for token in tokens:
        if token["level"] <= depth:
            result.append(dict(token, children=_toc_tokens(token.get("children") or [], depth)))
        else:
            result.extend(_toc_tokens(token.get("children") or [], depth))
    return tuple(result)


def _heading_count(toc: Iterable[dict]) -> int:
    return sum(1 + _heading_count(token["children"]) for token in toc)

def strip_front_matter(text: str) -> str:
    """Drop the leading front matter block; MkDocs' `meta` extension did this in 4.1.0."""
    match = _FRONT_MATTER_RE.match(text)
    return text[match.end():] if match else text


# 标题末尾的括号注释，如“黑框眼镜（作品）”的“（作品）”或 “标题(xxx)”；后面不能再有别的字
_TRAILING_NOTE_RE = re.compile(r"[（(][^（()）]*[)）]\s*\Z")
# 正文开头只写日期的引用行：`> 写于 2026-08-29`、`>更新于 2026-10-20`
_DATE_NOTE_RE = re.compile(r"[ \t]*>\s*(?:更新于|写于)\s*\d{4}-\d{1,2}-\d{1,2}\s*\Z")
_MINUTES_PER_CHAR = 400
# 首页开头的 <h1> 和第一个 <p>：气泡标题取第一段的纯文字，其余 HTML 是作者的话
_H1_RE = re.compile(r"<h1\b[^>]*>.*?</h1>\s*", re.DOTALL)
_P_RE = re.compile(r"<p\b[^>]*>(?P<inner>.*?)</p>", re.DOTALL)


def giant_chars(title: str) -> tuple[str, str]:
    """The big faded characters behind the article title: (main, second).

    The main character is the first letter (upper-cased) or Chinese character of the
    title, skipping punctuation and the trailing parenthetical note; the second is the
    last two characters when the title still has four or more after removing
    punctuation, and "" otherwise. A title of punctuation only gives ("", "").
    """
    title = _TRAILING_NOTE_RE.sub("", title)
    letters = [char for char in title if char.isalnum()]
    if not letters:
        return "", ""
    main = letters[0].upper()
    second = "".join(letters[-2:]) if len(letters) >= 4 else ""
    return main, second


def strip_date_notes(markdown: str) -> str:
    """Drop the "写于 / 更新于 日期" quote block at the top of the body; the source stays as it is.

    The title block already shows those dates. Only the opening quote region is
    touched: a block made of date lines (with blank lines between them) goes away
    as a whole; other blocks (star ratings, links, the note on the entry page) are
    left as they are; the walk stops at the first line that is neither blank nor a
    quote.
    """
    lines = markdown.split("\n")
    removed: set[int] = set()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
        elif line.startswith(">"):
            # 一块一块地看：整块只有日期就整块删，否则只删块里的日期行
            end = index
            while end + 1 < len(lines) and (not lines[end + 1].strip() or lines[end + 1].strip().startswith(">")):
                end += 1
            while end > index and not lines[end].strip():
                end -= 1
            if any(_DATE_NOTE_RE.match(lines[number].strip()) for number in range(index, end + 1)):
                removed.update(number for number in range(index, end + 1) if _DATE_NOTE_RE.match(lines[number].strip()))
            index = end + 1
        else:
            break
    return "\n".join(line for number, line in enumerate(lines) if number not in removed)


def reading_minutes(html: str) -> int:
    """How many minutes the body takes: non-space characters after removing tags / 400, at least 1."""
    text = _TAG_RE.sub("", html)
    return max(1, round(len(_SPACE_RE.sub("", text)) / _MINUTES_PER_CHAR))


def split_home_intro(html: str) -> tuple[str, str]:
    """Split the rendered `docs/index.md` into (bubble headline, author's words).

    The heading at the top ("首页") is not shown on the home page. The text of the
    first paragraph becomes the bubble headline; everything else stays the author's
    words. Without a heading at the top, or without a paragraph right after it,
    there is no headline and the rest is shown as the author's words.
    """
    body = html.lstrip()
    if not _H1_RE.match(body):
        return "", html  # 开头不是一级标题：整份都算作者的话，气泡里不画标题
    body = _H1_RE.sub("", body, count=1).lstrip()
    match = _P_RE.match(body)  # 只有紧跟标题的那一段才是气泡标题
    if match is None:
        return "", body
    headline = _TAG_RE.sub("", match.group("inner"))
    return _SPACE_RE.sub(" ", headline).strip(), body[: match.start()] + body[match.end() :]


def render_markdown(text: str) -> tuple[str, tuple[dict, ...]]:
    """Markdown (already converted from Obsidian) to HTML plus its heading tree.

    Heading ids follow Python-Markdown's `toc` rules, which is also what the converter
    assumes when it builds fragment links; a title without ASCII letters gets `_1`,
    `_2` and so on, never an empty id.
    """
    md = _markdown()
    body = md.convert(text)
    return body, _toc_tokens(getattr(md, "toc_tokens", ()))


def _anchor_for(index: VaultIndex, target: Path, anchor: str | None) -> str:
    """Turn a `#标题` anchor into the heading id of the page it points at."""
    if not anchor:
        return ""
    record = index.pages.get(target)
    heading = index.page_heading(record, anchor) if record is not None else None
    return "#" + quote(heading[1], safe="-._~^") if heading else ""


_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def _rewrite_page_links(
    text: str,
    url: str,
    urls: dict[str, str],
    index: VaultIndex,
    references: list,
) -> str:
    """Point Markdown links to other notes at that note's URL.

    The converter resolves the target of every link (that is what fills `references`)
    but leaves the link text as a `.md` path, because MkDocs used to resolve it.
    Each reference is matched by the file name it points at, so links with their own
    alias and anchor are rewritten too. Links to pages that are not published (or do
    not exist) lose the link and keep the text.
    """
    by_name: dict[str, list] = {}
    for reference in references:
        if reference.kind != "link":
            continue
        name = Path(reference.target).name + ".md"
        by_name.setdefault(name, []).append(reference)

    def replace(match: re.Match[str]) -> str:
        label, href = match.group(1), match.group(2)
        path, _, fragment = href.partition("#")
        candidates = by_name.get(posixpath.basename(unquote(path)), [])
        if not candidates:
            return match.group(0)
        reference = candidates[0]
        target_url = urls.get(reference.target + ".md") or urls.get(reference.target)
        if target_url is None:
            return label
        anchor = _anchor_for(index, Path(reference.target), reference.anchor)
        if not anchor and fragment:
            anchor = "#" + quote(fragment, safe="-._~^")
        relative = posixpath.relpath(target_url, posixpath.dirname(url) or ".")
        return "[" + label + "](" + quote(relative, safe="/-._~") + anchor + ")"

    return _MD_LINK_RE.sub(replace, text)



def _rewrite_embeds(text: str, source_path: Path, url: str, attachments: list[Path]) -> str:
    """Point embedded attachments at the copies written under `assets/`.

    The converter writes an embed as a path relative to the source folder
    (`../09%E9%99%84%E4%BB%B6/图.png`); the page needs it relative to its own URL.
    """
    prefix = posixpath.dirname(source_path.as_posix())
    for attachment in attachments:
        relative = posixpath.relpath(attachment.as_posix(), prefix or ".")
        href = quote(posixpath.relpath(_asset_url(attachment), posixpath.dirname(url) or "."), safe="/-._~()!$&*,;=:@")
        for written in {relative, quote(relative, safe="/-._~()!$&*,;=:@"), quote(relative, safe="/")}:
            text = text.replace(f"]({written})", f"]({href})")
            # 视频由转换层写成原始 HTML 的 <video src="...">，不走 Markdown 的图片语法
            text = text.replace(f'src="{written}"', f'src="{href}"')
    return text


def _copy_theme_assets(theme: Path, destination: Path) -> None:
    source = theme / "assets"
    if not source.is_dir():
        return
    for file in sorted(source.rglob("*")):
        if file.is_file():
            target = destination / ASSETS_DIR / _THEME_ASSETS_DIR / file.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)

def _environment(theme: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(theme / "templates")),
        autoescape=select_autoescape(("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _root(url: str) -> str:
    """The relative prefix that leads from page `url` back to the site root.

    根目录的页面（首页）本身就在站点根下，前缀是空串；站点根下的子目录才要往上一层。
    """
    depth = 0 if url.rstrip("/") == "" else url.rstrip("/").count("/") + 1
    return "../" * depth or "./"


def _href(from_url: str, to_url: str) -> str:
    """A link from one page of the site to another, always relative."""
    return quote(posixpath.relpath(to_url, posixpath.dirname(from_url.rstrip("/")) or "."), safe="/-._~") or "."


# 首页和全部文章页在站点根目录下的相对位置
HOME_URL = ""
POSTS_URL = "posts/"



def _tag_counts(articles: Iterable[Article]) -> tuple[str, ...]:
    """Every topic tag used by an article, most used first, ties by name."""
    counts: dict[str, int] = {}
    for article in articles:
        for tag in article.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return tuple(sorted(counts, key=lambda tag: (-counts[tag], tag)))


def _rows(articles: Iterable[Article]) -> tuple[dict, ...]:
    """One list row per article, with the values the filter reads back from `data-` attributes."""
    return tuple(
        {"article": article, "stage": article.stage.name, "tags": list(article.tags)}
        for article in articles
    )


_MONTH_NAMES = ("一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月")


def group_by_month(articles: Iterable[Article]) -> tuple[tuple[int, int | None, tuple[Article, ...]], ...]:
    """Group articles into (year, month, articles), keeping their order (newest first).

    Articles without a createdDate cannot be put in a month; they form one last group
    whose year and month are both None (the build already warned about them).
    """
    groups: dict[tuple[int, int] | None, list[Article]] = {}
    for article in articles:
        if article.date is None:
            groups.setdefault(None, []).append(article)
        else:
            groups.setdefault((article.date.year, article.date.month), []).append(article)
    dated = [key for key in groups if key is not None]
    return tuple((key[0], key[1], tuple(groups[key])) for key in dated) + (
        ((None, None, tuple(groups[None])),) if None in groups else ()
    )


def _context(config: SiteConfig, page: Page, url: str) -> dict:
    return {
        "site": config,
        "page": page,
        "url": url,
        "root": _root(url),
        "month_names": _MONTH_NAMES,
        "toc": page.toc if _heading_count(page.toc) >= _TOC_MIN_HEADINGS else (),
        "mathjax": page.has_math,
        "unit_separator": "\u0001",  # 列表项的 data-tags 用它拼多个主题标签
    }


def _render_template(environment: Environment, template: str, context: dict) -> str:
    html = environment.get_template(template).render(**context)
    return html if html.endswith("\n") else html + "\n"


def _asset_url(attachment: Path) -> str:
    return posixpath.join(ASSETS_DIR, attachment.as_posix())


def write_site(
    site: Path,
    catalog: Catalog,
    converted: dict[str, str],
    urls: dict[str, str],
    attachments: list[Path],
    config: SiteConfig,
    docs: Path,
    index: VaultIndex,
    references: dict[str, list],
    diagnostics: list[Diagnostic] | None = None,
    legacy: Iterable[tuple[str, str]] = (),
) -> list[Diagnostic]:
    """Write every page into `site`; return the diagnostics found on the way.

    Pages: the home page (the author's words from `docs/index.md` plus the blog and work
    list), the article list at `posts/`, one page per article and a `404.html`. `urls`
    maps source paths to article URLs, `attachments` lists the files public articles embed,
    `legacy` holds `(old address, new address)` redirects kept from earlier releases.
    """
    found: list[Diagnostic] = list(diagnostics or [])
    for attachment in attachments:
        target = site / _asset_url(attachment)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(docs / attachment, target)

    # 给每篇文章填上相对网址，列表页和上下篇链接才有地方可指
    catalog = replace(
        catalog,
        articles=tuple(replace(item, url=urls[item.source_path.as_posix()]) for item in catalog.articles if item.source_path.as_posix() in urls),
    )

    pages: list[Page] = []
    for article in catalog.articles:
        key = article.source_path.as_posix()
        url = urls[key]
        text = converted[key]
        text = _rewrite_embeds(text, article.source_path, url, attachments)
        text = _rewrite_page_links(text, url, urls, index, references.get(key, ()))
        # 标题区已经写了日期，正文开头那几行只写日期的引用块不再显示；源文件不动
        text = strip_date_notes(strip_front_matter(text))
        body, toc = render_markdown(text)
        previous, following = catalog.neighbours(article)
        giant, giant_second = giant_chars(article.title)
        # 公式在转换后的 Markdown 里保持原样（$...$ / $...$），渲染成 HTML 后也能看
        has_math = bool(_MATH_RE.search(strip_front_matter(text)))
        pages.append(
            Page(
                url=url,
                title=article.title,
                body=body,
                article=article,
                toc=toc,
                has_math=has_math,
                previous=previous,
                following=following,
                series=catalog.series(article),
                headings=bool(toc),
                comments=config.giscus.enabled,
                giant=giant,
                giant_second=giant_second,
                minutes=reading_minutes(body),
            )
        )

    home_html, _ = render_markdown(strip_front_matter(converted.get(HOME_PAGE.as_posix(), "")))
    headline, home_intro = split_home_intro(home_html)
    home_articles = catalog.home()
    pages.append(
        Page(
            url=HOME_URL,
            title=config.site_name,
            body=home_intro,
            headline=headline,
            articles=home_articles,
            stage_counts=catalog.stage_counts(),
            total=len(catalog.articles),  # 黑圈写的是公开文章总数，不是首页列表的条数
            months=group_by_month(home_articles),
            highlight_nav="home",
        )
    )
    pages.append(
        Page(
            url=POSTS_URL,
            title="全部文章",
            articles=catalog.articles,
            highlight_nav="posts",
            tags=_tag_counts(catalog.articles),
            rows=_rows(catalog.articles),
            # 全部文章页和首页共用按月分组；首页只装博客和作品，这里装全部公开文章
            months=group_by_month(catalog.articles),
            total=len(catalog.articles),  # 标题下面那行写的是全部文章篇数
        )
    )

    environment = _environment(config.theme)
    names = {HOME_URL: "home.html", POSTS_URL: "posts.html"}
    for page in pages:
        template = names.get(page.url, "article.html")
        html = _render_template(environment, template, _context(config, page, page.url))
        target = site / page.url / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8", newline="")
    if not any(page.has_math for page in pages if page.article):  # 内容检查，不阻止构建
        found.append(
            Diagnostic(
                "W_MATHJAX_UNUSED",
                SourceSpan(Path("."), 1, 1),
                "公开发布的文章里没有公式，MathJax 没有被任何页加载。",
            )
        )
    not_found = _render_template(environment, "404.html", _context(config, Page(url="404.html", title="页面不存在"), "404.html"))
    (site / "404.html").write_text(not_found, encoding="utf-8", newline="")

    for old_url, new_url in legacy:  # 5.0.0 之前的旧地址，交给 write_redirects 生成跳转页
        found += legacy_redirects(site, [(old_url, new_url)], config.site_url)

    _copy_theme_assets(config.theme, site)
    for page in pages:
        found.extend(check_body(site, page.url, page.body))
    return found


def _is_warning(diagnostic: Diagnostic) -> bool:
    """Codes starting with `W_` only warn: the page is still written, the report keeps the note."""
    return diagnostic.code.startswith("W_")


def build_pages(
    docs: Path,
    destination: Path,
    config: SiteConfig,
    layout: Layout = LAYOUT,
    legacy: Iterable[tuple[str, str]] = (),
    font_specs: tuple[FontSpec, ...] | None | object = _UNSET_FONT_SPECS,
) -> list[Diagnostic]:
    """Scan `docs`, convert every page and write the whole site into `destination`.

    `legacy` lists `(old address, new address)` redirects that still need to work, like
    `/tech/subscribe-claude-quick/` for the subscription tutorial. `font_specs` are the
    font roles subset out of `<destination>/assets/fonts/` after the pages are written;
    leave it out to use `fonts.default_specs()`, pass `None` to skip the font step
    (the pages then fall back to system fonts).
    """
    index = VaultIndex.scan(docs)
    diagnostics: list[Diagnostic] = list(index.diagnostics)

    def prefix_of(path: Path) -> str | None:
        stage = layout.stage_of(path)
        return stage.prefix if stage is not None else None

    converter = Converter(index, lambda path: is_published(path, layout))
    urls, url_diagnostics = plan_page_urls(docs, index.pages, converter.is_published, prefix_of)
    diagnostics.extend(url_diagnostics)
    diagnostics.extend(series_diagnostics(docs, index.pages, layout))
    if HOME_PAGE not in index.pages:
        diagnostics.append(
            Diagnostic("E_HOME_PAGE_MISSING", SourceSpan(HOME_PAGE, 1, 1), "首页需要 docs/index.md 里的作者的话，但这个文件不存在。")
        )
    catalog, catalog_diagnostics = Catalog.load(docs, index.pages, layout)
    diagnostics.extend(catalog_diagnostics)
    if [item for item in diagnostics if not _is_warning(item)]:
        return diagnostics  # 有错误就不写站点；只有提示时接着写

    converted: dict[str, str] = {}
    references: dict[str, list] = {}
    attachments: list[Path] = []
    for source_path in sorted(index.pages, key=lambda item: item.as_posix()):
        if not converter.is_published(source_path):
            continue
        result = converter.convert(source_path, (docs / source_path).read_text(encoding="utf-8"))
        diagnostics.extend(result.diagnostics)
        converted[source_path.as_posix()] = result.text
        references[source_path.as_posix()] = list(result.references)
        for reference in result.references:
            if reference.kind != "embed" or not reference.target:
                continue
            for attachment in index.resolve_attachment_candidates(source_path, reference.target):
                if attachment.source_path not in attachments:
                    attachments.append(attachment.source_path)

    written = write_site(
        destination,
        catalog,
        converted,
        urls,
        attachments,
        config,
        docs,
        index,
        references,
        diagnostics,
        legacy,
    )
    if font_specs is _UNSET_FONT_SPECS:
        font_specs = default_specs()
    if font_specs is not None:
        # 站点文件都写完之后再收字子集化：这一步要扫刚写出的 HTML
        written.extend(subset_fonts(destination, font_specs))
    return written