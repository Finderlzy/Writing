from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from mkdocs.config import load_config

from tools.obsidian_compat.converter import Converter
from tools.obsidian_compat.index import VaultIndex


class RepositoryAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.docs = self.root / "docs"

    def test_structure_configuration_matches_repository_layout(self):
        self.assertTrue((self.docs / "index.md").is_file())

        config = load_config(str(self.root / "mkdocs.yml"))
        self.assertEqual("https://finderlzy.github.io/Writing/", config["site_url"])
        self.assertIn("material/search", config["plugins"])
        self.assertFalse(any(name.endswith("/redirects") for name in config["plugins"]))

        theme = config["theme"]
        for setting in ("logo", "favicon"):
            configured = theme[setting]
            self.assertIsInstance(configured, str)
            target = self._safe_docs_path(configured)
            self.assertTrue(target.is_file(), f"theme {setting} does not resolve: {configured}")

        app_path = self.docs / ".obsidian" / "app.json"
        app = json.loads(app_path.read_text(encoding="utf-8"))
        for setting in ("attachmentFolderPath", "newFileFolderPath"):
            configured = app[setting]
            self.assertIsInstance(configured, str)
            target = self._safe_docs_path(configured)
            self.assertTrue(target.is_dir(), f"Obsidian {setting} does not resolve: {configured}")
        self.assertEqual("folder", app["newFileLocation"])
        self.assertEqual("relative", app["newLinkFormat"])
        self.assertTrue(app["alwaysUpdateLinks"])

        checked_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                self.root / "README.md",
                self.root / "mkdocs.yml",
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

    def test_all_repository_notes_convert_without_diagnostics_or_mutation(self):
        before = {
            path.relative_to(self.docs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.docs.rglob("*")
            if path.is_file() and ".obsidian" not in path.parts
        }
        index = VaultIndex.scan(self.docs)
        diagnostics = list(index.diagnostics)
        for record in index.pages.values():
            result = Converter(index).convert(
                record.source_path,
                (self.docs / record.source_path).read_text(encoding="utf-8"),
            )
            diagnostics.extend(result.diagnostics)
        after = {
            path.relative_to(self.docs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.docs.rglob("*")
            if path.is_file() and ".obsidian" not in path.parts
        }
        self.assertEqual([], diagnostics)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
