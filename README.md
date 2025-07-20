# 数据处理部分

数据处理主要分为两个部分，一是数据获取，二是数据过滤。这其中，数据获取部分是本数据库所有数据源的获取代码，数据过滤部分是需要从全部数据过滤到AI风险新闻数据的过滤代码。

## 数据获取

数据源主要有六个，分别是AIID,AIAAIC,CommonCrawlNews,OpenNewsArchive,Crawled_Dataset和Hot-list-word_Dataset。
这其中AIID和AIAAIC是先前类似工作形成的小型数据集，CommonCrawlNews,OpenNewsArchive是大型的普通新闻数据集，Crawled_Dataset是自行根据关键词在新闻网站上爬取的数据集，Hot-list-word_Dataset是根据各社交媒体热榜词获取的热榜词数据集。

### AIID
处理AIID数据库中供下载的事件与案例数据
### AIAAIC
处理AIAAIC数据库中的事件链接，通过爬虫获取事件对应的案例链接，再通过crawl4ai使用llm爬取页面获取新闻内容
### CommonCrawlNews
下载commoncrawl中的CommonCrawlNews，下载为warc文件格式，后续需要处理wacr文件
### OpenNewsArchive
下载OpenNewsArchive数据集，下载格式为jsonl
### Crawl_Dataset
详见 文件夹 Crawled_Dataset下的readme文件
### Hot-list-word_Dataset
通过douyin-hot-hub项目获取抖音，头条，v2ex，微博和知乎的热榜词

## 数据过滤

### CommonCrawlNews
首先从WARC文件中提取新闻内容，进行AI关键词过滤，并保存有效内容
使用了多进程和NLTK进行文本处理  
得到AI相关新闻

其次调用qwen2.5对AI新闻进行风险新闻一轮筛
然后用qwen3进行风险新闻二轮筛

### 其他数据集

处理流程 类似 也是先用关键词形成AI新闻，在通过大模型进行两轮筛