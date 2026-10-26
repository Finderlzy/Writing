from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

import tools.fonts as fonts
from tools.fonts import (
    ROLE_NAMES,
    FontSpec,
    collect_chars,
    default_specs,
    source_dir,
    subset_fonts,
    unknown_roles,
)


def _font_available(directory: Path, name: str) -> bool:
    return (directory / name).is_file()


def _write_html(root: Path, name: str, html: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


class CollectCharsTests(unittest.TestCase):
    def test_collects_text_of_tagged_elements_and_their_children(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            _write_html(
                site,
                "posts/index.html",
                """<!doctype html><html><body>
                <h1 data-font="head">全部文章</h1>
                <a class="why"><span data-font="slab">2026</span></a>
                <p data-font="cute">标题里的<b>粗体</b>也算</p>
                <p>没标 data-font 的正文不算</p>
                <button data-font="hand">yep!</button>
                </body></html>""",
            )
            chars = collect_chars(site)
            self.assertEqual({"全", "部", "文", "章"}, chars["head"])
            self.assertEqual({"2", "0", "6"}, chars["slab"])
            self.assertEqual({"标", "题", "里", "的", "粗", "体", "也", "算"}, chars["cute"])
            self.assertEqual({"y", "e", "p", "!"}, chars["hand"])
            # 没有 data-font 的文字不属于任何角色
            for role_chars in chars.values():
                self.assertNotIn("没", role_chars)

    def test_nested_data_font_overrides_the_outer_one(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            _write_html(
                site,
                "index.html",
                '<h2 data-font="head">外<span data-font="slab">内</span>外</h2>',
            )
            chars = collect_chars(site)
            self.assertEqual({"外"}, chars["head"])
            self.assertEqual({"内"}, chars["slab"])

    def test_sibling_elements_do_not_leak_into_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            _write_html(
                site,
                "index.html",
                '<h1 data-font="head">甲</h1><p>乙</p><time data-font="slab">丙</time>',
            )
            chars = collect_chars(site)
            self.assertEqual({"甲"}, chars["head"])
            self.assertEqual({"丙"}, chars["slab"])

    def test_scans_every_page_under_the_site(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            _write_html(site, "index.html", '<h1 data-font="head">首页</h1>')
            _write_html(site, "blog/a/index.html", '<h1 data-font="head">文章</h1>')
            _write_html(site, "404.html", '<h1 data-font="head">找不到</h1>')
            chars = collect_chars(site)
            self.assertEqual({"首", "页", "文", "章", "找", "不", "到"}, chars["head"])

    def test_unknown_role_is_reported_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            _write_html(site, "index.html", '<h1 data-font="head">甲</h1><p data-font="serif">乙</p>')
            self.assertEqual({"serif"}, unknown_roles(site))
            chars = collect_chars(site)
            self.assertNotIn("serif", chars)
            self.assertNotIn("乙", chars["head"])


class SubsetTests(unittest.TestCase):
    """子集化要真的干活：用 fontTools 读回 cmap，确认该有的字形在里面、不该有的不在。"""

    @classmethod
    def setUpClass(cls):
        cls.sources = source_dir()
        cls.available = all(_font_available(cls.sources, spec.source.name) for spec in default_specs(cls.sources))
        if not cls.available:
            raise unittest.SkipTest(
                f"源字体不在 {cls.sources}，先运行 python -m tools.fetch_fonts（或设置 FONT_SOURCE_DIR）"
            )

    def _run(self, html: str, specs=None) -> tuple[Path, list]:
        root = Path(tempfile.mkdtemp())
        site = root / "site"
        _write_html(site, "index.html", html)
        diagnostics = subset_fonts(site, specs if specs is not None else default_specs(self.sources))
        return site, diagnostics

    @staticmethod
    def _cmap(path: Path) -> set[int]:
        font = TTFont(str(path), lazy=True)
        try:
            return set((font.getBestCmap() or {}).keys())
        finally:
            font.close()

    def test_subset_contains_the_collected_glyphs_and_drops_the_rest(self):
        site, diagnostics = self._run('<h1 data-font="head">全部文章</h1><time data-font="slab">2026-10-21</time>')
        self.assertEqual([], [item.format() for item in diagnostics if not item.code.startswith("W_")])
        head = self._cmap(site / "assets/fonts/head.woff2")
        for char in "全部文章":
            self.assertIn(ord(char), head, f"head.woff2 里没有 {char}")
        # 随便一个字不该被带进去；“鼎”在正文语料里也没有
        self.assertNotIn(ord("鼎"), head)
        slab = self._cmap(site / "assets/fonts/slab-600.woff2")
        for char in "2026-10-21":
            self.assertIn(ord(char), slab)
        self.assertNotIn(ord("黑"), slab)

    def test_every_output_file_is_a_readable_woff2(self):
        site, _ = self._run('<h1 data-font="head">全部文章</h1>')
        files = sorted((site / "assets/fonts").glob("*.woff2"))
        self.assertEqual(
            {"cute.woff2", "hand.woff2", "head.woff2", "slab-600.woff2", "slab-700.woff2"},
            {path.name for path in files},
            "五个产物（四个角色、slab 两个字重）都该生成",
        )
        for path in files:
            font = TTFont(str(path), lazy=True)
            self.assertIn("cmap", font.reader.tables)
            self.assertIn("head", font.reader.tables)
            font.close()

    def test_unused_role_still_gets_a_file_with_its_fixed_text(self):
        # 页面里没有 cute 的元素：仍然生成文件，并带上固定字，CSS 引用不会 404
        site, diagnostics = self._run('<h1 data-font="head">全部文章</h1>')
        cute = site / "assets/fonts/cute.woff2"
        self.assertTrue(cute.is_file())
        cmap = self._cmap(cute)
        fixed = next(spec for spec in default_specs(self.sources) if spec.output == "cute").text
        self.assertTrue(fixed)
        for char in fixed:
            self.assertIn(ord(char), cmap, f"cute.woff2 没带上固定字 {char}")
        self.assertEqual([], [item.code for item in diagnostics if not item.code.startswith("W_")])

    def test_weight_is_fixed_so_the_browser_matches_the_family(self):
        site, _ = self._run('<h1 data-font="head">全部文章</h1>')
        for name, weight in (("slab-600.woff2", 600), ("slab-700.woff2", 700), ("head.woff2", 900)):
            font = TTFont(str(site / "assets/fonts" / name), lazy=True)
            self.assertNotIn("fvar", font.reader.tables, f"{name} 应该已经实例化，不再是可变字体")
            self.assertEqual(weight, font["OS/2"].usWeightClass)
            font.close()
        slab = TTFont(str(site / "assets/fonts/slab-600.woff2"), lazy=True)
        # 两个 Zilla Slab 必须共用一个家族名，浏览器才知道是同一家族的两个字重
        self.assertEqual("Zilla Slab Lzy", slab["name"].getDebugName(1))
        slab.close()

    def test_missing_source_font_fails_the_build(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory) / "site"
            _write_html(site, "index.html", '<h1 data-font="head">全部文章</h1>')
            missing = FontSpec(role="head", source=Path(directory) / "不存在.ttf", output="head", text="全部")
            diagnostics = subset_fonts(site, (missing,))
            codes = [item.code for item in diagnostics]
            self.assertEqual(["E_FONT_SOURCE_MISSING"], codes)
            self.assertIn("fetch_fonts", diagnostics[0].message)
            self.assertFalse((site / "assets/fonts/head.woff2").exists(), "源字体缺失时不该写出半成品")

    def test_unknown_data_font_role_fails_the_build(self):
        site, diagnostics = self._run('<h1 data-font="head">全部文章</h1><p data-font="serif">乙</p>')
        codes = [item.code for item in diagnostics]
        self.assertIn("E_FONT_ROLE_UNKNOWN", codes)
        self.assertNotIn("serif", ROLE_NAMES)

    def test_missing_glyph_only_warns(self):
        # cute 的源字体是中文手写标题体，里面没有日文假名；缺字只提示，交给下一个字体兜底
        site, diagnostics = self._run('<p data-font="cute">あ</p>')
        codes = [item.code for item in diagnostics]
        self.assertIn("W_FONT_GLYPH_MISSING", codes)
        self.assertFalse([code for code in codes if code.startswith("E_")])

    def test_over_budget_only_warns(self):
        site, diagnostics = self._run('<h1 data-font="head">全部文章</h1>')
        total = sum(path.stat().st_size for path in (site / "assets/fonts").glob("*.woff2"))
        self.assertLessEqual(total, fonts.FONT_BUDGET_BYTES)
        self.assertFalse([item.code for item in diagnostics if item.code == "W_FONT_BUDGET"])

        # 把预算调成 1 字节：同样的产物必须给出 W_FONT_BUDGET，而且不阻止构建
        original = fonts.FONT_BUDGET_BYTES
        fonts.FONT_BUDGET_BYTES = 1
        try:
            site, diagnostics = self._run('<h1 data-font="head">全部文章</h1>')
        finally:
            fonts.FONT_BUDGET_BYTES = original
        budgets = [item for item in diagnostics if item.code == "W_FONT_BUDGET"]
        self.assertEqual(1, len(budgets), [item.format() for item in diagnostics])
        self.assertIn("超过", budgets[0].message)
        self.assertIn("head.woff2", budgets[0].message)
        self.assertFalse([item for item in diagnostics if item.code.startswith("E_")])
        self.assertTrue((site / "assets/fonts/head.woff2").is_file())

    def test_fixed_text_keeps_the_output_small(self):
        site, _ = self._run('<h1 data-font="head">全部文章</h1>')
        widths = {path.name: path.stat().st_size for path in (site / "assets/fonts").glob("*.woff2")}
        # 只收用到的字：head 不该接近源字体 17 MB 的量级
        self.assertLess(widths["head.woff2"], 120_000)
        self.assertLess(widths["cute.woff2"], 40_000)
        self.assertLess(widths["hand.woff2"], 20_000)


if __name__ == "__main__":
    unittest.main()
