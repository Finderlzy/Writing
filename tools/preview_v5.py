"""临时入口：用新流水线把真实内容构建到指定目录，供 5.0.0 改版逐条核对。

用法：`.venv/bin/python tools/preview_v5.py <输出目录>`

预览用旧文件夹布局：03思考 → thoughts、03思考/初稿 → drafts、04技术 → blog、05作品 → opus。
系列按架构文档 §6 配成 04技术/原理版、04技术/操作版，入口篇在 04技术 根目录（线上正式布局
换成 04博客 时，只需把前缀替换掉）。
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_site import REDIRECTS
from tools.content import Layout, Stage
from tools.render import build_pages, load_config

DOCS = ROOT / "docs"
CONFIG = ROOT / "site.toml"

PREVIEW_LAYOUT = Layout(
    stages=(
        Stage("03思考", "思考", "thoughts"),
        Stage("03思考/初稿", "初稿", "drafts"),
        Stage("04技术", "博客", "blog"),
        Stage("05作品", "作品", "opus"),
    ),
    series={
        "04技术/原理版": "04技术/如何订阅claude.md",
        "04技术/操作版": "04技术/如何订阅claude（纯操作版）.md",
    },
)


def preview(destination: Path) -> int:
    destination = destination.resolve()
    if destination == ROOT or ROOT in destination.parents and destination.name in {"docs", "tools", "theme", "tests"}:
        print(f"不能把预览输出到仓库目录：{destination}", file=sys.stderr)
        return 2
    if destination.is_dir():
        shutil.rmtree(destination)  # 上一次的残留会让跳转页撞上自己，每次从空目录开始
    destination.mkdir(parents=True, exist_ok=True)
    config = load_config(CONFIG)
    if not config.theme.is_absolute():
        config = replace(config, theme=ROOT / config.theme)
    diagnostics = build_pages(DOCS, destination, config, PREVIEW_LAYOUT, list(REDIRECTS.items()))
    warnings = [diagnostic for diagnostic in diagnostics if diagnostic.code.startswith("W_")]
    errors = [diagnostic for diagnostic in diagnostics if not diagnostic.code.startswith("W_")]
    for diagnostic in warnings:
        print(diagnostic.format(), file=sys.stderr)
    if errors:
        for diagnostic in errors:
            print(diagnostic.format(), file=sys.stderr)
        print(f"构建失败：{len(errors)} 个问题", file=sys.stderr)
        return 1
    pages = sorted(destination.rglob("index.html"))
    print(f"preview succeeded: {len(pages)} pages in {destination}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("用法：tools/preview_v5.py <输出目录>", file=sys.stderr)
        return 2
    return preview(Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))