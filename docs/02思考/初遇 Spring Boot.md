---
createdDate: 2026-10-29
tags:
  - SpringBoot
  - Java
  - Web服务
  - 学习
description: "记录初次接触 Spring Boot 的体会：它封装了请求回复、业务、数据库和配置，只需给类和方法贴注解、写业务逻辑。并讲解 @RestController、@GetMapping、@RequestParam 的作用，附一个 hello …"
slug: spring-boot-first-look
---
> 写于 2026-10-29

我没有对比过不用 Spring Boot 框架写代码会发生什么，但是我体验下来觉得很方便。所以我猜测，使用 Spring Boot 框架的原因是便利与高效。

Spring Boot 通过把四种功能（请求与回复、实现业务、数据库、配置）封装起来，我们只需要给类贴标签，然后写逻辑代码，不需要去自己写请求与回复代码。

`@RestController`：这个标签贴在**类**上，用来说明这个类是负责接收请求以及回复的，往往会和 `@GetMapping` 或者 `@PostMapping` 一起使用。Rest 是表示，把方法的返回值直接作为请求的回复。

`@XxxxMapping("/path")`：这个标签贴在**方法**上，用来说明，当访问到 /path 这个路径的时候，执行这个方法。

`@RequestParam`：这个标签**放在方法的参数前面**，用来说明，需要去路径的的 ？后面寻找类型为方法参数，并把那个值作为方法的参数。有点绕了，举个例子：
```java
@RestController
public class HelloController {

@GetMapping("/hello")
	public String hello(@RequestParam(defaultValue = "") String name) {
	return name + "你好呀";
	}
}
```

hello 方法里面有一个参数是 name，然后参数的前面贴了 `@RequestParam` 标签 。当一个请求来了，假设是 `http://localhost:8080/hello?name=小明`。由于访问路径是 `/hello` 正好是 `@GetMapping` 监听的路径，于是就会调用 hello 方法。由于有 `@RequestParam` 标签，程序就会在请求路径的 `?` 去找有没有 name 类型的参数，找到了，是“小明”，就把它作为 hello 方法的参数值。最后输出：“小明你好呀”。