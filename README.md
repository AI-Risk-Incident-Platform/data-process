# 数据处理部分

数据处理主要分为三个部分，一是数据获取，二是数据过滤，三是在标准数据集的方法校验。这其中，数据获取部分是本数据库所有数据源的获取代码，数据过滤部分是需要从全部数据过滤到AI风险新闻数据的过滤代码，方法校验是将本数据处理的方法在标准数据集上进行测试并得出相关指标的测试代码。

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

## 方法校验
使用data项目中的cases.jsonl标准数据集验证  “关键词过滤AI相关新闻”  这一步的具体效果

由于标准数据集来自AIID和AIAAIC两个数据集，这两个数据集都通过了人工测验，因此认为其均是AI相关的真实新闻。
### 具体方法

具体方法为，使用nltk和jieba对文章进行分词，然后和AI关键词取交集，如果存在交集，说明该新闻是AI相关新闻，需要注意的是，在分词过程中，需要确定一些固定短语，比如Artificial Intelligence，遇到这种词需将其看为一个整体，在代码中进行额外操作使其不分为两个词。

### 测试结果

经过测试，使用该方法总计发现AI相关新闻：9131条，非AI相关新闻：430条，AI相关新闻占比95.50%  
也就是说，对AI相关新闻的召回率达到了95%
这证实了在后续全量新闻数据集上首先进行AI相关新闻过滤的合理性