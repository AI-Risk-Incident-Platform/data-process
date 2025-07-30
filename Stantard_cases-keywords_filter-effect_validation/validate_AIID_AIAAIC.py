import os
import json
import time
import logging
import sys
from functools import partial
from multiprocessing import Pool
from langdetect import detect
import jieba.analyse
import nltk
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import ahocorasick  # ✅ 新增依赖

# 初始化NLTK资源
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)

# 配置类
class Config:
    KEYWORDS_FILE = "merge_keywords_AI.txt"
    PHRASES_FILE = "custom_phrases.txt"
    LOG_FILE = "filter_log.txt"
    AI_RELATED_OUTPUT = "ai_related_news_AIID_AIAAIC.json"
    AI_UNRELATED_OUTPUT = "ai_unrelated_news_AIID_AIAAIC.json"
    STOPWORDS_FILE = "unique_stopwords.txt"

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

# ✅ 短语匹配器：基于Aho-Corasick自动机
class PhraseMatcher:
    def __init__(self, phrases):
        self.automaton = ahocorasick.Automaton()
        for idx, phrase in enumerate(phrases):
            self.automaton.add_word(phrase, phrase)
        self.automaton.make_automaton()

    def find_matches(self, text):
        matches = set()
        for end_index, phrase in self.automaton.iter(text):
            matches.add(phrase)
        return matches

# 关键词处理器类
class KeywordProcessor:
    def __init__(self, stopwords_file=Config.STOPWORDS_FILE):
        self.lemmatizer = WordNetLemmatizer()
        self.custom_stopwords = set()
        self.en_default_stopwords = set(stopwords.words('english'))

        self.keywords = self._load_keywords()
        self.phrases = self._load_phrases()
        self.phrase_matcher = PhraseMatcher(self.phrases)

        if stopwords_file:
            self.load_stopwords(stopwords_file)

        logger.info(f"已加载AI关键词：{len(self.keywords)}个")
        logger.info(f"已加载自定义短语：{len(self.phrases)}个")

    def _load_keywords(self):
        try:
            with open(Config.KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                return set(line.strip().lower() for line in f if line.strip())
        except Exception as e:
            logger.error(f"加载关键词文件失败：{e}")
            return set()

    def _load_phrases(self):
        try:
            if not os.path.exists(Config.PHRASES_FILE):
                logger.warning(f"短语词典文件 {Config.PHRASES_FILE} 不存在")
                return set()
            with open(Config.PHRASES_FILE, 'r', encoding='utf-8') as f:
                return {line.strip().lower() for line in f if line.strip()}
        except Exception as e:
            logger.error(f"加载短语词典失败：{e}")
            return set()

    def load_stopwords(self, stopwords_file):
        try:
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        self.custom_stopwords.add(word)
            logger.info(f"已加载自定义停用词：{len(self.custom_stopwords)}个")
        except FileNotFoundError:
            logger.warning(f"未找到停用词文件 {stopwords_file}")
        except Exception as e:
            logger.error(f"加载停用词时出错：{str(e)}")

    def detect_language(self, text):
        try:
            return detect(text[:1000]) if text else 'en'
        except:
            return 'en'

    def extract_keywords(self, text, lang, top_n=100):
        if not text.strip():
            return set()

        if lang == 'zh':
            filtered = set()
            current_top = top_n
            max_attempts = 5
            attempt = 0

            while len(filtered) < top_n and attempt < max_attempts:
                raw_keywords = set(jieba.analyse.extract_tags(text, topK=current_top, withWeight=False))
                new_filtered = raw_keywords - self.custom_stopwords
                filtered.update(new_filtered)
                if len(filtered) < top_n:
                    current_top += int((top_n - len(filtered)) * 1.5)
                    attempt += 1
            return set(list(filtered)[:top_n])

        elif lang == 'en':
            lower_text = text.lower()

            # 短语匹配
            phrase_matches = self.phrase_matcher.find_matches(lower_text)

            # 词元化并过滤已匹配短语中出现的单词
            tokens = [t for t in word_tokenize(lower_text) if t.isalpha()]
            phrase_words = set()
            for phrase in phrase_matches:
                phrase_words.update(phrase.split())

            residual_tokens = [
                self.lemmatizer.lemmatize(t)
                for t in tokens
                if t not in phrase_words and
                   t not in self.en_default_stopwords and
                   t not in self.custom_stopwords
            ]

            freq_dist = FreqDist(residual_tokens)
            top_residuals = [w for w, _ in freq_dist.most_common(top_n)]

            return set(list(phrase_matches) + top_residuals)

        return set()

# 单文件处理逻辑
def process_jsonl_file(file_path, keyword_processor):
    ai_related_news = []
    ai_unrelated_news = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    content = data.get('text', '')
                    if not content:
                        continue

                    lang = keyword_processor.detect_language(content)
                    keywords = keyword_processor.extract_keywords(content, lang)
                    is_ai_related = not keyword_processor.keywords.isdisjoint(keywords)

                    data['keywords'] = list(keywords)
                    data['language'] = lang
                    data['is_ai_related'] = is_ai_related

                    if is_ai_related:
                        ai_related_news.append(data)
                        if line_num % 100 == 0:
                            logger.info(f"处理到第{line_num}行，已发现{len(ai_related_news)}条AI相关新闻")
                    else:
                        ai_unrelated_news.append(data)

                except json.JSONDecodeError:
                    logger.warning(f"文件{file_path}第{line_num}行JSON解析错误，已跳过")
                except Exception as e:
                    logger.error(f"处理文件{file_path}第{line_num}行时出错：{str(e)}")

        logger.info(f"完成处理文件 {file_path}，找到{len(ai_related_news)}条AI相关新闻，{len(ai_unrelated_news)}条非AI新闻")
    except Exception as e:
        logger.error(f"处理文件{file_path}时出错：{str(e)}")

    return ai_related_news, ai_unrelated_news

# 保存结果
def save_results(related, unrelated):
    with open(Config.AI_RELATED_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(related, f, ensure_ascii=False, indent=4)
    with open(Config.AI_UNRELATED_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(unrelated, f, ensure_ascii=False, indent=4)
    logger.info(f"结果已保存：{Config.AI_RELATED_OUTPUT}（{len(related)}条）和{Config.AI_UNRELATED_OUTPUT}（{len(unrelated)}条）")

# 主函数
def main(input_files):
    start_time = time.time()
    logger.info(f"开始处理，共{len(input_files)}个文件")
    keyword_processor = KeywordProcessor(stopwords_file=Config.STOPWORDS_FILE)

    all_related = []
    all_unrelated = []

    if len(input_files) > 1 and os.cpu_count() > 1:
        num_workers = min(8, os.cpu_count())
        logger.info(f"使用{num_workers}个进程并行处理")
        process_func = partial(process_jsonl_file, keyword_processor=keyword_processor)
        with Pool(num_workers) as pool:
            results = pool.map(process_func, input_files)
        for rel, unrel in results:
            all_related.extend(rel)
            all_unrelated.extend(unrel)
    else:
        logger.info("使用单进程处理")
        for file_path in input_files:
            rel, unrel = process_jsonl_file(file_path, keyword_processor)
            all_related.extend(rel)
            all_unrelated.extend(unrel)

    save_results(all_related, all_unrelated)
    total_time = time.time() - start_time
    logger.info(f"所有文件处理完成，总耗时：{total_time:.2f}秒")
    logger.info(f"总计发现AI相关新闻：{len(all_related)}条，非AI相关新闻：{len(all_unrelated)}条")
    ai_ratio=len(all_related)*100/(len(all_related)+len(all_unrelated))
    logger.info(f"AI相关新闻占比{ai_ratio:.2f}%")

# 程序入口
if __name__ == "__main__":
    input_files = [
        "cases.jsonl"
    ]
    main(input_files)
