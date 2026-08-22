from __future__ import annotations

import re
from pathlib import Path

from .models import Diagnostic, SourceSpan

_RESIDUAL_RE = re.compile(r"!\[\[|\[\[|>\s*\[![A-Za-z]+\]")


def body_lines(text: str):
    """Yield non-frontmatter, non-fenced lines with their source positions."""
    lines = text.splitlines(keepends=True)
    start = 0
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                start = index + 1
                break
    fence: str | None = None
    for index in range(start, len(lines)):
        line = lines[index].rstrip("\r\n")
        stripped = line.lstrip()
        if fence is None:
            match = re.match(r"(`{3,}|~{3,})", stripped)
            if match:
                fence = match.group(1)[0]
                continue
            yield index + 1, line
        elif re.match(re.escape(fence) + r"{3,}[ \t]*$", stripped):
            fence = None


def strip_inline_code(text: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "`":
            result.append(text[index])
            index += 1
            continue
        run = 1
        while index + run < len(text) and text[index + run] == "`":
            run += 1
        end = text.find("`" * run, index + run)
        if end < 0:
            break
        result.append(" " * (end + run - index))
        index = end + run
    return "".join(result)


def residual_diagnostics(path: Path, text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for line_number, line in body_lines(text):
        visible = strip_inline_code(line)
        match = _RESIDUAL_RE.search(visible)
        if match:
            diagnostics.append(
                Diagnostic(
                    "E_RESIDUAL_OBSIDIAN",
                    SourceSpan(path, line_number, match.start() + 1),
                    "转换后仍残留受支持的 Obsidian 语法。",
                )
            )
    return diagnostics

