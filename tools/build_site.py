from __future__ import annotations

import hashlib
import posixpath
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CACHE = ROOT / ".cache" / "converted-docs"
SITE = ROOT / "site"
THEME = ROOT / "theme"
EXTRA_CSS_SOURCE = THEME / "extra.css"
EXTRA_CSS_DESTINATION = CACHE / "stylesheets" / "extra.css"
# 只在本地 Obsidian 中保留、不部署到网站的一级目录或根目录文件
UNPUBLISHED_PATHS = ("00收集", "07自己", "AGENTS.md")
# 一级目录在网址中的英文前缀：04技术/xxx.md → /tech/<slug>/
SECTION_SLUGS = {
    "00收集": "inbox",
    "01系统": "system",
    "02笔记": "notes",
    "03思考": "thoughts",
    "04技术": "tech",
    "05作品": "opus",
    "07自己": "self",
    "09归档": "archive",
}
# 导航顺序：首页 · 思考 · 技术 · 作品 · 笔记。没列出的一级目录（01系统、09归档）不进导航，页面照常发布
NAV_POSTS = {"思考": "03思考", "技术": "04技术", "作品": "05作品"}
NAV_NOTES = ("笔记", "02笔记")
# 构建时生成的文章列表页及其网址
ARTICLES_INDEX = "03思考/index.md"
ARTICLES_URL = "thoughts/"
# 首页“最近的思考”的篇数：带上摘要后，常见桌面屏幕不用滚动就能看完首页
HOME_RECENT_POSTS = 4
# 改过名的一级目录：旧网址生成跳转页。4.0.0 把 03文章（articles）改名为 03思考（thoughts）
RENAMED_SECTIONS = {"03思考": ("03文章", "articles")}


def _is_published_4_1_0(path: Path) -> bool:
    """4.1.0 的发布范围：一级目录不在 UNPUBLISHED_PATHS 里的页面和附件（含根目录页面）。

    4.1.0 的 is_unpublished 只看一级目录，所以 09附件 里的图片也算公开；附件是否复制
    再由嵌引用规则另行决定，原样保留。
    """
    return not path.parts or path.parts[0] not in UNPUBLISHED_PATHS


def _prefix_4_1_0(path: Path) -> str | None:
    """4.1.0 的网址前缀：按一级目录查 SECTION_SLUGS；根目录页面没有前缀。"""
    return SECTION_SLUGS.get(path.parts[0]) if len(path.parts) > 1 else None


sys.dont_write_bytecode = True

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.obsidian_compat.converter import Converter
from tools.obsidian_compat.diagnostics import emit_diagnostics
from tools.obsidian_compat.html_check import check_site
from tools.obsidian_compat.index import VaultIndex
from tools.obsidian_compat.models import Diagnostic, SourceSpan
from tools.obsidian_compat.parser import residual_diagnostics
from tools.obsidian_compat.urls import PageUrlPlugin, plan_page_urls, renamed_folder_redirects, write_redirects
from tools.site_nav import articles_page, build_nav, collect_posts, home_with_recent, section_nav


def _safe_child(path: Path, parent: Path) -> Path:
    resolved_parent = parent.resolve()
    resolved = path.resolve()
    if resolved != resolved_parent and resolved_parent not in resolved.parents:
        raise RuntimeError(f"refusing path outside {resolved_parent}: {resolved}")
    return resolved


def _manifest(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file() and ".obsidian" not in path.parts:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            values[path.relative_to(root).as_posix()] = digest
    return values


def _clean_output(path: Path, parent: Path) -> None:
    target = _safe_child(path, parent)
    if target.is_symlink():
        raise RuntimeError(f"refusing to remove symlink: {target}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def _copy_and_convert(index: VaultIndex, converter: Converter) -> list:
    diagnostics = list(index.diagnostics)
    public_embeds: set[Path] = set()
    unpublished_embeds: set[Path] = set()
    for record in index.pages.values():
        source = DOCS / record.source_path
        result = converter.convert(record.source_path, source.read_text(encoding="utf-8"))
        diagnostics.extend(result.diagnostics)
        unpublished = not converter.is_published(record.source_path)
        for reference in result.references:
            if reference.kind == "embed" and reference.target:
                for attachment in index.resolve_attachment_candidates(record.source_path, reference.target):
                    (unpublished_embeds if unpublished else public_embeds).add(attachment.source_path)
        if unpublished:
            continue
        reference_spans = {reference.span for reference in result.references}
        diagnostics.extend(
            diagnostic
            for diagnostic in residual_diagnostics(record.source_path, result.text)
            if not (
                diagnostic.code == "E_RESIDUAL_OBSIDIAN"
                and diagnostic.span in reference_spans
            )
        )
        destination = CACHE / record.source_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(result.text, encoding="utf-8", newline="")
    for record in index.attachments.values():
        if not converter.is_published(record.source_path) or (
            record.source_path in unpublished_embeds and record.source_path not in public_embeds
        ):
            continue
        destination = CACHE / record.output_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DOCS / record.source_path, destination)
    return diagnostics


def _copy_theme_assets() -> None:
    if not EXTRA_CSS_SOURCE.is_file():
        raise FileNotFoundError(f"主题样式源文件不存在：{EXTRA_CSS_SOURCE}")
    EXTRA_CSS_DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EXTRA_CSS_SOURCE, EXTRA_CSS_DESTINATION)


def _write_site_pages(pages: list[Path]) -> tuple[list, list[Diagnostic]]:
    """Generate the article list page and the home page's recent posts in CACHE; return the nav."""
    if (DOCS / ARTICLES_INDEX).exists():
        return [], [
            Diagnostic(
                "E_GENERATED_PAGE_CONFLICT",
                SourceSpan(Path(ARTICLES_INDEX), 1, 1),
                "文章列表页由构建生成，请给 docs 里的这个同名文件改名。",
            )
        ]
    posts = {title: collect_posts(DOCS, pages, folder) for title, folder in NAV_POSTS.items()}
    articles = posts["思考"]
    emit_diagnostics(
        Diagnostic("W_POST_DATE_MISSING", SourceSpan(post.source_path, 1, 1), "文章没有 createdDate，列表中排在最后。")
        for post in articles
        if post.date is None
    )
    (CACHE / ARTICLES_INDEX).write_text(articles_page(articles, posixpath.dirname(ARTICLES_INDEX)), encoding="utf-8")
    home = CACHE / "index.md"
    home.write_text(home_with_recent(home.read_text(encoding="utf-8"), articles, ARTICLES_INDEX, HOME_RECENT_POSTS), encoding="utf-8")
    sections = {title: section_nav(DOCS, section) for title, section in posts.items()}
    sections["思考"].insert(0, ARTICLES_INDEX)
    return build_nav(pages, sections, NAV_NOTES), []


def build() -> int:
    before = _manifest(DOCS)
    try:
        _clean_output(CACHE, ROOT / ".cache")
        _clean_output(SITE, ROOT)
        index = VaultIndex.scan(DOCS)
        converter = Converter(index, _is_published_4_1_0)
        diagnostics = _copy_and_convert(index, converter)
        page_urls, url_diagnostics = plan_page_urls(DOCS, index.pages, converter.is_published, _prefix_4_1_0)
        diagnostics.extend(url_diagnostics)
        if diagnostics:
            emit_diagnostics(diagnostics)
            return 1
        _copy_theme_assets()
        nav, nav_diagnostics = _write_site_pages([path for path in index.pages if converter.is_published(path)])
        if nav_diagnostics:
            emit_diagnostics(nav_diagnostics)
            return 1
        page_urls[ARTICLES_INDEX] = ARTICLES_URL

        from mkdocs.commands.build import build as mkdocs_build
        from mkdocs.config import load_config

        config = load_config(str(ROOT / "mkdocs.yml"))
        config["docs_dir"] = str(CACHE)
        config["site_dir"] = str(SITE)
        config["strict"] = True
        config["nav"] = nav
        url_plugin = PageUrlPlugin(page_urls)
        config.plugins["page-urls"] = url_plugin
        mkdocs_build(config)
        redirects = [*url_plugin.redirects, *renamed_folder_redirects(page_urls, RENAMED_SECTIONS)]
        html_diagnostics = write_redirects(SITE, redirects, config.get("site_url"))
        html_diagnostics.extend(check_site(SITE, config.get("site_url")))
        if html_diagnostics:
            emit_diagnostics(html_diagnostics)
            return 1
        after = _manifest(DOCS)
        if before != after:
            changed = sorted(set(before) | set(after))
            changed = [path for path in changed if before.get(path) != after.get(path)]
            print(f"[E_SOURCE_MUTATED] 构建期间源文件发生变化：{', '.join(changed)}", file=sys.stderr)
            return 1
        published = sum(1 for path in index.pages if not path.parts or path.parts[0] not in UNPUBLISHED_PATHS)
        print(f"build succeeded: {published} pages published, {len(index.pages) - published} unpublished")
        return 0
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"[E_TOOL_CONFIG] 构建依赖不可用：{exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[E_TOOL_INTERNAL] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(build())
