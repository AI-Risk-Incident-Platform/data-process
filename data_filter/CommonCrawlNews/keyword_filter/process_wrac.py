#这是用于处理Common Crawl新闻数据的脚本
#它会从WARC文件中提取新闻内容，进行AI关键词过滤，并保存有效内容
#使用了多进程和NLTK进行文本处理
#其输入是WARC文件，输出是过滤后的AI新闻文本和HTML内容

#注意修改文件中的路径，关键词文件路径，月份和年份等配置项
#注意 这里为了方便测试和及时修改错误，文件运行只处理三个月的数据，并生成相关log文件

import os
import gzip
import time
import logging
import hashlib
import multiprocessing
from functools import partial
from multiprocessing import Pool, Manager
from warcio.archiveiterator import ArchiveIterator
from boilerpy3 import extractors
import jieba.analyse
from bs4 import BeautifulSoup
from langdetect import detect
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# 初始化配置
class Config:
    WARC_FOLDER = "WARC_FOLDER"
    OUTPUT_DIR = "OUTPUT_DIR"
    LOG_FILE = "LOG_FILE"
    KEYWORDS_FILE = "keywords.txt"
    NLTK_DATA = ['punkt', 'stopwords', "punkt_tab", 'wordnet']
    MAX_WORKERS = 32

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(process)d - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化NLTK
def init_nltk():
    for data in Config.NLTK_DATA:
        try:
            if data in ['punkt', 'punkt_tab']:
                nltk.data.find(f'tokenizers/{data}')
            else:
                nltk.data.find(f'corpora/{data}')
        except LookupError:
            nltk.download(data)

init_nltk()

# 关键词处理
class KeywordProcessor:
    def __init__(self):
        self.keywords = self._load_keywords()
        self.lemmatizer = WordNetLemmatizer()
        self.en_stopwords = set(stopwords.words('english'))
    
    def _load_keywords(self):
        try:
            with open(Config.KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                return set(line.strip().lower() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to load keywords: {e}")
            return set()
    
    def extract_keywords(self, text, lang, top_n=10):
        if lang == 'zh':
            return set(jieba.analyse.extract_tags(text, topK=top_n, withWeight=False))
        elif lang == 'en':
            tokens = [self.lemmatizer.lemmatize(t.lower()) 
                     for t in word_tokenize(text) 
                     if t.isalpha() and t.lower() not in self.en_stopwords]
            return set(w for w, _ in nltk.FreqDist(tokens).most_common(top_n))
        return set()

keyword_processor = KeywordProcessor()

# 内容处理工具
class ContentProcessor:
    @staticmethod
    def clean_html(html):
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'a']):
            tag.decompose()
        return str(soup)
    
    @staticmethod
    def extract_content(html):
        try:
            if not html:
                return "empty content"
            content = extractors.ArticleExtractor().get_content(html)
            return content if content else "empty content"
        except Exception as e:
            logger.warning(f"Content extraction failed: {e}")
            return "empty content"
    
    @staticmethod
    def detect_language(text):
        try:
            return detect(text[:1000])  # 只检测前1000字符提高效率
        except:
            return 'unknown language'  # 默认英语

# WARC处理核心
class WARCAnalyzer:
    def __init__(self, output_dir, stats):
        self.output_dir = output_dir
        self.stats = stats
    
    def process_record(self, record):
        try:
            # 基础数据提取
            payload = record.content_stream().read().decode(errors='ignore')
            clean_html = ContentProcessor.clean_html(payload)
            main_content = ContentProcessor.extract_content(clean_html)
            
            # 空内容检查
            if not main_content.strip() or main_content == "empty content":
                return False
            
            # 语言检测和关键词提取
            lang = ContentProcessor.detect_language(main_content)
            if lang not in ("en", "zh"):
                return False
                
            keywords = keyword_processor.extract_keywords(main_content, lang)
            if not keyword_processor.keywords.intersection(keywords):
                return False
            
            # 保存有效内容
            url = record.rec_headers.get("WARC-Target-URI", "")
            self._save_results(url, payload, main_content)
            return True
            
        except Exception as e:
            logger.error(f"Record processing error: {e}")
            return False
    
    def _save_results(self, url, html, text):
        """原子化文件保存操作"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        html_path = os.path.join(self.output_dir, "htmls")
        text_path = os.path.join(self.output_dir, "texts")
        os.makedirs(html_path, exist_ok=True)
        os.makedirs(text_path, exist_ok=True)
        
        # 先写入临时文件再重命名，避免部分写入
        temp_html = os.path.join(html_path, f"temp_{url_hash}.html")
        final_html = os.path.join(html_path, f"{url_hash}.html")
        
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(f"<!-- URL: {url} -->\n{html}")
        os.rename(temp_html, final_html)
        
        # 同样处理文本内容
        temp_text = os.path.join(text_path, f"temp_{url_hash}.txt")
        final_text = os.path.join(text_path, f"{url_hash}.txt")
        
        with open(temp_text, 'w', encoding='utf-8') as f:
            f.write(text)
        os.rename(temp_text, final_text)
        
        logger.info(f"Saved results for {url}")

# 主处理函数
def process_warc_file(warc_path, year, month, stats):
    analyzer = WARCAnalyzer(
        output_dir=os.path.join(Config.OUTPUT_DIR, year, month),
        stats=stats
    )
    
    local_stats = {'total': 0, 'ai': 0, 'failed': 0}
    
    try:
        with gzip.open(warc_path, 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type == "response":
                    local_stats['total'] += 1
                    if analyzer.process_record(record):
                        local_stats['ai'] += 1
    except Exception as e:
        local_stats['failed'] = local_stats['total']
        logger.error(f"Failed to process {warc_path}: {e}")
    
    # 更新共享统计
    # 不需要锁（每个赋值操作自身是原子的）
    for k, v in local_stats.items():
        stats[k] += v  # 每个键的更新是独立的原子操作
    stats['files_processed'] += 1
    
    return warc_path, local_stats

def main():
    start_time = time.time()


    year = "2022"
    months = ["9","10","11","12"]  # 可扩展为多个月份
    
    # 初始化共享统计
    manager = Manager()
    stats = manager.dict({
        'total': 0,
        'ai': 0,
        'failed': 0,
        'files_processed': 0,
        'files_failed': 0
    })
    
    for month in months:
        month = str(month)
        warc_files = [
            os.path.join(root, f) 
            for root, _, files in os.walk(os.path.join(Config.WARC_FOLDER, year, month))
            for f in files if f.endswith(".warc.gz")
        ]
        
        if not warc_files:
            logger.warning(f"No WARC files found for {year}-{month}")
            continue
            
        logger.info(f"Processing {len(warc_files)} files for {year}-{month}")
        
        # 准备输出目录
        os.makedirs(os.path.join(Config.OUTPUT_DIR, year, month, "texts"), exist_ok=True)
        
        # 进程池处理
        num_workers = min(Config.MAX_WORKERS, os.cpu_count(), len(warc_files))
        with Pool(num_workers) as pool:
            results = pool.imap_unordered(
                partial(process_warc_file, year=year, month=month, stats=stats),
                warc_files 
            )
            
            for warc_path, local_stats in results:
                logger.info(
                    f"Completed {os.path.basename(warc_path)}: "
                    f"Total={local_stats['total']} "
                    f"AI={local_stats['ai']} "
                    f"Failed={local_stats['failed']}"
                )
            
    # 最终统计
    end_time = time.time()
    stats_dict = dict(stats)
    
    summary = (
        f"\n=== Processing Summary ===\n"
        f"Time elapsed: {end_time - start_time:.2f} seconds\n"
        f"WARC files processed: {stats_dict['files_processed']}\n"
        f"HTML pages processed: {stats_dict['total']}\n"
        f"AI-related pages found: {stats_dict['ai']}\n"
        f"Failed pages: {stats_dict['failed']}\n"
    )
    
    with open(Config.LOG_FILE, 'a') as f:
        f.write(summary)
    
    logger.info(summary)

if __name__ == "__main__":
    multiprocessing.freeze_support()  # 对于Windows打包支持
    main()