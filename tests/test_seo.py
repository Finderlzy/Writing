from __future__ import annotations

import json
import re
import unittest

from tests.test_render import Workspace
from tools.seo import excerpt, first_image


class SeoFunctionTests(unittest.TestCase):
    def test_excerpt_skips_code_and_cuts_long_text(self):
        html = "<h2>小标题</h2><p>开头一段。</p><pre><code>print(1)</code></pre><p>" + "字" * 200 + "</p>"
        text = excerpt(html, 20)
        self.assertNotIn("print", text)
        self.assertNotIn("小标题", text)
        self.assertTrue(text.startswith("开头一段。"))
        self.assertTrue(text.endswith("…"))

    def test_first_image_becomes_absolute(self):
        html = '<p><img alt="" src="../../assets/09%E9%99%84%E4%BB%B6/a.png"></p>'
        self.assertEqual(
            "https://example.org/writing/assets/09%E9%99%84%E4%BB%B6/a.png",
            first_image("https://example.org/writing/", "blog/post/", html),
        )


class SeoPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = Workspace(
            {
                "04技术/有简介.md": "---\nslug: with-desc\ncreatedDate: 2026-10-02\nupdatedDate: 2026-10-20\ntags: [AI]\ndescription: 一句简介\n---\n# 有简介\n\n正文。\n",
                "03思考/没简介.md": "---\nslug: no-desc\ncreatedDate: 2026-10-01\n---\n正文第一句。\n",
            }
        )
        diagnostics = cls.workspace.build()
        assert not diagnostics, [item.format() for item in diagnostics]

    def test_article_has_canonical_description_and_dates(self):
        html = self.workspace.html("blog/with-desc")
        self.assertIn('<link rel="canonical" href="https://finderlzy.github.io/writing/blog/with-desc/">', html)
        self.assertIn('<meta name="description" content="一句简介">', html)
        self.assertIn('<meta property="article:modified_time" content="2026-10-20">', html)
        data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual("BlogPosting", data["@type"])
        self.assertEqual("2026-10-02", data["datePublished"])

    def test_article_without_description_uses_its_opening_text(self):
        self.assertIn('<meta name="description" content="正文第一句。">', self.workspace.html("thoughts/no-desc"))

    def test_sitemap_lists_public_pages_with_last_change(self):
        sitemap = (self.workspace.site / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("<loc>https://finderlzy.github.io/writing/</loc><lastmod>2026-10-20</lastmod>", sitemap)
        self.assertIn("<loc>https://finderlzy.github.io/writing/posts/</loc>", sitemap)
        self.assertIn("<loc>https://finderlzy.github.io/writing/thoughts/no-desc/</loc><lastmod>2026-10-01</lastmod>", sitemap)
        self.assertNotIn("404", sitemap)

    def test_not_found_page_is_not_indexed(self):
        html = (self.workspace.site / "404.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="robots" content="noindex">', html)
        self.assertNotIn('rel="canonical"', html)


if __name__ == "__main__":
    unittest.main()
