from __future__ import annotations

import datetime
import tempfile
import unittest
from pathlib import Path

from tools.content import Layout, Stage
from tools.obsidian_compat.urls import legacy_redirects
from tools.content import Article
from tools.render import (
    SiteConfig,
    build_pages,
    giant_chars,
    group_by_month,
    load_config,
    reading_minutes,
    render_markdown,
    split_home_intro,
    strip_date_notes,
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
        self.layout = LAYOUT  # 要测系列时在 build 之前换成带 series 的那份
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
            for diagnostic in self.build_pages()
            if not diagnostic.code.startswith("W_")
        ]

    def build_pages(self, legacy=()):
        # font_specs=None：这些测试只关心模板、网址和诊断，不装源字体也不联网。
        # 字体子集化本身由 tests/test_fonts.py 覆盖。
        return build_pages(
            self.docs, self.site, SiteConfig(theme=self.theme), self.layout, legacy, font_specs=None
        )

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


class HomeFunctionTests(unittest.TestCase):
    """split_home_intro / group_by_month：R-VIS-2 首页的展示数据。"""

    def test_heading_goes_and_first_paragraph_becomes_the_headline(self):
        html, _ = render_markdown("# 首页\n\n欢迎来到这里。\n\n这些文字大多是自己的想法。\n")
        headline, intro = split_home_intro(html)
        self.assertEqual("欢迎来到这里。", headline)
        self.assertNotIn("<h1", intro)
        self.assertNotIn("欢迎来到这里", intro)
        self.assertIn("这些文字大多是自己的想法。", intro)

    def test_only_a_heading_leaves_an_empty_headline_and_no_words(self):
        html, _ = render_markdown("# 首页\n")
        self.assertEqual(("", ""), split_home_intro(html))

    def test_headline_is_plain_text(self):
        html, _ = render_markdown("# 首页\n\n你好**这里**，还有`代码`。\n\n正文。\n")
        headline, intro = split_home_intro(html)
        self.assertEqual("你好这里，还有代码。", headline)
        self.assertNotIn("<strong>", headline)
        self.assertIn("正文。", intro)

    def test_heading_without_a_paragraph_keeps_the_following_html_as_words(self):
        headline, intro = split_home_intro("<h1>首页</h1>\n<blockquote>\n<p>引用里的话。</p>\n</blockquote>\n")
        self.assertEqual("", headline)
        self.assertNotIn("<h1", intro)
        self.assertIn("引用里的话。", intro)

    def test_intro_that_does_not_start_with_a_heading_keeps_everything_as_words(self):
        headline, intro = split_home_intro("<p>第一段。</p>\n<p>第二段。</p>\n")
        self.assertEqual("", headline)
        self.assertIn("第一段。", intro)
        self.assertIn("第二段。", intro)

    def _article(self, title: str, date) -> Article:
        return Article(
            source_path=Path(title + ".md"),
            stage=Stage("04技术", "博客", "blog"),
            title=title,
            date=date,
            tags=(),
            description="",
        )

    def test_months_keep_newest_first_and_period_without_a_date_goes_last(self):
        articles = (
            self._article("十月五号", datetime.date(2026, 10, 5)),
            self._article("十月一号", datetime.date(2026, 10, 1)),
            self._article("九月三十", datetime.date(2026, 9, 30)),
            self._article("没日期", None),
        )
        groups = group_by_month(articles)
        self.assertEqual(
            [(2026, 10, ["十月五号", "十月一号"]), (2026, 9, ["九月三十"]), (None, None, ["没日期"])],
            [(year, month, [article.title for article in items]) for year, month, items in groups],
        )

    def test_no_articles_gives_no_groups(self):
        self.assertEqual((), group_by_month(()))

    def test_same_period_of_another_year_is_its_own_group(self):
        articles = (
            self._article("今年十月", datetime.date(2026, 10, 1)),
            self._article("去年十月", datetime.date(2025, 10, 1)),
        )
        self.assertEqual([(2026, 10), (2025, 10)], [(year, month) for year, month, _ in group_by_month(articles)])


class HomeCoverTests(unittest.TestCase):
    """封面式首页（R-VIS-2）：气泡、大字、黑圈、两条线、按月分组。"""

    FILES = {
        "index.md": "# 首页\n\n欢迎来到这里。\n\n这些文字大多是自己的想法。\n\np.s. 学习笔记也放这里了。\n",
        "03思考/一篇思考.md": "---\ncreatedDate: 2026-10-05\n---\n# 一篇思考\n",
        "03思考/初稿/黑框眼镜.md": "---\ncreatedDate: 2026-10-06\n---\n# 黑框眼镜\n",
        "04技术/新博客.md": "---\ncreatedDate: 2026-10-02\ndescription: 一句简介\n---\n# 新博客\n",
        "04技术/旧博客.md": "---\ncreatedDate: 2026-09-30\n---\n# 旧博客\n",
        "05作品/星期四.md": "---\ncreatedDate: 2026-10-01\n---\n# 星期四\n",
    }

    def build(self, files: dict[str, str] | None = None) -> Workspace:
        workspace = Workspace(files or dict(self.FILES))
        self.assertFalse(workspace.build(), [diagnostic.format() for diagnostic in workspace.build_pages()])
        return workspace

    def test_bubble_headline_is_the_first_paragraph_and_the_heading_is_gone(self):
        html = self.build().html("")
        self.assertNotIn("首页", html[html.index("<main"): html.index("</main>")])
        self.assertIn("欢迎来到这里。", html)
        self.assertIn("这些文字大多是自己的想法。", html)
        self.assertIn("", html)
        self.assertIn('<span class="slab" data-font="slab">finderlzy\'s writing</span>', html)
        # 作者的话在列表之前
        self.assertLess(html.index("欢迎来到这里"), html.index("博客与作品"))

    def test_count_and_cards_use_every_published_article(self):
        html = self.build().html("")
        self.assertIn('aria-label="已发布 5 篇"', html)  # 5 篇公开文章，首页列表只有 3 篇
        self.assertIn("<b data-font=\"slab\">5</b>", html)
        self.assertIn("全部 5 篇", html)
        self.assertIn('<span data-font="slab">1</span> 篇思考 · <span data-font="slab">2</span> 篇博客', html)
        self.assertIn('<span data-font="slab">1</span> 篇初稿 · <span data-font="slab">1</span> 篇作品', html)

    def test_stage_names_on_the_cards_link_to_the_filtered_list(self):
        html = self.build().html("")
        for stage in ("思考", "初稿", "博客", "作品"):
            self.assertIn(f'href="./posts/?stage={stage}"', html)
        self.assertIn("冒出一个想法", html)
        self.assertIn("来了一点灵感", html)

    def test_list_is_grouped_by_month_newest_first(self):
        html = self.build().html("")
        list_html = html[html.index('class="list"'):]
        self.assertIn("· 十月</small>", list_html)
        self.assertIn("· 九月</small>", list_html)
        self.assertLess(list_html.index("· 十月</small>"), list_html.index("· 九月</small>"))
        self.assertIn('<span data-font="slab">10</span><small><span data-font="slab">2026</span> · 十月</small>', list_html)
        titles = ("新博客", "星期四", "旧博客")
        positions = [list_html.index(title) for title in titles]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("一句简介", list_html)

    def test_only_blog_and_work_are_listed(self):
        list_html = self.build().html("")
        list_html = list_html[list_html.index('class="list"'):]
        self.assertNotIn("一篇思考", list_html)
        self.assertNotIn("黑框眼镜", list_html)
        self.assertNotIn('data-stage="思考"', list_html)
        self.assertNotIn('data-stage="初稿"', list_html)

    def test_article_without_a_date_gets_its_own_last_group(self):
        files = {**self.FILES, "04技术/没日期.md": "---\ndescription: 还没写日期\n---\n# 没日期\n"}
        list_html = self.build(files).html("")
        list_html = list_html[list_html.index('class="list"'):]
        self.assertIn("日期<small>不详</small>", list_html)
        self.assertLess(list_html.index("九月"), list_html.index("日期<small>不详</small>"))
        self.assertLess(list_html.index("旧博客"), list_html.index("没日期"))

    def test_home_with_no_articles_still_has_the_way_to_the_list(self):
        html = self.build({"03思考/一篇.md": "---\ncreatedDate: 2026-10-01\n---\n# 一篇\n"}).html("")
        self.assertIn('aria-label="已发布 1 篇"', html)
        self.assertIn("全部 1 篇", html)
        self.assertNotIn('class="month"', html)
        self.assertIn('href="./posts/"', html)

    def test_giant_words_and_count_have_no_reading_blocking_side_effects(self):
        html = self.build().html("")
        self.assertIn('<div class="giant v g1" aria-hidden="true" data-font="head">想法</div>', html)
        self.assertIn('<div class="giant v g2" aria-hidden="true" data-font="head">灵感</div>', html)
        self.assertIn('class="count" role="note"', html)


class PostsPageTests(unittest.TestCase):
    def build(self, files: dict[str, str] | None = None, series: dict[str, str] | None = None) -> Workspace:
        workspace = Workspace(
            files
            or {
                "03思考/学术一点的思考.md": "---\ncreatedDate: 2026-10-05\ntags: [学习, AI]\ndescription: 思考简介\n---\n# 学术一点的思考\n",
                "04技术/博客.md": "---\ncreatedDate: 2026-10-02\ntags: [AI]\n---\n# 博客\n",
            }
        )
        if series:
            workspace.layout = Layout(stages=LAYOUT.stages, series=series)  # 系列配置由调用方换成要测的那份
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

    def test_title_area_puts_a_faded_giant_behind_the_heading(self):
        html = self.build().html("posts/")
        self.assertIn('<div class="giant g1" aria-hidden="true" data-font="head">全</div>', html)
        self.assertIn('<h1 class="page-title" data-font="head">全部文章</h1>', html)
        # 大字在标题之前，标题下面写着总篇数
        main = html[html.index("<main"):]
        self.assertLess(main.index(">全</div>"), main.index('class="page-title"'))
        self.assertIn('<span class="hero-lead-count" data-font="slab">2 pieces</span>', html)

    def test_stage_buttons_take_their_chip_colour_and_tags_stay_neutral(self):
        html = self.build().html("posts/")
        for stage in ("思考", "初稿", "博客", "作品"):
            self.assertIn(f'data-stage-chip="{stage}"', html)
        # 主题按钮不带阶段色
        self.assertNotIn('data-tag="学习" data-stage-chip', html)
        css = _article("site.css")
        self.assertIn('.filter-button[data-stage-chip="初稿"]', css)
        self.assertIn(".filter-button[data-stage-chip][aria-pressed=\"true\"]", css)

    def test_list_is_grouped_by_month_and_keeps_filter_data_on_each_item(self):
        html = self.build().html("posts/")
        self.assertIn('<section class="month" data-month="2026-10">', html)
        self.assertIn('<span data-font="slab">10</span><small><span data-font="slab">2026</span> · 十月</small>', html)
        self.assertIn('class="article-item" data-stage="思考" data-tags="学习\x01AI"', html)
        self.assertIn('class="article-item" data-stage="博客" data-tags="AI"', html)
        # 每条文章都在它那一个月里
        month_html = html[html.index('data-month="2026-10"'):]
        self.assertLess(month_html.index("学术一点的思考"), month_html.index("博客"))

    def test_articles_without_a_date_form_the_last_month_group(self):
        files = {
            "04技术/旧博客.md": "---\ncreatedDate: 2025-09-01\n---\n# 旧博客\n",
            "04技术/没日期.md": "---\ndescription: 还没写日期\n---\n# 没日期\n",
        }
        html = self.build(files).html("posts/")
        self.assertIn('<section class="month" data-month="2025-09">', html)
        self.assertIn('<section class="month" data-month="no-date">', html)
        self.assertIn("日期<small>不详</small>", html)
        self.assertLess(html.index('data-month="2025-09"'), html.index('data-month="no-date"'))

    def test_series_name_is_still_shown_in_the_list(self):
        files = {
            "04技术/订阅教程.md": "---\ncreatedDate: 2026-10-01\n---\n# 订阅教程\n",
            "04技术/原理版/一.md": "---\ncreatedDate: 2026-09-30\n---\n# 一\n",
        }
        html = self.build(files, series={"04技术/原理版": "04技术/订阅教程.md"}).html("posts/")
        self.assertIn('<span class="article-series">系列：订阅教程</span>', html)

    def test_script_hides_the_months_that_the_filter_emptied(self):
        script = _article("site.js")
        self.assertIn('list.querySelectorAll("[data-month]")', script)
        self.assertIn('month.querySelectorAll(".article-item:not([hidden])")', script)
        self.assertIn("month.hidden = shown.length === 0", script)


class WarningTests(unittest.TestCase):
    def test_article_without_a_date_is_listed_last_and_only_warns(self):
        workspace = Workspace(
            {
                "03思考/有日期.md": "---\ncreatedDate: 2026-10-01\n---\n# 有日期\n",
                "03思考/没日期.md": "---\n---\n# 没日期\n",
            }
        )
        workspace.site.mkdir(parents=True, exist_ok=True)
        diagnostics = build_pages(
            workspace.docs, workspace.site, SiteConfig(theme=workspace.theme), LAYOUT, font_specs=None
        )
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


class ArticleHeaderFunctionTests(unittest.TestCase):
    """giant_chars / strip_date_notes / reading_minutes：R-VIS-3 的展示数据。"""

    def test_giant_chars_skips_the_note_and_punctuation(self):
        self.assertEqual(("黑", "眼镜"), giant_chars("黑框眼镜（作品）"))
        self.assertEqual(("棋", "子王"), giant_chars("《棋王 树王 孩子王》"))
        self.assertEqual(("黑", "眼镜"), giant_chars("黑框眼镜(作品)"))

    def test_giant_chars_takes_letters_of_a_latin_title_in_capitals(self):
        self.assertEqual(("C", "RY"), giant_chars("CLANNAD~AFTER STORY~"))  # 第二个只该是汉字；英文标题退回字母
        self.assertEqual(("C", "AD"), giant_chars("《CLANNAD》"))
        self.assertEqual(("A", "ca"), giant_chars("Ave Mujica"))

    def test_giant_chars_second_only_when_four_or_more_characters(self):
        self.assertEqual(("龙", ""), giant_chars("龙与虎"))  # 三个字：只要一个
        self.assertEqual(("完", ""), giant_chars("完"))
        self.assertEqual(("怎", "人续"), giant_chars("《怎样花两年时间去面试一个人》续"))

    def test_giant_chars_of_a_title_with_only_punctuation_is_empty(self):
        self.assertEqual(("", ""), giant_chars("《》"))
        self.assertEqual(("", ""), giant_chars("……？"))

    def test_date_block_at_the_top_is_removed(self):
        markdown = "> 更新于 2026-10-20\n\n> 写于 2026-08-20\n\n正文\n"
        self.assertEqual("\n\n正文\n", strip_date_notes(markdown))

    def test_date_lines_inside_a_block_of_stars_and_links_are_removed(self):
        markdown = (
            "> 更新于 2026-10-20\n\n> 写于 2026-08-20\n\n"
            ">写于 2026-08-20\n> 更新于 2026-10-20\n>⭐⭐⭐⭐⭐\n>下一季：[[02思考/CLANNAD~AFTER STORY~]]\n\n正文\n"
        )
        self.assertEqual("\n\n>⭐⭐⭐⭐⭐\n>下一季：[[02思考/CLANNAD~AFTER STORY~]]\n\n正文\n", strip_date_notes(markdown))

    def test_explanation_after_the_dates_stays(self):
        markdown = "> 写于 2026-10-08\n> 更新于 2026-10-12\n\n> 这是只有操作步骤的版本。\n\n正文\n"
        self.assertEqual("\n> 这是只有操作步骤的版本。\n\n正文\n", strip_date_notes(markdown))

    def test_date_note_in_the_middle_of_the_body_stays(self):
        markdown = "正文\n\n> 写于 2026-01-01\n"
        self.assertEqual(markdown, strip_date_notes(markdown))

    def test_reading_minutes_counts_characters_and_never_goes_below_one(self):
        self.assertEqual(1, reading_minutes("<p>短</p>"))
        self.assertEqual(1, reading_minutes("<p>" + "字" * 199 + "</p>"))  # 199/400 不到半分钟
        self.assertEqual(2, reading_minutes("<p>" + "字" * 600 + "</p>"))
        self.assertEqual(5, reading_minutes("<p>" + "字" * 2000 + "</p>"))
        self.assertEqual(1, reading_minutes("<p><strong>字</strong> 字</p>"))

    def test_reading_minutes_ignores_tags_and_spaces(self):
        text = "<h2 id=\"_1\">标题</h2><p>正文正文</p>"
        self.assertEqual(1, reading_minutes(text))


class ArticlePageTests(unittest.TestCase):
    """文章页标题区和文末（R-VIS-3）。"""

    def build(self, files: dict[str, str] | None = None) -> Workspace:
        workspace = Workspace(
            files
            or {
                "05作品/黑框眼镜（作品）.md": (
                    "---\ncreatedDate: 2026-08-29\nupdatedDate: 2026-10-20\ntags: [暗恋]\n"
                    "description: 黑框眼镜女孩考上了我的大学。\n---\n> 写于 2026-08-29\n\n> 更新于 2026-10-20\n\n正文。\n"
                ),
                "03思考/CLANNAD~AFTER STORY~.md": "---\ncreatedDate: 2026-09-04\n---\n正文。\n",
                "03思考/没简介.md": "---\ncreatedDate: 2026-09-01\n---\n正文。\n",
            }
        )
        self.assertFalse(workspace.build())
        return workspace

    def page(self, workspace: Workspace, folder: str, title: str) -> str:
        for path in (workspace.site / folder).glob("*/index.html"):
            html = path.read_text(encoding="utf-8")
            if title + "</h1>" in html:
                return html
        raise AssertionError(f"没有找到《{title}》")

    def test_giant_characters_are_hidden_and_use_the_head_font(self):
        html = self.page(self.build(), "opus", "黑框眼镜（作品）")
        self.assertIn('<div class="giant g1" aria-hidden="true" data-font="head">黑</div>', html)
        self.assertIn('<div class="giant g2" aria-hidden="true" data-font="head">眼镜</div>', html)
        other = self.page(self.build(), "thoughts", "CLANNAD~AFTER STORY~")
        self.assertIn('data-font="head">C</div>', other)
        only = self.page(self.build(), "thoughts", "没简介")
        self.assertIn('data-font="head">没</div>', only)  # 三个字：只有一个大字
        self.assertNotIn('class="giant g2"', only)

    def test_minutes_ring_shows_reading_time(self):
        html = self.page(self.build(), "opus", "黑框眼镜（作品）")
        self.assertIn('aria-label="读完大约 1 分钟"', html)
        self.assertIn("min read", html)

    def test_header_dates_and_stage_prefix(self):
        html = self.page(self.build(), "opus", "黑框眼镜（作品）")
        self.assertIn("2026.08.29 写", html)
        self.assertIn("10.20 改", html)
        self.assertIn('class="post-prefix" data-font="slab">opus', html)
        self.assertIn('data-stage="作品"', html)
        self.assertIn("黑框眼镜女孩考上了我的大学。", html)

    def test_article_without_updated_date_has_no_rewrite_date(self):
        html = self.page(self.build(), "thoughts", "没简介")
        self.assertNotIn(" 改<", html)
        self.assertNotIn('<div class="say">', html)

    def test_date_block_at_the_top_is_not_rendered(self):
        html = self.page(self.build(), "opus", "黑框眼镜（作品）")
        body = html[html.index('<div class="article-body">'):]
        self.assertNotIn("写于 2026-08-29", body)
        self.assertNotIn("更新于 2026-10-20", body)

    def test_fin_mark_closes_the_body(self):
        html = self.page(self.build(), "opus", "黑框眼镜（作品）")
        self.assertIn('class="fin"', html)
        self.assertIn('data-font="cute">完', html)


class NotFoundTests(unittest.TestCase):
    def test_404_page_is_written_with_way_back(self):
        workspace = Workspace({"03思考/一.md": "---\ncreatedDate: 2026-10-01\n---\n# 一\n"})
        self.assertFalse(workspace.build())
        html = (workspace.site / "404.html").read_text(encoding="utf-8")
        self.assertIn("页面不存在", html)
        self.assertIn('href="../"', html)
        self.assertIn('href="../posts/"', html)

    def test_404_page_matches_the_site_visual(self):
        workspace = Workspace({"03思考/一.md": "---\ncreatedDate: 2026-10-01\n---\n# 一\n"})
        self.assertFalse(workspace.build())
        html = (workspace.site / "404.html").read_text(encoding="utf-8")
        self.assertIn('<div class="giant g1" aria-hidden="true" data-font="head">404</div>', html)
        self.assertIn("这个地址没有对应的文章", html)
        self.assertEqual(2, html.count('class="back-link"'))
        self.assertIn('<a class="back-link" href="../">', html)
        self.assertIn('<a class="back-link" href="../posts/">', html)


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
            font_specs=None,
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
            font_specs=None,
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