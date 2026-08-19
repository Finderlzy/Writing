---
aliases:
  - Stack
  - Queue
  - 栈
  - 队列
  - 容器适配器
  - std::stack
  - std::queue
date: 2026-04-15
---
## [[Container Adaptor|std::stack]]（栈）
[std::stack - cppreference.cn - C++参考手册](https://cppreference.cn/w/cpp/container/stack)

## [[Container Adaptor|std::queue]]（队列）
[std::queue - cppreference.cn - C++参考手册](https://cppreference.cn/w/cpp/container/queue)

## 一个注意事项

假设我要清空队列或者栈，在循环中不能出现下面这样：
```
for(int i=0; i<oneStack.size(); i++)
{
    oneStack.pop();
}
```
因为每次弹出元素，==栈的大小都会实时调整==。队列同理。