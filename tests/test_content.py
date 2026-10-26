from __future__ import annotations

import datetime
import tempfile
import unittest
from pathlib import Path

from tools.content import LAYOUT, Article, Catalog, Layout, Stage, is_published, read_meta

PREVIEW_LAYOUT = Layout(
    stages=(
        Stage("03思考", "思考", "thoughts"),
        Stage("03思考/初稿", "初稿", "drafts"),
        Stage("04技术", "博客", "blog"),
        Stage("05作品", "作品", "opus"),
    ),
    series={},
)


def _write(root: Path, files: dict[str, str]) -> list[Path]:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return [Path(name) for name in files]


class LayoutTests(unittest.TestCase):
    def test_longest_prefix_wins(self):
        path = Path("03思考/初稿/黑框眼镜.md")
        self.assertEqual("初稿", PREVIEW_LAYOUT.stage_of(path).name)
        self.assertEqual("drafts", PREVIEW_LAYOUT.stage_of(path).prefix)
        self.assertEqual("思考", PREVIEW_LAYOUT.stage_of(Path("03思考/关于读书.md")).name)
        self.assertIsNone(PREVIEW_LAYOUT.stage_of(Path("02笔记/概念/链表.md")))

    def test_official_layout_covers_the_four_stages(self):
        self.assertEqual(
            ["思考", "初稿", "博客", "作品"],
            [stage.name for stage in LAYOUT.stages],
        )
        self.assertEqual(
            ["thoughts", "drafts", "blog", "opus"],
            [stage.prefix for stage in LAYOUT.stages],
        )
        for stage in LAYOUT.stages:
            self.assertTrue(is_published(Path(stage.folder) / "a.md"))

    def test_is_published_accepts_the_home_page_and_rejects_other_folders(self):
        self.assertTrue(is_published(Path("index.md"), PREVIEW_LAYOUT))
        self.assertFalse(is_published(Path("00收集/灵感.md"), PREVIEW_LAYOUT))
        self.assertFalse(is_published(Path("02笔记/a.md"), PREVIEW_LAYOUT))
        self.assertFalse(is_published(Path("07自己/a.md"), PREVIEW_LAYOUT))
        self.assertFalse(is_published(Path("AGENTS.md"), PREVIEW_LAYOUT))


class ReadMetaTests(unittest.TestCase):
    def test_slug_with_a_comment_reads_as_the_value(self):
        self.assertEqual("abc", read_meta("---\nslug: abc # note\n---\n")["slug"])

    def test_quoted_slug(self):
        self.assertEqual("abc", read_meta("---\nslug: \"abc\"\n---\n")["slug"])

    def test_unclosed_front_matter_has_no_slug(self):
        self.assertNotIn("slug", read_meta("---\nslug: abc\n正文\n"))

    def test_broken_yaml_reads_as_empty(self):
        self.assertEqual({}, read_meta("---\n: [\n---\n"))

    def test_no_front_matter_is_empty(self):
        self.assertEqual({}, read_meta("# 标题\n"))


class CatalogTests(unittest.TestCase):
    def load(self, files: dict[str, str], layout: Layout = PREVIEW_LAYOUT):
        root = Path(tempfile.mkdtemp())
        pages = _write(root, files)
        return Catalog.load(root, pages, layout)

    def test_newest_first_and_undated_last_with_a_warning(self):
        catalog, diagnostics = self.load(
            {
                "03思考/旧.md": "---\ncreatedDate: 2026-03-01\ntags:\n  - 学习\n---\n",
                "03思考/新.md": "---\ncreatedDate: 2026-10-01\ntags: [AI, AI]\n---\n",
                "03思考/没日期.md": "---\ntags: [AI]\n---\n",
                "02笔记/别的.md": "---\ncreatedDate: 2026-12-01\n---\n",
            }
        )
        self.assertEqual(["新", "旧", "没日期"], [article.title for article in catalog.articles])
        self.assertEqual(("学习",), catalog.articles[1].tags)
        self.assertEqual(("AI",), catalog.articles[0].tags)
        self.assertEqual(("AI",), catalog.articles[2].tags)
        self.assertIsNone(catalog.articles[2].date)
        self.assertEqual(["W_POST_DATE_MISSING"], [diagnostic.code for diagnostic in diagnostics])
        self.assertEqual(Path("03思考/没日期.md"), diagnostics[0].span.path)

    def test_reads_title_stage_date_and_description(self):
        catalog, diagnostics = self.load(
            {
                "04技术/教程.md": "---\ntitle: 好标题\ncreatedDate: 2026-10-14\ndescription: 一句话简介\n---\n",
                "03思考/初稿/黑框眼镜.md": "---\ncreatedDate: 2026-08-01\n---\n",
            }
        )
        by_path = {article.source_path.as_posix(): article for article in catalog.articles}
        article = by_path["04技术/教程.md"]
        self.assertEqual("好标题", article.title)
        self.assertEqual("博客", article.stage.name)
        self.assertEqual(datetime.date(2026, 10, 14), article.date)
        self.assertEqual("一句话简介", article.description)
        self.assertEqual("初稿", by_path["03思考/初稿/黑框眼镜.md"].stage.name)
        self.assertEqual("黑框眼镜", by_path["03思考/初稿/黑框眼镜.md"].title)
        self.assertFalse(diagnostics)

    def test_date_string_with_a_time(self):
        catalog, _ = self.load({"03思考/a.md": "---\ncreatedDate: '2026-10-14 10:00'\n---\n"})
        self.assertEqual(datetime.date(2026, 10, 14), catalog.articles[0].date)

    def test_home_lists_blogs_and_works_only(self):
        catalog, _ = self.load(
            {
                "04技术/博客.md": "---\ncreatedDate: 2026-10-03\n---\n",
                "05作品/作品.md": "---\ncreatedDate: 2026-10-02\n---\n",
                "03思考/思考.md": "---\ncreatedDate: 2026-10-01\n---\n",
                "03思考/初稿/初稿.md": "---\ncreatedDate: 2026-09-01\n---\n",
            }
        )
        self.assertEqual(["博客", "作品"], [article.title for article in catalog.home()])

    def test_neighbours_follow_created_date_within_a_stage(self):
        catalog, _ = self.load(
            {
                "03思考/一.md": "---\ncreatedDate: 2026-01-01\n---\n",
                "03思考/二.md": "---\ncreatedDate: 2026-02-01\n---\n",
                "03思考/三.md": "---\ncreatedDate: 2026-03-01\n---\n",
                "05作品/别的.md": "---\ncreatedDate: 2026-02-15\n---\n",
            }
        )
        articles = {article.title: article for article in catalog.articles}
        previous, following = catalog.neighbours(articles["二"])
        self.assertEqual("一", previous.title)
        self.assertEqual("三", following.title)
        previous, following = catalog.neighbours(articles["一"])
        self.assertIsNone(previous)
        self.assertEqual("二", following.title)


if __name__ == "__main__":
    unittest.main()
