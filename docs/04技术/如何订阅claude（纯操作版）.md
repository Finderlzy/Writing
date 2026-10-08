---
createdDate: 2026-10-08
updatedDate: 2026-10-08
---
> 写于 2026-10-08
> 这是只有操作步骤的版本。想知道每一步为什么这么做，看完整版：[[04技术/如何订阅claude|如何订阅claude]]

## 前言
---
说实话，我有点犹豫要不要现在发这篇。我的 claude 才订阅了四天。时间太短，我没法保证这套方法长期有效，只能说它目前对我管用。而且为了走到这一步，我前前后后折腾了很久，所以流程会有点繁琐。

这一版只写怎么做，不讲为什么。哪一步想知道原因，或者某个细节失效了想自己调，去完整版里找对应的小节。

文中没写的情况，我不一定可以给出答案，请见谅。

>[!warning] 看之前先确认
>这篇默认你**已经会用代理**：会导入节点、切换节点、打开和关闭代理。还不会的话，先看[[04技术/自建梯子：VPS + 3x-ui + VLESS Reality#六、导入代理软件|自建梯子]]里“导入代理软件”那一节，能正常打开外网之后再回来。

>[!caution] 免责声明
>- 本文只是记录个人的操作经历，仅供学习和技术交流，不构成任何建议。
>- 请遵守你所在地区的法律法规，自行判断相关操作是否合规，并自行承担由此产生的风险和后果。
>- 不要将文中的任何方法用于违法违规的用途。
>- 文中的购买链接都是我的推广链接，通过它们购买我会拿到一点返佣，介意的话直接搜商家名字就行。除此之外我和这些商家没有其他关系，它们的稳定性、安全性和合规性，我无法保证。

先叠个甲：如果照着做还是被封号了，请不要骂我，麻烦去骂 a/，谢谢🌹

## 开始之前
---
**流程：** 准备住宅 IP → 配置代理软件 → 防泄漏 → 改时区 → 注册 Gmail → 注册 claude 并先用几天 → 注册美区 Apple ID → 买礼品卡充值 → 在 app 里订阅。

**每一步都做完再做下一步，全程开着住宅节点。**

## 一、准备住宅 IP
---
三选一，选好后只看对应的那一条，做完跳到「确认出口 IP」。

| 方案 | 折腾程度 | 适合谁 |
| --- | --- | --- |
| 一：自建节点 + 套住宅 IP | 高 | 喜欢折腾 |
| 二：住宅 IP 服务器 + 自建节点 | 中 | 愿意自建，不想配链式代理 |
| 三：直接买住宅节点 | 低 | 不想碰服务器 |

**买之前**：先找商家要 IP，用 [ipinfo.io](https://ipinfo.io/what-is-my-ip) 和 [scamalytics.com](https://scamalytics.com/) 测一下，类型要是“住宅/ISP”，风险分数要低。不要用 ping0.cc 测。

**不要用机场节点。**

### 方案一：自建节点 + 套住宅 IP

1. 按 [[04技术/自建梯子：VPS + 3x-ui + VLESS Reality|自建梯子]] 搭好自己的节点。
2. 在 [proxy.qsu.hk](https://proxy.qsu.hk/) 买住宅代理（不是主站 qsu.hk，主站卖的是方案二的服务器），记下协议、IP、端口、账号密码。
3. 按 [[04技术/给 VPS 节点套上住宅 IP|给 VPS 节点套上住宅 IP]] 操作：
   1. 3x-ui → Xray 设置 → 新增出站，填住宅 IP 的信息，标签填 `residential`。
   2. 新增路由规则，出站标签选 `residential`，domain 填：

```
geosite:anthropic
domain:ipinfo.io
```

   3. 保存并重启 Xray。

### 方案二：住宅 IP 服务器 + 自建节点

1. 买一台住宅 IP 服务器：[VoyraCloud](https://www.voyracloud.com/?ref_code=HYEWZ46M) 或 [QSU](https://qsu.hk/aff/GAZUQBSL)（这两家的住宅服务器我都没用过）。
2. 按 [[04技术/自建梯子：VPS + 3x-ui + VLESS Reality|自建梯子]] 在上面搭节点。不用再套住宅 IP。

### 方案三：直接买住宅节点

1. 在 ipequal 买套餐，**使用类型选“1 人独享”**。国内能打开的地址：[ipequal](https://www.ipequal.com/?ref=6adabd0307)；开代理才能打开的地址：[ipequal](https://www.equaldcdn.com/?ref=6adabd0307)。（我没用过，是很多人推荐的。建议先买一个月。）
2. 复制订阅链接，**通过剪贴板**导入代理软件。
3. 用 claude 时选中这个住宅节点。

已经有别的节点、想只让 claude 走住宅节点的，看文末「分流规则」。

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

## 五、注册 Gmail
---
已经有 Gmail 的跳过。美区 Apple ID 现在不能用 QQ 邮箱注册，必须用 Gmail。

1. 手机配好代理，和电脑一样走住宅节点。
2. 下载 Gmail：
   - iOS：App Store 搜 Gmail。
   - 安卓：先下载 Google Play，再从里面下载 Gmail。Google Play 只从手机自带的应用商店或其他可信来源下载。
3. 打开 Gmail →“设置电子邮件”→“Google”→“创建账号”，跟着提示做。手机号可以用 +86。

**可选**：打开 policies.google.com/terms，看“国家/地区版本”。如果是中国大陆或香港，在同一页面申请改成住宅 IP 所在地区。审核期间保持住宅 IP 网络。

## 六、注册 claude
---
1. 前面五步都做完、检测都通过，再注册。
2. 用 Google 账号注册。
3. 一个 IP 只注册一个账号。
4. **注册后先正常用几天**，最好用完免费额度、等它弹出升级提示，再订阅。

## 七、订阅（iPhone）
---
安卓用户：我没有验证过的方案。

### 1. 注册美区 Apple ID

已经有美区 Apple ID 的跳过。

1. 电脑浏览器打开 appleid.apple.com →“创建 Apple 账户”。
2. 国家/地区选“**美国**”；姓名可以填拼音；生日要满 18 岁；邮箱用 Gmail；手机号可以用 +86。
3. 完成邮箱和手机验证。
4. 重新登录一次，确认地区是美国。付款方式不用填。

### 2. 在 App Store 登录

1. 打开 **App Store（不是“设置”）** → 右上角头像 → 拉到最底部，退出原账号。
2. 登录美区 Apple ID。要求填账单地址的话，填免税州的地址（比如俄勒冈州），地址要真实存在、格式正确，网上能搜到。
3. 搜 Claude，认准开发者是 Anthropic，下载。
4. 设置 → 屏幕使用时间 → 内容与隐私访问限制 → iTunes 与 App Store 购买项目 → App 内购买项目 → 选“**允许**”。

### 3. 买礼品卡充值

1. 手机浏览器打开 [pockyt shop](https://shop.pockyt.io)，点左上角“游客”。
2. 登录页“其他登录方式”选支付宝，买美区 App Store 礼品卡。**先买 2 美元**，到账了再买 5 美元，一点点加。
3. App Store → 右上角头像 →“兑换充值卡或代码”→ 输入卡密。
4. 余额要比 claude app 里显示的订阅价格多一点。

不要买来路不明的便宜卡，可能是黑卡，兑换后 Apple ID 可能被锁。

### 4. 在 app 内订阅

1. 打开 Claude app，用 Google 账号登录你的 claude 账号。
2. 点升级 → 选方案 → 用 Apple ID 余额付款。
3. 订阅可以在 设置 → 你的名字 →“订阅”里管理或取消。

提示“购买未完成”的，**不要反复重试**，看文末「购买未完成」。

## 八、订阅之后
---
- 刚开始少用，慢慢增加使用量。
- 一直用同一个节点、同一个住宅 IP。
- 不要在很多设备上登录，没走代理的设备上绝对不要登录。

## 附：分流规则
---
只让 claude 走住宅节点、其他网站走原来的节点时用。规则放在最前面，`住宅节点` 换成你的节点或策略组名字。

**Clash Verge**（住宅节点和原来的节点要在同一份配置里）：

```
- DOMAIN-SUFFIX,claude.ai,住宅节点
- DOMAIN-SUFFIX,claude.com,住宅节点
- DOMAIN-SUFFIX,anthropic.com,住宅节点
- DOMAIN-SUFFIX,ipinfo.io,住宅节点
```

**Shadowrocket**：配置 → 规则 → 新增 `DOMAIN-SUFFIX` 规则，域名同上，策略选住宅节点。

**v2rayN**：不方便分流，用 claude 时直接切到住宅节点。

看不懂就不分流，用 claude 时全局走住宅节点。

## 附：购买未完成
---
1. App Store 购买记录里看有没有 claude 的扣款。
2. 联系 Apple Support 在线客服，用英文说：

```
I'm trying to purchase Claude Pro through the App Store, but I'm getting a "Purchase Not Completed" error.
```

   客服让生成 Support PIN 的话，去 account.apple.com 生成。如果 iCloud 和 App Store 登录的不是同一个账号，告诉客服：

```
I use a different Apple Account for iCloud and for the App Store.
```

3. 按客服说的做。我遇到时，客服先让我确认“App 内购买项目”是“允许”，然后让我**等 72 小时再买，期间不要尝试购买**。记下 Case ID。
4. 等待期间不换账号，不改付款信息。
5. 72 小时后再买。还失败的话，带着 Case ID 再联系客服：

```
My purchase is still not going through after waiting 72 hours. My case ID is xxxxxxxxx.
```

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
