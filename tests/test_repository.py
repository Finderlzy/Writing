from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools.obsidian_compat.converter import Converter
from tools.obsidian_compat.index import VaultIndex


class RepositoryAcceptanceTests(unittest.TestCase):
    def test_all_repository_notes_convert_without_diagnostics_or_mutation(self):
        root = Path(__file__).resolve().parents[1]
        docs = root / "docs"
        before = {
            path.relative_to(docs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in docs.rglob("*")
            if path.is_file() and ".obsidian" not in path.parts
        }
        index = VaultIndex.scan(docs)
        diagnostics = list(index.diagnostics)
        for record in index.pages.values():
            result = Converter(index).convert(record.source_path, (docs / record.source_path).read_text(encoding="utf-8"))
            diagnostics.extend(result.diagnostics)
        after = {
            path.relative_to(docs).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in docs.rglob("*")
            if path.is_file() and ".obsidian" not in path.parts
        }
        self.assertEqual([], diagnostics)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
