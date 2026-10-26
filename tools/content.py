"""Publishing scope and catalog of articles.

One module answers "which pages are articles, what are they, in what order".
Other modules ask this module instead of testing folders or parsing front
matter on their own.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .obsidian_compat.models import Diagnostic, SourceSpan

_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?\r?\n)?---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_WIKI_LINK_RE = re.compile(r"\[\[([^\]|#^]+)")

HOME_PAGE = Path("index.md")


def _within(path: Path, folder: str) -> bool:
    """True when path is in folder or one of its subfolders; folder is a POSIX path prefix."""
    return path.as_posix() == folder or path.as_posix().startswith(folder + "/")


@dataclass(frozen=True)
class Stage:
    folder: str  # 文件夹路径前缀，如 "02思考"；按最长前缀匹配
    name: str  # 思考 / 初稿 / 博客 / 作品
    prefix: str  # 网址前缀 thoughts / drafts / blog / opus


@dataclass(frozen=True)
class Layout:
    """Folder-to-stage mapping, plus the series configuration."""

    stages: tuple[Stage, ...]
    series: dict[str, str]

    def stage_of(self, path: Path) -> Stage | None:
        """The stage path belongs to; the longest matching folder prefix wins."""
        best: Stage | None = None
        for stage in self.stages:
            if _within(path, stage.folder) and (best is None or len(stage.folder) > len(best.folder)):
                best = stage
        return best

    def series_folder(self, path: Path) -> str | None:
        """The configured series folder that path is inside or stands for, if any."""
        for folder, entry in self.series.items():
            if _within(path, folder) or path.as_posix() == entry:
                return folder
        return None


# 04博客 的子文件夹各是一个系列，值是它的入口篇（在 04博客 根目录）。见 architecture.md §6。
SERIES = {
    "04博客/原理版": "04博客/如何订阅claude.md",
    "04博客/操作版": "04博客/如何订阅claude（纯操作版）.md",
}

LAYOUT = Layout(
    stages=(
        Stage("02思考", "思考", "thoughts"),
        Stage("03初稿", "初稿", "drafts"),
        Stage("04博客", "博客", "blog"),
        Stage("05作品", "作品", "opus"),
    ),
    series=SERIES,
)


def is_published(path: Path, layout: Layout = LAYOUT) -> bool:
    """The only "may this be published" check: a Markdown page of a stage, or the home page."""
    return path == HOME_PAGE or (path.suffix == ".md" and layout.stage_of(path) is not None)


def read_meta(text: str) -> dict:
    """The only front matter parser (YAML); broken front matter reads as {}."""
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return {}
    try:
        meta = yaml.safe_load(match.group(1) or "")
    except yaml.YAMLError:
        return {}
    return meta if isinstance(meta, dict) else {}


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


@dataclass(frozen=True)
class Article:
    source_path: Path
    stage: Stage
    title: str  # front matter 的 title，没写就用文件名
    date: datetime.date | None  # createdDate
    tags: tuple[str, ...]
    description: str
    url: str = ""  # 站内相对网址，如 "blog/subscribe-claude/"，由 plan_page_urls 给出
    series: str | None = None  # 所属系列名（入口篇标题）；入口篇自己也属于系列


def _read_article(docs: Path, source_path: Path, stage: Stage, layout: Layout = LAYOUT) -> Article:
    text = (docs / source_path).read_text(encoding="utf-8")
    meta = read_meta(text)
    if _has_front_matter(text) and not meta:
        meta = _strict_meta(text, source_path)
    title = meta.get("title")
    return Article(
        source_path=source_path,
        stage=stage,
        title=str(title).strip() if title else source_path.stem,
        date=_as_date(meta.get("createdDate")),
        tags=_as_tags(meta.get("tags")),
        description=str(meta.get("description") or "").strip(),
        series=_series_name(docs, source_path, layout),
    )


def _has_front_matter(text: str) -> bool:
    return _FRONT_MATTER_RE.match(text) is not None


def _strict_meta(text: str, source_path: Path) -> dict:
    """Re-read front matter and fail loudly when the YAML is broken (read_meta returns {})."""
    match = _FRONT_MATTER_RE.match(text)
    try:
        meta = yaml.safe_load((match.group(1) if match else "") or "")
    except yaml.YAMLError as error:
        line = getattr(getattr(error, "problem_mark", None), "line", 0) + 1
        raise ValueError(
            f"第 {line} 行附近的 front matter 不是合法的 YAML：{getattr(error, 'problem', error)}"
        ) from error
    return meta if isinstance(meta, dict) else {}


def _series_name(docs: Path, source_path: Path, layout: Layout) -> str | None:
    """The series an article belongs to, named after its entry page's title."""
    folder = layout.series_folder(source_path)
    if folder is None:
        return None
    entry = Path(layout.series[folder])
    meta = read_meta((docs / entry).read_text(encoding="utf-8")) if (docs / entry).is_file() else {}
    title = meta.get("title")
    return str(title).strip() if title else entry.stem


def series_diagnostics(
    docs: Path,
    pages: Iterable[Path],
    layout: Layout = LAYOUT,
) -> list[Diagnostic]:
    """Check the series layout: configured folders need an entry page, stage folders stay flat."""
    diagnostics: list[Diagnostic] = []
    page_set = sorted({path for path in pages if path.suffix == ".md"}, key=lambda item: item.as_posix())
    for stage in layout.stages:
        for path in sorted(page_set, key=lambda item: item.as_posix()):
            if not _within(path, stage.folder) or path == Path(stage.folder):
                continue
            relative = path.as_posix()[len(stage.folder) + 1 :]
            if "/" not in relative:
                continue
            folder = f"{stage.folder}/{relative.split('/')[0]}"
            if folder in layout.series:
                continue
            closest = max(
                (item for item in layout.stages if _within(path, item.folder)),
                key=lambda item: len(item.folder),
            )
            if closest != stage:
                continue  # 页面属于更具体的阶段，例如 04博客/原理版 下的页面归“博客”
            if any(_within(path, series) for series in layout.series):
                continue
            diagnostics.append(
                Diagnostic(
                    "E_STAGE_SUBFOLDER",
                    SourceSpan(path, 1, 1),
                    f"“{stage.name}”阶段不能有子文件夹“{relative.split('/')[0]}”。"
                    "只有博客（04博客）可以为系列建子文件夹，并在 Layout.series 里登记。",
                )
            )
    for folder, entry in layout.series.items():
        entry_path = Path(entry)
        stage = layout.stage_of(entry_path)
        parent = stage.folder if stage is not None else folder
        if Path(entry_path.as_posix()).parent.as_posix() != parent:
            diagnostics.append(
                Diagnostic(
                    "E_SERIES_ENTRY_MISSING",
                    SourceSpan(entry_path, 1, 1),
                    f"系列“{folder}”的入口篇要放在“{parent}”根目录里，而在这里写的是“{entry}”。",
                )
            )
        elif entry_path not in page_set:
            diagnostics.append(
                Diagnostic(
                    "E_SERIES_ENTRY_MISSING",
                    SourceSpan(entry_path, 1, 1),
                    f"系列“{folder}”的入口篇“{entry}”不存在。",
                )
            )
    for stage in layout.stages:
        if stage.name != "博客":
            continue
        reported: set[str] = set()
        for path in sorted(page_set, key=lambda item: item.as_posix()):
            if not _within(path, stage.folder) or path.as_posix() == stage.folder:
                continue
            relative = path.as_posix()[len(stage.folder) + 1 :]
            if "/" not in relative:
                continue
            name = relative.split("/")[0]
            folder = f"{stage.folder}/{name}"
            if folder in reported or folder in layout.series or not (docs / folder).is_dir():
                continue
            if any(_within(Path(entry), folder) for entry in layout.series.values()):
                continue  # 这里的页面是某个系列的入口篇（预览用旧布局时，入口篇在子文件夹里）
            if any(_within(path, series) for series in layout.series):
                continue
            reported.add(folder)
            diagnostics.append(
                Diagnostic(
                    "E_SERIES_UNCONFIGURED",
                    SourceSpan(Path(folder), 1, 1),
                    f"“{folder}”是“{stage.name}”下的子文件夹，但还没在 Layout.series 里登记成系列。",
                )
            )
    return diagnostics


def _newest_first(articles: Iterable[Article]) -> list[Article]:
    """createdDate newest first; undated articles last; ties and undated ordered by title."""
    ordered = sorted(articles, key=lambda article: article.title)
    ordered.sort(key=lambda article: article.date or datetime.date.min, reverse=True)
    return ordered


@dataclass(frozen=True)
class Catalog:
    """Every published article, ordered newest first; the home list; neighbours; series."""

    articles: tuple[Article, ...]
    layout: Layout
    docs: Path = Path(".")

    @classmethod
    def load(
        cls,
        docs: Path,
        pages: Iterable[Path],
        layout: Layout = LAYOUT,
    ) -> tuple[Catalog, list[Diagnostic]]:
        """Read every page of a stage; report pages without a createdDate but keep them."""
        diagnostics: list[Diagnostic] = []
        articles: list[Article] = []
        for source_path in sorted(pages, key=lambda item: item.as_posix()):
            stage = layout.stage_of(source_path)
            if stage is None:
                continue
            try:
                article = _read_article(docs, source_path, stage, layout)
            except ValueError as error:  # front matter 读不成 YAML
                diagnostics.append(Diagnostic("E_FRONT_MATTER_INVALID", SourceSpan(source_path, 1, 1), str(error)))
                continue
            if article.date is None:
                diagnostics.append(
                    Diagnostic(
                        "W_POST_DATE_MISSING",
                        SourceSpan(source_path, 1, 1),
                        "文章没有 createdDate，列表中排在最后。",
                    )
                )
            articles.append(article)
        return cls(tuple(_newest_first(articles)), layout, docs), diagnostics

    def entry_of(self, folder: str) -> Article | None:
        """The entry article that stands for a series folder."""
        entry = self.layout.series.get(folder)
        return self.article(Path(entry)) if entry else None

    def home(self) -> tuple[Article, ...]:
        """Blog articles outside a series folder plus every 作品 article, newest first.

        A series is represented by its entry page, which sits outside the folder and so stays on the list.
        """
        return tuple(
            article
            for article in self.articles
            if article.stage.name == "作品"
            or (
                article.stage.name == "博客"
                and not any(_within(article.source_path, folder) for folder in self.layout.series)
            )
        )

    def article(self, source_path: Path) -> Article | None:
        """The article read from a source path, if it was loaded."""
        for article in self.articles:
            if article.source_path == source_path:
                return article
        return None

    def neighbours(self, article: Article) -> tuple[Article | None, Article | None]:
        """The previous (earlier) and the next (later) article; series order for series members."""
        members = self.series(article)
        ordered = members if members else [item for item in reversed(self.articles) if item.stage == article.stage]
        position = next((index for index, item in enumerate(ordered) if item.source_path == article.source_path), None)
        if position is None:
            return None, None
        previous = ordered[position - 1] if position > 0 else None
        following = ordered[position + 1] if position + 1 < len(ordered) else None
        return previous, following

    def series(self, article: Article) -> tuple[Article, ...]:
        """article's series in reading order (configured entry page first); empty when it is in none."""
        folder = self.layout.series_folder(article.source_path)
        if folder is None:
            return ()
        members = {
            item.source_path: item
            for item in self.articles
            if self.layout.series_folder(item.source_path) == folder
        }
        # 系列文件夹里可能还躺着一份作者手写的目录页，路径和入口篇不同；
        # 阅读顺序以 Layout.series 里登记的入口篇开头，其余按它链出去的顺序。
        entry = Path(self.layout.series[folder])
        order = [entry, *self._reading_order(folder, members)]
        result: list[Article] = []
        seen: set[Path] = set()
        for path in order:
            if path in members and path not in seen:
                seen.add(path)
                result.append(members[path])
        return tuple(result)

    def _reading_order(self, folder: str, members: dict[Path, Article]) -> list[Path]:
        """Sub-folder pages in the order the entry page first links them; unlinked pages by file name.

        This is the rule 4.1.0 used for a folder group in the navigation: the page that links
        the most pages of the group opens it, the others follow the order its links reach them.
        """
        by_stem = {path.stem: path for path in members}
        links: dict[str, list[str]] = {}
        for path in members:
            text = (self.docs / path).read_text(encoding="utf-8")
            names = (match.strip().rsplit("/", 1)[-1] for match in _WIKI_LINK_RE.findall(text))
            wanted = {name.removesuffix(".md") for name in names if name.removesuffix(".md") in by_stem}
            links[path.stem] = sorted(wanted, key=lambda stem: list(by_stem).index(stem))
        entry = Path(self.layout.series[folder])
        start = entry.stem if entry.stem in by_stem else max(
            by_stem, key=lambda stem: (len(links[stem]), str(by_stem[stem]))
        )
        order = [start]
        for stem in order:
            order += [name for name in links[stem] if name not in order]
        order += sorted(stem for stem in by_stem if stem not in order)
        return [by_stem[stem] for stem in order]