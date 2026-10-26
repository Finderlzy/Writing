"""Download the source fonts into `.cache/fonts/` and check them against SHA-256.

Source fonts are not committed: they are 18.95 MB and would stay in the git history
forever. CI downloads them in `deploy.yml`; run this once locally before building.
The files, their source and their hashes are recorded in `theme/fonts/README.md` and
architecture.md §7.1.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .fonts import CACHE_FONTS

# google/fonts 的提交号固定下来，内容不会再变；URL 里的 main 换成这个提交号
COMMIT = "e7db6ca603fd4862010383ff17ffd6cc4ffac1c0"
BASE_URL = f"https://raw.githubusercontent.com/google/fonts/{COMMIT}/"

# 文件名 → (仓库路径, SHA-256)。前五个是源字体，OFL.txt 是许可原文。
FILES: dict[str, tuple[str, str]] = {
    "NotoSansSC[wght].ttf": ("ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf", "a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da"),
    "ZCOOLKuaiLe-Regular.ttf": ("ofl/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf", "812a6fc1fe54b6d73a419245c32dfeba8aa33104d5be90d1cf6af082007cb71d"),
    "ZillaSlab-SemiBold.ttf": ("ofl/zillaslab/ZillaSlab-SemiBold.ttf", "aafcb295b88d520357db1ecf9a1c3167055e87e9ddf5f63e560cbd139ec2805e"),
    "ZillaSlab-Bold.ttf": ("ofl/zillaslab/ZillaSlab-Bold.ttf", "4ec3a04a4eef37074b42ef542e4d874e13646668cfe65256e0bf100441cf8719"),
    "GochiHand-Regular.ttf": ("ofl/gochihand/GochiHand-Regular.ttf", "c46b029ab4846b2935e301af0b2cf85a1d74d2858e6a33636a3e64cf3cc4696b"),
    "NotoSansSC-OFL.txt": ("ofl/notosanssc/OFL.txt", "1c05c68c34f9708415aada51f17e1b0092d2cea709bf4a94cd38114f9e73d7d9"),
    "ZCOOLKuaiLe-OFL.txt": ("ofl/zcoolkuaile/OFL.txt", "538078469839b4a2e7ad22bef4ebe41681a4e53749bb2a072144024f1d6d703d"),
    "ZillaSlab-OFL.txt": ("ofl/zillaslab/OFL.txt", "240b385d3ec8c8d5c1d4af2bbba6ac72bac0309a80c1a8ff112c168643cc6811"),
    "GochiHand-OFL.txt": ("ofl/gochihand/OFL.txt", "b36cb03d6ddc163452d9935ce6f325741434272d3889acf42cc23584f31a85bf"),
}

_CHUNK = 1 << 20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str, repo_path: str, expected: str, directory: Path) -> str:
    """Fetch one file if missing or corrupt; returns "kept", "fetched" or "unchanged"."""
    target = directory / name
    if target.is_file() and sha256(target) == expected:
        return "kept"
    url = BASE_URL + repo_path
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
        data = response.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError(f"{name}: SHA-256 不符，期望 {expected}，实际 {actual}（上游改过内容，需要人来看）")
    target.write_bytes(data)
    return "fetched"


def fetch(directory: Path = CACHE_FONTS, *, only_fonts: bool = False) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    items = list(FILES.items())
    if only_fonts:
        items = [(name, item) for name, item in items if not name.endswith(".txt")]
    for name, (repo_path, expected) in items:
        try:
            state = download(name, repo_path, expected, directory)
        except (urllib.error.URLError, ValueError, OSError) as exc:
            print(f"[E_FONT_DOWNLOAD] {name}: {exc}", file=sys.stderr)
            return 1
        print(f"{name}: {state}")
    print(f"源字体就绪：{directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(fetch())
