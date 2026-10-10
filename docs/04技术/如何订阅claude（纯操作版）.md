---
slug: subscribe-claude-quick
createdDate: 2026-10-08
updatedDate: 2026-10-10
---
> 写于 2026-10-08
> 这是只有操作步骤的版本。想知道每一步为什么这么做，以及哪里看得不是很懂的，请看完整版：[[04技术/如何订阅claude|如何订阅claude]]

## 前言
---
说实话，我有点犹豫要不要现在发这篇。我的 claude 才订阅了四天。时间太短，我没法保证这套方法长期有效，只能说它目前对我管用。而且为了走到这一步，我前前后后折腾了很久，所以流程会有点繁琐。

这一版只写怎么做，不讲为什么。哪一步想知道原因，或者某个细节失效了想自己调，去完整版里找对应的小节。

文中没写的情况，我不一定可以给出答案，请见谅。

>[!caution] 免责声明
>- 本文只是记录个人的操作经历，仅供学习和技术交流，不构成任何建议。
>- 请遵守你所在地区的法律法规，自行判断相关操作是否合规，并自行承担由此产生的风险和后果。
>- 不要将文中的任何方法用于违法违规的用途。
>- 文中的购买链接都是我的推广链接。通过它们购买，你的价格只会低，不会高，但同时我会拿到一点佣金。介意的话直接搜商家名字就行。除此之外我和这些商家没有其他关系，它们的稳定性、安全性和合规性，我无法保证。

先叠个甲：如果照着做还是被封号了，请不要骂我，麻烦去骂 a/，谢谢🌹

## 开始之前
---
**成本**：按方案一做，每月 4.5 美元，是服务器的费用，每个月都要交。不含 claude 的订阅费。方案二、三的价格看商家。

**前置条件**：

- **一个 Gmail 账号**：注册 claude 和美区 Apple ID 都要用。
- **会用代理**：会导入节点、切换节点、打开和关闭代理。
- **一部 iPhone**：订阅是在 iPhone 的 Claude app 里完成的。

以上不会的，先看原理版：[[04技术/如何订阅claude|如何订阅claude]]。Gmail 看“Gmail 与 Google 账号”一节，代理看[[04技术/自建梯子：VPS + 3x-ui + VLESS Reality#六、导入代理软件|自建梯子]]里“导入代理软件”那一节。

**流程：** 准备住宅 IP → 配置代理软件 → 防泄漏 → 改时区 → 注册 claude 并先用几天 → 注册美区 Apple ID → 买礼品卡充值 → 在 app 里订阅。

**每一步都做完再做下一步，全程开着住宅节点。**

## 一、准备住宅 IP
---
三选一，只看你选的那一个，做完都到「确认出口 IP」。

| 方案 | 要做什么 | 适合谁 |
| --- | --- | --- |
| 一：普通服务器 + 白嫖住宅 IP | 买服务器 → 白嫖住宅 IP → 运行脚本 | 想省钱，我自己用的就是这个 |
| 二：住宅 IP 服务器 | 买服务器 → 运行脚本 | 不想多弄一个住宅 IP |
| 三：直接买住宅节点 | 导入代理软件 | 不想碰服务器 |

**不要用机场节点。**

### 方案一：普通服务器 + 白嫖住宅 IP

**流程：** 买服务器 → 白嫖住宅 IP → 运行脚本，按脚本的问题填前两步拿到的信息。

#### 1. 买服务器

**购买地址**：[VoyraCloud](https://www.voyracloud.com/?ref_code=HYEWZ46M)（我自己用的是它家的云 VPS）

**怎么选**：

| 选项 | 怎么选 |
| --- | --- |
| 系统 | **Ubuntu 22.04 / 24.04** 或 **Debian 12**（脚本只支持这两种） |
| 配置 | 1 核 CPU、1 GB 内存就够 |
| 流量 | 每月几百 GB 足够 |
| 机房位置 | 美国、日本、新加坡等 |

**买完记下三样东西**（在商家控制台的服务器详情页，或者发到你的邮箱）：

- **服务器 IP**：形如 `165.154.xxx.xxx`，第 3 步要填。
- **用户名**：一般是 `root`。
- **密码**：root 的密码。

顺便看一眼商家后台有没有“防火墙”“安全组”菜单，有的话记住位置，第 3 步要用。

**用 SSH 连上服务器**：

1. 打开本地命令行：
   - Windows：按 `Win + R`，输入 `cmd` 回车。
   - Mac：启动台搜索“终端”。
2. 输入下面的命令回车，`你的服务器IP` 换成真实 IP：

```bash
ssh root@你的服务器IP
```

3. 问 `Are you sure you want to continue connecting` 时，输入 `yes` 回车。
4. 出现 `password:` 时，输入 root 密码回车。**输入时屏幕上什么都不显示，是正常的**。可以复制密码后在命令行里右键粘贴。
5. 命令行开头变成 `root@...:~#`，就连上了。后面的命令都在这个窗口里输入。

#### 2. 白嫖住宅 IP

1. 打开 [proxy.qsu.hk](https://proxy.qsu.hk/) 注册账号（不是主站 qsu.hk，主站卖的是住宅服务器）。
2. 选择 **SOCKS5 协议**的套餐，下单时填优惠码 `qiansu998`，就能免费拿到一个住宅 IP。流量额度以下单页面为准。
3. 记下商家给的**住宅 IP、端口、用户名、密码**，第 3 步要填。

拿到后用 [ipinfo.io](https://ipinfo.io/what-is-my-ip) 和 [scamalytics.com](https://scamalytics.com/) 查一下这个住宅 IP：类型要是“住宅/ISP”，风险分数要低。不要用 ping0.cc 测。

#### 3. 运行脚本

> [!tip] 脚本不用改
> 下面的脚本**整段直接复制就行，不用改任何内容**。运行的时候它会一个个问你问题，到时候再填第 1、2 步记下的信息。

脚本会装好 Xray、建好节点、套上住宅 IP、开好防火墙。

1. 在 VPS 上输入下面的命令，回车，会打开一个空白的编辑器：

```bash
nano setup.sh
```

2. 复制下面整段脚本，在编辑器里右键（或 `Ctrl + Shift + V`）粘贴：

```bash
#!/usr/bin/env bash
set -euo pipefail

read -rp "服务器 IP（就是你 SSH 连接用的 IP）: " IP
read -rp "节点端口（直接回车用 8555）: " PORT; PORT=${PORT:-8555}
read -rp "伪装网站（直接回车用 www.microsoft.com）: " SNI; SNI=${SNI:-www.microsoft.com}
read -rp "住宅代理 IP（方案二直接回车跳过）: " RES_IP
if [ -n "$RES_IP" ]; then
  read -rp "住宅代理端口: " RES_PORT
  read -rp "住宅代理用户名: " RES_USER
  read -rp "住宅代理密码: " RES_PASS
fi

if [ -z "$IP" ]; then echo "服务器 IP 不能为空"; exit 1; fi

apt update
apt install -y curl openssl ufw
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

UUID=$(xray uuid)
KEYS=$(xray x25519)
PRI=$(echo "$KEYS" | grep -i 'private' | awk -F': ' '{print $2}' | tr -d ' ')
PUB=$(echo "$KEYS" | grep -iE 'public|password' | awk -F': ' '{print $2}' | tr -d ' ')
SID=$(openssl rand -hex 8)
SSH_PORT=$(ss -tlnpH | awk '/sshd/ {sub(/.*:/, "", $4); print $4; exit}')
SSH_PORT=${SSH_PORT:-22}

if [ -z "$PRI" ] || [ -z "$PUB" ]; then
  echo "没取到密钥，xray x25519 的输出是："; echo "$KEYS"; exit 1
fi

if [ -n "$RES_IP" ]; then
  RES_OUT=',
    {"protocol": "socks", "tag": "residential",
     "settings": {"servers": [{"address": "'"$RES_IP"'", "port": '"$RES_PORT"',
                               "users": [{"user": "'"$RES_USER"'", "pass": "'"$RES_PASS"'"}]}]}}'
  RES_RULE='{"type": "field", "domain": ["geosite:anthropic", "domain:ipinfo.io"], "outboundTag": "residential"}'
else
  RES_OUT=''
  RES_RULE=''
fi

cat > /usr/local/etc/xray/config.json <<EOF
{
  "log": {"loglevel": "warning"},
  "inbounds": [{
    "port": $PORT, "protocol": "vless",
    "settings": {"clients": [{"id": "$UUID", "flow": "xtls-rprx-vision"}], "decryption": "none"},
    "streamSettings": {"network": "tcp", "security": "reality",
      "realitySettings": {"dest": "$SNI:443", "serverNames": ["$SNI"],
                          "privateKey": "$PRI", "shortIds": ["$SID"]}},
    "sniffing": {"enabled": true, "destOverride": ["http", "tls", "quic"], "routeOnly": true}
  }],
  "outbounds": [
    {"protocol": "freedom", "tag": "direct"}$RES_OUT
  ],
  "routing": {"rules": [$RES_RULE]}
}
EOF

xray run -test -c /usr/local/etc/xray/config.json
systemctl enable xray
systemctl restart xray

ufw allow "$SSH_PORT"/tcp
ufw allow "$PORT"/tcp
ufw --force enable

echo
echo "===== 完成，复制下面这行导入代理软件 ====="
echo "vless://$UUID@$IP:$PORT?type=tcp&security=reality&sni=$SNI&fp=chrome&pbk=$PUB&sid=$SID&flow=xtls-rprx-vision#my-node"
```

3. 按 `Ctrl + O`，再按回车保存；按 `Ctrl + X` 退出编辑器。
4. 运行脚本：

```bash
bash setup.sh
```

5. 按提示回答问题：

| 问题 | 怎么填 |
| --- | --- |
| 服务器 IP | 第 1 步记下的服务器 IP，就是 SSH 连接时用的那个 |
| 节点端口 | 直接回车，用默认的 **8555** |
| 伪装网站 | 直接回车，用默认的 www.microsoft.com |
| 住宅代理 IP、端口、用户名、密码 | 第 2 步记下的。方案二：住宅代理 IP 直接回车，后面三个不会再问 |

6. 等脚本跑完（中途弹出紫色/蓝色对话框就直接回车）。最后一行是 `vless://` 开头的链接，复制下来，**通过剪贴板**导入代理软件。**这个链接不要发给别人。**
7. 商家后台有防火墙/安全组的话，放行 **TCP 8555**。

脚本报错停下了，把报错截图保存好，去完整版对照排查。

### 方案二：住宅 IP 服务器

方案二就是方案一**去掉“白嫖住宅 IP”这一步**：服务器本身就是住宅 IP，不用再套一层。

1. 买一台住宅 IP 服务器：[VoyraCloud](https://www.voyracloud.com/?ref_code=HYEWZ46M) 或 [QSU](https://qsu.hk/aff/GAZUQBSL)（这两家的住宅服务器我都没用过）。买之前先找商家要 IP，用 [ipinfo.io](https://ipinfo.io/what-is-my-ip) 和 [scamalytics.com](https://scamalytics.com/) 测一下：类型要是“住宅/ISP”，风险分数要低。
2. 系统怎么选、买完记什么、怎么 SSH 连上，和方案一的「1. 买服务器」一样。
3. 跳过「2. 白嫖住宅 IP」，直接做方案一的「3. 运行脚本」。**问到住宅代理 IP 时直接回车跳过。**

### 方案三：直接买住宅节点

不用买服务器，也不用运行脚本。

1. 在 ipequal 买套餐，**使用类型选“1 人独享”**。国内能打开的地址：[ipequal](https://www.ipequal.com/?ref=6adabd0307)；开代理才能打开的地址：[ipequal](https://www.equaldcdn.com/?ref=6adabd0307)。（我没用过，是很多人推荐的。建议先买一个月。）
2. 复制订阅链接，**通过剪贴板**导入代理软件。
3. 用 claude 时选中这个住宅节点。

### 确认出口 IP

开着代理打开 [ipinfo.io](https://ipinfo.io/what-is-my-ip)：

- 类型显示“住宅/ISP”，就成功了。
- 记下 IP 所在的地区。

## 二、配置代理软件
---
1. **电脑开 tun 模式**。以 v2rayN 为例：右键 → **以管理员身份运行** → 主界面底部打开“启用 Tun”。
2. **确认 claude 走代理**。不确定的话，用 claude 时直接开全局。
3. **手机**：Shadowrocket 这类软件打开就行，确认 claude 走的是住宅节点。
4. **用 claude 时固定用这一个节点，不要换来换去。**

## 三、防泄漏
---
### 1. DNS

1. 开 tun 模式（上一步已做）。
2. v2rayN → DNS 设置：国外域名用远程 DNS（`1.1.1.1` 或 `8.8.8.8`），并且通过代理查询。
3. v2rayN → 路由设置：“域名解析策略”选 `AsIs`。
4. 关掉浏览器的“安全 DNS”：
   - Chrome：设置 → 隐私和安全 → 安全 → 关闭“使用安全 DNS”。
   - Edge：设置 → 隐私、搜索和服务 → 关闭“使用安全 DNS”。

**检测**：打开 [browserleaks.com/dns](https://browserleaks.com/dns)，结果里不能有国内的 DNS（比如 China Telecom、China Unicom）。

### 2. WebRTC

- Chrome / Edge：装插件“WebRTC Leak Prevent”；或者在 uBlock Origin 设置里勾选“防止 WebRTC 泄露本地 IP 地址”。
- Firefox：地址栏输入 `about:config`，把 `media.peerconnection.enabled` 改为 `false`。

**检测**：打开 [browserleaks.com/webrtc](https://browserleaks.com/webrtc)，“Public IP”只能是你的住宅 IP。

### 3. IPv6

检测网站上如果出现国内的 IPv6 地址，在电脑网卡设置里关掉 IPv6。

## 四、改时区
---
时区选 claude 支持的地区，比如台湾、新加坡；不确定就选住宅 IP 所在城市的时区。**中国大陆和香港不行。**

**电脑（Windows）**：设置 → 时间和语言 → 日期和时间 → 关闭“自动设置时区” → 手动选时区。

**iPhone**：
1. 设置 → 隐私与安全性 → 定位服务 → 系统服务（滑到最底下）→ 关闭“设定时区”。
2. 设置 → 通用 → 日期与时间 → 关闭“自动设置” → 手动选城市。

两步都要做。

## 五、注册 claude
---
1. 前面五步都做完、检测都通过，再注册。
2. 用 Google 账号注册。
3. 一个 IP 只注册一个账号。
4. **注册后先正常用几天**，最好用完免费额度、等它弹出升级提示，再订阅。

## 六、订阅（iPhone）
---
安卓用户：我没有验证过的方案。听说可以用美区 Google Play 礼品卡，但我没试过。

### 1. 注册美区 Apple ID

已经有美区 Apple ID 的跳过。

1. 浏览器（手机、电脑都行）打开 appleid.apple.com → 点右上角箭头 →“创建你的 Apple 账户”。

![[09附件/订阅claude-AppleID-1-打开网址.jpg|262]]
![[09附件/订阅claude-AppleID-2-创建账户.jpg|262]]

2. 国家/地区选“**美国**”；姓名可以填拼音；生日要满 18 岁；邮箱用 Gmail；手机号可以用 +86。

![[09附件/订阅claude-AppleID-3-选择美国.jpg|262]]

3. 完成邮箱和手机验证。
4. 重新登录一次，确认地区是美国。付款方式不用填。

### 2. 在 App Store 登录

1. 打开 **App Store（不是“设置”）** → 右上角头像 → 拉到最底部，退出原账号。
2. 登录美区 Apple ID。
3. 配置**账单寄送地址**，**付款方式不要动**，保持“无”：
   1. 右上角头像 → 你的名字 →“账单寄送地址”（“付款方式”应该显示“无”）。

![[09附件/订阅claude-AppleStore-1-账户设置.jpg|262]]

   2. 跳到“添加付款方式”页面，不用填（第一次进入可能要求填付款方式才能保存，也不用管），直接返回。

![[09附件/订阅claude-AppleStore-2-添加付款方式.jpg|262]]

   3. 返回后进入“管理付款方式”，点下面的“账单寄送地址”→ 右上角“编辑”，填地址并保存。地址填免税州的（比如俄勒冈州），要真实存在、格式正确，网上能搜到。

![[09附件/订阅claude-AppleStore-3-管理付款方式.jpg|262]]
![[09附件/订阅claude-AppleStore-4-账单寄送地址.jpg|262]]

4. 搜 Claude，认准开发者是 Anthropic，下载。
5. 设置 → 屏幕使用时间 → 内容与隐私访问限制 → iTunes 与 App Store 购买项目 → App 内购买项目 → 选“**允许**”。

### 3. 买礼品卡充值

1. 手机浏览器搜索 pockyt shop，打开 [shop.pockyt.io](https://shop.pockyt.io)，点左上角“游客”。

![[09附件/订阅claude-pockyt-2-搜索结果.jpg|262]]
![[09附件/订阅claude-pockyt-3-游客.jpg|262]]

2. 登录页“其他登录方式”选支付宝。

![[09附件/微信图片_20261007133655_1_2.jpg|262]]

3. 在支付宝里：“美国”→“App Store & iTunes”→ 输入面额 → 购买。**先买 2 美元**，到账了再买 5 美元，一点点加。显示“缺货”的话，等页面上写的恢复时间再买。

![[09附件/订阅claude-pockyt-6-选择礼品卡.jpg|262]]
![[09附件/订阅claude-pockyt-7-输入面额.jpg|262]]

4. 订单页面复制礼品卡号码 → App Store → 右上角头像 →“兑换代码”→ 填入号码。

![[09附件/订阅claude-兑换-1-礼品卡号码.jpg|262]]
![[09附件/订阅claude-兑换-2-兑换代码.jpg|262]]

5. 余额要比 claude app 里显示的订阅价格多一点。

不要买来路不明的便宜卡，可能是黑卡，兑换后 Apple ID 可能被锁。

### 4. 在 app 内订阅

1. 打开 Claude app，用 Google 账号登录你的 claude 账号。
2. 点升级 → 选方案 → 用 Apple ID 余额付款。
3. 订阅可以在 App Store → 右上角头像 →“订阅”里管理或取消。

提示“购买未完成”的，**不要反复重试**，看文末「购买未完成」。

## 七、订阅之后
---
- 刚开始少用，慢慢增加使用量。
- 一直用同一个节点、同一个住宅 IP。
- 不要在很多设备上登录，没走代理的设备上绝对不要登录。

## 附：购买未完成
---
1. 把报错截图和 App Store 账户设置的截图发给 AI（claude 免费版、ChatGPT 都可以），说明情况，让它帮你检查设置。
2. 还是不行，按 AI 说的，打开苹果自带的“支持”app（Apple Support）联系在线客服。
3. “支持”app 里登录的是 iCloud 主账号（国区），订阅用的是美区账号，所以大概率会转到说英文的海外客服。**继续靠 AI**：客服发一句，复制给 AI；AI 的回答，再复制给客服。记得让 AI 跟客服说清楚，要处理的是 App Store 上的美区账号。
4. 客服让你等 72 小时的话，记下 Case ID，**这 72 小时里什么都别做**：不购买、不换账号、不改付款信息和账单地址。
5. 72 小时后再买。还失败的话，带着 Case ID 再联系客服，同样让 AI 帮你沟通。

## 致谢
---
为了这件事，我翻了很多很多教程，也从各位大佬的分享里学到了很多。可惜我记性不好，很多帮过我的人已经想不起名字了，真的很抱歉。下面是我还记得的几位：

X：水族馆刘老板（@leo_xiaolei）、不惑X nitama.de（@jaylenngx）
BiliBili：bili_33000000033（401651062）、归还你于人海（401864411）

也感谢所有我没能记住名字、但确实帮到我的人。

## 后记
---
谢谢你看到这里。

这篇文章只是一个普通人的经验记录，而不是标准答案。它是我这一次碰巧走通的路，不是一份保证。多看看别人的说法，自己判断。

如果你成功了，我会真心替你高兴。
