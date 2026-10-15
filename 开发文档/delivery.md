# 交付记录

## 2.0.0 — 2026-10-15：按“写给谁看”重构分类

- **基线**：`a1e51a9`（Obsidian Git 自动备份，已包含全部迁移文件，并已推送、部署）；README 和版本记录在其后单独提交。
- **范围**：`docs/` 分类重构、`docs/01系统/分类标准.md`、`SECTION_SLUGS`、README 重写、版本 2.0.0。不包括 Inbox Filer 插件本身。
- **环境**：Linux，Python 3.14.4，在临时 venv 中按 `requirements.txt` 安装依赖。系统 Python 缺少 `mkdocs-material`，不能直接构建。CI 使用 Python 3.13.15。

| 验收项 | 方式 | 结果 |
| --- | --- | --- |
| 单元测试与仓库验收测试 | `python -m unittest discover -s tests` | 通过（34 个） |
| 转换、构建、双链和锚点检查 | `python tools/build_site.py` | 通过：198 页公开，21 页不公开 |
| 受保护链接：本地构建产物 | 检查 `site/tech/subscribe-claude-quick/index.html` 和中文旧路径跳转页 | 两者都在，跳转目标正确 |
| 新栏目前缀 | 检查 `site/` 下的 `notes/`、`articles/`、`opus/` | 存在 |
| 不公开目录 | `00收集`、`07自己` 未出现在 `site/` | 通过 |
| 线上部署 | GitHub Actions run 38749696229（提交 `a1e51a9`） | 成功 |
| 线上受保护链接 | 请求 `/tech/subscribe-claude-quick/` 和中文旧路径 | 都返回 200 |
| 线上新栏目 | `sitemap.xml` 中出现 `/Writing/articles/…` | 通过 |
| README 本地预览命令 | `python -m http.server -d site` 后请求首页和受保护页 | 都返回 200，样式路径为相对路径 |

## 未解决项

- 除 `04技术` 外，几乎所有公开页面的网址都变了，旧外链会失效，旧评论不会跟过去。这是本次重构的预期后果，用户已确认。
- `docs/.obsidian/workspace.json` 的“最近打开”仍是旧路径，不影响构建；该文件不提交，Obsidian 打开后会自己更新。
- Inbox Filer 插件还没开发完成。插件可用之前，需要人工或请 Claude 按 `分类标准.md` 分类。
