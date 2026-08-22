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


def unique_toc_slugs(headings: list[str]) -> list[str]:
    used: set[str] = set()
    result: list[str] = []
    for title in headings:
        base = toc_slug(title)
        candidate = base or "_1"
        suffix = 1
        while candidate in used:
            suffix += 1
            candidate = f"{base}_{suffix}" if base else f"_{suffix}"
        used.add(candidate)
        result.append(candidate)
    return result
