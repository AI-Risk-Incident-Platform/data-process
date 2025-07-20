AI风险数据库平台
新闻网页爬虫系统说明文档
项目描述
这是一个专门用于收集 AI（人工智能）相关风险新闻和信息的网络爬虫系统。该系统支持多个新闻源，并提供自动化数据采集和处理功能。

注意，该项目相关爬虫代码 在2025年4月成立，如网页后续有更新，请修改crawlers中具体网页的爬虫代码

目录结构
AIGCdatacrawler/
├── news_web_crawler.py                 # 主程序入口
├── crawler_utils.py        # 工具函数
├── auto_crawler.py         # 自动爬虫模块
├── config.ini             # 配置文件
│
├── crawlers/              # 爬虫实现目录
│   ├── __init__.py
│   ├── site1_crawler.py   # 特定网站爬虫
│   └── site2_crawler.py   # 特定网站爬虫
│
├── results/               # 结果存储目录
│   ├── aigc/             # AIGC相关结果
│   └── all/              # 所有采集数据
│
└── logs/                  # 日志文件目录

目前已经撰写好爬虫的网站有  36氪新闻，人民网新闻，腾讯新闻，澎湃新闻，新华网新闻

配置说明
编辑 config.ini 配置以下内容：

目标新闻网站
各网站关键词
爬虫映射关系
最大爬取页数
测试模式设置
自动上传设置
使用方法
基本用法
运行普通模式：

使用方法

基本用法
运行普通模式：
python news_web_crawler.py

测试模式
测试特定网站爬虫：
python news_web_crawler.py --test --site=[网站名称]

自动模式
运行自动爬取：
python news_web_crawler.py --auto


主要功能
多站点支持
自动化爬取
测试模式
可配置关键词和页面限制
数据清洗和处理
自动上传功能
日志系统