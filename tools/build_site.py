from __future__ import annotations

import hashlib
import shutil
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CACHE = ROOT / ".cache" / "converted-docs"
SITE = ROOT / "site"
CONFIG = ROOT / "site.toml"
# 不发布的一级目录：发布范围由 content.LAYOUT 决定，这里只用来统计和文档化
UNPUBLISHED_PATHS = ("00收集", "01系统", "07自己")
# 5.0.0 之前发出去、改版后还要能打开的旧网址 → 现在的位置，写成 <旧地址前缀>: <新网址前缀>。
# 订阅教程的旧地址在视频里公开过，见 AGENTS.md“订阅教程旧链接”。
REDIRECTS = {
    "tech/subscribe-claude-quick": "blog/subscribe-claude-quick",
}

sys.dont_write_bytecode = True

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.content import LAYOUT, Layout, is_published
from tools.obsidian_compat.diagnostics import emit_diagnostics
from tools.render import build_pages, load_config


def _safe_child(path: Path, parent: Path) -> Path:
    resolved_parent = parent.resolve()
    resolved = path.resolve()
    if resolved != resolved_parent and resolved_parent not in resolved.parents:
        raise RuntimeError(f"refusing path outside {resolved_parent}: {resolved}")
    return resolved


def _manifest(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file() and ".obsidian" not in path.parts:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            values[path.relative_to(root).as_posix()] = digest
    return values


def _clean_output(path: Path, parent: Path) -> None:
    target = _safe_child(path, parent)
    if target.is_symlink():
        raise RuntimeError(f"refusing to remove symlink: {target}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def _site_config():
    config = load_config(CONFIG)
    return config if config.theme.is_absolute() else replace(config, theme=ROOT / config.theme)


def _count_published(docs: Path, layout: Layout) -> tuple[int, int]:
    published = unpublished = 0
    for path in docs.rglob("*.md"):
        if ".obsidian" in path.parts:
            continue
        if is_published(path.relative_to(docs), layout):
            published += 1
        else:
            unpublished += 1
    return published, unpublished


def build(layout: Layout = LAYOUT) -> int:
    before = _manifest(DOCS)
    try:
        _clean_output(CACHE, ROOT / ".cache")
        _clean_output(SITE, ROOT)
        diagnostics = build_pages(DOCS, SITE, _site_config(), layout, list(REDIRECTS.items()))
        emit_diagnostics(diagnostics)
        after = _manifest(DOCS)
        if before != after:
            changed = sorted(set(before) | set(after))
            changed = [path for path in changed if before.get(path) != after.get(path)]
            print(f"[E_SOURCE_MUTATED] 构建期间源文件发生变化：{', '.join(changed)}", file=sys.stderr)
            return 1
        if any(not diagnostic.code.startswith("W_") for diagnostic in diagnostics):
            return 1  # W_ 开头的只是提示，站点照常发布
        published, unpublished = _count_published(DOCS, layout)
        print(f"build succeeded: {published} pages published, {unpublished} unpublished")
        return 0
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"[E_TOOL_CONFIG] 构建依赖不可用：{exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[E_TOOL_INTERNAL] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(build())
