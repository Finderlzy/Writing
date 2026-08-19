
## 第一步：创建 KeePassXC 数据库

打开 KeePassXC：

1. 点击：

```
数据库 → 新建数据库
```
2. 输入数据库名称，比如：

```
My Password Database
```

3. 设置一个**主密码（Master Password）**

这个密码非常重要，相当于整个保险箱的钥匙。

注意：==**自己能记住**==。一定要记住，不然以后要用的时候忘记了就寄了。

4. 后面的设置保持默认即可。

5. 保存数据库：

最后会生成一个“.kdbx”文件。

这个文件就是你的密码保险箱。

---

## 第二步：在 KeePassXC 中创建 GitHub 条目

打开数据库后，右键空白处，新建条目。

填写：

标题：

```
GitHub
```

用户名：

```
你的GitHub用户名
```

密码：

```
你的GitHub密码
```

保存。

---

## 第三步：开启 GitHub 2FA

打开 GitHub：

头像 → Settings

然后：

```
Password and authentication
```

找到：

```
Two-factor authentication
```

点击：

```
Enable two-factor authentication
```

选择：

```
Authenticator app
```

---

## 第四步：让 KeePassXC 扫描 GitHub 的二维码

### GitHub 给你一串密钥

GitHub 通常会有：

```
Can't scan?
Enter this text code instead
```

类似：

```
JBSWY3DPEHPK3PXP
```

复制下来，回到KeePassXC：

```
右键 GitHub条目
↓
TOTP
↓
Set up TOTP
↓
Secret key
↓
粘贴
```

保存。

---

## 第五步：测试验证码

然后，右键 GitHub 条目：

```
TOTP
↓
Copy TOTP
```

会得到：

```
123456
```

这个就是 GitHub 要求输入的验证码。

输入完成即可。

---

## 第六步：保存 GitHub Recovery Codes（非常重要）

GitHub 开启 2FA 后，会给你：

```
Recovery codes
```

类似：

```
abcd-1234
efgh-5678
...
```

不要跳过。

建议：在 KeePassXC 新建一个条目：

```
GitHub Recovery Codes
```

密码栏或者备注栏保存这些代码。

---

## 第七步：备份 KeePassXC 数据库

你的关键文件：

```
xxx.kdbx
```

丢了：GitHub密码还在，但TOTP密钥没了，可能会无法登录。所以建议至少保存两个地方：

例如：

```
电脑硬盘
+
U盘
```

或者：

```
电脑
+
加密云盘
```

注意：不要把 `.kdbx` 文件裸放公开网盘。

---

完成之后，你的登录链路就是：

```
GitHub
   |
密码
   |
KeePassXC
   |
生成TOTP验证码
```

完全不需要国外手机号。