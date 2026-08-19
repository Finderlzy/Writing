---
aliases:
  - 流
  - stream
  - Ostringstream
  - ostringstream
  - Istringstream
  - istringstream
  - cout
  - cin
date: 2026-04-08
---
## 概述

stream是C++的一个[[类]]，主要用于数据的输入和输出。

```
#include <iostream>
#include <sstream>

cout  // 是 ostream 类的对象（预定义的全局变量）
cin   // 是 istream 类的对象

ostringstream oss;  // 你创建的 ostream 子类对象
istringstream iss;  // 你创建的 istream 子类对象
```

## ostringstream

用于存放输入的所有数据

```
#include <sstream>
using namespace std;

ostringstream oss;    // 创建一个空盒子

oss << "我" << 25 << "岁了";  // 往里面丢各种零件

string result = oss.str();    // 取出拼好的字符串

// result = "我25岁了"
```

先写入[[缓冲区]]，oss再从缓冲区中把数据拿出来

==要想取出oss里面的文本，必须得写“oss.str()”==

## istringstream

用于把接收到的文本分成实际的数据。

从流接受的文本都是string类型的，iss可以把他们自动变为他们应该属于的类型。

```
#include <sstream>
using namespace std;

string data = "张三 25 北京";
istringstream iss(data);   // 把字符串丢进拆解器

string name; int age; string city;
iss >> name >> age >> city;

// name="张三", age=25, city="北京"
```

### iss的读取规则

直接用代码演示了

```
istringstream iss("  100  3.14   hello world  ");
int i; double d; string s1, s2;

iss >> i;      // 跳过前导空格，读"100"，停在下个空格前 → i=100
iss >> d;      // 跳过空格，读"3.14" → d=3.14  
iss >> s1;     // 跳过空格，读"hello" → s1="hello"
iss >> s2;     // 读"world" → s2="world"
```

## cout

## cin
