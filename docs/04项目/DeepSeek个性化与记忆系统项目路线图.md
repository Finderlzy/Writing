---
createdDate: 2026-08-24
---
# DeepSeek 个性化与记忆系统项目路线图

## 1. 项目最终想解决什么

DeepSeek 网页端没有类似 ChatGPT 的“个性化指令”和“记忆”功能。

这个项目的目标，不是重新做一个聊天网站，也不是绕过官方 API，而是在用户正常使用 DeepSeek 网页版的前提下，增加一层属于用户自己的个性化系统。

长期来看，这一层甚至不应该只服务 DeepSeek，而是可以逐渐变成一个独立于具体模型的 Personalization Layer：

```text
                 用户自己的个性化层
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
    DeepSeek         ChatGPT          Claude
```

用户的偏好、人格设置和长期记忆属于用户自己，而不是绑定在某一家 AI 平台里。

不过，这只是长期方向。当前阶段不做这么大。

---

## 2. 当前阶段：只做个性化指令

现在先解决最核心、也最容易验证的一件事：

> 用户在 DeepSeek 输入消息时，插件自动把用户设置好的个性化指令加入 Prompt，再交给 DeepSeek。

基本链路：

```text
用户在 DeepSeek 输入消息
        ↓
插件读取本地保存的个性化指令
        ↓
组合：
个性化指令 + 用户原始输入
        ↓
发送给 DeepSeek
```

例如用户输入：

```text
为什么 Spring 要设计 IoC？
```

插件内部实际送给 DeepSeek 的内容可能变成：

```text
请遵守以下回答偏好：

- 直接回答，不要复述问题
- 少用模板式分点
- 解释技术问题时，优先讲“为什么会出现这个问题”
- 可以直接指出我的理解哪里不对

用户问题：

为什么 Spring 要设计 IoC？
```

这里的重点不是“做一个复杂 Prompt 系统”，而是先把“自动注入”这件事真正跑通。

---

## 3. V0：固定指令注入

第一版不要做 UI，不要做账号，也不要做 Memory。

目标只有一个：

> 在 DeepSeek 点击发送或按下发送快捷键时，自动在用户输入前加入一段固定指令。

这一阶段需要理解：

```text
manifest.json
        ↓
content script
        ↓
进入 DeepSeek 页面
        ↓
找到输入框和发送行为
        ↓
监听事件
        ↓
修改即将发送的内容
```

需要学习的核心知识：

- JavaScript 基础
- DOM
- `document.querySelector()`
- `addEventListener()`
- `click`
- `keydown`
- Chrome Extension Manifest V3
- Content Script

这个版本只要能稳定实现：

```text
原始输入
+
固定 Prompt
+
正常发送
```

就算完成。

---

## 4. V1：可编辑的个性化指令

V0 跑通以后，再加入设置能力。

用户可以通过插件 Popup 或设置页面编辑自己的指令：

```text
个性化指令

┌─────────────────────────┐
│ 直接回答，不要复述问题   │
│ 少分点                   │
│ 可以反驳我               │
│ ……                       │
└─────────────────────────┘

[保存]
```

插件使用 `chrome.storage` 将这些设置保存在本地。

基本结构：

```text
Popup / Settings
        ↓
chrome.storage
        ↓
Content Script
        ↓
读取指令
        ↓
注入 DeepSeek
```

这一阶段主要增加：

- Popup
- HTML / CSS
- `chrome.storage.local`
- 插件不同页面之间的数据读取

做到这里，这个插件已经真正具有日常使用价值。

---

## 5. V2：多套个性化配置

下一步可以让用户建立不同模式。

例如：

```text
日常模式

学习模式

编程模式

写作模式
```

每种模式拥有自己的 Prompt。

例如“学习模式”：

```text
解释知识时从问题产生的原因讲起。
不要只给定义。
尽量让我理解概念之间的因果关系。
```

“编程模式”：

```text
不要一上来给完整代码。
优先解释代码为什么这样写。
说明重要参数改变后的效果。
```

用户可以手动切换当前模式。

这一阶段仍然不需要 AI。

本质只是：

```text
多份 Prompt
+
当前选中的 Prompt
+
自动注入
```

---

## 6. 这一阶段暂时不要做的东西

当前项目最容易出现的问题，不是技术做不出来，而是不断往里面增加设想，最后同时面对太多陌生知识。

所以在个性化指令功能稳定之前，先明确不做：

- 用户注册
- 云同步
- 自己的网站
- 后端服务器
- 数据库服务器
- 多设备同步
- 自动判断当前是什么场景
- AI 自动选择 Prompt
- Memory
- 本地大模型
- Embedding
- 向量数据库

这些不是不要，而是暂时不进入主线。

当前主线只有：

```text
DeepSeek
↓
Chrome Extension
↓
个性化指令
```

---

# 第二阶段：Memory

个性化指令稳定以后，再开始研究记忆系统。

Memory 的核心不是：

> 把所有聊天记录保存下来。

而是：

> 从聊天里提取值得长期保留的信息，并在未来需要的时候重新取出来。

完整结构大概是：

```text
用户与 AI 对话
        ↓
Memory Extractor
        ↓
判断有没有值得保存的信息
        ↓
Memory Manager
        ↓
本地数据库
        ↓
未来用户再次提问
        ↓
Memory Retrieval
        ↓
找出相关记忆
        ↓
与 Prompt 一起发送
```

---

## 7. Memory V0：手动记忆

最早的 Memory 不需要任何 AI。

用户可以手动：

```text
添加记忆
编辑记忆
删除记忆
```

例如：

```text
用户正在学习 Java

用户希望技术解释从原理出发

用户目前正在开发 DeepSeek 个性化插件
```

发送消息时，可以先简单把 Memory 一起放进 Prompt。

这一阶段真正学习的是：

> Memory 本身是一个数据管理系统，而不是某个神奇的“大模型功能”。

---

## 8. Memory V1：分类与检索

当记忆越来越多以后，就不能全部加入 Prompt。

所以 Memory 需要结构。

例如：

```json
{
  "content": "用户正在学习 Java",
  "category": "learning",
  "tags": ["Java", "编程"],
  "importance": 8
}
```

然后根据当前问题选择相关 Memory。

最早可以只做：

```text
关键词
+
标签
+
重要度
```

不需要 Embedding。

例如用户问：

```text
ArrayList 为什么不能使用 []？
```

系统发现其中包含 Java / 编程相关内容，于是检索：

```text
用户正在学习 Java
用户希望理解原理而不是只拿答案
```

再把这些 Memory 加入 Prompt。

---

## 9. Memory V2：本地小模型自动提取记忆

这是目前设想中比较重要的一步。

当用户开启高级 Memory 后，在本地运行一个小型语言模型。

它不负责聊天，也不负责整个 Memory 系统，只负责语义理解：

```text
一段新对话
        ↓
本地小模型
        ↓
判断：
有没有值得记住的信息？
        ↓
生成结构化 Memory 操作
```

例如：

```text
我已经不学 C++ 了，现在主要学习 Java。
```

模型可以输出：

```json
{
  "operations": [
    {
      "type": "update",
      "content": "用户当前主要学习 Java"
    },
    {
      "type": "invalidate",
      "content": "用户当前主要学习 C++"
    }
  ]
}
```

真正修改数据库的仍然是 Memory Manager。

也就是：

```text
LLM
负责理解

程序
负责执行
```

不要让大模型直接控制数据库。

---

## 10. 为什么考虑本地模型

Memory 非常适合本地模型。

因为它处理的往往是：

- 用户长期偏好
- 学习状态
- 项目状态
- 个人习惯
- 对话历史

这些数据本身就比较私人。

本地模型的优势是：

```text
聊天数据不需要上传第三方服务器
↓
隐私更好

用户越多
↓
开发者不需要承担 API 推理费用

每个人
↓
拥有自己独立的 Memory
```

而且记忆提取不需要非常大的模型。

它主要完成：

```text
分类
抽取
判断
结构化输出
```

因此未来可以研究 1B～3B 左右的小型量化模型，而不是直接部署大型聊天模型。

---

## 11. 本地 Memory Engine 的可能架构

长期可以形成：

```text
Chrome Extension
        ↓
Local Memory Service
        ↓
┌────────────────────────┐
│ Memory Extractor       │
│ 小型本地 LLM            │
├────────────────────────┤
│ Memory Retrieval       │
│ Embedding Model        │
├────────────────────────┤
│ Memory Manager         │
├────────────────────────┤
│ Local Database         │
└────────────────────────┘
```

插件只负责与网页交互。

真正的 Memory 系统运行在本地。

这样以后即使增加其他 AI 网站：

```text
DeepSeek
ChatGPT
Claude
Gemini
```

它们都可以连接同一个：

```text
Local Memory Engine
```

---

## 12. 最终可能形成的产品

这个项目最开始解决的是：

> DeepSeek 没有个性化指令。

但如果一直往后发展，真正的产品可能变成：

> 一个属于用户自己的 AI Personalization Layer。

结构是：

```text
                  Personalization Layer

        个性化指令
             +
          Persona
             +
           Memory
             +
           Skills

                │
                ↓

       Local Memory Engine

                │
     ┌──────────┼──────────┐
     ↓          ↓          ↓
 DeepSeek    ChatGPT     Claude
```

AI 平台可以换。

模型可以换。

但是：

```text
“AI 对我的了解”
```

保存在用户自己这里。

这才是这个项目长期最值得探索的地方。

---

# 当前真正要做的事情

现在不要从最终架构开始开发。

当前路线保持：

```text
学习 DOM
↓
理解 Content Script
↓
在 DeepSeek 页面运行自己的 JS
↓
找到输入框
↓
监听发送事件
↓
注入固定 Prompt
↓
V0 完成
↓
学习 chrome.storage
↓
做可编辑的个性化设置
↓
V1 完成
↓
再考虑多模式
```

到这里以后，再重新讨论 Memory。

当前项目的原则可以压缩成一句话：

> **先让一个最小版本真正工作，再让系统一层一层长出来。**
