Spring 框架的本质：**Dependency Injection Container（依赖注入容器）**。这是一个偏正短语，也就是说，重点是后面的“容器”。简单来讲，就是一个管家。一个框架的提出，必然是为了解决一个问题。Spring 也是如此，它解决的是“依赖地狱”的问题。


## 依赖地狱
---
下面介绍“依赖”地狱这个问题，是怎么来的。

在使用 java 使用数据库的时候，需要先建立连接，这个连接的成本是非常大的，具体多大，我也不知道。反正程序员们为了解决这个问题，就想到了”依赖注入“这个方法。什么是“依赖注入”呢？就是只建立一次连接，然后其他类要使用数据库的时候，就把这个连接类注入进去。这个连接就是“依赖”。

这是不使用“依赖注入”方法的时候要写的类：
```java
import com.mysql.cj.jdbc.MysqlDataSource;

public class UserDao {

    public User findById(Integer id) {
	    // 这里就是建立连接
        MysqlDataSource dataSource = new MysqlDataSource(); // (1)
        dataSource.setURL("jdbc:mysql://localhost:3306/myDatabase");
        dataSource.setUser("root");
        dataSource.setPassword("s3cr3t");

        try (Connection connection = dataSource.getConnection()) { // (2)
             PreparedStatement selectStatement = connection.prepareStatement("select * from users where id =  ?");
             // execute the statement..convert the raw jdbc resultset to a user
             return user;
        }
    }
}
```

这是使用“依赖注入”方法要写的类：
```java
import com.mysql.cj.jdbc.MysqlDataSource;

public class UserDao {

	// 这里是把建立连接的过程封装为一个方法
    public DataSource newDataSource() {
        MysqlDataSource dataSource = new MysqlDataSource(); // (3)
        dataSource.setUser("root");
        dataSource.setPassword("s3cr3t");
        dataSource.setURL("jdbc:mysql://localhost:3306/myDatabase");
        return dataSource;
    }

    public User findById(Integer id) {
        try (Connection connection = newDataSource().getConnection()) { // (1)
               PreparedStatement selectStatement = connection.prepareStatement("select * from users where id =  ?");
               // TODO execute the select , handle exceptions, return the user
        }
    }

    public User findByFirstName(String firstName) {
        try (Connection connection = newDataSource().getConnection()) { // (2)
               PreparedStatement selectStatement = connection.prepareStatement("select * from users where first_name =  ?");
               // TODO execute the select ,  handle exceptions, return the user
        }
    }
}
```

由此可见，在并行使用依赖的情况下，“依赖注入”很好地解决了多次建立连接成本高这个问题。但是，当依赖是串行的时候，就会出现“依赖地狱”这个问题。

一个串行的依赖关系图：
```txt
UserService
    |
    v
UserRepository
    |
    v
DataSource
    |
    v
AppConfig
```

这是“依赖地狱”的依赖关系图：
```text
                         UserService
                        /           \
                       v             v
          UserRepository           AuditService
                |                     /     \
                |                    /       \
                v                   v         v
             DataSource <-----+-----+      UserRepository
                |                         /
                v                        /
             AppConfig <----------------+
```
`UserService` 依赖 `UserRepository` 和 `AuditService` 。`UserRepository` 依赖 `DataSource`，`DataSource` 依赖 `AppConfig` 。`AuditService` 依赖 `DataSource` 和 `UserRepository` 。

程序员需要不断地 `new` 依赖，然后注入。非常地麻烦。Spring 框架就是来解决这个问题的。仔细想一想，程序员要做的那些操作都是十分机械的操作，而这些操作正是程序最擅长处理的部分。


## Spring 是如何解决这个问题的？
---
Spring 框架的核心是：**Inversion of Control（控制权反转）**。以前，创建一个实例的控制权是在开发者手里，Spring 框架则是把这个控制权交给了程序，也就是最开头提到的“管家”，专业一点的名字叫做：**ApplicationContext** 。**使用 Spring 框架，我们只需要告诉管家，哪些类是管家负责管理的**。管家就会把该准备的依赖准备好，我们要用的时候，就可以直接使用了，不需要再关注依赖问题。


## 如何告诉管家这个类归它管理？
---
那么问题来了：我们要怎么告诉管家，这个类归它管呢？

Spring 框架借助 java 的“Annotation“来实现，也就是打标签。最简单的标签是 `@Component`，作用就是告诉管家，这个类归你管了。当管家看见归他管的类中，需要注入其他的依赖，它就会去把那个依赖准备好，然后注入进来，得到一个实例。
> 由管家 `new` 出来的实例叫做”Bean“，我们自己 `new` 出来的实例叫做”Object“。

比如说这个类，先把连接建立好：
```java
@Configuration // 告诉管家：这是一个图纸类
public class DatabaseConfig {

    @Bean // 贴在方法上，告诉管家：把下面 new 出来的东西收进仓库
    public DataSource dataSource() {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl("jdbc:mysql://localhost:3306/mydb"); // 填具体内容
        ds.setUsername("root");
        ds.setPassword("123456");
        return ds; // 管家会接收这个返回值，并把它变成一个 Bean ,放在仓库里
    }
}
```

这个类就可以通过依赖注入，直接使用了：
```java
@Repository
public class UserDao {

    private final DataSource dataSource;
    
    // 推荐方式：构造器注入
    // 管家看到你要 DataSource，就会把上面存进仓库的那个塞进来
    public UserDao(DataSource dataSource) {
        this.dataSource = dataSource;
    }
    
    // ... 后续使用
}
```


## 一个疑问
---
然后我学到这里的时候，想到了一个问题：**管家是怎么知道依赖的具体内容是多少？比如说，DataSource，管家new出来了一个实例，但是里面总得填充东西吧？它怎么知道里面填的是什么？“

Spring 框架提供了两种方法，一个是像上面的 `DatabaseConfig` 类一样，把具体内容填好，管家直接创建就好了。另一种是写配置文件配置 最现代、最常用）在项目里，创建一个叫 `application.properties`(或 `application.yml`)的文件。你在里面写上：
```properties
spring.datasource.url=jdbc:mysql://localhost:3306/mydb
spring.datasource.username=root
spring.datasource.password=123456
```
管家启动的时候，会**优先读取**这个文件。它发现你要造 `DataSource`，就会去文件里找对应的 key，把值拿出来，通过反射塞进你 `new` 出来的实例里。


## 小结
---
Spring 框架是用来解决依赖的问题，通过贴标签让管家管理错综复杂的依赖，我们就可以把重心放在业务逻辑上。


## claude 认为需要修正的地方
---
**① 第二段代码其实还不是「依赖注入」**

文章里那一步只是把创建 DataSource 的代码**抽成了一个方法**，作用是消除重复代码。它有两个问题：

- `newDataSource()` 每调用一次，就会 `new` 一个新的 DataSource。所以并没有做到「只建立一次」，`findById` 和 `findByFirstName` 各建了一个。
- 依赖还是 UserDao **自己去造的**。

**依赖注入的标志是：依赖从外面递进来，类自己不造。** 你后面写的 `public UserDao(DataSource dataSource)` 才是依赖注入。所以那两处注释「这里就是依赖注入」要改成「这里是调用抽出来的方法」。

还有一处顺带要改：DI 要解决的核心问题不是「连接成本高」。连接贵这个问题，是靠**连接池**（就是你后面写的 HikariDataSource）来解决的。DI 要解决的是：**谁来创建依赖，以及怎么让大家共用同一个**。

**② 「串行 / 并行」的说法不太准**

就算只有一条直线的依赖链，也已经很麻烦了：你必须按 AppConfig → DataSource → UserRepository → UserService 的顺序，一个个手动 `new`，再一个个传进去。你画的那张网状图，难点则在于**共享**：UserRepository 和 AuditService 必须拿到**同一个** DataSource。如果各 new 一个，就又回到了第 1 个问题。

所以可以改成这样的表述：依赖一多，**创建顺序**和**共享同一个实例**这两件事，手动管理起来就会非常痛苦。

**③ Bean 也是 Object**

Bean 和 Object 不是两种东西。Bean 只是「**由容器创建和管理的 Object**」，它本质上还是一个普通的 Java 对象。

**④ 你的「疑问」，答案其实是 Spring Boot，不是 Spring**

光写 `spring.datasource.url` 就能自动得到一个 DataSource，这是 **Spring Boot 的自动配置**在起作用，纯 Spring 不会这么做。这一点正好就是 Marco Behler 第二篇文章《How Spring Boot’s Autoconfigurations Work》要讲的内容。另外「优先读取」这几个字可以删掉，读配置只是启动过程中的一个步骤而已。