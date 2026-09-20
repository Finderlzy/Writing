---
createdDate: 2026-09-18
---
> 写于 2026-09-18

```java
package com.itheima.a01jdk7datedemo;  
  
import java.text.ParseException;  
import java.text.SimpleDateFormat;  
import java.util.Date;  
  
public class SimpleDateFormatDemo1 {  
    static void main() throws ParseException {  
        // 第一个功能：让Date对象按照一定格式来展示时间  
  
        // 空参构造，默认的时间格式  
        SimpleDateFormat sdf1 = new SimpleDateFormat();  
        // 创建一个Date对象  
        Date date1 = new Date(0L);  
        // 将时间对象格式化。这个format()方法返回的是一个字符串，要接收一下  
        String str1 = sdf1.format(date1);  
        System.out.println(str1); // 结果：1970/1/1 08:00（默认格式）  
  

        // 带参构造，参数是想要的时间格式。y表示年，M表示月，d表示日，H表示小时，m表示分钟，s表示秒  
        SimpleDateFormat sdf2 = new SimpleDateFormat("yyyy年MM月dd日 HH:mm:ss");  
        String str2 = sdf2.format(date1);  
        System.out.println(str2); // 结果：1970年01月01日 08:00:00  
  
  
  
  
        // 第二个功能：解析字符串。把表示时间的字符串转化为一个Date对象。使用parse()方法  
        String str3 = "2026/9/18 13:56:00";  
        // 注意：这里必须使用带参构造，并且，带参构造的格式要和字符串的格式一摸一样  
        SimpleDateFormat sdf3 = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");  
        Date date3 = sdf3.parse(str3);  
        System.out.println(date3); // Fri Sep 18 13:56:00 CST 2026  

    }  
}
```

任务1：
```java
package com.itheima.a01jdk7datedemo;  
  
import java.text.ParseException;  
import java.text.SimpleDateFormat;  
import java.util.Date;  
  
public class SimpleDateFormatDemo2 {  
    static void main() throws ParseException {  
        // 创建一个字符串，存入初恋的出生日期  
        String str = "2000-11-11";  
        // 使用带参构造创建一个SimpleDateFormat对象，参数格式和出生日期一样，用来解析出生日期  
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");  
        // 转化为一个Date对象  
        Date date = sdf.parse(str);  
        // 再次新建一个SimpleDateFormat对象，用来格式化日期，参数就是我想要的格式  
        SimpleDateFormat sdf2 = new SimpleDateFormat("yyyy年MM月dd日");  
        // 格式化  
        String format = sdf2.format(date);  
        System.out.println(format); // 2000年11月11日  
    }  
}
```

任务2：
```java
package com.itheima.a01jdk7datedemo;  
  
import java.text.ParseException;  
import java.text.SimpleDateFormat;  
import java.util.Date;  
  
public class SimpleDateFormatDemo3 {  
    static void main() throws ParseException {  
        // 思路：  
        // 1.计算活动的持续时间。  
        // 2.分别计算2人下单时间距离活动开始时间过了多久  
        // 3.只要距离活动开始时间小于活动持续时间即可  
  
        String start = "2023年11月11日 0:0:0";  
        String end = "2023年11月11日 0:10:0";  
  
        SimpleDateFormat sdf1 = new SimpleDateFormat("yyyy年MM月dd日 HH:mm:ss");  
        SimpleDateFormat sdf2 = new SimpleDateFormat("yyyy年MM月dd日 HH:mm:ss");  
  
        Date strDate = sdf1.parse(start);  
        Date endDate = sdf2.parse(end);  
        // 计算持续时间。注意：由于毫秒值很大，因此用long来存。好像不对，最后存的数不大，int好像也行  
        long duration = endDate.getTime() - strDate.getTime();  
        // 字符串和变量拼接必须使用 +        System.out.println("活动持续时间为：" + duration);  
  
        String jia = "2023年11月11日 0:01:00";  
        String pi = "2023年11月11日 0:11:0";  
  
        SimpleDateFormat sdf3 = new SimpleDateFormat("yyyy年MM月dd日 HH:mm:ss");  
        SimpleDateFormat sdf4 = new SimpleDateFormat("yyyy年MM月dd日 HH:mm:ss");  
  
        Date jiaDate = sdf3.parse(jia);  
        Date piDate = sdf4.parse(pi);  
  
        System.out.println("小贾买的时候，活动开始了：" + (jiaDate.getTime() - strDate.getTime()));  
        System.out.println("小皮买的时候，活动开始了：" + (piDate.getTime() - strDate.getTime()));  
  
        if( (jiaDate.getTime() - strDate.getTime()) > duration){  
            System.out.println("小贾参加没有参加上");  
        }else{  
            System.out.println("小贾参加上了");  
        }  
  
        if( (piDate.getTime() - strDate.getTime()) > duration){  
            System.out.println("小皮没有参加上");  
        }else{  
            System.out.println("小皮参加上了");  
        }  
    }  
}
```