---
createdDate: 2026-09-08
---
> 写于 2026-09-08

## 三句话
---
### ==static修饰的成员方法没有[[02学习/⭐主线/Java/day02/this关键字|this关键字]]==

一般的成员方法，也就是非静态成员方法，在调用的时候，**虚拟机会自动传入一个参数**，这个参数是调用者的地址值。
```java
public class Student {  
    private String name;  

	public void show(){
		ystem.out.println(name);
	}
```

也就是这个样子：
```java
public class Student {  
    private String name;  

	public void show(Student this){    // <———— 虚拟机传入的变量
		ystem.out.println(this.name);
	}
```

而静态的成员方法是没有这个this关键字的。

==static修饰的成员方法不能访问非静态变量，也就是**实例变量**==

==非静态的成员方法可以访问所有==