from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from .index import _IMAGE_SUFFIXES, VaultIndex
from .models import ConversionResult, Diagnostic, Reference, ResolvedTarget, SourceSpan

_CALLOUT_RE = re.compile(
    r"^(?P<prefix>[ \t]*)>[ \t]*\[!(?P<kind>[A-Za-z]+)(?P<collapse>[+-])?\][ \t]*(?P<title>.*)$"
)
_BLOCK_RE = re.compile(r"(?:^|\s)\^([A-Za-z0-9_-]+)[ \t]*$")
_SUPPORTED_CALLOUTS = {"note", "question", "warning", "example"}
_LIST_RE = re.compile(r"^(?P<indent>[ \t]*)(?:[-+*]|\d+[.)])[ \t]+")


def _relative_url(current: Path, target: Path) -> str:
    value = PurePosixPath(target.as_posix())
    base = PurePosixPath(current.as_posix()).parent
    import posixpath

    relative = PurePosixPath(*posixpath.relpath(value.as_posix(), base.as_posix()).split("/"))
    return quote(relative.as_posix(), safe="/-._~()!$&'*,;=:@")


def _normalize_loose_lists(text: str) -> str:
    """Add only the blank lines Python-Markdown needs before loose lists."""
    lines = text.splitlines(keepends=True)
    result: list[str] = []
    fence: str | None = None
    frontmatter = bool(lines and lines[0].strip() == "---")
    in_frontmatter = frontmatter
    for line in lines:
        body = line.rstrip("\r\n")
        stripped = body.lstrip()
        if in_frontmatter:
            result.append(line)
            if len(result) > 1 and body.strip() == "---":
                in_frontmatter = False
            continue
        if fence is not None:
            result.append(line)
            if re.match(re.escape(fence) + r"{3,}[ \t]*$", stripped):
                fence = None
            continue
        opening = re.match(r"(`{3,}|~{3,})", stripped)
        if opening:
            fence = opening.group(1)[0]
            result.append(line)
            continue
        current = _LIST_RE.match(body)
        if current and result:
            previous = result[-1].rstrip("\r\n")
            previous_is_list = bool(_LIST_RE.match(previous))
            previous_is_admonition = previous.lstrip().startswith("!!! ")
            if previous and not previous_is_list and not previous_is_admonition:
                result.append("\n")
        result.append(line)
    return "".join(result)


class Converter:
    def __init__(self, index: VaultIndex):
        self.index = index

    def convert(self, source_path: Path, text: str) -> ConversionResult:
        lines = text.splitlines(keepends=True)
        output: list[str] = []
        diagnostics: list[Diagnostic] = []
        references: list[Reference] = []
        fence: str | None = None
        frontmatter = bool(lines and lines[0].strip() == "---")
        in_frontmatter = frontmatter
        line_number = 0
        index = 0
        while index < len(lines):
            raw = lines[index]
            line_number = index + 1
            body = raw.rstrip("\r\n")
            newline = raw[len(body) :]
            stripped = body.lstrip()

            if in_frontmatter:
                output.append(raw)
                if line_number > 1 and body.strip() == "---":
                    in_frontmatter = False
                index += 1
                continue

            if fence is not None:
                output.append(raw)
                if re.match(re.escape(fence) + r"{3,}[ \t]*$", stripped):
                    fence = None
                index += 1
                continue
            fence_match = re.match(r"(`{3,}|~{3,})", stripped)
            if fence_match:
                fence = fence_match.group(1)[0]
                output.append(raw)
                index += 1
                continue

            callout = _CALLOUT_RE.match(body)
            if callout:
                kind = callout.group("kind").casefold()
                if kind not in _SUPPORTED_CALLOUTS:
                    diagnostics.append(
                        Diagnostic(
                            "E_UNSUPPORTED_CALLOUT",
                            SourceSpan(source_path, line_number, body.find("[!") + 1),
                            f"不支持的 Callout 类型 “{kind}”。",
                        )
                    )
                    output.append(raw)
                    index += 1
                    continue
                if callout.group("collapse"):
                    diagnostics.append(
                        Diagnostic(
                            "E_UNSUPPORTED_CALLOUT_COLLAPSE",
                            SourceSpan(source_path, line_number, body.find("[!") + 1),
                            "首期不支持折叠 Callout。",
                        )
                    )
                title = callout.group("title").strip()
                title_part = f' "{title.replace(chr(34), chr(92) + chr(34))}"' if title else ""
                output.append(f"!!! {kind}{title_part}\n")
                index += 1
                while index < len(lines):
                    nested_raw = lines[index]
                    nested_body = nested_raw.rstrip("\r\n")
                    nested_match = re.match(r"^\s*>[ \t]?(.*)$", nested_body)
                    if not nested_match:
                        break
                    nested_text = nested_match.group(1)
                    converted, inline_diags, inline_refs = self._convert_inline(
                        source_path, index + 1, nested_text, source_path
                    )
                    diagnostics.extend(inline_diags)
                    references.extend(inline_refs)
                    output.append((f"    {converted}" if converted else "") + "\n")
                    index += 1
                continue

            anchor = _BLOCK_RE.search(body)
            if anchor:
                block_id = anchor.group(1)
                output.append(f'<a id="^{block_id}"></a>\n')
                body = body[: anchor.start()] + body[anchor.end() :]
                body = body.rstrip()
            converted, inline_diags, inline_refs = self._convert_inline(
                source_path, line_number, body, source_path
            )
            diagnostics.extend(inline_diags)
            references.extend(inline_refs)
            output.append(converted + newline)
            index += 1

        if fence is not None:
            diagnostics.append(
                Diagnostic("E_UNCLOSED_FENCE", SourceSpan(source_path, len(lines), 1), "代码围栏未闭合。")
            )
        return ConversionResult(_normalize_loose_lists("".join(output)), diagnostics, references)

    def _convert_inline(
        self, source_path: Path, line_number: int, text: str, current: Path
    ) -> tuple[str, list[Diagnostic], list[Reference]]:
        result: list[str] = []
        diagnostics: list[Diagnostic] = []
        references: list[Reference] = []
        index = 0
        while index < len(text):
            if text[index] == "`":
                run = 1
                while index + run < len(text) and text[index + run] == "`":
                    run += 1
                closing = text.find("`" * run, index + run)
                if closing < 0:
                    result.append(text[index:])
                    break
                result.append(text[index : closing + run])
                index = closing + run
                continue
            marker = "![[" if text.startswith("![[", index) else "[[" if text.startswith("[[", index) else None
            if marker:
                end = text.find("]]", index + len(marker))
                span = SourceSpan(source_path, line_number, index + 1)
                if end < 0:
                    diagnostics.append(Diagnostic("E_UNCLOSED_LINK", span, "双链语法未闭合。"))
                    result.append(text[index:])
                    break
                raw_target = text[index + len(marker) : end]
                reference, replacement, ref_diags = self._resolve_reference(
                    current, raw_target, marker == "![[", span
                )
                references.append(reference)
                diagnostics.extend(ref_diags)
                result.append(replacement)
                index = end + 2
                continue
            if text.startswith("==", index):
                end = text.find("==", index + 2)
                span = SourceSpan(source_path, line_number, index + 1)
                if end < 0:
                    diagnostics.append(Diagnostic("E_UNCLOSED_HIGHLIGHT", span, "高亮语法未闭合。"))
                    result.append(text[index:])
                    break
                inner, inner_diags, inner_refs = self._convert_inline(
                    source_path, line_number, text[index + 2 : end], current
                )
                diagnostics.extend(
                    Diagnostic(
                        item.code,
                        SourceSpan(item.span.path, item.span.line, item.span.column + index + 2),
                        item.message,
                        item.candidates,
                    )
                    for item in inner_diags
                )
                references.extend(
                    Reference(item.kind, item.target, item.alias, item.anchor, SourceSpan(item.span.path, item.span.line, item.span.column + index + 2))
                    for item in inner_refs
                )
                result.append(f"<mark>{inner}</mark>")
                index = end + 2
                continue
            result.append(text[index])
            index += 1
        return "".join(result), diagnostics, references

    def _resolve_reference(
        self, current: Path, raw_target: str, is_embed: bool, span: SourceSpan
    ) -> tuple[Reference, str, list[Diagnostic]]:
        alias = None
        target = raw_target
        if "|" in raw_target:
            target, alias = raw_target.split("|", 1)
            target = target.strip()
            alias = alias.strip()
        anchor = None
        if "#" in target:
            target, anchor = target.split("#", 1)
        target = target.strip()
        ref = Reference("embed" if is_embed else "link", target, alias, anchor, span)
        diagnostics: list[Diagnostic] = []

        if is_embed and alias:
            diagnostics.append(Diagnostic("E_UNSUPPORTED_EMBED_OPTION", span, "首期不支持附件嵌入尺寸或其他选项。"))
        suffix = Path(target).suffix.casefold()
        attachment_candidates = self.index.resolve_attachment_candidates(current, target)
        page_candidates = self.index.resolve_page_candidates(current, target)
        if is_embed and suffix not in _IMAGE_SUFFIXES and not attachment_candidates:
            diagnostics.append(Diagnostic("E_UNSUPPORTED_PAGE_EMBED", span, "首期不支持页面嵌入。"))
            return ref, raw_target, diagnostics

        if is_embed and suffix in _IMAGE_SUFFIXES or (is_embed and attachment_candidates):
            if not attachment_candidates:
                variants = self.index.case_variants(Path(target), page=False)
                if variants:
                    diagnostics.append(
                        Diagnostic(
                            "E_CASE_MISMATCH",
                            span,
                            f"附件路径大小写不一致，应使用 “{variants[0].as_posix()}”。",
                            tuple(variants),
                        )
                    )
                else:
                    diagnostics.append(Diagnostic("E_ATTACHMENT_MISSING", span, f"找不到附件 “{target}”。"))
                return ref, raw_target, diagnostics
            if len(attachment_candidates) > 1:
                diagnostics.append(Diagnostic("E_ATTACHMENT_AMBIGUOUS", span, f"附件 “{target}”匹配到多个文件。", tuple(v.source_path for v in attachment_candidates)))
                return ref, raw_target, diagnostics
            record = attachment_candidates[0]
            href = _relative_url(current, record.output_path)
            label = alias or Path(target).name
            if is_embed:
                return ref, f"![{label}]({href})", diagnostics
            return ref, f"[{label}]({href})", diagnostics

        if not page_candidates:
            variants = self.index.case_variants(Path(target), page=True)
            if variants:
                diagnostics.append(Diagnostic("E_CASE_MISMATCH", span, f"页面路径大小写不一致，应使用 “{variants[0].as_posix()}”。", tuple(variants)))
            else:
                diagnostics.append(Diagnostic("E_LINK_MISSING", span, f"找不到页面 “{target}”。"))
            return ref, raw_target, diagnostics
        if len(page_candidates) > 1:
            diagnostics.append(Diagnostic("E_LINK_AMBIGUOUS", span, f"“{target}”匹配到多个页面，请写明路径。", tuple(v.source_path for v in page_candidates)))
            return ref, raw_target, diagnostics
        record = page_candidates[0]
        fragment = None
        if anchor:
            if anchor.startswith("^"):
                if anchor[1:] not in record.block_ids:
                    diagnostics.append(Diagnostic("E_BLOCK_MISSING", span, f"页面 “{record.source_path.as_posix()}”不存在块 ID “{anchor}”。"))
                fragment = anchor
            else:
                count = self.index.page_heading_count(record, anchor)
                heading = self.index.page_heading(record, anchor)
                if count == 0 or heading is None:
                    diagnostics.append(Diagnostic("E_ANCHOR_MISSING", span, f"页面 “{record.source_path.as_posix()}”不存在标题 “{anchor}”。"))
                elif count > 1:
                    diagnostics.append(Diagnostic("E_ANCHOR_AMBIGUOUS", span, f"页面 “{record.source_path.as_posix()}”中的标题 “{anchor}”重复。"))
                else:
                    fragment = heading[1]
        href = _relative_url(current, record.output_path)
        if fragment:
            href += "#" + quote(fragment, safe="-._~^")
        label = alias or Path(target).stem
        return ref, f"[{label}]({href})", diagnostics
