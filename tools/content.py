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

HOME_PAGE = Path("index.md")


def _within(path: Path, folder: str) -> bool:
    """True when path is in folder or one of its subfolders; folder is a POSIX path prefix."""
    return path.as_posix() == folder or path.as_posix().startswith(folder + "/")


@dataclass(frozen=True)
class Stage:
    folder: str  # 文件夹路径前缀，如 "02思考"；按最长前缀匹配，所以也可以是 "03思考/初稿"
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


LAYOUT = Layout(
    stages=(
        Stage("02思考", "思考", "thoughts"),
        Stage("03初稿", "初稿", "drafts"),
        Stage("04博客", "博客", "blog"),
        Stage("05作品", "作品", "opus"),
    ),
    series={},
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


def _read_article(docs: Path, source_path: Path, stage: Stage) -> Article:
    meta = read_meta((docs / source_path).read_text(encoding="utf-8"))
    title = meta.get("title")
    return Article(
        source_path=source_path,
        stage=stage,
        title=str(title).strip() if title else source_path.stem,
        date=_as_date(meta.get("createdDate")),
        tags=_as_tags(meta.get("tags")),
        description=str(meta.get("description") or "").strip(),
    )


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
            article = _read_article(docs, source_path, stage)
            if article.date is None:
                diagnostics.append(
                    Diagnostic(
                        "W_POST_DATE_MISSING",
                        SourceSpan(source_path, 1, 1),
                        "文章没有 createdDate，列表中排在最后。",
                    )
                )
            articles.append(article)
        return cls(tuple(_newest_first(articles)), layout), diagnostics

    def home(self) -> tuple[Article, ...]:
        """Blog articles outside a series folder plus every 作品 article, newest first."""
        return tuple(
            article
            for article in self.articles
            if article.stage.name == "作品"
            or (article.stage.name == "博客" and self.layout.series_folder(article.source_path) is None)
        )

    def neighbours(self, article: Article) -> tuple[Article | None, Article | None]:
        """The previous (earlier) and the next (later) article within the same stage."""
        ordered = [item for item in reversed(self.articles) if item.stage == article.stage]
        if article not in ordered:
            return None, None
        position = ordered.index(article)
        previous = ordered[position - 1] if position > 0 else None
        following = ordered[position + 1] if position + 1 < len(ordered) else None
        return previous, following

    def series(self, article: Article) -> tuple[Article, ...]:
        """article's series in reading order (entry page first); empty when it is in none."""
        folder = self.layout.series_folder(article.source_path)
        if folder is None:
            return ()
        members = {
            item.source_path: item
            for item in self.articles
            if self.layout.series_folder(item.source_path) == folder
        }
        order: list[Path] = []
        entry = Path(self.layout.series[folder])
        if entry in members:
            order.append(entry)
        order += [path for path in sorted(members, key=lambda item: item.as_posix()) if path not in order]
        return tuple(members[path] for path in order)
