from __future__ import annotations

import posixpath
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from .models import Diagnostic, SourceSpan

_OBSIDIAN_RE = re.compile(r"!\[\[|\[\[|>\s*\[![A-Za-z]+\]")


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.text: list[str] = []
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if "name" in values:
            self.ids.add(values["name"])
        if tag == "a" and "href" in values:
            self.links.append(("href", values["href"]))
        if tag == "img" and "src" in values:
            self.links.append(("src", values["src"]))
        if tag in {"code", "pre", "script", "style"}:
            self._ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"code", "pre", "script", "style"}:
            self._ignored = max(0, self._ignored - 1)

    def handle_data(self, data: str) -> None:
        if not self._ignored:
            self.text.append(data)


def _base_path(site_url: str | None) -> str:
    if not site_url:
        return "/"
    path = urlsplit(site_url).path or "/"
    return path if path.endswith("/") else path + "/"


def _target_file(site: Path, url_path: str) -> Path | None:
    path = unquote(url_path).lstrip("/")
    if path.endswith("/"):
        path += "index.html"
    elif path.endswith(".md"):
        path = path[:-3] + "index.html"
    else:
        options = [site / path / "index.html", site / (path + ".html")]
        directory_target = next((candidate for candidate in options if candidate.is_file()), None)
        if directory_target is not None:
            return directory_target
    candidate = site / path
    return candidate if candidate.is_file() else None


def check_site(site: Path, site_url: str | None = None) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    base = _base_path(site_url)
    html_files = sorted(site.rglob("*.html"))
    parsed: dict[Path, _PageParser] = {}
    for html in html_files:
        parser = _PageParser()
        parser.feed(html.read_text(encoding="utf-8"))
        parsed[html] = parser

    for html, parser in parsed.items():
        relative = html.relative_to(site).as_posix()
        for kind, raw_url in parser.links:
            parts = urlsplit(raw_url)
            if parts.scheme or parts.netloc or raw_url.startswith(("mailto:", "javascript:", "data:")):
                continue
            if kind == "src" and parts.query:
                continue
            path = parts.path
            if path.startswith(base):
                path = path[len(base) - 1 :]
            elif path.startswith("/"):
                path = path[1:]
            resolved_url = urljoin("/" + relative, path)
            target = _target_file(site, posixpath.normpath(resolved_url).lstrip("/"))
            if target is None:
                diagnostics.append(
                    Diagnostic("E_HTML_BROKEN_LINK", SourceSpan(Path(relative), 1, 1), f"HTML 中的 {kind} 地址无效：“{raw_url}”。")
                )
                continue
            if parts.fragment:
                target_parser = parsed.get(target)
                if target_parser and unquote(parts.fragment) not in target_parser.ids:
                    diagnostics.append(
                        Diagnostic("E_HTML_BROKEN_ANCHOR", SourceSpan(Path(relative), 1, 1), f"HTML 片段锚点不存在：“{raw_url}”。")
                    )
        raw_text = "".join(parser.text)
        if _OBSIDIAN_RE.search(raw_text):
            diagnostics.append(
                Diagnostic("E_HTML_RESIDUAL_OBSIDIAN", SourceSpan(Path(relative), 1, 1), "生成的 HTML 正文仍残留 Obsidian 标记。")
            )
    return diagnostics
