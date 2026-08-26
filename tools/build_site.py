from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CACHE = ROOT / ".cache" / "converted-docs"
SITE = ROOT / "site"
sys.dont_write_bytecode = True

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.obsidian_compat.converter import Converter
from tools.obsidian_compat.diagnostics import emit_diagnostics
from tools.obsidian_compat.html_check import check_site
from tools.obsidian_compat.index import VaultIndex
from tools.obsidian_compat.parser import residual_diagnostics


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


def _copy_and_convert(index: VaultIndex, converter: Converter) -> list:
    diagnostics = list(index.diagnostics)
    for record in index.pages.values():
        source = DOCS / record.source_path
        result = converter.convert(record.source_path, source.read_text(encoding="utf-8"))
        diagnostics.extend(result.diagnostics)
        reference_spans = {reference.span for reference in result.references}
        diagnostics.extend(
            diagnostic
            for diagnostic in residual_diagnostics(record.source_path, result.text)
            if not (
                diagnostic.code == "E_RESIDUAL_OBSIDIAN"
                and diagnostic.span in reference_spans
            )
        )
        destination = CACHE / record.source_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(result.text, encoding="utf-8", newline="")
    for record in index.attachments.values():
        destination = CACHE / record.output_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DOCS / record.source_path, destination)
    return diagnostics


def build() -> int:
    before = _manifest(DOCS)
    try:
        _clean_output(CACHE, ROOT / ".cache")
        _clean_output(SITE, ROOT)
        index = VaultIndex.scan(DOCS)
        diagnostics = _copy_and_convert(index, Converter(index))
        if diagnostics:
            emit_diagnostics(diagnostics)
            return 1

        from mkdocs.commands.build import build as mkdocs_build
        from mkdocs.config import load_config

        config = load_config(str(ROOT / "mkdocs.yml"))
        config["docs_dir"] = str(CACHE)
        config["site_dir"] = str(SITE)
        config["strict"] = True
        mkdocs_build(config)
        html_diagnostics = check_site(SITE, config.get("site_url"))
        if html_diagnostics:
            emit_diagnostics(html_diagnostics)
            return 1
        after = _manifest(DOCS)
        if before != after:
            changed = sorted(set(before) | set(after))
            changed = [path for path in changed if before.get(path) != after.get(path)]
            print(f"[E_SOURCE_MUTATED] 构建期间源文件发生变化：{', '.join(changed)}", file=sys.stderr)
            return 1
        print(f"build succeeded: {len(index.pages)} pages, {len(index.attachments)} attachments")
        return 0
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"[E_TOOL_CONFIG] 构建依赖不可用：{exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[E_TOOL_INTERNAL] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(build())
