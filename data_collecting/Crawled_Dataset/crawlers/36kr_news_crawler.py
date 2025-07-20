#爬取36氪新闻的异步爬虫
#该爬虫使用aiohttp库进行异步请求，使用Selenium处理动态

import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.webdriver.common.by import By
from crawlers.caseinfo import CaseInfo
from crawlers.DuplicateDataCase import DuplicateDataCase
from crawlers.img_to_base64 import url_to_base64
from crawlers.check_AIGCrisk_title import check_AIGCrisk_news
from crawlers.time_convert import convert_date_format

async def fetch_html(session, url, headers):
    """异步获取HTML页面内容"""
    try:
        async with session.get(url, headers=headers) as response:
            return await response.text()
    except Exception as e:
        logging.error(f"获取HTML页面失败 {url}: {e}")
        return None

async def fetch_json_data(session, post_url, headers, params):
    async with session.post(post_url, headers=headers, json=params) as response:
        response_text = await str(response.text())
        response_json = json.loads(response_text)
        return response_json

async def process_news_detail(session,case_link, result,widgetImage,case_link_number):
    """使用Selenium处理新闻详情页"""
    #36氪的新闻详情页在网络中找不到，是动态加载的，需要使用Selenium来处理
    #widgetImage是新闻卡片中的图片，需要加入到图片集中
    #case_link_number是新闻卡片中的新闻编号，用于拼接新闻详情页的链接
    try:
        service = Service()
        chrome_options = ChromiumOptions()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(case_link) 
        await asyncio.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 提取新闻内容
        content_element = soup.find('div', class_='article-main-content').find('div', class_='content-wrapper').find_all('div', class_='common-width')
        if content_element:
            description_element = content_element[1].find('div', class_='content')
            # 提取所有子标签的文本内容，并用换行符连接
            if description_element:
                texts = []
                for child in description_element.children:
                    if child.name:  # 确保是标签
                        texts.append(child.get_text(strip=True))
                description = "\n".join(texts)
            result.set_attribute('description', description)
            
            # 提取图片
            images = []
            # 添加 widgetImage 图片
            if widgetImage:
                try:
                    response = requests.get(widgetImage)
                    if response.status_code == 200:
                        single_img = {
                            "image_name": "",
                            "image_url": widgetImage,
                            "base64_encoding": url_to_base64(widgetImage)
                        }
                        images.append(single_img)
                    else:
                        logging.warning(f"图片链接 {widgetImage} 不可访问，状态码: {response.status_code}")
                except requests.RequestException as e:
                    logging.error(f"检查图片链接 {widgetImage} 时出现异常: {e}")
            #提取新闻内容中的图片
            img_elements = content_element.select("img")
            for img in img_elements:
                if 'src' in img.attrs:
                    img_link = img['src']
                    try:
                        response = requests.get(img_link)
                        if response.status_code == 200:
                            single_img = {
                                "image_name": "",
                                "image_url": img_link,
                                "base64_encoding": url_to_base64(img_link)
                            }
                            images.append(single_img)
                        else:
                            logging.warning(f"图片链接 {img_link} 不可访问，状态码: {response.status_code}")
                    except requests.RequestException as e:
                        logging.error(f"检查图片链接 {img_link} 时出现异常: {e}")
            result.set_attribute('images', images)
        #获取新闻评论 初始化评论数和评论内容
        comments_count=0
        text_comments=[]
        
        #"commentSort":1表示爬取热评论 2表示爬取新评论 将两个评论合并 并爬取前10页的评论
        comments_count,text_comments=fetch_comments(session,case_link_number)
        result.set_attribute("comments",comments_count)
        print(comments_count)
        result.set_attribute("text_comments",text_comments)
        # 提取发布时间和来源
        timeandsource_element = content_element[0].find('div').find('div', class_='article-title-icon')
        if timeandsource_element:
            time_element = timeandsource_element.find('span', class_='item-time')
            release_date = convert_date_format(time_element.get_text(strip=True))
            result.set_attribute('release_date', release_date)
            source_element = timeandsource_element.find('a', class_='item-a')
            result.set_attribute('source', source_element.get_text(strip=True))
        
        driver.quit()
        return result.__json__()
    except Exception as e:
        logging.error(f"处理新闻详情页出错 {case_link}: {e}")
        return None

async def fetch_comments(session, case_link_number):
    """异步获取新闻评论"""
    comments_url = f"https://gateway.36kr.com/api/mis/page/comment/list"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {
        "partner_id": "web",
        "param": {
            "itemId": case_link_number,
            "pageSize": 20,
            "pageEvent": 1,
            "pageCallback": "",
            "siteId": 1,
            "platformId": 2,
            "itemType": 10
        }
    }
    response_json = await fetch_json_data(session, comments_url, headers, params)
    comment_count=0
    text_comments=[]
    comment_list=response_json.get('data', {}).get("commentList", [])
    for comment_element in comment_list:#爬取的每一个一级评论
        comment_content = comment_element.get("content", "")
        if  comment_content!="":
            text_comment={"comment_content":comment_content}
            text_comments.append(text_comment)
            comment_count+=1
        comment_replycomments=comment_element.get("subCommentList",[])#获取爬取的子评论
        if comment_replycomments!=[] and comment_replycomments!=None:
            for comment_replycomment in comment_replycomments:
                replycomment_content=comment_replycomment.get("content","")
                if replycomment_content!="":
                    text_comment={"comment_content":replycomment_content}
                    text_comments.append(text_comment)
                    comment_count+=1
    return comment_count,text_comments

async def scrape_36kr_news(url, keyword, max_pages=5):
    """异步爬取36氪新闻"""
    logging.basicConfig(level=logging.INFO)
    logging.info("开始爬取36氪新闻")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    all_results = []
    other_results = []
    
    async with aiohttp.ClientSession() as session:
#sort=date表示按时间排序
        for page in range(1, max_pages + 1):
            logging.info(f"正在爬取第{page}页")
            if page == 1:
                pageCallback = ""
                search_url = f"{url}/search/articles/{keyword}?sort=date"
                html = await fetch_html(session, search_url, headers)
                if not html:
                    continue
                soup = BeautifulSoup(html, 'html.parser')
                script_tags = soup.find_all('script')
                for script_tag in script_tags:
                    if script_tag.string and "window.initialState" in script_tag.string:
                        target_script = script_tag
                        break
                if target_script:
                    content = target_script.string
                    content = content.replace('window.initialState = ', '')
                    content = str(content.strip().rstrip(';'))
                    news_cards = json.loads(content).get("searchResultData", {}).get('data', {}).get("searchResult", {})
            else:
                post_url = "https://gateway.36kr.com/api/mis/nav/search/resultbytype"
                params = {
                    "partner_id": "web",
                    "param": {
                        "searchType": "article",
                        "searchWord": keyword,
                        "sort": "date",
                        "pageSize": 20,
                        "pageEvent": 1,
                        "pageCallback": pageCallback,
                        "siteId": 1,
                        "platformId": 2
                    }
                }
                news_cards = await fetch_json_data(session, post_url, headers, params)
            
            if not news_cards:
                logging.info(f"第{page}页未找到新闻，爬取下一页")
                continue
            
            tasks = []
            pageCallback = news_cards.get('data', {}).get('pageCallback', '')
            news_cards = news_cards.get('data', {}).get('itemList', [])
            for card in news_cards:
                try:
                    result = CaseInfo()
                    result.set_attribute('platform', '36氪')
                    result.set_attribute('case_type', 'news')
                    result.set_attribute('search_keywords', keyword)
                    result.set_attribute('uploaded_by', 3)
                    
                    title = card.get('widgetTitle', "")
                    
                    result.set_attribute('title', title)
                    widgetImage = card.get('widgetImage', '')
                    
                    case_link_number = card.get('itemId', '')
                    case_link = f"https://36kr.com/p/{case_link_number}" if case_link_number else ""
                    result.set_attribute('case_link', case_link)
                    
                    summary = card.get('content', "")
                    result.set_attribute('summary', summary)
                    
                    AIGC_check = check_AIGCrisk_news(title)
                    other_result = DuplicateDataCase()
                    other_result.set_title(title)
                    other_result.set_url(case_link)
                    other_result.set_is_AIGC(1 if AIGC_check else 0)
                    
                    if AIGC_check:
                        task = asyncio.create_task(process_news_detail(session,case_link, result,widgetImage,case_link_number))#处理新闻详情页
                        #将澎湃新闻中显示的图片加入到图片集中
                        tasks.append(task)
                    other_result = other_result.__json__()
                    other_results.append(other_result)
                    
                    logging.info(f"已爬取标题: {title}")
                except Exception as e:
                    logging.error(f"处理新闻卡片时出错: {e}")
                    continue
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if result and not isinstance(result, Exception):
                        all_results.append(result)
            
            await asyncio.sleep(2)
    
    logging.info(f"36氪关键词 {keyword} 爬取完成")
    return all_results, other_results

def run_scraper(url, keyword, max_pages=5):
    """运行异步爬虫的包装函数"""
    return asyncio.run(scrape_36kr_news(url, keyword, max_pages))


