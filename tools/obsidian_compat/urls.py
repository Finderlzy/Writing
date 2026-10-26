from __future__ import annotations

import hashlib
import html
import json
import posixpath
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from ..content import read_meta
from .models import Diagnostic, SourceSpan

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SLUG_LINE_RE = re.compile(r"^slug:[ \t]*(.*?)[ \t]*$")


@dataclass(frozen=True)
class Redirect:
    old_dest: str
    new_url: str


def _slug_line(text: str) -> int | None:
    """Line number of the `slug` entry in the first front matter block, for diagnostics only."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return None
        if _SLUG_LINE_RE.match(lines[index]):
            return index + 1
    return None


def front_matter_slug(text: str) -> tuple[str, int] | None:
    """Return the `slug` value from front matter and its line number.

    The value comes from `content.read_meta` (YAML), so `slug: abc # note` is `abc`;
    a hand-written `slug:` line whose value YAML cannot read yields no slug at all.
    """
    line = _slug_line(text)
    value = read_meta(text).get("slug")
    if line is None or not isinstance(value, str) or not value.strip():
        return None
    return value.strip(), line


def auto_slug(source_path: Path) -> str:
    """Stable short ID for pages without a handwritten slug."""
    return hashlib.sha1(source_path.as_posix().encode("utf-8")).hexdigest()[:8]


def plan_page_urls(
    docs: Path,
    pages: Iterable[Path],
    is_published: Callable[[Path], bool],
    prefix_of: Callable[[Path], str | None],
) -> tuple[dict[str, str], list[Diagnostic]]:
    """Map each published page's src_uri to `<网址前缀>/<slug>/`, e.g. `blog/vless-reality/`.

    `prefix_of` returns the URL prefix of the page's stage, or None when it has none.
    """
    diagnostics: list[Diagnostic] = []
    owners: dict[str, list[tuple[Path, int]]] = {}
    for source_path in sorted(pages, key=lambda item: item.as_posix()):
        if not is_published(source_path) or source_path == Path("index.md"):
            continue
        section = prefix_of(source_path)
        if section is None:
            diagnostics.append(
                Diagnostic(
                    "E_URL_SECTION_MISSING",
                    SourceSpan(source_path, 1, 1),
                    _section_missing_message(source_path),
                )
            )
            continue
        found = front_matter_slug((docs / source_path).read_text(encoding="utf-8"))
        if found is None:
            slug, line = auto_slug(source_path), 1
        else:
            slug, line = found
            if not _SLUG_RE.match(slug):
                diagnostics.append(
                    Diagnostic(
                        "E_SLUG_INVALID",
                        SourceSpan(source_path, line, 1),
                        f"slug “{slug}”只能包含小写字母、数字和单个连字符，且不能以连字符开头或结尾。",
                    )
                )
                continue
        owners.setdefault(f"{section}/{slug}/", []).append((source_path, line))

    urls: dict[str, str] = {}
    for url, sources in owners.items():
        if len(sources) > 1:
            for source_path, line in sources:
                diagnostics.append(
                    Diagnostic(
                        "E_SLUG_DUPLICATE",
                        SourceSpan(source_path, line, 1),
                        f"网址“{url}”被同一目录下的多个页面使用。",
                        tuple(other for other, _ in sources if other != source_path),
                    )
                )
            continue
        urls[sources[0][0].as_posix()] = url
    return urls, diagnostics


def _section_missing_message(source_path: Path) -> str:
    if len(source_path.parts) <= 1:
        return f"根目录的文件“{source_path.as_posix()}”没有对应的网址前缀，请把它放进某个阶段文件夹。"
    return f"文件夹“{source_path.parts[0]}”没有对应的网址前缀，请把它加入 Layout 的阶段里。"


def redirect_html(old_dest: str, new_url: str, site_url: str | None) -> str:
    target = posixpath.relpath(new_url, posixpath.dirname(old_dest)) + "/"
    href = html.escape(target, quote=True)
    canonical = html.escape((site_url or "/").rstrip("/") + "/" + new_url, quote=True)
    return (
        "<!doctype html>\n"
        '<html lang="zh">\n<head>\n<meta charset="utf-8">\n'
        "<title>页面已迁移</title>\n"
        '<meta name="robots" content="noindex">\n'
        f'<link rel="canonical" href="{canonical}">\n'
        f'<meta http-equiv="refresh" content="0; url={href}">\n'
        f"<script>location.replace({json.dumps(target)} + location.search + location.hash)</script>\n"
        "</head>\n<body>\n"
        f'<p>页面已迁移到 <a href="{href}">新地址</a>。</p>\n'
        "</body>\n</html>\n"
    )


def legacy_redirects(site: Path, pairs: Iterable[tuple[str, str]], site_url: str | None) -> list[Diagnostic]:
    """Hand written old address → current page redirects, declared as `(old address, new address)` prefixes.

    Used for addresses that were published before 5.0.0 and have no source page any more,
    like the subscription tutorial that moved from `/tech/subscribe-claude-quick/` to `/blog/`.
    A target that was not written means the new address is wrong, so it stops the build.
    """
    diagnostics: list[Diagnostic] = []
    targets = {path.relative_to(site).as_posix() for path in site.rglob("index.html")}
    for old_url, new_url in pairs:
        old_url = "/" + old_url.strip("/") + "/"
        new_url = "/" + new_url.strip("/") + "/"
        if not new_url.strip("/") or new_url.lstrip("/") + "index.html" not in targets:
            diagnostics.append(
                Diagnostic(
                    "E_REDIRECT_TARGET_MISSING",
                    SourceSpan(Path(old_url.lstrip("/")), 1, 1),
                    f"跳转的旧地址“{old_url}”指向“{new_url}”，但那里没有页面。",
                )
            )
            continue
        diagnostics += write_redirects(site, [Redirect(old_url.lstrip("/") + "index.html", new_url.lstrip("/"))], site_url)
    return diagnostics


def write_redirects(site: Path, redirects: Iterable[Redirect], site_url: str | None) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for redirect in redirects:
        destination = site / redirect.old_dest
        if destination.exists():
            diagnostics.append(
                Diagnostic(
                    "E_REDIRECT_CONFLICT",
                    SourceSpan(Path(redirect.old_dest), 1, 1),
                    f"旧地址与现有页面冲突，无法生成跳转到“{redirect.new_url}”的页面。",
                )
            )
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(redirect_html(redirect.old_dest, redirect.new_url, site_url), encoding="utf-8")
    return diagnostics
