from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceSpan:
    path: Path
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.path.as_posix()}:{self.line}:{self.column}"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    span: SourceSpan
    message: str
    candidates: tuple[Path, ...] = ()

    def format(self) -> str:
        lines = [f"{self.span}\n[{self.code}] {self.message}"]
        lines.extend(f"- {candidate.as_posix()}" for candidate in self.candidates)
        return "\n".join(lines)


@dataclass(frozen=True)
class Reference:
    kind: str
    target: str
    alias: str | None
    anchor: str | None
    span: SourceSpan


@dataclass(frozen=True)
class ResolvedTarget:
    source_path: Path
    output_path: Path
    fragment: str | None = None


@dataclass
class ConversionResult:
    text: str
    diagnostics: list[Diagnostic] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)


@dataclass(frozen=True)
class PageRecord:
    source_path: Path
    output_path: Path
    logical_path: str
    file_name: str
    headings: tuple[tuple[str, str], ...]
    block_ids: tuple[str, ...]


@dataclass(frozen=True)
class AttachmentRecord:
    source_path: Path
    output_path: Path

