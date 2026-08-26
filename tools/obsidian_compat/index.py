from __future__ import annotations

import re
import posixpath
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .models import AttachmentRecord, Diagnostic, PageRecord, SourceSpan
from .parser import body_lines
from .slug import unique_toc_slugs, visible_text

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#?[ \t]*$")
_BLOCK_RE = re.compile(r"(?:^|\s)\^([A-Za-z0-9_-]+)[ \t]*$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:($|/)")


def _relative(path: Path) -> Path:
    return Path(PurePosixPath(posixpath.normpath(path.as_posix())))


def _normalize_candidate(candidate: Path | str) -> Path | None:
    """Normalize a user-supplied relative candidate without creating invalid Paths."""
    raw = candidate.as_posix() if isinstance(candidate, Path) else str(candidate)
    raw = raw.replace("\\", "/")
    if not raw or not raw.strip() or "\x00" in raw:
        return None
    if raw.startswith("/") or raw.endswith("/") or _WINDOWS_DRIVE_RE.match(raw):
        return None

    normalized = posixpath.normpath(raw)
    if normalized in {".", "..", "/"} or normalized.endswith("/"):
        return None
    path = PurePosixPath(normalized)
    if path.is_absolute() or not path.name or path.name in {".", ".."}:
        return None
    return Path(path)


@dataclass
class VaultIndex:
    root: Path
    pages: dict[Path, PageRecord]
    attachments: dict[Path, AttachmentRecord]
    diagnostics: list[Diagnostic]

    def __init__(self, root: Path):
        self.root = root
        self.pages = {}
        self.attachments = {}
        self.diagnostics = []
        self._by_logical: dict[str, list[PageRecord]] = {}
        self._by_name: dict[str, list[PageRecord]] = {}
        self._attachments_by_name: dict[str, list[AttachmentRecord]] = {}

    @classmethod
    def scan(cls, root: Path) -> "VaultIndex":
        index = cls(root)
        for source in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            if not source.is_file() or ".obsidian" in source.parts:
                continue
            relative = _relative(source.relative_to(root))
            if source.suffix.casefold() == ".md":
                index._add_page(relative, source.read_text(encoding="utf-8"))
            else:
                record = AttachmentRecord(relative, relative)
                index.attachments[relative] = record
                index._attachments_by_name.setdefault(source.name, []).append(record)
        return index

    def _add_page(self, relative: Path, text: str) -> None:
        heading_titles: list[str] = []
        block_ids: list[str] = []
        seen_blocks: dict[str, int] = {}
        for line_number, line in body_lines(text):
            heading = _HEADING_RE.match(line)
            if heading:
                title = visible_text(heading.group(2))
                heading_titles.append(title)
            block = _BLOCK_RE.search(line)
            if block:
                block_id = block.group(1)
                if block_id in seen_blocks:
                    self.diagnostics.append(
                        Diagnostic(
                            "E_BLOCK_DUPLICATE",
                            SourceSpan(relative, line_number, max(1, line.rfind("^") + 1)),
                            f"块 ID “{block_id}”在同一页面中重复。",
                        )
                    )
                else:
                    seen_blocks[block_id] = line_number
                    block_ids.append(block_id)
        headings = list(zip(heading_titles, unique_toc_slugs(heading_titles), strict=True))
        logical = relative.with_suffix("").as_posix()
        record = PageRecord(
            relative,
            relative.with_suffix(".md"),
            logical,
            relative.stem,
            tuple(headings),
            tuple(block_ids),
        )
        self.pages[relative] = record
        self._by_logical.setdefault(logical, []).append(record)
        self._by_name.setdefault(relative.stem, []).append(record)

    def _page_at(self, candidate: Path) -> PageRecord | None:
        candidate = _normalize_candidate(candidate)
        if candidate is None:
            return None
        if candidate.suffix.casefold() != ".md":
            candidate = Path(f"{candidate.as_posix()}.md")
        return self.pages.get(candidate)

    def _attachment_at(self, candidate: Path) -> AttachmentRecord | None:
        candidate = _normalize_candidate(candidate)
        return self.attachments.get(candidate) if candidate is not None else None

    def current_page(self, current: Path) -> PageRecord | None:
        return self._page_at(current)

    def case_variants(self, path: Path, *, page: bool) -> list[Path]:
        normalized = _normalize_candidate(path)
        if normalized is None:
            return []
        if page and normalized.suffix.casefold() != ".md":
            normalized = Path(f"{normalized.as_posix()}.md")
        wanted = normalized.as_posix().casefold()
        values = self.pages if page else self.attachments
        if page and "/" not in normalized.as_posix():
            return [candidate for candidate in values if candidate.stem.casefold() == normalized.stem.casefold()]
        return [candidate for candidate in values if candidate.as_posix().casefold() == wanted]

    def resolve_page_candidates(self, current: Path, target: str) -> list[PageRecord]:
        target = target.replace("\\", "/")
        normalized_target = _normalize_candidate(target)
        if normalized_target is None:
            return []
        candidates: list[PageRecord] = []
        explicit = target.startswith("./") or target.startswith("../")
        has_path = "/" in target
        if explicit or has_path:
            paths = []
            if explicit or has_path:
                paths.append(_relative(current.parent / normalized_target))
            if has_path and not explicit:
                paths.append(_relative(normalized_target))
            for path in paths:
                record = self._page_at(path)
                if record and record not in candidates:
                    candidates.append(record)
            return candidates[:1]

        local = self._page_at(current.parent / target)
        if local:
            return [local]
        return list(self._by_name.get(Path(target).stem, []))

    def resolve_attachment_candidates(self, current: Path, target: str) -> list[AttachmentRecord]:
        target = target.replace("\\", "/")
        normalized_target = _normalize_candidate(target)
        if normalized_target is None:
            return []
        candidates: list[AttachmentRecord] = []
        explicit = target.startswith("./") or target.startswith("../")
        has_path = "/" in target
        if explicit or has_path:
            paths = [_relative(current.parent / normalized_target)]
            if has_path and not explicit:
                paths.append(_relative(normalized_target))
            for path in paths:
                record = self._attachment_at(path)
                if record and record not in candidates:
                    candidates.append(record)
            return candidates[:1]
        local = self._attachment_at(current.parent / target)
        if local:
            return [local]
        return list(self._attachments_by_name.get(Path(target).name, []))

    def page_heading(self, record: PageRecord, anchor: str) -> tuple[str, str] | None:
        wanted = anchor.removeprefix("#")
        by_text = [heading for heading in record.headings if heading[0] == wanted]
        if len(by_text) == 1:
            return by_text[0]
        by_slug = [heading for heading in record.headings if heading[1] == wanted]
        if len(by_slug) == 1:
            return by_slug[0]
        return None

    def page_heading_count(self, record: PageRecord, anchor: str) -> int:
        wanted = anchor.removeprefix("#")
        return sum(heading[0] == wanted or heading[1] == wanted for heading in record.headings)
