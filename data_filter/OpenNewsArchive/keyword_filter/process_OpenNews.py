#这个文件是用来筛选OpenNewsArchive中AI相关的新闻的
#通过调用关键词过滤器来筛选新闻内容
#注意修改关键词文件路径，日志文件路径，和输入输出目录
import os
import json
from functools import partial
from multiprocessing import Pool
# 初始化NLTK（这里假设你已经安装并配置好NLTK）
import nltk

# 初始化配置
class Config:
    KEYWORDS_FILE = "keywords.txt"# 关键词文件路径

# 初始化日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(process)d - %(message)s',
    handlers=[
        logging.FileHandler("filter_OpenNews_log.txt"),# 日志文件路径
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 关键词处理
class KeywordProcessor:
    def __init__(self):
        self.keywords = self._load_keywords()
        self.lemmatizer = nltk.stem.WordNetLemmatizer()
        self.en_stopwords = set(nltk.corpus.stopwords.words('english'))

    def _load_keywords(self):
        try:
            with open(Config.KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                return set(line.strip().lower() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to load keywords: {e}")
            return set()

    def extract_keywords(self, text, lang, top_n=10):
        if lang == 'zh':
            import jieba.analyse
            return set(jieba.analyse.extract_tags(text, topK=top_n, withWeight=False))
        elif lang == 'en':
            tokens = [self.lemmatizer.lemmatize(t.lower())
                      for t in nltk.word_tokenize(text)
                      if t.isalpha() and t.lower() not in self.en_stopwords]
            return set(w for w, _ in nltk.FreqDist(tokens).most_common(top_n))
        return set()

keyword_processor = KeywordProcessor()

def process_jsonl_file(file_path):
    ai_related_news = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                content = data.get('content', '')
                lang = data.get('language', 'unknown')

                keywords = keyword_processor.extract_keywords(content, lang)
                if keyword_processor.keywords.intersection(keywords):
                    ai_related_news.append(data)
                    logger.info(f"Found AI-related news with ID: {data.get('id', 'unknown')} from file {file_path}")
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")
    return ai_related_news

def main(input_dir):
    jsonl_files = [os.path.join(root, f)
                   for root, _, files in os.walk(input_dir)
                   for f in files if f.endswith(".jsonl")]

    logger.info(f"Processing {len(jsonl_files)} JSONL files")

    num_workers = min(8, os.cpu_count())
    with Pool(num_workers) as pool:
        results = pool.map(process_jsonl_file, jsonl_files)

    all_ai_news = [news for sublist in results for news in sublist]

    logger.info(f"Found {len(all_ai_news)} AI-related news in total")

    # 可以在这里将筛选出的新闻保存到文件中
    with open('ai_related_news.jsonl', 'w', encoding='utf-8') as f:
        # 'ai_related_news.jsonl'是输出文件路径
        for news in all_ai_news:
            f.write(json.dumps(news, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    input_directory = "path/to/your/jsonl/files"  # 替换为你的输入目录
    if not os.path.exists(input_directory):
        main(input_directory)
    