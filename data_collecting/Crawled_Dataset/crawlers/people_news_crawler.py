#爬取人民网新闻的异步爬虫
#该爬虫使用aiohttp库进行异步请求，使用Selenium处理动态

import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import requests
from crawlers.caseinfo import CaseInfo
from crawlers.DuplicateDataCase import DuplicateDataCase
from crawlers.img_to_base64 import url_to_base64
from crawlers.check_AIGCrisk_title import check_AIGCrisk_news
from crawlers.time_convert import convert_date_format
from crawlers.get_base_url import get_base_url

async def fetch_page_json(session,url, headers, params):
    """异步获取页面内容 返回格式为json"""
    try:
            async with session.post(url, headers=headers, json=params) as response:
                # 获取JSON响应
                response_text = await response.text()
                
                return response_text
    except Exception as e:
        logging.error(f"获取页面失败 {url}: {e}")
        return None
async def fetch_html(session, url, headers):
    """异步获取HTML页面内容"""
    try: 
        async with session.get(url, headers=headers) as response:
            return await response.text()
    except Exception as e:
        logging.error(f"获取HTML页面失败 {url}: {e}")
        return None
async def process_news_detail(session, case_link, headers, result):
    """异步处理新闻详情页"""
    try:
        html = await fetch_html(session, case_link, headers)
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取新闻内容
        content_element = soup.find_all('div',class_='rm_txt_con')  # 更新选择器
        if content_element:
            # 提取所有子标签的文本内容，并用换行符连接
            texts = []
            for child in content_element[0].children:
                if child.name:  # 确保是标签
                    texts.append(child.get_text(strip=True))
            description = "\n".join(texts)
            result.set_attribute('description', description)
            
            # 提取图片
            images = []
            img_elements = content_element[0].select("img")
            for img in img_elements:
                #print(img if img else "1")
                if  'alt' in img.attrs:
                    img_link =get_base_url(case_link)+img['src']
                    try:
                        response = requests.get(img_link)
                        if response.status_code == 200:  # 状态码200表示资源存在且可访问
                            single_img = {"image_name": "",
                                        "image_url": "",
                                        "base64_encoding": ""
                                        }
                            base64_encoding = url_to_base64(img_link)
                            single_img["image_url"] = img_link
                            single_img["base64_encoding"] = base64_encoding
                            images.append(single_img)
                        else:
                            print(f"图片链接 {img_link} 不可访问，状态码: {response.status_code}")
                    except requests.RequestException as e:
                        print(f"检查图片链接 {img_link} 时出现异常: {e}")
            result.set_attribute('images' , images)  
 
        # 提取发布时间
        timeandsource_elements = soup.find_all("div",class_="col-1-1")  # 更新选择器
        if timeandsource_elements:
            timeandsource = timeandsource_elements[0].text.strip()
            timeandsource = timeandsource.split('|')
            release_date = convert_date_format(timeandsource[0].strip())
            result.set_attribute('release_date', release_date)
            # 提取来源
            source_part= timeandsource[1].strip()# 更新选择器
            # 查找 "来源：" 并提取其后的文字
            if "来源：" in source_part:
                source = source_part.split("来源：")[1].strip()
                result.set_attribute('source', source)
        
        return result.__json__()
        
    except Exception as e:
        logging.error(f"处理新闻详情页出错 {case_link}: {e}")
        return None

async def scrape_people_news(url, keyword, max_pages=5):
    """
    异步爬取人民网新闻
    
    参数:
    url: 人民网搜索API的URL
    keyword: 搜索关键词
    max_pages: 最大爬取页数
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("开始爬取人民网新闻")
    search_url = "http://search.people.cn/search-platform/front/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    
    all_results = []
    other_results = []
    
    async with aiohttp.ClientSession() as session:
        for page in range(1, max_pages + 1):
            # 构建搜索参数
            params ={
                    "key": keyword,
                    "page": page,
                    "limit": 10,
                    "hasTitle": "true",
                    "hasContent": "true",
                    "isFuzzy": "false",
                    "type": 0,
                    # 0表示精确搜索
                    "sortType": 0,
                    #时间范围
                    "startTime": 0,
                    "endTime": 0
                    }

            
            logging.info(f"正在爬取第{page}页")
            
            # 获取搜索结果
            response_data = await fetch_page_json(session, search_url, headers, params)
            if not response_data:
                continue
            response_data=json.loads(response_data)
            # 从响应中获取新闻列表
            news_cards = response_data.get('data', {}).get('records', [])
            
            if not news_cards:
                logging.info(f"第{page}页未找到新闻，爬取下一页")
                continue
            
            # 创建任务列表
            tasks = []
            
            for card in news_cards:
                try:
                    # 创建CaseInfo对象存储新闻信息
                    result = CaseInfo()
                    result.set_attribute('platform', '人民网')
                    result.set_attribute('case_type', 'news')
                    result.set_attribute('search_keywords', keyword)
                    result.set_attribute('uploaded_by', 3)
                    
                    # 从JSON中直接获取标题和链接
                    title = card.get('title', '')
                    case_link = card.get('url', '')
                    
                    if not title or not case_link:
                        continue
                        
                    result.set_attribute('title', title)
                    result.set_attribute('case_link', case_link)
                    
                    # 获取摘要
                    summary = card.get('content', '')
                    result.set_attribute('summary', summary)
                    print(case_link)
                    # 使用大模型判断是否为AIGC风险相关新闻
                    AIGC_check = check_AIGCrisk_news(title)
                    
                    # 创建DuplicateDataCase对象
                    other_result = DuplicateDataCase()
                    other_result.set_title(title)
                    other_result.set_url(case_link)
                    other_result.set_is_AIGC(1 if AIGC_check else 0)
                    
                    # 如果是AIGC相关新闻，创建异步任务获取详细信息
                    if AIGC_check:
                        task = asyncio.create_task(
                            process_news_detail(session, case_link, headers, result)
                        )
                        tasks.append(task)
                    
                    other_result = other_result.__json__()
                    other_results.append(other_result)
                    
                    logging.info(f"已爬取标题: {title}")
                    
                except Exception as e:
                    logging.error(f"处理新闻卡片时出错: {e}")
                    continue
            
            # 等待所有任务完成
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if result and not isinstance(result, Exception):
                        all_results.append(result)
            
            await asyncio.sleep(2)  # 页面间隔
    
    logging.info(f"人民网关键词 {keyword} 爬取完成")
    return all_results, other_results

def run_scraper(url, keyword, max_pages=5):
    """运行异步爬虫的包装函数"""
    return asyncio.run(scrape_people_news(url, keyword, max_pages)) 