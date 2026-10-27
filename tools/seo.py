"""What search engines and link previews read: page metadata and `sitemap.xml`.

`page_meta` gives each page its canonical address, a description, a preview image
and JSON-LD; `base.html` writes them into `<head>`. `write_sitemap` lists every
public page with its last change. Addresses here are always absolute, built from
`site_url`, because crawlers and chat apps read them out of context.
"""

from __future__ import annotations

import json
import re
from html import escape, unescape
from pathlib import Path
from urllib.parse import quote, urljoin

DESCRIPTION_CHARS = 120
SITEMAP = "sitemap.xml"
# 文章里没有图片时，链接预览用的图：顶栏那颗星星的 PNG（SVG 很多平台不认）
FALLBACK_IMAGE = "assets/theme/apple-touch-icon.png"

_PARAGRAPH_RE = re.compile(r"<p\b(?![^>]*admonition-title)[^>]*>(.*?)</p>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_IMG_RE = re.compile(r"<img\b[^>]*\bsrc=\"([^\"]+)\"", re.I)


def absolute_url(site_url: str, url: str) -> str:
    """`site_url` plus a site-relative address such as "blog/vless-reality/"."""
    return site_url.rstrip("/") + "/" + quote(url, safe="/-._~%")


def excerpt(html: str, limit: int = DESCRIPTION_CHARS) -> str:
    """The first `limit` characters of the body's plain text, for pages without a description.

    Only paragraphs count: headings, code, tables and callout titles read badly in a
    search result.
    """
    text = unescape(_TAG_RE.sub("", " ".join(_PARAGRAPH_RE.findall(html))))
    text = _SPACE_RE.sub(" ", text.replace("\\(", "").replace("\\)", "")).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def first_image(site_url: str, url: str, html: str) -> str:
    """The absolute address of the body's first image, or "" when it has none."""
    match = _IMG_RE.search(html)
    if not match:
        return ""
    src = unescape(match.group(1))
    if re.match(r"[a-z]+:", src, re.I):
        return src
    return urljoin(absolute_url(site_url, url), src)


def page_meta(config, page) -> dict:
    """The `<head>` values of one page; `page` is a `render.Page`, `config` a `render.SiteConfig`.

    The 404 page gets only a description and `noindex`: it has no address of its own.
    """
    site_url = config.site_url
    article = page.article
    if page.url == "404.html":
        return {"noindex": True, "description": config.description}
    if article is not None:
        description = article.description or excerpt(page.body) or config.description
    elif page.url == "":
        description = config.description or page.headline
    else:
        description = f"{config.site_name} 的全部 {page.total} 篇文章，可以按阶段和主题筛选。"
    image = (first_image(site_url, page.url, page.body) if article else "") or absolute_url(site_url, FALLBACK_IMAGE)
    canonical = absolute_url(site_url, page.url)
    meta = {
        "noindex": False,
        "canonical": canonical,
        "description": description,
        "type": "article" if article else "website",
        "image": image,
        "large_image": article is not None and not image.endswith(FALLBACK_IMAGE),
        "published": article.date.isoformat() if article and article.date else "",
        "modified": (article.updated or article.date).isoformat() if article and (article.updated or article.date) else "",
    }
    meta["json_ld"] = _json_ld(config, page, meta)
    return meta


def _json_ld(config, page, meta: dict) -> str:
    author = {"@type": "Person", "name": config.author or config.site_name}
    if page.article is None:
        data = {
            "@context": "https://schema.org",
            "@type": "WebSite" if page.url == "" else "CollectionPage",
            "name": config.site_name if page.url == "" else page.title,
            "url": meta["canonical"],
            "description": meta["description"],
            "inLanguage": "zh-CN",
            "author": author,
        }
    else:
        data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": page.title,
            "description": meta["description"],
            "url": meta["canonical"],
            "mainEntityOfPage": meta["canonical"],
            "image": meta["image"],
            "inLanguage": "zh-CN",
            "author": author,
            "keywords": list(page.article.tags),
        }
        if meta["published"]:
            data["datePublished"] = meta["published"]
        if meta["modified"]:
            data["dateModified"] = meta["modified"]
    # 放进 <script> 里：只要不出现 "</" 就不会提前结束标签
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def sitemap_xml(site_url: str, entries: list[tuple[str, str]]) -> str:
    """A sitemap from (site-relative address, last change as YYYY-MM-DD or "")."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod in entries:
        lines.append(f"  <url><loc>{escape(absolute_url(site_url, url))}</loc>" + (f"<lastmod>{lastmod}</lastmod>" if lastmod else "") + "</url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def write_sitemap(site: Path, site_url: str, pages) -> None:
    """Write `sitemap.xml` for the home page, the article list and every article.

    The home page and the list change whenever an article does, so they take the newest date.
    """
    entries: list[tuple[str, str]] = []
    dates = [meta for meta in (_lastmod(page) for page in pages) if meta]
    newest = max(dates) if dates else ""
    for page in pages:
        entries.append((page.url, _lastmod(page) if page.article else newest))
    (site / SITEMAP).write_text(sitemap_xml(site_url, entries), encoding="utf-8", newline="")


def _lastmod(page) -> str:
    article = page.article
    day = (article.updated or article.date) if article else None
    return day.isoformat() if day else ""
