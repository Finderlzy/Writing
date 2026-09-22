---
createdDate: 2026-09-21
---
> 写于 2026-09-21

## 地位
---
所有单列集合的祖宗

## 基本方法
---
### .add(E e)——添加

这个函数的返回值类型是boolean，分成下面的情况：
1. 如果是往List系列中添加，始终返回true
2. 如果是往Set系列中添加，若添加的元素不存在，则返回true；若添加的元素已经存在，则放回false。（因为Set系列中的元素不可以重复）

### .clear()——清空

### .remove(E e)——删除

### .contains(E d)——是否包含

这个方法底层是依赖与`equals()`方法，而如果集合添加的是自定义对象，则需要重写`equals()`方法，不然调用的是`Object`的`equals()`，是根据地址值来判断是否包含的。

### .isEmpty()——判断是否为空

### .size()——获取集合长度


## 遍历方式
---
### 迭代器
^3825be
三个方法：
1.  collection.iterator()，获取迭代器对象
2.  it.hasNext()，判断当前位置是否有元素
3.  it.next()，获取当前元素，并将指针往后移动一位。如果当前位置没有元素，则会报错：`NoSuchElementException`。

```java
package com.itheima.mycollection;  
  
import java.util.ArrayList;  
import java.util.Iterator;  
  
public class demo3 {  
    static void main(String[] args) {  
        // 创建一个集合对象  
        ArrayList<String> arrayList = new ArrayList<>();  
  
        // 往集合中添加元素  
        arrayList.add("aaa");  
        arrayList.add("bbb");  
        arrayList.add("ccc");  
        arrayList.add("ddd");  
  
        // 获取迭代器对象  
        // 默认指向0索引元素  
        Iterator<String> it = arrayList.iterator();  
        // .hasNext方法会判断当前指向有没有元素  
        while (it.hasNext()) {  
            // .next方法会获取当前元素并把指针往后移动一位  
            String s = it.next();  
            System.out.println(s);  
        }  
    }  
}
```

### 增强for
^4a1b9d

```java
for(String s : arrayList){
	System.out.println(s);
}
```

其中的第三方变量s会是**集合中的每一个元素**。

### lambda表达式

会调用里面的一个方法`foreach()`。

感觉太麻烦了，而且增强for够用了，先不学这个。

> [!note] 什么时候用[[02学习/⭐主线/Java/集合进阶/Collection接口#^3825be|迭代器]]什么时候用[[02学习/⭐主线/Java/集合进阶/Collection接口#^4a1b9d|增强for]]循环？
> 如果想在遍历的过程中**删除**某些元素 ——> 迭代器
> 只是想遍历 ——> 增强for和lambda

