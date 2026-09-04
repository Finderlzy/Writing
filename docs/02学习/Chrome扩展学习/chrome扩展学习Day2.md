---
createdDate: 2026-08-26
---

> 写于 2026-08-26
> gpt优化版：[[chrome扩展学习Day2_优化版]]

这个扩展的v1版本已经实现了，基本功能：用户输入自定义指令，然后就正常发送问题。最终会输出指令+问题。

接下来梳理一下学习开发过程
## 找到输入框

因为这个扩展的功能会修改发送的信息，因此需要找到输入框。似乎这种页面的输入框都是`<textarea></textarea>`标签。
## 修改发送的信息

由于deepseek官网使用了一些前端框架，所以无法简单地修改，于是需要下面这个函数：
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
先拿到**真正保存输入信息的地方**，把它放入setter。然后使用call把`text`放入`input`里面。 ^57ac7b
## 保存用户指令

这里要用到chrome.storage这个功能，简单来说就是chrome为插件提供的一个存储空间。
```js
/**   scripts/popup.js
**/

const input = document.querySelector('#instruction');
const saveButton = document.querySelector('#save');

chrome.storage.local.get('instruction', function (result) {
    input.value = result.instruction || '';
});

saveButton.addEventListener('click', function () {
    chrome.storage.local.set({
        instruction: input.value // 直接在chrome.storage里面创建一个instruction对象
    });
});
```
第二个函数就是在用户输入自定义指令之后，保存到local
## 把指令加入输入框

只需要把之前的[[#^57ac7b|text]]换为用户的指令即可，使用下面这个函数：
```js
/**   scripts/content.js
**/

let instruction = ''; // 在这个js环境里创建一个instruction变量

// 读取本地保存的instruction数据
// 页面刚打开时读取一次
chrome.storage.local.get('instruction', function (result) {
    instruction = result.instruction || '';
});

// 页面打开后，继续监听后续修改
chrome.storage.onChanged.addListener(function (changes, areaName) {
    if (areaName === 'local' && changes.instruction) {
        instruction = changes.instruction.newValue || '';
    }
});

function handleSend(text) {
    const input = document.querySelector('textarea');
    const newText = instruction
        ? instruction + '\n\n' + text
        : text;
    setInputValue(input, newText);
}
```
