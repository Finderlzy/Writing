# 本站字体

标题、数字和手写短句用的四款字体都按 SIL Open Font License 1.1 发布，许可原文在同一个目录里。R-VIS-5 要求字体放本站、只包含用得到的字；`tools/fonts.py` 在构建时把源字体子集化成 woff2。

## 字体来自哪里

源字体**不提交进仓库**（五个文件合计 18.95 MB，提交后会永久留在 git 历史里）。构建和本地开发都按下面的固定地址下载，并逐个校验 SHA-256；地址里的提交号固定，内容不会再变。

- 来源：<https://github.com/google/fonts>，提交 `e7db6ca603fd4862010383ff17ffd6cc4ffac1c0`
- 下载脚本：`python -m tools.fetch_fonts`，下载到 `.cache/fonts/`（已在 `.gitignore` 里）
- 也可以用环境变量 `FONT_SOURCE_DIR` 指向别处放源字体的目录；本地没网、又只想先看页面时，用 `python tools/build_site.py --skip-fonts`，标题会退回系统字体
- CI（`.github/workflows/deploy.yml`）在构建前跑同一条命令；下载或校验失败时构建失败，线上维持上一版

| 文件 | 用途（`data-font`） | 许可 | SHA-256 |
| --- | --- | --- | --- |
| `NotoSansSC[wght].ttf`（可变字体，固定到 wght=900） | `head`：标题、站名、粗字 | `NotoSansSC-OFL.txt` | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| `ZCOOLKuaiLe-Regular.ttf` | `cute`：区块标题、“复制”、“留言” | `ZCOOLKuaiLe-OFL.txt` | `812a6fc1fe54b6d73a419245c32dfeba8aa33104d5be90d1cf6af082007cb71d` |
| `ZillaSlab-SemiBold.ttf` | `slab` 600：日期、数字 | `ZillaSlab-OFL.txt` | `aafcb295b88d520357db1ecf9a1c3167055e87e9ddf5f63e560cbd139ec2805e` |
| `ZillaSlab-Bold.ttf` | `slab` 700：站名 | `ZillaSlab-OFL.txt` | `4ec3a04a4eef37074b42ef542e4d874e13646668cfe65256e0bf100441cf8719` |
| `GochiHand-Regular.ttf` | `hand`：手写英文短句（“yep!”） | `GochiHand-OFL.txt` | `c46b029ab4846b2935e301af0b2cf85a1d74d2858e6a33636a3e64cf3cc4696b` |

正文不加载任何网络字体，用读者系统里的中文字体栈（PingFang SC、Microsoft YaHei、Noto Sans CJK SC 等）。

## 产物

`site/assets/fonts/` 下是构建产物，不提交：

| 文件 | 角色 | 实测体积 |
| --- | --- | --- |
| `head.woff2` | 很粗的标题 | 约 50 KB |
| `cute.woff2` | 手写味的中文标题 | 约 2 KB |
| `slab-600.woff2` / `slab-700.woff2` | 数字、日期、站名 | 各约 15 KB |
| `hand.woff2` | 手写英文短句 | 约 1 KB |

合计约 81 KB，预算是 300 KB（需求 §9 的非功能要求），超过时构建给 `W_FONT_BUDGET` 提示。

## 改动时注意

- 模板里写 `data-font="head|cute|slab|hand"` 的元素，它和它子元素的**文字**会收进对应字体；写了别的值会报 `E_FONT_ROLE_UNKNOWN`。
- 模板里用不到 `data-font` 的固定字（比如只在 CSS 里出现的数字、标点）写在 `tools/fonts.py` 的 `FontSpec.text` 里。
- `site.css` 里 `@font-face` 的家族名必须和 `:root` 的 `--font-*` 引用完全一致，否则浏览器静默回退到系统字体，从截图上看不出来。两个 Zilla Slab 共用 `Zilla Slab Lzy` 一个家族，靠 `font-weight` 区分。
