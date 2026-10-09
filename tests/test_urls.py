from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.obsidian_compat.urls import auto_slug, front_matter_slug, plan_page_urls, redirect_html


class PageUrlTests(unittest.TestCase):
    def plan(self, files: dict[str, str], unpublished: tuple[str, ...] = ()):
        root = Path(tempfile.mkdtemp())
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        pages = [Path(name) for name in files]
        return plan_page_urls(root, pages, lambda path: path.parts[0] in unpublished)

    def test_front_matter_slug_only_reads_front_matter(self):
        self.assertEqual(("vless-reality", 2), front_matter_slug("---\nslug: vless-reality\n---\n"))
        self.assertEqual(("a-b", 3), front_matter_slug('---\ncreatedDate: 2026-09-25\nslug: "a-b"\n---\n'))
        self.assertIsNone(front_matter_slug("# 标题\n\nslug: not-meta\n"))
        self.assertIsNone(front_matter_slug("---\ncreatedDate: 2026-09-25\n---\nslug: body\n"))

    def test_handwritten_slug_and_stable_auto_id(self):
        urls, diagnostics = self.plan(
            {
                "index.md": "# 首页\n",
                "04技术/自建梯子.md": "---\nslug: vless-reality\n---\n",
                "02学习/链表.md": "# 链表\n",
                "07自己/日记.md": "---\nslug: diary\n---\n",
            },
            unpublished=("07自己",),
        )
        self.assertFalse(diagnostics)
        self.assertEqual("p/vless-reality/", urls["04技术/自建梯子.md"])
        self.assertEqual(f"p/{auto_slug(Path('02学习/链表.md'))}/", urls["02学习/链表.md"])
        self.assertEqual(auto_slug(Path("02学习/链表.md")), auto_slug(Path("02学习/链表.md")))
        self.assertNotIn("index.md", urls)
        self.assertNotIn("07自己/日记.md", urls)

    def test_invalid_and_duplicate_slugs_are_reported(self):
        urls, diagnostics = self.plan(
            {
                "甲.md": "---\nslug: Bad Slug\n---\n",
                "乙.md": "---\nslug: same\n---\n",
                "丙.md": "---\nslug: same\n---\n",
            }
        )
        self.assertEqual(["E_SLUG_DUPLICATE", "E_SLUG_DUPLICATE", "E_SLUG_INVALID"], sorted(d.code for d in diagnostics))
        self.assertEqual({}, urls)

    def test_redirect_points_from_old_path_to_new_url(self):
        page = redirect_html("04技术/自建梯子/index.html", "p/vless-reality/", "https://finderlzy.github.io/Writing/")
        self.assertIn('url=../../p/vless-reality/"', page)
        self.assertIn('href="https://finderlzy.github.io/Writing/p/vless-reality/"', page)


if __name__ == "__main__":
    unittest.main()
