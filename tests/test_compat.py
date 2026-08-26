from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.obsidian_compat.converter import Converter
from tools.obsidian_compat.index import VaultIndex


class CompatibilityTests(unittest.TestCase):
    def make_index(self, files: dict[str, str]) -> tuple[Path, VaultIndex]:
        temp = Path(tempfile.mkdtemp())
        for name, text in files.items():
            path = temp / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return temp, VaultIndex.scan(temp)

    def test_inline_highlight_and_multiple_links(self):
        root, index = self.make_index({"当前.md": "# 当前\n", "甲.md": "# 甲\n", "乙.md": "# 乙\n"})
        result = Converter(index).convert(Path("当前.md"), "中文==高亮== [[甲]] 和 [[乙|第二个]]\n")
        self.assertEqual("中文<mark>高亮</mark> [甲](%E7%94%B2.md) 和 [第二个](%E4%B9%99.md)\n", result.text)
        self.assertFalse(result.diagnostics)
        self.assertEqual(2, len(result.references))

    def test_yaml_code_and_inline_code_are_isolated(self):
        root, index = self.make_index({"当前.md": "---\ntitle: [[不转换]]\n---\n", "目标.md": "# 目标\n"})
        text = "---\ntitle: [[不转换]]\n---\n\n```md\n[[不转换]] ==不转换==\n```\n\n`[[不转换]]` [[目标]]\n"
        result = Converter(index).convert(Path("当前.md"), text)
        self.assertIn("title: [[不转换]]", result.text)
        self.assertIn("[[不转换]] ==不转换==", result.text)
        self.assertIn("`[[不转换]]` [目标](%E7%9B%AE%E6%A0%87.md)", result.text)
        self.assertFalse(result.diagnostics)

    def test_callout_and_block_anchor(self):
        root, index = self.make_index({"当前.md": "# 当前\n", "目标.md": "# 目标\n"})
        text = "> [!note] 补充\n> 这是==重点==。\n\n内容 ^block-id\n"
        result = Converter(index).convert(Path("当前.md"), text)
        self.assertIn('!!! note "补充"', result.text)
        self.assertIn("    这是<mark>重点</mark>。", result.text)
        self.assertIn('<a id="^block-id"></a>\n内容\n', result.text)
        self.assertFalse(result.diagnostics)

    def test_loose_lists_are_separated_without_touching_fences(self):
        root, index = self.make_index({"当前.md": "# 当前\n"})
        text = "段落：\n- [ ] 第一项\n- 第二项\n\n```md\n段落：\n- 代码示例\n```\n"
        result = Converter(index).convert(Path("当前.md"), text)
        self.assertIn("段落：\n\n- [ ] 第一项", result.text)
        self.assertIn("```md\n段落：\n- 代码示例\n```", result.text)

    def test_relative_and_cross_directory_links(self):
        root, index = self.make_index(
            {
                "临时/当前.md": "# 当前\n",
                "临时/目标.md": "# 目标\n",
                "追番/Ave Mujica.md": "# Ave Mujica\n",
            }
        )
        result = Converter(index).convert(Path("临时/当前.md"), "[[目标]] [[追番/Ave Mujica]]\n")
        self.assertEqual("[目标](%E7%9B%AE%E6%A0%87.md) [Ave Mujica](../%E8%BF%BD%E7%95%AA/Ave%20Mujica.md)\n", result.text)
        self.assertFalse(result.diagnostics)

    def test_missing_and_ambiguous_targets(self):
        root, index = self.make_index(
            {
                "当前.md": "# 当前\n",
                "a/同名.md": "# 同名\n",
                "b/同名.md": "# 同名\n",
            }
        )
        result = Converter(index).convert(Path("当前.md"), "[[同名]] [[不存在]]\n")
        self.assertEqual({"E_LINK_AMBIGUOUS", "E_LINK_MISSING"}, {item.code for item in result.diagnostics})
        self.assertEqual((Path("a/同名.md"), Path("b/同名.md")), result.diagnostics[0].candidates)

    def test_local_name_wins_and_case_mismatch_is_an_error(self):
        root, index = self.make_index(
            {
                "当前.md": "# 当前\n",
                "当前/目标.md": "# 目标\n",
                "其他/目标.md": "# 目标\n",
                "Case.md": "# Case\n",
            }
        )
        result = Converter(index).convert(Path("当前/笔记.md"), "[[目标]] [[case]]\n")
        self.assertIn("%E7%9B%AE%E6%A0%87.md", result.text)
        self.assertEqual({"E_CASE_MISMATCH"}, {item.code for item in result.diagnostics})
        self.assertEqual((Path("Case.md"),), result.diagnostics[0].candidates)

    def test_heading_and_block_validation(self):
        root, index = self.make_index(
            {
                "当前.md": "# 当前\n[[目标#存在]] [[目标#缺失]] [[目标#^ok]] [[目标#^nope]]\n",
                "目标.md": "# 目标\n## 存在\n正文 ^ok\n",
            }
        )
        result = Converter(index).convert(Path("当前.md"), (root / "当前.md").read_text(encoding="utf-8"))
        self.assertIn("#_2", result.text)
        self.assertIn("[[目标#缺失]]", result.text)
        self.assertIn("[[目标#^nope]]", result.text)
        self.assertEqual({"E_ANCHOR_MISSING", "E_BLOCK_MISSING"}, {item.code for item in result.diagnostics})

    def test_current_page_heading_and_block_references(self):
        root, index = self.make_index(
            {
                "当前.md": "# 当前页\n## 标题\n正文 ^block-id\n",
            }
        )
        result = Converter(index).convert(
            Path("当前.md"),
            "[[#标题]] [[#^block-id|别名]] [[#^block-id]]\n",
        )
        self.assertEqual(
            "[标题](#_2) [别名](#^block-id) [block-id](#^block-id)\n",
            result.text,
        )
        self.assertFalse(result.diagnostics)
        self.assertEqual(
            [("", "标题"), ("", "^block-id"), ("", "^block-id")],
            [(reference.target, reference.anchor) for reference in result.references],
        )

    def test_reference_boundary_matrix_is_diagnostic_and_preserved(self):
        root, index = self.make_index({"当前.md": "# 当前\n"})
        text = "[[]] [[ ]] [[|别名]] [[#]] [[#^]] [[.]] [[./]] [[../]] [[a/..]] [[/]] [[\\\\]]\n"
        result = Converter(index).convert(Path("当前.md"), text)
        self.assertEqual(text, result.text)
        self.assertEqual(
            [
                "E_REFERENCE_EMPTY",
                "E_REFERENCE_EMPTY",
                "E_REFERENCE_EMPTY",
                "E_ANCHOR_EMPTY",
                "E_ANCHOR_EMPTY",
                "E_REFERENCE_INVALID_PATH",
                "E_REFERENCE_INVALID_PATH",
                "E_REFERENCE_INVALID_PATH",
                "E_REFERENCE_INVALID_PATH",
                "E_REFERENCE_INVALID_PATH",
                "E_REFERENCE_INVALID_PATH",
            ],
            [item.code for item in result.diagnostics],
        )

    def test_index_invalid_candidates_are_safe_and_parent_links_work(self):
        root, index = self.make_index(
            {
                "目录/当前.md": "# 当前\n",
                "目标.md": "# 目标\n",
            }
        )
        invalid = ("", " ", ".", "./", "../", "a/..", "/", "\\")
        for target in invalid:
            with self.subTest(target=target):
                self.assertEqual([], index.resolve_page_candidates(Path("目录/当前.md"), target))
                self.assertEqual([], index.resolve_attachment_candidates(Path("目录/当前.md"), target))
                self.assertEqual([], index.case_variants(target, page=True))

        result = Converter(index).convert(Path("目录/当前.md"), "[[../目标]]\n")
        self.assertEqual("[目标](../%E7%9B%AE%E6%A0%87.md)\n", result.text)
        self.assertFalse(result.diagnostics)

    def test_unsupported_embed_and_unclosed_syntax(self):
        root, index = self.make_index({"当前.md": "# 当前\n", "目标.md": "# 目标\n"})
        result = Converter(index).convert(Path("当前.md"), "![[目标]] ==未闭合\n")
        self.assertEqual({"E_UNSUPPORTED_PAGE_EMBED", "E_UNCLOSED_HIGHLIGHT"}, {item.code for item in result.diagnostics})
        self.assertIn("![[目标]]", result.text)


if __name__ == "__main__":
    unittest.main()
