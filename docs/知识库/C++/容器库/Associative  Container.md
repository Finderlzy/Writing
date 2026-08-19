---
aliases:
  - 关联容器
  - map
  - set
  - std::map
  - std::set
  - multimap
date: 2026-04-15
---
## [[Associative  Container|std::map]]
[std::map - cppreference.cn - C++参考手册](https://cppreference.cn/w/cpp/container/map)

map里的每个元素是一个 [[pair]]，就像快递包裹：
```
pair{
    first = "收件人地址"  (key)
    second = "包裹内容"   (value)
}
```


在使用方括号操作时，如果方括号里面的key不存在，则直接新建一个key，**value为0**.

### map的[[Iterator|迭代器]]

```
map<string, int> myMap = {{“test”， 666}};
map<string, int>::iterator iter = myMap.begin();

此时iter指向pair，而pair像是一个结构体：
pair{
    first = test;
    second = 666;
}

```

## [[Associative  Container|std::set]]
[std::set - cppreference.cn - C++参考手册](https://cppreference.cn/w/cpp/container/set)

set可以看成value只能是1的map。如果key存在，则value必定为1；kay不存在，则无value。

## [[Associative  Container|multimap]]
[std::multimap - cppreference.cn - C++参考手册](https://cppreference.cn/w/cpp/container/multimap)

不同的键可以为相同的值