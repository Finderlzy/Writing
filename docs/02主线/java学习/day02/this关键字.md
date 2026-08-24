## 解决的问题

目前定义的类有一个问题，就是方法接收的参数的变量名没有见名知意。
```java
public class GirlFriend {  
    private String name;  
  
    public void setName(String n){
	    name = n; // 这个n很别扭
    }
}
```

## `this`的作用

可以用`this`来表示”这是成员变量的`name`“：

```java
public class GirlFriend {  
    private String name;  
  
    public void setName(String name){
	    this.name = name; 
    }
}
```
