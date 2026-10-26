from __future__ import annotations

import datetime
import tempfile
import unittest
from pathlib import Path

from tools.content import read_meta
from tools.site_nav import Post, articles_page, build_nav, collect_posts, home_with_recent, read_page_meta, section_nav


def _write(root: Path, files: dict[str, str]) -> list[Path]:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return [Path(name) for name in files]


class ReadMetaTests(unittest.TestCase):
    def test_reads_date_and_tags_from_front_matter(self):
        meta = read_meta("---\ncreatedDate: 2026-10-14\ntags:\n  - 学习\n  - AI\n---\n正文\n")
        self.assertEqual(datetime.date(2026, 10, 14), meta["createdDate"])
        self.assertEqual(["学习", "AI"], meta["tags"])

    def test_tags_are_deduplicated_and_date_strings_may_carry_a_time(self):
        root = Path(tempfile.mkdtemp())
        pages = _write(root, {"03思考/a.md": "---\ncreatedDate: '2026-10-14 10:00'\ntags: [学习, 学习]\n---\n"})
        post = collect_posts(root, pages, "03思考")[0]
        self.assertEqual(datetime.date(2026, 10, 14), post.date)
        self.assertEqual(("学习",), post.tags)

    def test_missing_or_broken_front_matter_is_empty(self):
        self.assertEqual({}, read_meta("# 标题\n"))
        self.assertEqual({}, read_meta("---\n: [\n---\n"))

    def test_read_page_meta_reads_the_page_from_docs(self):
        root = Path(tempfile.mkdtemp())
        _write(root, {"03思考/a.md": "---\ncreatedDate: 2026-10-14\ntags: [学习]\n---\n"})
        self.assertEqual(["学习"], read_page_meta(root, Path("03思考/a.md"))["tags"])


class CollectPostsTests(unittest.TestCase):
    def test_newest_first_and_undated_last(self):
        root = Path(tempfile.mkdtemp())
        pages = _write(
            root,
            {
                "03思考/旧.md": "---\ncreatedDate: 2026-03-01\ntags:\n  - 学习\n---\n",
                "03思考/新.md": "---\ncreatedDate: 2026-10-01\n---\n",
                "03思考/没日期.md": "---\ntags: [AI]\n---\n",
                "02笔记/别的.md": "---\ncreatedDate: 2026-12-01\n---\n",
            },
        )
        posts = collect_posts(root, pages, "03思考")
        self.assertEqual(["新", "旧", "没日期"], [post.title for post in posts])
        self.assertEqual(("学习",), posts[1].tags)
        self.assertEqual(("AI",), posts[2].tags)
        self.assertIsNone(posts[2].date)

    def test_front_matter_title_wins_over_file_name(self):
        root = Path(tempfile.mkdtemp())
        pages = _write(root, {"03思考/a.md": "---\ntitle: 好标题\ncreatedDate: 2026-01-01\n---\n"})
        self.assertEqual("好标题", collect_posts(root, pages, "03思考")[0].title)

    def test_reads_description_from_front_matter(self):
        root = Path(tempfile.mkdtemp())
        pages = _write(root, {"03思考/a.md": "---\ndescription: 一句话简介\n---\n", "03思考/b.md": "正文\n"})
        posts = {post.source_path.stem: post for post in collect_posts(root, pages, "03思考")}
        self.assertEqual("一句话简介", posts["a"].description)
        self.assertEqual("", posts["b"].description)


POSTS = [
    Post(Path("03思考/关于读书.md"), "关于读书", datetime.date(2026, 10, 14), ("学习",)),
    Post(Path("03思考/CLANNAD~AFTER STORY~（p9—p11）.md"), "CLANNAD~AFTER STORY~（p9—p11）", datetime.date(2026, 8, 23), ("二次元",)),
    Post(Path("03思考/[奇怪] *名字*.md"), "[奇怪] *名字*", None, ()),
]


class ArticlesPageTests(unittest.TestCase):
    def test_lists_every_post_with_date_link_and_tags(self):
        page = articles_page(POSTS, "03思考")
        self.assertTrue(page.startswith("# 思考\n"))
        self.assertIn('<time class="post-date">2026-10-14</time> [关于读书](<关于读书.md>)', page)
        self.assertIn("(<CLANNAD~AFTER STORY~（p9—p11）.md>)", page)
        self.assertIn('data-tags="[&quot;二次元&quot;]"', page)
        self.assertIn(r"[\[奇怪\] \*名字\*](<[奇怪] *名字*.md>)", page)
        self.assertLess(page.index("关于读书"), page.index("CLANNAD"))

    def test_html_in_titles_and_tags_is_shown_as_text(self):
        post = Post(Path("03思考/a.md"), "a<b & c", None, ("<i>x</i>",))
        page = articles_page([post], "03思考")
        self.assertIn("[a&lt;b &amp; c](<a.md>)", page)
        self.assertIn("<span>&lt;i&gt;x&lt;/i&gt;</span>", page)
        self.assertNotIn("<i>", page)

    def test_description_shown_under_title_only_when_present(self):
        with_desc = Post(Path("03思考/a.md"), "a", None, (), "简介 <b>*重点*</b>")
        page = articles_page([with_desc, POSTS[0]], "03思考")
        self.assertIn(r'<span class="post-desc">简介 &lt;b&gt;\*重点\*&lt;/b&gt;</span>', page)
        self.assertEqual(1, page.count("post-desc"))

    def test_filter_buttons_count_each_tag(self):
        page = articles_page(POSTS, "03思考")
        self.assertIn('data-tag="" aria-pressed="true">全部（3）</button>', page)
        self.assertIn('data-tag="学习" aria-pressed="false">学习（1）</button>', page)
        self.assertIn('data-tag="二次元" aria-pressed="false">二次元（1）</button>', page)


class HomeTests(unittest.TestCase):
    def test_appends_recent_posts_linked_from_site_root(self):
        home = home_with_recent("# 首页\n\n欢迎。\n", POSTS, "03思考/index.md", limit=2)
        self.assertTrue(home.startswith("# 首页\n\n欢迎。\n"))
        self.assertIn("## 最近的思考", home)
        self.assertIn("[关于读书](<03思考/关于读书.md>)", home)
        self.assertNotIn("奇怪", home)
        self.assertIn("[全部思考 →](<03思考/index.md>)", home)
        self.assertNotIn("post-filter", home)

    def test_recent_posts_show_description(self):
        post = Post(Path("03思考/a.md"), "a", datetime.date(2026, 1, 1), (), "简介")
        self.assertIn('<span class="post-desc">简介</span>', home_with_recent("# 首页\n", [post], "03思考/index.md"))


class BuildNavTests(unittest.TestCase):
    def test_sections_in_order_and_hidden_folders_left_out(self):
        pages = [
            Path("index.md"),
            Path("01系统/规则.md"),
            Path("02笔记/课程/Java/泛型.md"),
            Path("02笔记/概念/链表.md"),
            Path("02笔记/一篇.md"),
            Path("04技术/教程.md"),
            Path("05作品/星期四.md"),
            Path("09归档/旧.md"),
        ]
        nav = build_nav(
            pages,
            {
                "思考": ["03思考/index.md", *(post.source_path.as_posix() for post in POSTS[:2])],
                "技术": ["04技术/教程.md"],
                "作品": ["05作品/星期四.md"],
            },
            ("笔记", "02笔记"),
        )
        self.assertEqual(["首页", "思考", "技术", "作品", "笔记"], [next(iter(item)) for item in nav])
        self.assertEqual(
            ["03思考/index.md", "03思考/关于读书.md", "03思考/CLANNAD~AFTER STORY~（p9—p11）.md"],
            nav[1]["思考"],
        )
        notes = nav[4]["笔记"]
        self.assertEqual("02笔记/一篇.md", notes[0])
        self.assertIn({"Java": ["02笔记/课程/Java/泛型.md"]}, notes[2]["课程"])
        flat = repr(nav)
        self.assertNotIn("01系统", flat)
        self.assertNotIn("09归档", flat)


    def test_empty_notes_folder_is_left_out(self):
        nav = build_nav([Path("index.md")], {"思考": []}, ("笔记", "02笔记"))
        self.assertEqual(["首页", "思考"], [next(iter(item)) for item in nav])


class SectionNavTests(unittest.TestCase):
    def test_subfolder_becomes_one_group_in_link_order(self):
        root = Path(tempfile.mkdtemp())
        pages = _write(
            root,
            {
                "04技术/新.md": "---\ncreatedDate: 2026-10-10\n---\n",
                "04技术/旧.md": "---\ncreatedDate: 2026-01-01\n---\n",
                "04技术/教程/目录.md": "---\ncreatedDate: 2026-05-01\n---\n1. [[开始]]\n2. [[教程/结束|结束]]\n",
                "04技术/教程/结束.md": "上一步：[[开始]]\n",
                "04技术/教程/开始.md": "下一步：[[结束]] 见 [[问答#细节]]\n",
                "04技术/教程/问答.md": "",
                "04技术/教程/没人链.md": "",
            },
        )
        nav = section_nav(root, collect_posts(root, pages, "04技术"))
        self.assertEqual(
            [
                "04技术/新.md",
                {"教程": ["04技术/教程/目录.md", "04技术/教程/开始.md", "04技术/教程/结束.md", "04技术/教程/问答.md", "04技术/教程/没人链.md"]},
                "04技术/旧.md",
            ],
            nav,
        )


class RealSiteTests(unittest.TestCase):
    def test_real_nav_keeps_published_tech_links_and_hides_system_and_archive(self):
        from tools import build_site

        pages = [path.relative_to(build_site.DOCS) for path in build_site.DOCS.rglob("*.md")]
        pages = [path for path in pages if path.parts[0] not in build_site.UNPUBLISHED_PATHS and ".obsidian" not in path.parts]
        posts = {title: collect_posts(build_site.DOCS, pages, folder) for title, folder in build_site.NAV_POSTS.items()}
        nav = build_nav(pages, {title: section_nav(build_site.DOCS, section) for title, section in posts.items()}, build_site.NAV_NOTES)
        self.assertEqual(["首页", "思考", "技术", "作品", "笔记"], [next(iter(item)) for item in nav])
        self.assertIn("04技术/如何订阅claude（纯操作版）.md", nav[2]["技术"])
        flat = repr(nav)
        self.assertNotIn("01系统", flat)
        self.assertNotIn("09归档", flat)
        self.assertEqual("thoughts/", build_site.ARTICLES_URL)
        self.assertEqual("tech", build_site.SECTION_SLUGS["04技术"])
        self.assertEqual("thoughts", build_site.SECTION_SLUGS["03思考"])


if __name__ == "__main__":
    unittest.main()
