from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.content import Layout, Stage
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
        return build_pages(self.docs, self.site, SiteConfig(theme=self.theme), LAYOUT)

    def html(self, url: str) -> str:
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
        written = sorted(
            path.relative_to(workspace.site).parts[0]
            for path in workspace.site.rglob("index.html")
        )
        self.assertEqual(["blog", "drafts", "opus", "thoughts"], sorted(set(written)))
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


class ConfigTests(unittest.TestCase):
    def test_reads_site_toml(self):
        path = Path(tempfile.mkdtemp()) / "site.toml"
        path.write_text(
            "# 注释\nsite_name = \"Writing\"\nsite_url = \"https://example.test/Writing/\"\ntheme = \"theme\"\n",
            encoding="utf-8",
        )
        config = load_config(path)
        self.assertEqual("Writing", config.site_name)
        self.assertEqual("https://example.test/Writing/", config.site_url)
        self.assertEqual(Path("theme"), config.theme)

    def test_the_repository_config_points_at_the_real_theme(self):
        config = load_config(Path(__file__).resolve().parents[1] / "site.toml")
        self.assertEqual(Path("theme"), config.theme)
        self.assertTrue((Path(__file__).resolve().parents[1] / config.theme / "templates" / "article.html").is_file())


if __name__ == "__main__":
    unittest.main()