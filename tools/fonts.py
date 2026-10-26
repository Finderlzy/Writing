"""Self-hosted fonts for the section headings and labels (R-VIS-5).

Four font roles, each a `FontSpec`. The build scans the generated HTML for
`data-font` attributes, collects the characters each role has to draw, and writes
one small woff2 per role into `site/assets/fonts/`. The body text never loads a
web font: it uses the reader's system fonts ("PingFang SC", "Microsoft YaHei", …).

Source fonts are not committed. CI downloads them from google/fonts at a fixed
commit and checks the SHA-256 (`.github/workflows/deploy.yml`); locally run
`python tools/fetch_fonts.py` once to fill `.cache/fonts/`. `FONT_SOURCE_DIR`
overrides both.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from .obsidian_compat.models import Diagnostic, SourceSpan

ROOT = Path(__file__).resolve().parents[1]
# 本地缓存源字体的位置（.gitignore 里已有 .cache/）
CACHE_FONTS = ROOT / ".cache" / "fonts"
# 产物的网址前缀，site.css 用 ../fonts/<output>.woff2 引用
FONTS_URL_DIR = "assets/fonts"
FONT_BUDGET_BYTES = 300 * 1024

# 模板里 data-font 的合法取值：head（很粗的标题）、cute（手写味的中文标题）、
# slab（英文数字和日期）、hand（手写英文短句）。其余取值报 E_FONT_ROLE_UNKNOWN。
ROLE_NAMES = ("head", "cute", "slab", "hand")

# 可打印 ASCII，slab 的固定字靠它，模板里不用给每个字符写一遍
_PRINTABLE_ASCII = "".join(chr(code) for code in range(32, 127))


@dataclass(frozen=True)
class FontSpec:
    """One role: where the source font is, what it is called in CSS, what it must contain."""

    role: str  # "head" | "cute" | "slab" | "hand"，对应模板里的 data-font 属性
    source: Path  # 源字体文件
    output: str  # 写到 site/assets/fonts/<output>.woff2
    text: str = ""  # 固定要带的字；模板里没写 data-font 的数字、标点靠它
    weight: int | None = None  # 可变字体固定到的 wght；静态字体保持原样
    optional: tuple[str, ...] = ()  # 只在源字体里出现过的字：有就收，没有不报错
    family: str = ""  # @font-face 的家族名；默认用源字体自己的名字

    @property
    def label(self) -> str:
        return f"{self.role}（{self.output}）"


def source_dir() -> Path:
    """Where the source fonts are: `FONT_SOURCE_DIR` if set, otherwise `.cache/fonts/`."""
    configured = os.environ.get("FONT_SOURCE_DIR", "").strip()
    return Path(configured) if configured else CACHE_FONTS


def default_specs(directory: Path | None = None) -> tuple[FontSpec, ...]:
    """The four roles of this site, with the fixed text each role needs.

    Sources are read from `directory` when given (tests), otherwise from `source_dir()`.
    """
    root = Path(directory) if directory is not None else source_dir()
    return (
        FontSpec(
            role="head",
            source=root / "NotoSansSC[wght].ttf",
            output="head",
            # 模板里用 head 的粗字有“博客与作品”“首页”“全部文章”和页脚的站名，
            # 页面里没有 data-font 的数字和标点也靠它补齐
            text="首页全部文章博客与作品0123456789 ·—",
            weight=900,
            family="Noto Sans SC",
        ),
        FontSpec(
            role="cute",
            source=root / "ZCOOLKuaiLe-Regular.ttf",
            output="cute",
            text="博客与作品留言复制404页面不存在",
            family="ZCOOL KuaiLe",
        ),
        FontSpec(
            role="slab",
            source=root / "ZillaSlab-SemiBold.ttf",
            output="slab-600",
            text=_PRINTABLE_ASCII + "·—×“”·",
            weight=600,
            family="Zilla Slab Lzy",
        ),
        FontSpec(
            role="slab",
            source=root / "ZillaSlab-Bold.ttf",
            output="slab-700",
            text=_PRINTABLE_ASCII,
            weight=700,
            family="Zilla Slab Lzy",
        ),
        FontSpec(
            role="hand",
            source=root / "GochiHand-Regular.ttf",
            output="hand",
            text="yep!",
            family="Gochi Hand",
        ),
    )


class _DataFontCollector(HTMLParser):
    """Collect the text under every element that has a `data-font` attribute.

    The attribute applies to the element and all of its children until the
    matching end tag; nested `data-font` attributes win for their own subtree.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chars: dict[str, set[str]] = {}
        self.unknown: set[str] = set()
        self.roles = set(ROLE_NAMES)
        # 每层标签记下它当时生效的角色；None 表示这一层不加字
        self._roles: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        role = next((value for name, value in attrs if name == "data-font" and value), None)
        if role is not None:
            role = role.strip()
            if role not in ROLE_NAMES:
                self.unknown.add(role)
        else:
            role = self._current_role()
        self._roles.append((tag, role))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # <img data-font="…"> 这类自闭合标签：不算打开一层，里面的字本来也不会有
        role = next((value for name, value in attrs if name == "data-font" and value), None)
        if role is not None and role.strip() not in ROLE_NAMES:
            self.unknown.add(role.strip())

    def handle_endtag(self, tag: str) -> None:
        # 容错：遇到对不上的结束标签时一直弹到匹配的那一层
        for index in range(len(self._roles) - 1, -1, -1):
            if self._roles[index][0] == tag:
                del self._roles[index:]
                return

    def handle_data(self, data: str) -> None:
        role = self._current_role()
        # 不认识的 role 只在 unknown 里留个记号，字不收（报错后模板要改）
        if role is None or role not in self.roles:
            return
        bucket = self.chars.setdefault(role, set())
        bucket.update(char for char in data if not char.isspace())

    def _current_role(self) -> str | None:
        for _, role in reversed(self._roles):
            if role is not None:
                return role
        return None


def collect_chars(site: Path) -> dict[str, set[str]]:
    """Scan every `site/**/*.html` and return the characters each font role must draw."""
    site = Path(site)
    collected: dict[str, set[str]] = {}
    for path in sorted(site.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        parser = _DataFontCollector()
        parser.feed(text)
        parser.close()
        for role, chars in parser.chars.items():
            collected.setdefault(role, set()).update(chars)
        # 不认识的取值直接扔掉；诊断由 subset_fonts 统一报
    return collected


def unknown_roles(site: Path) -> set[str]:
    """`data-font` values used in the pages that are not one of `ROLE_NAMES`."""
    site = Path(site)
    found: set[str] = set()
    for path in sorted(site.rglob("*.html")):
        parser = _DataFontCollector()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.close()
        found |= parser.unknown
    return found


def _subset_options():
    from fontTools import subset

    options = subset.Options()
    # 体积相关的三项按 V0 的实测写死（architecture.md §7.1）：不设 name_IDs 会多带
    # copyright、license 等条目；全开 layout_features 会把 palt、halt 之类带进来
    options.name_IDs = [1, 2, 4, 6]
    options.name_languages = [0x409]
    options.notdef_outline = True
    options.drop_tables += ["FFTM"]
    options.flavor = "woff2"
    options.with_zopfli = False
    return options


def _subset(font, text: str, options) -> None:
    from fontTools import subset

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)


def _rename(font, family: str | None, weight: int | None) -> None:
    """Give the subset the family name CSS uses and the weight the browser matches on."""
    if family:
        # fontTools 的 name 表按 (platformID, platEncID, langID, nameID) 组织：
        # 1 = family，4 = full name，16 = typographic family。两个 Zilla Slab 要共用
        # 一个家族名，浏览器才会把它们当成同一家族的两个字重。
        for record in font["name"].names:
            if record.nameID == 1:
                record.string = family
            elif record.nameID == 16:
                record.string = family
            elif record.nameID == 4 and weight is not None:
                record.string = f"{family} {weight}"
    if weight is not None and "OS/2" in font:
        os2 = font["OS/2"]
        head = font["head"]
        bold = weight >= 600
        # fsSelection 的 bit 0 italic、bit 5 bold、bit 6 regular 互斥，还要和 head.macStyle
        # 的 bit 0 bold、bit 1 italic 对得上，否则 fontTools 保存时会打警告。这里统一设一次。
        os2.fsSelection &= ~(0b1 | 0b100000 | 0b1000000)
        os2.fsSelection |= 0b100000 if bold else 0b1000000
        head.macStyle = (head.macStyle & ~0b11) | (0b1 if bold else 0)
        os2.usWeightClass = weight


def _codepoints(spec: FontSpec, chars: Iterable[str]) -> set[int]:
    """Which characters of the required and fixed text the source font actually has."""
    from fontTools.ttLib import TTFont

    font = TTFont(str(spec.source), lazy=True)
    try:
        cmap = font.getBestCmap() or {}
    finally:
        font.close()
    return {ord(char) for char in chars if ord(char) in cmap}


def _required_chars(spec: FontSpec, collected: Mapping[str, set[str]]) -> str:
    chars = set(spec.text) | set(collected.get(spec.role, set()))
    return "".join(sorted(chars))


def subset_one(spec: FontSpec, chars: str | Iterable[str] | None = None, *, destination: Path | None = None) -> Path:
    """Write the woff2 of `spec`; the output goes to `destination` or next to the source.

    With `chars` empty the file still contains the spec's fixed text, so a role that
    no page uses yet still gets a file and the CSS reference never 404s.
    """
    from fontTools import subset
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.ttLib import TTFont

    text = "".join(sorted(set(chars if chars is not None else spec.text)))
    if not text:
        text = ""  # 完全没有字时只留 .notdef，仍是合法的 woff2
    font = TTFont(str(spec.source))
    options = _subset_options()
    # 顺序很重要（V0 实测）：先子集化可变字体，再把剩下的字形固定到目标字重，
    # 反过来会重算全部 3 万多个字形，慢 20 倍以上
    _subset(font, text, options)
    if spec.weight is not None and "fvar" in font:
        instantiateVariableFont(font, {"wght": spec.weight}, inplace=True, optimize=False)
    _rename(font, spec.family or None, spec.weight)
    target = destination if destination is not None else ROOT / "site" / FONTS_URL_DIR / f"{spec.output}.woff2"
    target.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(str(target))
    font.close()
    return target


def subset_fonts(
    site: Path,
    specs: Iterable[FontSpec] | None = None,
    *,
    collected: Mapping[str, set[str]] | None = None,
) -> list[Diagnostic]:
    """Collect the characters each role needs and write one woff2 per spec.

    `site` is the build output; files go to `<site>/assets/fonts/<output>.woff2`.
    `collected` overrides the HTML scan (tests build one by hand).
    Returns the diagnostics: `E_FONT_SOURCE_MISSING` and `E_FONT_ROLE_UNKNOWN` stop
    the build; `W_FONT_GLYPH_MISSING` and `W_FONT_BUDGET` only warn.
    """
    site = Path(site)
    specs = tuple(specs) if specs is not None else default_specs()
    found: list[Diagnostic] = []

    if collected is None:
        collected = collect_chars(site)
        for role in sorted(unknown_roles(site)):
            found.append(
                Diagnostic(
                    "E_FONT_ROLE_UNKNOWN",
                    SourceSpan(site, 1, 1),
                    f"模板里有 data-font=\"{role}\"，不是 {', '.join(ROLE_NAMES)} 中的一个；"
                    "这个元素的字会退回系统字体。",
                )
            )

    missing_sources = [spec for spec in specs if not spec.source.is_file()]
    for spec in missing_sources:
        found.append(
            Diagnostic(
                "E_FONT_SOURCE_MISSING",
                SourceSpan(spec.source, 1, 1),
                f"找不到 {spec.role} 角色的源字体，先运行 python tools/fetch_fonts.py，"
                f"或者把 FONT_SOURCE_DIR 指向放源字体的目录（也可以用 python tools/build_site.py --skip-fonts 跳过）。",
            )
        )
    if missing_sources:
        return found  # 源字体不齐就不生成任何文件，免得写出一份半成品

    written: list[tuple[FontSpec, Path]] = []
    for spec in specs:
        required = _required_chars(spec, collected)
        covered = _codepoints(spec, required + "".join(spec.optional)) if required or spec.optional else set()
        absent = sorted(char for char in required if ord(char) not in covered)
        if absent:
            found.append(
                Diagnostic(
                    "W_FONT_GLYPH_MISSING",
                    SourceSpan(spec.source, 1, 1),
                    f"{spec.role} 角色的源字体里没有这些字：{''.join(absent)}；它们会退回字体栈里的下一个字体。",
                )
            )
        target = subset_one(spec, required, destination=site / FONTS_URL_DIR / f"{spec.output}.woff2")
        written.append((spec, target))

    total = sum(path.stat().st_size for _, path in written)
    if total > FONT_BUDGET_BYTES:
        detail = "，".join(f"{spec.output}.woff2 {path.stat().st_size:,} B" for spec, path in written)
        found.append(
            Diagnostic(
                "W_FONT_BUDGET",
                SourceSpan(site / FONTS_URL_DIR, 1, 1),
                f"字体合计 {total:,} B（{detail}），超过 {FONT_BUDGET_BYTES:,} B 的预算。"
                "文章标题变多时 woff2 会跟着变大，需要检查是不是收字范围失控了。",
            )
        )
    return found
