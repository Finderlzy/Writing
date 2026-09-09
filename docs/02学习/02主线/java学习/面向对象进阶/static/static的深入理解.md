---
createdDate: 2026-09-09
---
> 写于 2026-09-09
> 是[[02学习/02主线/java学习/面向对象进阶/static/static|static]]的一个补充

这是一段代码
```
class Student {
    static String school = "北京科技大学";
    String name;
}
```

这是这段代码的内存关系
```
Student 类
└── school = "北京科技大学"

        ↓ new

s1 对象
└── name = "张三"

s2 对象
└── name = "李四"
```

`static`会修改成员变量和方法的归属——将其变为**类**的东西。

所以，使用`static`修饰的成员方法可以通过类名直接调用。