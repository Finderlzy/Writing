---
createdDate: 2026-09-18
---
> 写于 2026-09-18

```java
package com.itheima.a01jdk7datedemo;  
  
import java.util.Calendar;  
import java.util.Date;  
  
public class CalendarDemo1 {  
    static void main() {  
        // 创建一个Calendar对象，只能使用这个静态方法去创建  
        Calendar cal = Calendar.getInstance();  
        Date date = new Date(0L);  
        // 把这个Date对象存入Calendar对象中  
        cal.setTime(date);  
          
        // Calendar在底层是用一个数组存放年、月、日、时、分、秒的  
        // 细节1：在存月份的时候，Calendar存的是：0~11。  
        // 细节2：在外国人眼里，周日才是一周的第一天  
        System.out.println(cal);  
        // 获取Calendar中的时间。Calendar类定义了一些常量来表示  
        int year = cal.get(Calendar.YEAR);  
        // 加一是为了让显示出来的月份和实际一样  
        int month = cal.get(Calendar.MONTH) + 1;  
        int dayOfMonth = cal.get(Calendar.DAY_OF_MONTH);  
        // 减一是为了和我们自己的习惯一样  
        int dayOfWeek = cal.get(Calendar.DAY_OF_WEEK) - 1;  
  
        System.out.println(year + ", " + month + ", " + dayOfMonth + ", " + dayOfWeek);  
		// 1970, 1, 1, 4  
    }  
}
```