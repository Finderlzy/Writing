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
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .content import LAYOUT, Article, Catalog, Layout, is_published
from .obsidian_compat.converter import Converter
from .obsidian_compat.index import VaultIndex
from .obsidian_compat.html_check import check_body
from .obsidian_compat.models import Diagnostic
from .obsidian_compat.parser import residual_diagnostics
from .obsidian_compat.urls import plan_page_urls

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
_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


@dataclass(frozen=True)
class SiteConfig:
    """What a build needs besides `docs/`: the site name and where templates and assets live."""

    site_name: str = "Writing"
    site_url: str = "https://finderlzy.github.io/Writing/"
    theme: Path = Path("theme")


@dataclass(frozen=True)
class Page:
    """One rendered HTML page."""

    url: str  # 输出目录内的相对网址目录，如 "blog/vless-reality/"
    title: str
    body: str
    article: Article | None = None
    toc: tuple[dict, ...] = ()
    has_math: bool = False
    home: bool = True


def load_config(path: Path) -> SiteConfig:
    """Read `site.toml`: top-level `key = "value"` pairs, with comments and blank lines."""
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return SiteConfig(
        site_name=values.get("site_name", SiteConfig.site_name),
        site_url=values.get("site_url", SiteConfig.site_url),
        theme=Path(values.get("theme", SiteConfig.theme)),
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


def _context(config: SiteConfig, page: Page, url: str) -> dict:
    return {
        "site": config,
        "page": page,
        "url": url,
        "root": "../" * (url.rstrip("/").count("/") + 1),
        "toc": page.toc if _heading_count(page.toc) >= _TOC_MIN_HEADINGS else (),
        "mathjax": config.site_url.rstrip("/") + "/assets/theme/mathjax.js" if page.has_math else None,
    }


def _render_template(environment: Environment, template: str, context: dict) -> str:
    return environment.get_template(template).render(**context)


def _embed_links(source_path: Path, target: Path) -> set[str]:
    """The link texts the converter writes for an embed of `target` inside `source_path`.

    转换器把 `![[09附件/图.png]]` 写成 `../09%E9%99%84%E4%BB%B6/图.png`（相对源文件目录），
    这里把两种转义形式都算出来，后面整段替换成 assets 里的地址。
    """
    relative = posixpath.relpath(target.as_posix(), posixpath.dirname(source_path.as_posix()) or ".")
    return {
        relative,
        quote(relative, safe="/-._~()!$&!$&*,;=:@"),
        quote(relative, safe="/"),
    }


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
) -> list[Diagnostic]:
    """Write every article page into `site`; return the diagnostics found on the way.

    `converted` holds the converted Markdown of every public page (already containing
    the links the converter rewrote), `urls` maps source paths to article URLs, and
    `attachments` lists the files that public articles embed. Front matter is dropped
    here because MkDocs' `meta` extension did that in 4.1.0.
    """
    found: list[Diagnostic] = list(diagnostics or [])
    for attachment in attachments:
        target = site / _asset_url(attachment)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(docs / attachment, target)

    pages: list[Page] = []
    for article in catalog.articles:
        key = article.source_path.as_posix()
        url = urls[key]
        text = converted[key]
        text = _rewrite_embeds(text, article.source_path, url, attachments)
        text = _rewrite_page_links(text, url, urls, index, references.get(key, ()))
        body, toc = render_markdown(strip_front_matter(text))
        pages.append(
            Page(
                url=url,
                title=article.title,
                body=body,
                article=article,
                toc=toc,
                has_math=_MATH_RE.search(body) is not None,
            )
        )

    environment = _environment(config.theme)
    for page in pages:
        html = _render_template(environment, "article.html", _context(config, page, page.url))
        target = site / page.url / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8", newline="")

    _copy_theme_assets(config.theme, site)
    for page in pages:
        found.extend(check_body(site, page.url, page.body))
    return found


def build_pages(
    docs: Path,
    destination: Path,
    config: SiteConfig,
    layout: Layout = LAYOUT,
) -> list[Diagnostic]:
    """Scan `docs`, convert every page and write the article pages into `destination`."""
    index = VaultIndex.scan(docs)
    diagnostics: list[Diagnostic] = list(index.diagnostics)

    def prefix_of(path: Path) -> str | None:
        stage = layout.stage_of(path)
        return stage.prefix if stage is not None else None

    converter = Converter(index, lambda path: is_published(path, layout))
    urls, url_diagnostics = plan_page_urls(docs, index.pages, converter.is_published, prefix_of)
    diagnostics.extend(url_diagnostics)
    catalog, catalog_diagnostics = Catalog.load(docs, index.pages, layout)
    diagnostics.extend(catalog_diagnostics)
    if diagnostics:
        return diagnostics

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

    return write_site(
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
    )


    _copy_theme_assets(config.theme, destination)
    for page in pages:
        diagnostics.extend(check_body(destination, page.url, page.body))
    return diagnostics