"""本地预览：站点挂在 /writing/ 子路径下，和线上路径一致；根目录的 404.html 相对网址按线上做法处理。
不存在的页面返回构建出来的 site/404.html（GitHub Pages 的做法）。
用法：.venv/bin/python .preview-v510/serve.py [端口]
"""
from __future__ import annotations

import http.server
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site"
PREFIX = "/writing"
SITE_URL = "https://finderlzy.github.io/writing/"
NOT_FOUND = (ROOT / "404.html").read_text(encoding="utf-8")
# 线上 404.html 在站点根，相对网址要按根来解析；本地它是 /writing/404.html，把相对网址改成绝对
NOT_FOUND_LOCAL = re.sub(r'(href|src)="(?!https?:|#|/)([^"]+)"', lambda m: f'{m.group(1)}="{PREFIX}/{m.group(2).lstrip("./")}"', NOT_FOUND)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def translate_path(self, path):
        target = path.split("?", 1)[0].split("#", 1)[0]
        if target == PREFIX or target.startswith(PREFIX + "/"):
            return super().translate_path(target[len(PREFIX):] or "/")
        return super().translate_path("/__missing__")

    def do_GET(self):
        target = self.path.split("?", 1)[0].split("#", 1)[0]
        if target != PREFIX and not target.startswith(PREFIX + "/"):
            self.send_response(302)
            self.send_header("Location", PREFIX + "/")
            self.end_headers()
            return
        fs = Path(self.translate_path(self.path))
        if fs.is_dir() and not target.endswith("/"):
            self.send_response(301)
            self.send_header("Location", self.path + "/")
            self.end_headers()
            return
        return super().do_GET()

    def send_error(self, code, message=None, explain=None):
        if code == 404 and self.command in {"GET", "HEAD"}:
            body = NOT_FOUND_LOCAL.encode("utf-8")
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8321
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"serving {ROOT} at http://127.0.0.1:{port}{PREFIX}/", flush=True)
    server.serve_forever()
