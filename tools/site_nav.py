"""Site navigation, the article list page and the home page's recent posts.

Only the converted copies in `.cache/converted-docs` are touched; Obsidian sources stay as they are.
"""

from __future__ import annotations

import datetime
import html
import json
import posixpath
import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .content import read_meta

_MD_SPECIAL_RE = re.compile(r"([\\`*_\[\]])")
_WIKI_LINK_RE = re.compile(r"\[\[([^\]|#^]+)")


@dataclass(frozen=True)
class Post:
    source_path: Path
    title: str
    date: datetime.date | None
    tags: tuple[str, ...]
    description: str = ""


def read_page_meta(docs: Path, source_path: Path) -> dict:
    """Front matter of a page in docs; the parsing itself lives in content.read_meta."""
    return read_meta((docs / source_path).read_text(encoding="utf-8"))


def _as_date(value) -> datetime.date | None:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.datetime.fromisoformat(value.strip()).date()
        except ValueError:
            return None
    return None


def _as_tags(value) -> tuple[str, ...]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return ()
    tags = (str(tag).strip() for tag in value if tag is not None)
    return tuple(dict.fromkeys(tag for tag in tags if tag))


def collect_posts(docs: Path, pages: Iterable[Path], folder: str) -> list[Post]:
    """Pages directly or deeper under `folder`, newest `createdDate` first; undated posts go last."""
    posts = []
    for source_path in pages:
        if source_path.parts[0] != folder or len(source_path.parts) < 2:
            continue
        meta = read_meta((docs / source_path).read_text(encoding="utf-8"))
        title = meta.get("title")
        posts.append(
            Post(
                source_path,
                str(title) if title else source_path.stem,
                _as_date(meta.get("createdDate")),
                _as_tags(meta.get("tags")),
                str(meta.get("description") or "").strip(),
            )
        )
    posts.sort(key=lambda post: post.title)
    posts.sort(key=lambda post: post.date or datetime.date.min, reverse=True)
    return posts


def _md_text(text: str) -> str:
    """Show `text` literally inside a markdown line."""
    return _MD_SPECIAL_RE.sub(r"\\\1", html.escape(text, quote=False))


def _link(post: Post, from_dir: str) -> str:
    target = posixpath.relpath(post.source_path.as_posix(), from_dir or ".")
    text = _md_text(post.title)
    if "<" in target or ">" in target:
        target = target.replace("<", "%3C").replace(">", "%3E")
    return f"[{text}](<{target}>)"


def _post_line(post: Post, from_dir: str, show_tags: bool) -> str:
    parts = []
    if post.date:
        parts.append(f'<time class="post-date">{post.date.isoformat()}</time>')
    parts.append(_link(post, from_dir))
    if show_tags:
        tags = html.escape(json.dumps(post.tags, ensure_ascii=False), quote=True)
        labels = " ".join(f"<span>{_md_text(tag)}</span>" for tag in post.tags)
        parts.append(f'<span class="post-tags" data-tags="{tags}">{labels}</span>')
    if post.description:
        parts.append(f'<span class="post-desc">{_md_text(post.description)}</span>')
    return "- " + " ".join(parts)


def articles_page(posts: Sequence[Post], from_dir: str, title: str = "思考") -> str:
    """The article list page in `from_dir`: every post newest first, with tag filter buttons."""
    counts = Counter(tag for post in posts for tag in post.tags)
    buttons = [f'<button type="button" class="post-filter__tag" data-tag="" aria-pressed="true">全部（{len(posts)}）</button>']
    for tag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        value = html.escape(tag, quote=True)
        buttons.append(
            f'<button type="button" class="post-filter__tag" data-tag="{value}" aria-pressed="false">'
            f"{html.escape(tag)}（{count}）</button>"
        )
    lines = [f"# {title}", "", '<div class="post-filter" data-post-filter hidden>', *buttons, "</div>", ""]
    lines += [_post_line(post, from_dir, show_tags=True) for post in posts]
    if not posts:
        lines.append("还没有文章。")
    return "\n".join(lines) + "\n"


def home_with_recent(home: str, posts: Sequence[Post], all_posts_page: str, limit: int = 8) -> str:
    """Append the newest dated posts to the home page, linked from the site root."""
    recent = [post for post in posts if post.date][:limit]
    if not recent:
        return home
    lines = ["", "## 最近的思考", ""]
    lines += [_post_line(post, "", show_tags=False) for post in recent]
    lines += ["", f"[全部思考 →](<{all_posts_page}>)", ""]
    return home.rstrip("\n") + "\n" + "\n".join(lines)


def _wiki_targets(text: str) -> list[str]:
    """File names that `[[...]]` links in `text` point to, in order of first appearance."""
    names = (target.strip().rsplit("/", 1)[-1] for target in _WIKI_LINK_RE.findall(text))
    return list(dict.fromkeys(name.removesuffix(".md") for name in names if name.strip()))


def _reading_order(docs: Path, group: Sequence[Post]) -> list[Post]:
    """The group's table-of-contents page first, then pages in the order its links reach them; unlinked pages last."""
    by_stem = {post.source_path.stem: post for post in group}
    links = {
        post.source_path.stem: [name for name in _wiki_targets((docs / post.source_path).read_text(encoding="utf-8")) if name in by_stem]
        for post in group
    }
    # 目录页：链到同组页面最多的那篇
    start = max(group, key=lambda post: (len(links[post.source_path.stem]), post.date is not None))
    order = [start.source_path.stem]
    for stem in order:
        order += [name for name in links[stem] if name not in order]
    order += sorted(stem for stem in by_stem if stem not in order)
    return [by_stem[stem] for stem in order]


def section_nav(docs: Path, posts: Sequence[Post]) -> list:
    """Pages right in the section folder stay flat; each subfolder becomes one group, placed where its newest page would be."""
    groups: dict[str, list[Post]] = {}
    for post in posts:
        if len(post.source_path.parts) > 2:
            groups.setdefault(post.source_path.parts[1], []).append(post)
    nav: list = []
    for post in posts:
        if len(post.source_path.parts) == 2:
            nav.append(post.source_path.as_posix())
        elif post.source_path.parts[1] in groups:
            name = post.source_path.parts[1]
            nav.append({name: [p.source_path.as_posix() for p in _reading_order(docs, groups.pop(name))]})
    return nav


def build_nav(pages: Iterable[Path], sections: dict[str, list[str]]) -> list:
    """首页, then `sections` in order; other folders stay off the navigation."""
    del pages  # 导航只用 sections；参数保留，调用方和测试仍然传入全部页面
    nav: list = [{"首页": "index.md"}]
    nav += [{title: entries} for title, entries in sections.items()]
    return nav
