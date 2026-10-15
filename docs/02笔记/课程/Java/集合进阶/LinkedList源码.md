---
createdDate: 2026-09-22
---
> 写于 2026-09-22

## 基本
---
LinkedList在底层是通过[[双向链表]]实现的。

LinkedList自己会维护三个成员变量：`int size`、`Node<E> first`、`Node<E> last`


## 新增结点（源码）
---
```java
void linkLast(E e) {
	// 使用一个结点 l 记录LinkedList维护的尾结点    
    final Node<E> l = last;               ↓
    // 使用全参构造创建一个新的结点，参数（前一个结点——l， 要添加的对象——e， 下一个结点——null）  
    final Node<E> newNode = new Node<>(l, e, null);  
    // LinkedList维护的尾结点变为这个新创建的结点
    last = newNode;
  
    if (l == null)  // 如果新增的时候没有尾结点，也就是现在这个New的是第一个结点
        first = newNode; // LinkedList维护的首结点就是当前New的结点  
    else  
        l.next = newNode; // 原先维护的尾结点指向现在New的结点
    size++; // LinkedList长度加一   
    modCount++;  
}
```