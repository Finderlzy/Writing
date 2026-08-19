---
aliases:
  - getline
  - getline()
date: 2026-04-08
---
## 功能

读取一整行，直到遇到换行符或者抵达缓冲区末尾

遇到换行符会消耗

```geiline
string name;

// cin >> name
输入：Zhang San
结果：name = "Zhang"（只读到空格前！）

// getline(cin, name)
输入：Zhang San
结果：name = "Zhang San"（整行都拿走）

```
**注意geiline的参数**