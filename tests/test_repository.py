from __future__ import annotations

import hashlib
import json
import tempfile
import re
import unittest
from pathlib import Path

from tools.content import LAYOUT, is_published
from tools.obsidian_compat.converter import Converter
from tools.obsidian_compat.index import VaultIndex
from tools.render import load_config

# R-STR-1 的文件夹表：一级文件夹只有这些，00收集 不分子文件夹
TOP_LEVEL_FOLDERS = {"00收集", "01系统", "02思考", "03初稿", "04博客", "05作品", "07自己", "09附件"}
# 只允许 04博客 为系列建子文件夹（R-STR-1）
FLAT_STAGE_FOLDERS = ("00收集", "01系统", "02思考", "03初稿", "05作品", "07自己")


class RepositoryAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.docs = self.root / "docs"

    def _top_level_folders(self) -> set[str]:
        return {path.name for path in self.docs.iterdir() if path.is_dir() and not path.name.startswith(".")}

    def test_docs_top_level_folders_follow_r_str_1(self):
        self.assertEqual(TOP_LEVEL_FOLDERS, self._top_level_folders())
        self.assertEqual((), tuple((self.docs / "00收集").rglob("*/*.md")), "00收集 不能再有子文件夹")

    def test_stage_folders_have_no_subfolders_except_blog_series(self):
        for folder in FLAT_STAGE_FOLDERS:
            nested = [path.as_posix() for path in (self.docs / folder).rglob("*") if path.is_dir()]
            self.assertEqual([], nested, f"“{folder}”不能有子文件夹")
        self.assertEqual(
            {"原理版", "操作版"},
            {path.name for path in (self.docs / "04博客").iterdir() if path.is_dir()},
            "04博客 下只为订阅教程系列建了 原理版、操作版 两个子文件夹",
        )
        self.assertEqual({"04博客/原理版", "04博客/操作版"}, set(LAYOUT.series))

    def test_published_folders_are_exactly_the_four_stages(self):
        published = {
            path.relative_to(self.docs).parts[0]
            for path in self.docs.rglob("*.md")
            if ".obsidian" not in path.parts and is_published(path.relative_to(self.docs))
        }
        self.assertEqual({"02思考", "03初稿", "04博客", "05作品", "index.md"}, published)

    def test_docs_has_no_site_scripts(self):
        scripts = [
            path.relative_to(self.docs).as_posix()
            for path in self.docs.rglob("*")
            if path.suffix in {".js", ".css"} and ".obsidian" not in path.parts
        ]
        self.assertEqual([], scripts, "站点脚本和样式放在 theme/，不进 Obsidian 仓库")

    def test_attachments_live_in_the_attachment_folder(self):
        # 没被引用的附件允许留着（作者可能以后要用），网站只复制公开文章引用到的那些
        index = VaultIndex.scan(self.docs)
        self.assertEqual({"09附件"}, {path.parts[0] for path in index.attachments})

    def test_site_configuration_matches_repository_layout(self):
        self.assertTrue((self.docs / "index.md").is_file())

        config = load_config(self.root / "site.toml")
        self.assertEqual("https://finderlzy.github.io/Writing/", config.site_url)
        # site.toml 里写的是相对仓库根目录的路径，build_site 会补成绝对路径
        self.assertEqual("theme", config.theme.as_posix())
        self.assertTrue((config.theme / "templates" / "base.html").is_file())
        self.assertTrue((config.theme / "assets" / "site.css").is_file())
        self.assertEqual("Finderlzy/Writing", config.giscus.repo)
        self.assertRegex(config.giscus.repo_id, r"^R_\w+$")
        if config.giscus.category_id:
            self.assertRegex(config.giscus.category_id, r"^DIC_\w+$")

        app_path = self.docs / ".obsidian" / "app.json"
        app = json.loads(app_path.read_text(encoding="utf-8"))
        for setting in ("attachmentFolderPath", "newFileFolderPath"):
            configured = app[setting]
            self.assertIsInstance(configured, str)
            target = self._safe_docs_path(configured)
            self.assertTrue(target.is_dir(), f"Obsidian {setting} does not resolve: {configured}")
        self.assertEqual("folder", app["newFileLocation"])
        self.assertEqual(
            "absolute", app["newLinkFormat"],
            "Obsidian 内部链接类型应选择“基于仓库根目录的绝对路径”，"
            "避免新插入的中央附件引用依赖笔记目录深度。",
        )
        self.assertTrue(app["alwaysUpdateLinks"])

        checked_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                self.root / "README.md",
                self.root / "site.toml",
                app_path,
            )
        )
        old_path_patterns = (
            r"知识库/",
            r"临时笔记/",
            r"(?<![0-9])附件/",
            r"docs/知识库",
            r"docs/碎碎念",
            r"docs/临时笔记",
            r"docs/附件",
        )
        for pattern in old_path_patterns:
            self.assertIsNone(re.search(pattern, checked_text), f"old path remains: {pattern}")

    def _safe_docs_path(self, configured: str) -> Path:
        relative = Path(configured.replace("\\", "/"))
        self.assertFalse(relative.is_absolute(), f"path must be relative to docs/: {configured}")
        docs = self.docs.resolve()
        target = (self.docs / relative).resolve()
        self.assertTrue(target == docs or docs in target.parents, f"path leaves docs/: {configured}")
        return target

    def _unique_page_by_file_name(self, index: VaultIndex, file_name: str):
        matches = sorted(
            (record for record in index.pages.values() if record.file_name == file_name),
            key=lambda record: record.source_path.as_posix(),
        )
        if not matches:
            self.fail(f"页面身份缺失：file_name={file_name!r}")
        if len(matches) > 1:
            candidates = ", ".join(record.source_path.as_posix() for record in matches)
            self.fail(f"页面身份不唯一：file_name={file_name!r}; candidates={candidates}")
        return matches[0]

    def _is_depth_dependent_central_attachment_embed(self, reference, current: Path) -> bool:
        target = reference.target.replace("\\", "/")
        if reference.kind != "embed" or not target.startswith("../"):
            return False
        resolved = (self.docs / current.parent / Path(target)).resolve()
        attachment_root = (self.docs / "09附件").resolve()
        return resolved != attachment_root and attachment_root in resolved.parents

    def _assert_no_depth_dependent_central_attachment_embeds(self, references):
        violations = []
        for reference in references:
            current = reference.span.path
            if self._is_depth_dependent_central_attachment_embed(reference, current):
                target = reference.target.replace("\\", "/")
                suggested = (self.docs / current.parent / target).resolve().relative_to(
                    self.docs.resolve()
                ).as_posix()
                violations.append(
                    f"{reference.span} target={reference.target!r} "
                    f"建议路径={suggested!r}"
                )
        if violations:
            self.fail("禁止使用依赖目录深度的中央附件嵌入：\n" + "\n".join(violations))

    def test_giscus_comments_are_wired_in_the_article_template(self):
        template = self.root / "theme" / "templates" / "article.html"
        self.assertTrue(template.is_file())
        self.assertIn("giscus.app/client.js", template.read_text(encoding="utf-8"))

    def test_central_attachment_violations_are_reported_together(self):
        index = VaultIndex.scan(self.docs)
        references = []
        for current, target in (
            (Path("一级/当前.md"), "../09附件/甲.png"),
            (Path("一级/二级/当前.md"), "../../09附件/乙.png"),
        ):
            references.extend(Converter(index).convert(current, f"![[{target}]]\n").references)
        with self.assertRaises(AssertionError) as caught:
            self._assert_no_depth_dependent_central_attachment_embeds(references)
        message = str(caught.exception)
        for reference in references:
            self.assertIn(str(reference.span), message)
            self.assertIn(f"target={reference.target!r}", message)
        self.assertIn("建议路径='09附件/甲.png'", message)
        self.assertIn("建议路径='09附件/乙.png'", message)

    def test_page_identity_lookup_requires_exactly_one_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a").mkdir()
            (root / "b").mkdir()
            (root / "a" / "唯一.md").write_text("# 唯一\n", encoding="utf-8")
            index = VaultIndex.scan(root)
            self.assertEqual(Path("a/唯一.md"), self._unique_page_by_file_name(index, "唯一").source_path)
            with self.assertRaises(AssertionError):
                self._unique_page_by_file_name(index, "不存在")
            (root / "b" / "唯一.md").write_text("# 唯一\n", encoding="utf-8")
            index = VaultIndex.scan(root)
            with self.assertRaisesRegex(AssertionError, r"a/唯一\.md.*b/唯一\.md"):
                self._unique_page_by_file_name(index, "唯一")

    def test_central_attachment_embed_path_rule_uses_real_references(self):
        index = VaultIndex.scan(self.docs)
        current = Path("05二次元/对看过的番的评价/当前.md")
        result = Converter(index).convert(
            current,
            "---\nexample: ![[../../09附件/foo.webp]]\n---\n\n"
            "```md\n![[../../09附件/foo.webp]]\n```\n\n"
            "`![[../../09附件/foo.webp]]`\n"
            "![[../../09附件/foo.webp]] ![[09附件/foo.webp]]\n",
        )
        embeds = [reference for reference in result.references if reference.kind == "embed"]
        self.assertEqual(["../../09附件/foo.webp", "09附件/foo.webp"], [item.target for item in embeds])
        self.assertTrue(self._is_depth_dependent_central_attachment_embed(embeds[0], current))
        self.assertFalse(self._is_depth_dependent_central_attachment_embed(embeds[1], current))

    def test_all_repository_notes_convert_without_diagnostics_or_mutation(self):
        before = {
            path.relative_to(self.docs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.docs.rglob("*")
            if path.is_file() and ".obsidian" not in path.parts
        }
        index = VaultIndex.scan(self.docs)
        diagnostics = list(index.diagnostics)
        references = []
        for record in index.pages.values():
            result = Converter(index).convert(
                record.source_path,
                (self.docs / record.source_path).read_text(encoding="utf-8"),
            )
            diagnostics.extend(result.diagnostics)
            references.extend(result.references)
        after = {
            path.relative_to(self.docs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.docs.rglob("*")
            if path.is_file() and ".obsidian" not in path.parts
        }
        self.assertEqual(before, after)
        self._assert_no_depth_dependent_central_attachment_embeds(references)
        self.assertEqual([], diagnostics)

    def test_real_current_page_heading_link_uses_fragment_only(self):
        index = VaultIndex.scan(self.docs)
        source_path = self._unique_page_by_file_name(index, "自建梯子：VPS + 3x-ui + VLESS Reality").source_path
        result = Converter(index).convert(
            source_path,
            (self.docs / source_path).read_text(encoding="utf-8"),
        )
        self.assertIn("[[#原理]]", (self.docs / source_path).read_text(encoding="utf-8"))
        self.assertNotIn("[[#原理]]", result.text)
        self.assertIn("(#", result.text)
        self.assertFalse(result.diagnostics)


if __name__ == "__main__":
    unittest.main()
