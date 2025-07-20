#这个文件是根据标题用来筛选热搜词中AI相关的新闻的

import pandas as pd
from fuzzywuzzy import fuzz
# 初始化配置
keywords_file="keywords.txt"# 关键词文件路径

def load_keywords(keywords_file):
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return set(line.strip().lower() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to load keywords: {e}")
            return set()
keywords = load_keywords(keywords_file)
# 筛选包含关键词的行
# 筛选包含关键词的行
def contains_keyword(title):
    if not isinstance(title, str):
        print(f"Invalid title: {title}")
        return False
    for keyword in keywords:
        if keyword in title:
            return True
        if fuzz.partial_ratio(keyword, title) > 65:  # 模糊匹配阈值，可以根据需要调整
            return True
    return False
import json
import csv
import urllib.parse

# 读取JSON文件
with open('dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
#注意修改json文件名称，路径

# 打开CSV文件进行写入
#注意修改csv文件名称，路径
with open('dataset.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['id', '日期', 'title', 'url']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # 初始化id
    id_counter = 0

    # 遍历JSON数据
    for date, items in data.items():
        for item in items:
            title = item.get('title').get('title')
            url = item.get('title').get('url')
            writer.writerow({'id': id_counter, '日期': date, 'title': title, 'url': url})
            id_counter += 1
# 读取CSV文件
#注意修改csv文件名称，路径
df = pd.read_csv('dataset.csv')
filtered_df = df[df['title'].apply(contains_keyword)]
# 将筛选后的数据保存到新的CSV文件
#注意修改csv文件名称，路径
filtered_df.to_csv('filtered_dataset.csv', index=False)
# 遍历每一行
