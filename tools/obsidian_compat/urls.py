from __future__ import annotations

import hashlib
import html
import json
import posixpath
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from mkdocs.plugins import BasePlugin

from .models import Diagnostic, SourceSpan

# 所有页面统一发布在 /p/<slug>/ 下，网址不随标题或栏目变化
URL_PREFIX = "p"
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SLUG_LINE_RE = re.compile(r"^slug:[ \t]*(.*?)[ \t]*$")


@dataclass(frozen=True)
class Redirect:
    old_dest: str
    new_url: str


def front_matter_slug(text: str) -> tuple[str, int] | None:
    """Return the raw `slug` value in YAML front matter and its line number."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return None
        match = _SLUG_LINE_RE.match(lines[index])
        if match:
            value = match.group(1)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value, index + 1
    return None


def auto_slug(source_path: Path) -> str:
    """Stable short ID for pages without a handwritten slug."""
    return hashlib.sha1(source_path.as_posix().encode("utf-8")).hexdigest()[:8]


def plan_page_urls(
    docs: Path,
    pages: Iterable[Path],
    is_unpublished: Callable[[Path], bool],
) -> tuple[dict[str, str], list[Diagnostic]]:
    """Map published page src_uri to its directory URL, e.g. `p/vless-reality/`."""
    diagnostics: list[Diagnostic] = []
    owners: dict[str, list[tuple[Path, int]]] = {}
    for source_path in sorted(pages, key=lambda item: item.as_posix()):
        if is_unpublished(source_path) or source_path == Path("index.md"):
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
        owners.setdefault(slug, []).append((source_path, line))

    urls: dict[str, str] = {}
    for slug, sources in owners.items():
        if len(sources) > 1:
            for source_path, line in sources:
                diagnostics.append(
                    Diagnostic(
                        "E_SLUG_DUPLICATE",
                        SourceSpan(source_path, line, 1),
                        f"slug “{slug}”被多个页面使用。",
                        tuple(other for other, _ in sources if other != source_path),
                    )
                )
            continue
        urls[sources[0][0].as_posix()] = f"{URL_PREFIX}/{slug}/"
    return urls, diagnostics


class PageUrlPlugin(BasePlugin):
    """Move pages to their planned URL and remember the old address for redirects."""

    def __init__(self, urls: dict[str, str]):
        super().__init__()
        self.urls = urls
        self.redirects: list[Redirect] = []

    def on_files(self, files, config):
        self.redirects = []
        for file in files.documentation_pages():
            new_url = self.urls.get(file.src_uri)
            if new_url is None:
                continue
            self.redirects.append(Redirect(file.dest_uri, new_url))
            file.dest_uri = new_url + "index.html"
            for cached in ("url", "abs_dest_path"):
                file.__dict__.pop(cached, None)
        return files


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
