---
createdDate: 2026-08-26
---

> 写于 2026-08-26

## Chrome 扩展 Day 2：让“自定义指令 + 用户问题”一起发送
---
这个扩展的 v1 已经实现。

它做的事情很简单：
```text
用户在 popup 中填写自定义指令
        ↓
保存到 chrome.storage.local
        ↓
content.js 读取指令
        ↓
用户在 DeepSeek 输入问题并发送
        ↓
把“自定义指令 + 用户问题”拼接起来
        ↓
写回 DeepSeek 输入框
        ↓
正常发送
```

所以这一版实际上要解决三个问题：
1. 怎么保存用户设置的指令？
2. content.js 怎么拿到这个指令？
3. 怎么把“指令 + 问题”真正写进 DeepSeek 的输入框？

## 1. 保存用户的自定义指令
---
用户在插件 popup 中输入指令，因此 popup.js 负责把它保存起来。

这里使用 [[../01概念/chrome.storage|chrome.storage]]。它是 Chrome Extension 提供的存储 API，可以让扩展保存自己的数据。
```js
/** scripts/popup.js */

const input = document.querySelector('#instruction');
const saveButton = document.querySelector('#save');

// 打开 popup 时，读取之前保存的指令
chrome.storage.local.get('instruction', function (result) {
    input.value = result.instruction || '';
});

// 点击保存按钮后，把当前输入保存下来
saveButton.addEventListener('click', function () {
    chrome.storage.local.set({
        instruction: input.value
    });
});
```

这一部分的数据流是：
```text
popup 输入框
    ↓
点击保存
    ↓
chrome.storage.local
```


## 2. content.js 获取用户指令
---
真正修改 DeepSeek 网页的是 `content.js`，所以它还需要读取 popup 保存的数据。
```js
/** scripts/content.js */

let instruction = '';

// 页面打开时读取一次
chrome.storage.local.get('instruction', function (result) {
    instruction = result.instruction || '';
});

// 如果用户之后修改了指令，就同步更新
chrome.storage.onChanged.addListener(function (changes, areaName) {
    if (areaName === 'local' && changes.instruction) {
        instruction = changes.instruction.newValue || '';
    }
});
```

这里的 `instruction` 可以理解成 content.js 当前持有的“用户指令”。数据流：
```text
chrome.storage.local
        ↓
content.js 中的 instruction
```

页面打开时先读取一次；之后再监听 storage 的变化，这样用户修改指令后，不需要重新打开 DeepSeek 页面。

## 3. 用户发送时，拼接“指令 + 问题”
---
当用户发送问题时，先把当前问题和 `instruction` 拼起来：
```js
function handleSend(text) {
    const input = document.querySelector('textarea');

    const newText = instruction
        ? instruction + '\n\n' + text
        : text;

    setInputValue(input, newText);
}
```

这里真正完成的是：
```text
instruction + 用户输入 text
            ↓
          newText
```

如果没有设置 instruction，就直接使用原来的 `text`。`handleSend()` 本身不是一个通用知识点，它只是这个项目里负责组织发送流程的函数。

## 4. 把 newText 写回 DeepSeek 输入框
---
普通网页上通常可以直接：
```js
input.value = newText;
```

但 DeepSeek 使用前端框架管理输入框。只修改 DOM 上的 `value`，可能不会让框架意识到输入内容发生了变化。所以这里使用：
```js
function setInputValue(input, text) {
    const setter = Object.getOwnPropertyDescriptor(
        HTMLTextAreaElement.prototype,
        'value'
    ).set;

    setter.call(input, text);

    input.dispatchEvent(
        new Event('input', { bubbles: true })
    );
}
```

它实际上做了两件事：
```text
newText
   ↓
调用 textarea.value 的原生 setter
   ↓
textarea 的内容发生变化
   ↓
主动触发 input 事件
   ↓
DeepSeek 的前端框架知道“输入变了”
```

这里的重点不是记住整个函数，而是知道：

> 对一些由前端框架控制的输入框，只修改 DOM 的 `value` 可能不够，还需要让网页自己的状态系统感知到变化。

## 整个 v1 的数据流
---
```text
                    popup.js
                       │
                用户填写自定义指令
                       │
                       ▼
             chrome.storage.local
                       │
                       ▼
                  content.js
                       │
               instruction 变量
                       │
                       │
用户在 DeepSeek 输入问题 ──────┐
                       │       │
                       ▼       │
                  handleSend()
                       │
                       ▼
              instruction + text
                       │
                       ▼
                   newText
                       │
                       ▼
                setInputValue()
                       │
                       ▼
               DeepSeek textarea
                       │
                       ▼
                 触发 input 事件
                       │
                       ▼
               DeepSeek 正常发送
```

## 这一阶段真正学到的东西
---
这一版项目并不是“学了几个函数”，而是第一次把几个不同部分串成了一条完整的数据流：

```text
popup
→ storage
→ content script
→ 网页 DOM
→ 网页自己的前端状态
```

具体的函数只是实现这条链路所使用的工具。
