---
slug: residential-ip-test
createdDate: 2026-10-13
---
> 写于 2026-10-13
> 相关文章：[[04技术/如何订阅claude|如何订阅claude]]

## 前言
---
读者 [@xiaobeizz](https://github.com/xiaobeizz) 照着[[04技术/如何订阅claude|如何订阅claude]]，把[[04技术/如何订阅claude#方案一：普通服务器 + 白嫖住宅 IP|方案一]]和[[04技术/如何订阅claude#方案三：直接买住宅节点|方案三]]都搭了一遍，用五个检测网站各测了一次，整理好发给了我。我觉得对正在选方案的人很有参考价值，就整理成这篇文章。

先说他的结论：**这次测下来，方案三的 IP 质量很难说比方案一白嫖的强。**

截图里的具体 IP 已经遮住，换成了“方案一”“方案三”；读者本地的 IP 和浏览器指纹也遮住了。

>[!caution] 先看这里
>- 每个方案只测了一次，只能代表测试那一刻、那一个 IP 的情况，不代表长期表现。
>- 免费住宅 IP 和买来的住宅节点，每个人拿到的 IP 都不一样。别人测出来好，不代表你拿到的也好，反过来也一样。
>- 各检测网站的数据库和评分标准都不同，分数不能跨网站比较。

## 测试对象
---
|          | 方案一：普通服务器 + 白嫖住宅 IP | 方案三：直接买住宅节点 |
| -------- | ------------------ | ----------- |
| ASN      | AS2914，NTT America, Inc. | AS26407，Carolina Digital Phone, Inc. |
| ipinfo 显示的位置 | 美国洛杉矶 | 美国纽约 |
| 分流       | 只有 claude 相关域名和 ipinfo 走住宅 IP | — |

## 结果一览
---
| 检测网站 / 项目 | 方案一 | 方案三 | 对比 |
| --- | --- | --- | --- |
| ip.net.coffee 信任评分 | 100，极度纯净 | 100，极度纯净 | 持平 |
| ip.net.coffee：claude.ai 延迟 | 273 ms | 920 ms | 方案三更慢 |
| ip.net.coffee：anthropic.com 延迟 | 635 ms | 4118 ms | 方案三更慢 |
| IPKK：IP 属性 | 机房 IP（Hosting） | 住宅 IP（Residential） | 方案三更好 |
| IPKK：claude.ai 延迟 | 239 ms | 3682 ms | 方案三更慢 |
| IPKK：anthropic.com 延迟 | 235 ms | 8728 ms | 方案三更慢 |
| IPOK 风险值（越低越好） | 35，安全 | 70，高风险 | 方案三更差 |
| Scamalytics Fraud Score（越低越好） | 100，Very high Risk | 20，Medium Risk | 方案三更好 |

## 我的看法
---
### 延迟：方案三明显更高

ip.net.coffee 和 IPKK 都显示，方案三访问 claude.ai 和 anthropic.com 的延迟更高，有几项到了好几秒。

不过两次测试时，检测网站都显示 claude 服务处于“轻微故障”或 Partially Degraded Service 状态，延迟可能被拉高了。方案三的节点在纽约，离国内更远，本来也会慢一些。如果你用的是方案三，建议换个时间多测几次再下结论。

### 风险评分：各家说法不一样

- **Scamalytics**：方案三是 20 分，方案一是 100 分，方案三明显更好。
- **IPOK**：反过来，方案三是 70 分（高风险），方案一是 35 分。方案三扣分是因为命中了垃圾邮件黑名单（DNSBL），但页面也注明了“低置信，仅 DNSBL 一家给出直接证据”。
- **IPKK**：把方案一认成机房 IP，方案三认成住宅 IP。

所以我在教程里一直说，要用几个网站交叉测，不要只看一家。

### 免费住宅 IP 的质量看运气

方案一用的免费住宅 IP 属于 NTT 的段。ipinfo 把它标成 ISP 类型，但 IPKK 认为它是机房 IP，Scamalytics 也给了 100 分。这位读者拿到的这个 IP，质量只能算一般。

免费 IP 每个人拿到的不一样，我自己拿到的那个检测结果比这个好。所以拿到 IP 之后一定要自己测一遍，不满意可以找商家换。

### 关于 Scamalytics 的 0 分

读者在截图里标注了一处：某个页面上写着“正确配置应显示 Fraud Score: 0”，但实际测出来是 20 分。我的教程里没有这句话，我的看法是：**分数越低越好，不一定要做到 0**。

### 总结

这次对比里，没有哪个方案在所有项目上都更好：

- 方案一（免费住宅 IP）：延迟低，但这个 IP 在部分网站上被认成机房 IP，Scamalytics 风险分很高。
- 方案三（买的住宅节点）：住宅属性识别得更好，Scamalytics 分数低，但延迟高，IPOK 报了黑名单。

不管选哪个方案，搭好之后都先开着代理打开 [ipinfo.io](https://ipinfo.io/what-is-my-ip) 拿到自己的住宅 IP，再把这个 IP 拿到 [scamalytics.com](https://scamalytics.com/) 等几个网站交叉测一下，再决定要不要用。具体怎么看，见下一节。

## 怎么看 IP 质量
---
下面用我自己白嫖到的住宅 IP 举例。开着代理打开 [ipinfo.io](https://ipinfo.io/what-is-my-ip)（记得让 ipinfo 也走住宅 IP），页面最上面显示的就是你的出口 IP，先把它复制下来，后面去别的网站测要用。然后往下拉到 Summary，只看下面几行就够了。

![[09附件/住宅IP实测-ipinfo-作者的白嫖IP.png|600]]

### 逐项看

| 字段 | 我的结果 | 怎么看 |
| --- | --- | --- |
| AS Type | Isp | **最关键的一项。** `isp` 表示运营商的 IP，可以用；`hosting` 表示机房 IP，建议直接换；`business` 是企业网络，介于两者之间。 |
| Privacy | false | 有没有被识别成 VPN、代理、Tor 或中继。`false` 才对，`true` 基本就不能用了。 |
| ASN | AS174，Cogent Communications | 这段 IP 登记在哪个网络名下。看名字能大概知道是家庭宽带运营商，还是骨干网、云服务商。 |
| Company | NetLab | 这段 IP 实际交给谁在用。和 ASN 不一样时，说明运营商把这段地址分给了别的公司。 |
| Hosted domains | 0 | 这段 IP 上挂了多少网站。机房 IP 上常挂着网站，0 比较好。 |
| Anycast | false | 是不是多个节点共用的地址，正常是 `false`。 |

ASN 后面那个 `#6` 是 IPinfo 给这个网络的排名，综合的是它覆盖多少用户、承载多少线路，**和 IP 干不干净没有关系**。上面读者截图里方案三的 `#20,676`，也只说明那个网络规模小，不代表 IP 差。

### 我的这个 IP 怎么样

- AS Type 是 `isp`，Privacy 是 `false`，Hosted domains 是 0，ipinfo 这一关算过了。
- Scamalytics 风险分是 0，是最好的结果。
- 但严格说它不是家庭宽带。Scamalytics 下面的说明里也写了，它不是普通家庭网络（not a standard domestic connection）。Cogent 是美国的骨干网运营商，主要做企业和机房线路，不是 Comcast、AT&T、Spectrum 这类家庭宽带运营商；实际使用者 NetLab 也不是。这种 IP 一般叫“ISP IP”或“静态住宅”，教程里说的“ISP 类型也算这一类”就是指它。
- 目前我用它订阅和使用 claude 都正常，对我来说够用。

Scamalytics 的结果（IP 已遮盖）：

![[09附件/住宅IP实测-scamalytics-作者的白嫖IP.png|600]]

### 判断顺序

1. 开着代理打开 [ipinfo.io](https://ipinfo.io/what-is-my-ip)，复制最上面显示的 IP。AS Type 是 `isp`，Privacy 是 `false`。不满足就别用了，直接换。
2. 把复制的 IP 粘贴到 [scamalytics.com](https://scamalytics.com/) 查风险分，越低越好。我这个是 0 分，但不一定都能做到 0，分数低就可以。
3. 再把这个 IP 拿到一两个网站交叉测（比如上面的 IPKK、IPOK、ip.net.coffee）。各家结论不一致很正常，大部分说是住宅/ISP、风险低就可以。
4. 最后看实际使用：claude 能正常打开，不频繁弹人机验证。

## 截图
---
每个网站上面是方案一，下面是方案三（带读者的标注）。

### ip.net.coffee

方案一：

![[09附件/住宅IP实测-ip.net.coffee-方案一.png|600]]

方案三：

![[09附件/住宅IP实测-ip.net.coffee-方案三.png|600]]

### IPinfo

方案一：

![[09附件/住宅IP实测-ipinfo-方案一.png|600]]

方案三（标注里的“ASN 很差”指排名 `#20,676` 靠后。这个排名只反映网络规模，和 IP 质量无关，见[[#怎么看 IP 质量]]）：

![[09附件/住宅IP实测-ipinfo-方案三.png|600]]

### IPKK

方案一：

![[09附件/住宅IP实测-ipkk-方案一.png|600]]

方案三（标注里的“强于方案一”只指被识别为住宅 IP，延迟其实更高）：

![[09附件/住宅IP实测-ipkk-方案三.png|600]]

### IPOK

方案一：

![[09附件/住宅IP实测-ipok-方案一.png|600]]

方案三：

![[09附件/住宅IP实测-ipok-方案三.png|600]]

### Scamalytics

方案一：

![[09附件/住宅IP实测-scamalytics-方案一.png|600]]

方案三：

![[09附件/住宅IP实测-scamalytics-方案三.png|600]]

## 致谢
---
感谢 [@xiaobeizz](https://github.com/xiaobeizz) 花时间把两个方案都搭了一遍，还整理好对比结果和截图发给我。这样的实测对完善教程帮助很大，也能帮后来的人少走弯路 🌹

如果你也测过其他方案，欢迎分享你的结果。
