from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.content import Layout, Stage
from tools.obsidian_compat.urls import legacy_redirects
from tools.render import (
    SiteConfig,
    build_pages,
    load_config,
    render_markdown,
    strip_front_matter,
)

LAYOUT = Layout(
    stages=(
        Stage("03思考", "思考", "thoughts"),
        Stage("03思考/初稿", "初稿", "drafts"),
        Stage("04技术", "博客", "blog"),
        Stage("05作品", "作品", "opus"),
    ),
    series={},
)


class Workspace:
    """A throwaway `docs/` tree plus the config that points at the real theme."""

    def __init__(self, files: dict[str, str], attachments: dict[str, bytes] | None = None):
        self.root = Path(tempfile.mkdtemp())
        self.docs = self.root / "docs"
        self.site = self.root / "site"
        # 首页的作者的话来自 docs/index.md，每个测试的 docs/ 都得有一份
        files = {"index.md": "# 首页\n\n欢迎。\n", **files}
        for name, text in files.items():
            path = self.docs / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for name, data in (attachments or {}).items():
            path = self.docs / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.theme = Path(__file__).resolve().parents[1] / "theme"

    def build(self) -> list:
        self.site.mkdir(parents=True, exist_ok=True)
        return [
            diagnostic
            for diagnostic in build_pages(self.docs, self.site, SiteConfig(theme=self.theme), LAYOUT)
            if not diagnostic.code.startswith("W_")
        ]

    def html(self, url: str) -> str:
        """`url` 是文章自己的网址；首页是空串，文章不带结尾斜杠，例如 "thoughts/关于读书"。"""
        return (self.site / url / "index.html").read_text(encoding="utf-8")


class MarkdownTests(unittest.TestCase):
    def test_headings_get_ids_and_build_a_tree(self):
        body, toc = render_markdown("## 一、购买 VPS\n\n### 选购时注意什么\n")
        self.assertIn('<h2 id="vps">一、购买 VPS</h2>', body)
        self.assertIn("id=\"_1\"", body)
        self.assertEqual(2, toc[0]["level"])
        self.assertEqual(1, len(toc[0]["children"]))

    def test_heading_without_ascii_letters_gets_a_usable_id(self):
        body, _ = render_markdown("## 开心和难过交织\n")
        self.assertIn('id="_1"', body)
        self.assertNotIn('id=""', body)

    def test_front_matter_is_dropped(self):
        text = "---\nslug: vless-reality\ncreatedDate: 2026-09-25\n---\n\n正文\n"
        self.assertEqual("\n正文\n", strip_front_matter(text))
        body, _ = render_markdown(strip_front_matter(text))
        self.assertNotIn("slug", body)
        self.assertIn("正文", body)


class BuildTests(unittest.TestCase):
    def test_only_the_four_stages_are_written(self):
        workspace = Workspace(
            {
                "03思考/关于读书.md": "---\ncreatedDate: 2026-10-01\n---\n# 关于读书\n",
                "03思考/初稿/黑框眼镜.md": "---\ncreatedDate: 2026-09-01\n---\n# 黑框眼镜\n",
                "04技术/教程.md": "---\ncreatedDate: 2026-08-01\n---\n# 教程\n",
                "05作品/星期四.md": "---\ncreatedDate: 2026-07-01\n---\n# 星期四\n",
                "02笔记/链表.md": "# 链表\n",
                "00收集/灵感.md": "# 灵感\n",
                "07自己/日记.md": "# 日记\n",
                "09归档/旧文.md": "# 旧文\n",
                "index.md": "# 首页\n",
            }
        )
        diagnostics = workspace.build()
        self.assertFalse(diagnostics, [diagnostic.format() for diagnostic in diagnostics])
        written = {
            path.relative_to(workspace.site).parts[0]
            for path in workspace.site.rglob("index.html")
        }
        written.discard("index.html")  # 根目录的 index.html 是首页
        self.assertEqual({"blog", "drafts", "opus", "thoughts", "posts"}, written)
        for folder in ("00收集", "01系统", "02笔记", "07自己", "09归档"):
            self.assertFalse((workspace.site / folder).exists())

    def test_double_link_between_articles_becomes_a_working_url(self):
        workspace = Workspace(
            {
                "03思考/甲.md": "---\ncreatedDate: 2026-10-01\n---\n见[[03思考/乙]]和[[03思考/乙#一、开始]]。\n",
                "03思考/乙.md": "---\ncreatedDate: 2026-10-02\n---\n## 一、开始\n\n正文\n",
            }
        )
        self.assertFalse(workspace.build())
        html = workspace.html("thoughts/" + sorted(p.name for p in (workspace.site / "thoughts").iterdir())[0])
        self.assertIn("href=\"../", html)

    def test_link_to_an_unpublished_page_stays_plain_text(self):
        workspace = Workspace(
            {
                "03思考/甲.md": "---\ncreatedDate: 2026-10-01\n---\n想见[[02笔记/链表]]。\n",
                "02笔记/链表.md": "# 链表\n",
            }
        )
        self.assertFalse(workspace.build())
        page = next((workspace.site / "thoughts").rglob("index.html"))
        html = page.read_text(encoding="utf-8")
        self.assertIn("链表", html)
        self.assertNotIn("href=\"../..//", html)
        self.assertNotIn(".html\"", html)

    def test_attachment_with_spaces_and_chinese_is_copied_and_linked(self):
        workspace = Workspace(
            {"03思考/图片.md": "---\ncreatedDate: 2026-10-01\n---\n![[09附件/我 的 图片 1.png]]\n"},
            {"09附件/我 的 图片 1.png": b"\x89PNG\r\n\x1a\n"},
        )
        self.assertFalse(workspace.build())
        copied = workspace.site / "assets" / "09附件" / "我 的 图片 1.png"
        self.assertTrue(copied.is_file())
        html = next((workspace.site / "thoughts").rglob("index.html")).read_text(encoding="utf-8")
        self.assertIn("<img", html)
        self.assertIn("%E6%88%91%20%E7%9A%84", html)
        self.assertNotIn("09%E9%99%84%E4%BB%B6/我", html)

    def test_in_page_anchor_double_link_works(self):
        workspace = Workspace(
            {"03思考/甲.md": "---\ncreatedDate: 2026-10-01\n---\n## 一、开始\n\n回到[[#一、开始]]。\n"},
        )
        self.assertFalse(workspace.build())
        html = next((workspace.site / "thoughts").rglob("index.html")).read_text(encoding="utf-8")
        self.assertIn('href="#_1"', html)
        self.assertIn('id="_1"', html)

    def test_front_matter_never_reaches_the_page(self):
        workspace = Workspace(
            {"03思考/甲.md": "---\nslug: abc\ncreatedDate: 2026-10-14\n---\n\n正文\n"},
        )
        self.assertFalse(workspace.build())
        html = next((workspace.site / "thoughts").rglob("index.html")).read_text(encoding="utf-8")
        self.assertNotIn("slug", html)
        self.assertIn("正文", html)
        self.assertIn("2026-10-14", html)


def _article(url: str) -> str:
    return (Path(__file__).resolve().parents[1] / "theme" / "assets" / url).read_text(encoding="utf-8")


class HomePageTests(unittest.TestCase):
    def build(self) -> Workspace:
        workspace = Workspace(
            {
                "index.md": "# 首页\n\n欢迎来到这里。\n",
                "04技术/新博客.md": "---\ncreatedDate: 2026-10-02\ndescription: 一句简介\n---\n# 新博客\n",
                "04技术/旧博客.md": "---\ncreatedDate: 2026-09-01\n---\n# 旧博客\n",
                "05作品/星期四.md": "---\ncreatedDate: 2026-10-01\n---\n# 星期四\n",
                "03思考/一篇思考.md": "---\ncreatedDate: 2026-10-05\n---\n# 一篇思考\n",
                "03思考/初稿/黑框眼镜.md": "---\ncreatedDate: 2026-10-06\n---\n# 黑框眼镜\n",
            }
        )
        self.assertFalse(workspace.build())
        return workspace

    def test_author_words_come_first_then_blog_and_work_newest_first(self):
        html = self.build().html("")
        self.assertLess(html.index("欢迎来到这里"), html.index("博客与作品"))
        titles = ("新博客", "星期四", "旧博客")
        positions = [html.index(title) for title in titles]
        self.assertEqual(sorted(positions), positions)
        self.assertNotIn("一篇思考", html)
        self.assertNotIn("黑框眼镜", html)
        self.assertIn("一句简介", html)
        self.assertIn("全部文章", html)

    def test_header_has_only_home_and_posts(self):
        html = self.build().html("")
        header = html[html.index("<header"): html.index("</header>")]
        nav = header[header.index("<nav"):]
        self.assertIn('href="./"', nav)
        self.assertIn('href="./posts/"', nav)
        self.assertEqual(2, nav.count("<a "))
        self.assertIn('class="site-title" href="./"', header)

    def test_home_page_loads_theme_assets_from_the_site_root(self):
        """首页在站点根下，资源必须用站点根相对的地址，不能多退一层到 /assets/。"""
        html = self.build().html("")
        self.assertIn('href="./assets/theme/site.css"', html)
        self.assertIn('src="./assets/theme/site.js"', html)
        self.assertNotIn('"../assets/theme/', html)

    def test_article_page_loads_theme_assets_from_the_site_root(self):
        """文章在 thoughts/<slug>/ 下，比首页深两层，资源前缀也要跟着深两层。"""
        workspace = self.build()
        article = sorted(workspace.site.glob("thoughts/*/index.html"))[0]
        html = article.read_text(encoding="utf-8")
        self.assertIn('href="../../assets/theme/site.css"', html)
        self.assertIn('src="../../assets/theme/site.js"', html)
        self.assertIn('href="../../"', html)

    def test_home_page_has_no_comments_and_no_filters(self):
        html = self.build().html("")
        self.assertNotIn("giscus", html)
        self.assertNotIn("data-filters", html)


class PostsPageTests(unittest.TestCase):
    def build(self) -> Workspace:
        workspace = Workspace(
            {
                "03思考/学术一点的思考.md": "---\ncreatedDate: 2026-10-05\ntags: [学习, AI]\ndescription: 思考简介\n---\n# 学术一点的思考\n",
                "04技术/博客.md": "---\ncreatedDate: 2026-10-02\ntags: [AI]\n---\n# 博客\n",
            }
        )
        self.assertFalse(workspace.build())
        return workspace

    def test_lists_every_article_with_stage_and_tags(self):
        html = self.build().html("posts/")
        self.assertIn("学术一点的思考", html)
        self.assertIn("博客", html)
        self.assertIn('data-stage="思考"', html)
        self.assertIn('data-stage="博客"', html)
        self.assertIn("思考简介", html)
        self.assertIn('data-tag="学习"', html)

    def test_filters_and_list_work_without_javascript(self):
        html = self.build().html("posts/")
        self.assertIn("data-filters hidden", html)
        self.assertIn("data-empty-result hidden", html)
        self.assertEqual(2, html.count('class="article-item"'))

    def test_script_reads_and_writes_stage_and_tag_parameters(self):
        script = _article("site.js")
        self.assertIn('"stage"', script)
        self.assertIn('"tag"', script)
        self.assertIn("URLSearchParams", script)
        self.assertIn("replaceState", script)


class WarningTests(unittest.TestCase):
    def test_article_without_a_date_is_listed_last_and_only_warns(self):
        workspace = Workspace(
            {
                "03思考/有日期.md": "---\ncreatedDate: 2026-10-01\n---\n# 有日期\n",
                "03思考/没日期.md": "---\n---\n# 没日期\n",
            }
        )
        workspace.site.mkdir(parents=True, exist_ok=True)
        diagnostics = build_pages(workspace.docs, workspace.site, SiteConfig(theme=workspace.theme), LAYOUT)
        codes = [diagnostic.code for diagnostic in diagnostics]
        self.assertIn("W_POST_DATE_MISSING", codes)
        self.assertFalse([code for code in codes if not code.startswith("W_")])
        html = workspace.html("posts/")
        self.assertLess(html.index("有日期"), html.index("没日期"))

    def test_mathjax_is_only_loaded_where_there_is_math(self):
        workspace = Workspace(
            {
                "03思考/有公式.md": "---\ncreatedDate: 2026-10-01\n---\n\n能量公式 $E=mc^2$。\n",
                "03思考/没公式.md": "---\ncreatedDate: 2026-10-02\n---\n\n只有文字。\n",
            }
        )
        self.assertFalse(workspace.build())
        pages = {path.parent.name: path.read_text(encoding="utf-8") for path in (workspace.site / "thoughts").glob("*/index.html")}
        self.assertEqual(1, sum("mathjax@3.2.2" in html for html in pages.values()))
        self.assertNotIn("mathjax", workspace.html("posts/"))
        self.assertNotIn("mathjax", workspace.html(""))


class NotFoundTests(unittest.TestCase):
    def test_404_page_is_written_with_way_back(self):
        workspace = Workspace({"03思考/一.md": "---\ncreatedDate: 2026-10-01\n---\n# 一\n"})
        self.assertFalse(workspace.build())
        html = (workspace.site / "404.html").read_text(encoding="utf-8")
        self.assertIn("页面不存在", html)
        self.assertIn('href="../"', html)
        self.assertIn('href="../posts/"', html)


class LegacyRedirectTests(unittest.TestCase):
    def test_old_address_redirects_to_the_page_that_exists(self):
        workspace = Workspace(
            {"04技术/如何订阅claude（纯操作版）.md": "---\nslug: subscribe-claude-quick\ncreatedDate: 2026-10-08\n---\n# 纯操作版\n"}
        )
        workspace.site.mkdir(parents=True, exist_ok=True)
        target = "blog/subscribe-claude-quick"
        diagnostics = build_pages(
            workspace.docs,
            workspace.site,
            SiteConfig(theme=workspace.theme),
            LAYOUT,
            [("tech/subscribe-claude-quick", target)],
        )
        self.assertFalse([d for d in diagnostics if not d.code.startswith("W_")], [d.format() for d in diagnostics])
        page = workspace.site / "tech" / "subscribe-claude-quick" / "index.html"
        self.assertTrue(page.is_file())
        html = page.read_text(encoding="utf-8")
        self.assertIn('http-equiv="refresh"', html)
        self.assertIn("../../blog/subscribe-claude-quick/", html)
        self.assertIn('<meta name="robots" content="noindex">', html)
        self.assertTrue((workspace.site / target / "index.html").is_file())

    def test_missing_target_stops_the_build(self):
        workspace = Workspace(
            {"04技术/如何订阅claude（纯操作版）.md": "---\nslug: subscribe-claude-quick\ncreatedDate: 2026-10-08\n---\n# 纯操作版\n"}
        )
        workspace.site.mkdir(parents=True, exist_ok=True)
        diagnostics = build_pages(
            workspace.docs,
            workspace.site,
            SiteConfig(theme=workspace.theme),
            LAYOUT,
            [("tech/subscribe-claude-quick", "blog/not-here")],
        )
        self.assertIn("E_REDIRECT_TARGET_MISSING", [d.code for d in diagnostics])

    def test_conflict_with_a_real_page_is_reported(self):
        workspace = Workspace({"03思考/甲.md": "---\ncreatedDate: 2026-10-01\n---\n# 甲\n"})
        workspace.build()
        page_url = next(
            path.parent.relative_to(workspace.site).as_posix()
            for path in sorted(workspace.site.rglob("index.html"))
            if path.parent.name not in {"site", "posts"}
        )
        self.assertTrue((workspace.site / page_url / "index.html").is_file())
        diagnostics = legacy_redirects(workspace.site, [(page_url + "/", page_url)], None)
        self.assertEqual(["E_REDIRECT_CONFLICT"], [d.code for d in diagnostics])


class SiteConfigTests(unittest.TestCase):
    def test_reads_site_toml(self):
        path = Path(tempfile.mkdtemp()) / "site.toml"
        path.write_text(
            "# 注释\nsite_name = \"Writing\"\nsite_url = \"https://example.test/Writing/\"\ntheme = \"theme\"\n"
            "\n[[social]]\nname = \"GitHub\"\nlink = \"https://github.com/example\"\n"
            "\n[[social]]\nname = \"X\"\nlink = \"https://x.com/example\"\n"
            "\n[giscus]\nrepo = \"a/b\"\nrepo_id = \"R_1\"\ncategory = \"Comments\"\ncategory_id = \"D_1\"\n",
            encoding="utf-8",
        )
        config = load_config(path)
        self.assertEqual("Writing", config.site_name)
        self.assertEqual("https://example.test/Writing/", config.site_url)
        self.assertEqual(Path("theme"), config.theme)
        self.assertEqual(["GitHub", "X"], [link.name for link in config.social])
        self.assertEqual("a/b", config.giscus.repo)
        self.assertTrue(config.giscus.enabled)

    def test_giscus_is_off_without_a_category_id(self):
        path = Path(tempfile.mkdtemp()) / "site.toml"
        path.write_text("[giscus]\nrepo = \"a/b\"\nrepo_id = \"R_1\"\ncategory_id = \"\"\n", encoding="utf-8")
        self.assertFalse(load_config(path).giscus.enabled)

    def test_the_repository_config_points_at_the_real_theme(self):
        config = load_config(Path(__file__).resolve().parents[1] / "site.toml")
        self.assertEqual(Path("theme"), config.theme)
        self.assertTrue((Path(__file__).resolve().parents[1] / config.theme / "templates" / "article.html").is_file())
        self.assertTrue(config.giscus.enabled)
        self.assertIn(
            'data-mapping="pathname"',
            (Path(__file__).resolve().parents[1] / "theme" / "templates" / "article.html").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()