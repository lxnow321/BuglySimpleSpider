# BuglySimpleSpider
Bugly简单爬虫，用于爬取应用异常信息

## 准备工作
使用指令打开浏览器：
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"

或者将参数配置到浏览器的快捷方式中
在 chrome 的快捷方式上右击，选择属性，快捷方式的目标栏后面加空格加上--remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"

参考：https://www.jiubing.site/pages/c62e69/


## 执行步骤

1. 上述方法打开浏览器
2. 进入bugly网站，登陆自己账号进入到对应应用的异常信息页面，点击“异常信息”
3. 执行BuglySimpleSpider程序

## 说明
1. 由于直接用Selenium.WebDriver打开的浏览器被Bugly网站识别出来，总是无法连接到服务器。故使用Selenium连接外部浏览器进行爬取数据。
2. 这是一个简单的bugly错误信息爬取程序，只是简单的模拟点击并获取页面数据。临时起意想做这么个东西来方便自己查询bugly中的报错信息，相关知识了解不深，所以怎么简单怎么来。后续可能会学习深入后进行修改更新。