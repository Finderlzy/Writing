from __future__ import annotations

import re
import unicodedata


def visible_text(text: str) -> str:
    """Return the text used by Markdown's heading slugger."""
    text = re.sub(r"!?(\[\[)(.*?)(\]\])", lambda match: match.group(2).split("|")[-1], text)
    text = re.sub(r"!?\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"<[^>]*>", "", text)
    return text.strip()


def toc_slug(text: str) -> str:
    """Match Python-Markdown's Unicode TOC slug shape for this site."""
    value = unicodedata.normalize("NFKD", visible_text(text))
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^\w\s-]", "", value).strip()
    value = re.sub(r"[-\s]+", "-", value)
    return value


_IDCOUNT_RE = re.compile(r"^(.*)_([0-9]+)$")


def unique_toc_slugs(headings: list[str]) -> list[str]:
    """Match Python-Markdown's toc.unique(): duplicates get _1, _2, ..."""
    used: set[str] = set()
    result: list[str] = []
    for title in headings:
        candidate = toc_slug(title)
        while candidate in used or not candidate:
            match = _IDCOUNT_RE.match(candidate)
            if match:
                candidate = f"{match.group(1)}_{int(match.group(2)) + 1}"
            else:
                candidate = f"{candidate}_1"
        used.add(candidate)
        result.append(candidate)
    return result
