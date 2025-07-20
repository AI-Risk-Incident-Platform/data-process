import json
import pandas as pd
import requests
from bs4 import BeautifulSoup  

def aiaaic_parse_url(url):
    """
    解析给定的 URL，提取倒数第二个 h3 标签后紧挨着的 ul 标签中的所有链接。

    参数:
        url (str): 要解析的网页 URL。

    返回:
        list: 提取的链接列表。如果未找到符合条件的 ul 标签，则返回空列表。
    """

    try:
        # 发送 HTTP 请求
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()  # 检查请求是否成功

        # 使用 BeautifulSoup 解析 HTML 内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到所有 h3 标签
        h3_tags = soup.find_all('h3')

        # 获取倒数第二个 h3 标签
        if len(h3_tags) < 2:
            return []  # 如果 h3 标签少于 2 个，返回空列表
        second_last_h3 = h3_tags[-2]

        # 找到该 h3 标签紧挨着的下一个兄弟元素，判断是否为 ul 标签
        next_sibling = second_last_h3.find_next_sibling()
        if next_sibling and next_sibling.name == 'ul':
            # 找到 ul 标签中的所有 a 标签
            a_tags = next_sibling.find_all('a')
            parsed_links = [link['href'] for link in a_tags if 'href' in link.attrs]
            return parsed_links
        else:
            return []  # 未找到符合条件的 ul 标签
    except Exception as e:
        print(f"[ERROR] Failed to parse URL {url}: {e}")
        return []

# 读取 AIAAIC.xlsx 文件并跳过首行
df = pd.read_excel('AIAAIC_Repository.xlsx', sheet_name="Incidents", skiprows=[0,2])
filtered_data = df[df['Description/links'].notna()]
filtered_data = filtered_data.drop_duplicates(subset=['AIAAIC ID#']).set_index('AIAAIC ID#')
# 筛选出非空的 Description/links，并将其与 Headline 和 AIAAIC ID# 转换为字典
headline_links_dict = filtered_data[['Headline', 'Description/links']].to_dict('index')

# 遍历 headline_links_dict 中的每个条目
for aiaaic_id, details in headline_links_dict.items():
    url = details.get("Description/links")
    print(f"[正在处理]{aiaaic_id}")
    try:
        headline_links_dict[aiaaic_id]["parsed_links"] = aiaaic_parse_url(url)
    except Exception as e:
        print(f"[ERROR] Failed to parse URL {url}: {e}")
        headline_links_dict[aiaaic_id]["parsed_links"] = []

# 保存到文件中
with open('aiaaic_processed_data.jsonl', 'w', encoding='utf-8') as file:
    for key, value in headline_links_dict.items():
        json.dump({key: value}, file, ensure_ascii=False)
        file.write('\n')  # Add a newline after each JSON object
