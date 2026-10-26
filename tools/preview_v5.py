"""临时入口：用新流水线把真实内容构建到指定目录，供 5.0.0 改版逐条核对。

用法：`.venv/bin/python tools/preview_v5.py <输出目录>`

只生成文章页（T1 范围）；首页、全部文章、系列页、404 和跳转页在后续任务里补。
预览用旧文件夹布局：03思考 → thoughts、03思考/初稿 → drafts、04技术 → blog、05作品 → opus，
系列先留空，所以首页不排除任何博客。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.content import Layout, Stage  # noqa: E402
from tools.render import build_pages, load_config  # noqa: E402

DOCS = ROOT / "docs"
CONFIG = ROOT / "site.toml"

PREVIEW_LAYOUT = Layout(
    stages=(
        Stage("03思考", "思考", "thoughts"),
        Stage("03思考/初稿", "初稿", "drafts"),
        Stage("04技术", "博客", "blog"),
        Stage("05作品", "作品", "opus"),
    ),
    series={},
)


def preview(destination: Path) -> int:
    destination = destination.resolve()
    if destination == ROOT or ROOT in destination.parents and destination.name in {"docs", "tools", "theme", "tests"}:
        print(f"不能把预览输出到仓库目录：{destination}", file=sys.stderr)
        return 2
    destination.mkdir(parents=True, exist_ok=True)
    config = load_config(CONFIG)
    if not config.theme.is_absolute():
        config = type(config)(
            site_name=config.site_name,
            site_url=config.site_url,
            theme=ROOT / config.theme,
        )
    diagnostics = build_pages(DOCS, destination, config, PREVIEW_LAYOUT)
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        print(f"构建失败：{len(diagnostics)} 个问题", file=sys.stderr)
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
