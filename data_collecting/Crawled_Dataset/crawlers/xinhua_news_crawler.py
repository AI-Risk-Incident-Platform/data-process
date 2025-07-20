#爬取新华网新闻的异步爬虫
#该爬虫使用aiohttp库进行异步请求，使用Selenium处理动态

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time as tm
import logging
import requests
from bs4 import BeautifulSoup
import json
from crawlers.caseinfo import CaseInfo  # 假设 CaseInfo 类定义在名为 your_module.py 的文件中
from crawlers.DuplicateDataCase import DuplicateDataCase
from crawlers.wechat_crawler import wechat_crawler
from crawlers.img_to_base64 import url_to_base64
from crawlers.check_AIGCrisk_title import check_AIGCrisk_news
from crawlers.time_convert import convert_date_format
from crawlers.get_element_with_retry import get_element_with_retry
# 假设这里已经有了新闻的soup，以下是获取body标签id属性的示例代码
def get_body_id(soup):
    try:
        
        body_tag = soup.find('body')  # 查找body标签
        if body_tag:
            body_id = body_tag.get('id')  # 获取body标签的id属性
            return body_id
        return None  # 如果没找到body标签则返回None
    except requests.RequestException as e:
        print(f"请求链接 出现问题: {e}")
        return None
def scrape_xinhua_news(url, keyword, max_pages=5):
    logging.basicConfig(level=logging.INFO)
    logging.info("程序开始运行")
    service = Service()
    #注意下载谷歌浏览器驱动并将其添加到环境变量 或者直接复制到python下载界面
    # 创建ChromeOptions对象来设置浏览器相关选项
    chrome_options = ChromiumOptions()
    # 添加无头模式的选项
    chrome_options.add_argument('--headless')
    # 创建Chrome驱动对象，并传入服务和选项
    driver = webdriver.Chrome(service=service, options=chrome_options)
    all_results = []
    other_results=[]
    logging.info("浏览器开始运行")
    for page in range(1, max_pages + 1):
        search_url = f"{url}/#search/0/{keyword}/{page}/0"
        print(search_url)
        driver.get(search_url)
        tm.sleep(5)
        news_cards = driver.find_elements(By.XPATH, "//div[@class='content']/div[@class='items ']/div")#这里的元素是一个列表

        #！！！！！！ 注意 新华网的相关类名是items ，后面items后面有一个空格！！！！！

        # news_cards = WebDriverWait(driver, 30).until(
        # EC.presence_of_all_elements_located((By.XPATH, "//div[@class='card-margin img-text-card']")))
        if news_cards:#如果可以取到元素，打印1
            print("新华网搜索页面可以取到元素")
            # print(news_cards)
        else:#如果实在取不到元素 打印并前往下一个url
            print("新华网搜索页面取不到元素")
            continue
        for card in news_cards:
            # 创建 CaseInfo 对象
            result = CaseInfo()
            # 添加平台信息 搜索关键词和案例类型
            result.set_attribute('platform','新华网')  
            result.set_attribute('case_type','news')
            result.set_attribute('search_keywords',keyword)
            #暂时用用户id=3做测试
            result.set_attribute('uploaded_by',3)
            # 获取新闻标题（class为title的div内容）
            title_element = card.find_element(By.XPATH, "./div[@class='title']")
            title = title_element.text 
            print(title)
            result.set_attribute('title' , title)
            # 获取超链接
            case_link = title_element.find_element(By.XPATH, "./a").get_attribute('href')
            result.set_attribute('case_link' , case_link)
            print(case_link)
            # 获取新闻描述（如果有）注意 创建的数据库类中 描述是指案例内容 而案例内容的类型名多为content 而在腾讯新闻中 描述是指 案例简介 或是摘要 注意概念的
            try:
                brief_element = card.find_element(By.CSS_SELECTOR, "div.brief")
                summary = brief_element.find_element(By.XPATH, "./div/div[@class='abs']").text
                # 提取新闻来源
                source_element = brief_element.find_element(By.XPATH, "./div/div/div[@class='source']")
                source = source_element.text if source_element else ""
                result.set_attribute('source' , source)
                result.set_attribute('summary' , summary)
                release_date_item=brief_element.find_element(By.XPATH, "./div/div/div[@class='pub-tim']")
                release_date=release_date_item.text if release_date_item else ""
                release_date=convert_date_format(release_date)
                result.set_attribute('release_date',release_date)
                result.set_attribute('location', "")
                #新华网没有标签
                result.set_attribute('tags',"")
            except Exception as e:
                result.set_attribute('summary' , "")
                result.set_attribute('source' , "")
                result.set_attribute('location', "")
                result.set_attribute('tags',"")
            #使用大模型对新闻标题判断一次是否与AI风险相关 返回是，就正常爬取
            #用于判断是否为大模型链接错误
            # print(“正在检查是否为大模型链接错误”)
            AIGC_check=check_AIGCrisk_news(title)
            if AIGC_check:
                is_AIGC=1
            else:
                is_AIGC=0
            other_result=DuplicateDataCase()
            other_result.set_is_AIGC(is_AIGC)
            other_result.set_title(title)
            other_result.set_url(case_link)
            #查看新闻来源是否是微信公众号平台
            # 查看新闻来源是否是微信公众号平台
            if AIGC_check:
                try:
                    info_box = card.find_element(By.CLASS_NAME, "info-box")
                    wx_logo_span = info_box.find_element(By.CLASS_NAME, "wxLogo")
                    if wx_logo_span is not None:
                            # print(wx_logo_span.text)
                            # print(case_link)
                        fromwx = True
                except NoSuchElementException as e:
                        #print(f"未找到微信公众号标识元素，具体错误: {e}")
                    fromwx = False
                
                # 获取微信页面内容
                if fromwx==True:
                    wx_result=wechat_crawler(case_link)
                    result.set_attribute("source",wx_result['source'])
                    result.set_attribute('description',wx_result["description"])
                    #注意 这里的 事件实例中的location指的是事件发生的地点，而不是作者ip的地址 所以以下爬取内容暂不能用
                    # result.set_attribute('location',wx_result['location'])
                    release_date=convert_date_format(wx_result['release_date'])#将时间格式统一起来
                    result.set_attribute('release_date',release_date)
                    result.set_attribute("tags",wx_result["tags"])
                    result.set_attribute('images',wx_result['images'])
                else:
                    headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                    response = requests.get(case_link,headers=headers)
                    response.raise_for_status()  # 检查请求是否成功，若不成功抛出异常
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # 使用soup获取body标签的id属性
                    try:
                        body_id = get_body_id(soup)
                        if body_id and (body_id == "dc-video-body" or body_id == "dc-live-body"):
                            video = True
                        else:
                            video = False
                    except Exception as e:
                        print(f"获取body标签id属性时出现问题: {e}")
                        video = False
                    #如果不是视频，提取这些要素
                    if video==False: 

                        description_element=soup.find('span',id="detailContent") if soup.find('span',id="detailContent") else None
                        description=""
                        if description_element:
                           # 提取所有子标签的文本内容，并用换行符连接
                            texts = []
                            for child in description_element.children:
                                if child.name:  # 确保是标签
                                    texts.append(child.get_text(strip=True))
                            description = "\n".join(texts)
                            description = description_element.text
                        result.set_attribute('description',description)
                        #提取新闻内容中的图片
                        #提取图片链接
                        img_elements = description_element.select("img")
                        #print(img_elements if img_elements else "1")
                        images = []
                        for img in img_elements:
                            #print(img if img else "1")
                            # if  'alt' in img.attrs and img['alt'] == '图片':
                            case_link_deal = case_link.replace("c.html", "", 1)
                            img_link = case_link_deal+img['src']
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
                        # script_tags = soup.find_all('script')
                        # for script_tag in script_tags:
                        #     if script_tag.string:
                        #         if "window.DATA" in script_tag.string:  # 根据关键字筛选
                        #             target_script = script_tag
                        #             break
                        # if target_script:
                        #     content = target_script.string
                        #     content = content.replace('window.DATA = ', '')  # 去掉前面的定义部分，只保留类似JSON格式的内容
                        #     content=str(content)#在获取内容前后加单引号 使其成为字符串
                        #     # 去掉末尾分号
                        #     content = content.strip()
                        #     content=content.rstrip(';')
                        #     #print(content)
                        #     try:
                        #         data_dict = json.loads(content)
                        #         #注意 这里的 事件实例中的location指的是事件发生的地点，而不是作者ip的地址 所以以下爬取内容暂不能用
                        #         #result.set_attribute('location', data_dict['userAddress'])
                        #         release_date=convert_date_format(data_dict['pubtime'])
                        #         result.set_attribute('release_date' ,release_date)
                        #         result.set_attribute('tags',data_dict['tag_info_item']) 
                        #     except json.JSONDecodeError as e:
                        #         print(f"解析JSON数据出现问题: {e}")
                        #         result.set_attribute('location', "")
                        #         result.set_attribute('release_date', "")
                        #         result.set_attribute('tags',"")
                        # else:
                        #     #result.set_attribute('location', "")
                        #     result.set_attribute('release_date', "")
                        #     result.set_attribute('tags',"")
                    else:
                    #如果是视频 提取其中的script的信息
                        target_script = None
                        script_tags = soup.find_all('script')
                        # result.set_attribute('images',[])
                        for script_tag in script_tags:
                            if script_tag.string:
                                if "window.DATA" in script_tag.string:  # 根据关键字筛选
                                    target_script = script_tag
                                    break
                        if target_script:
                            content = target_script.string
                            content = content.replace('window.DATA = ', '')  # 去掉前面的定义部分，只保留类似JSON格式的内容
                            content=str(content)#在获取内容前后加单引号 使其成为字符串
                            # 去掉末尾分号
                            content = content.strip()
                            content=content.rstrip(';')
                            #print(content)
                            try:
                                data_dict = json.loads(content)
                                result.set_attribute('source' ,data_dict['media'])
                                release_date=convert_date_format(data_dict['pubtime'])
                                images = []
                                img_link=data_dict['shareImg']
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
                                #视频新闻 只取封面图片
                                result.set_attribute('release_date' ,release_date)
                                #注意 数据类型中的案例内容 键名是description
                                description=data_dict.get('content',"")
                                result.set_attribute('description',description)
                                if 'tags' in data_dict:
                                    tags = data_dict['tags']
                                else:
                                    tags = ""
                                result.set_attribute('tags',tags)
                            except json.JSONDecodeError as e:
                                print(f"解析JSON数据出现问题: {e}")
                                result.set_attribute('source', "")
                                result.set_attribute('release_date', "")
                                result.set_attribute('images',[])
                                result.set_attribute('description',"")
                                result.set_attribute('tags',"")
                        else:
                            result.set_attribute('source', "")
                            result.set_attribute('release_date', "")
                            result.set_attribute('description',"")
                            result.set_attribute('tags',"")
                result=result.__json__()
                all_results.append(result)
                    # link直接获取的响应中没有评论 需要另外找一个网页     
                    # # 提取评论部分
                    # comment_section = soup.find_all(By.ID, "Comment")
                    # comments = []
                    # comment_items = comment_section.find_all(By.CLASS_NAME, "qqcom-comment-item")
                    # for item in comment_items:
                    #     comment = {}
                    #     try:
                    #         # 提取评论人名称
                    #         commenter_name_element = item.find_all(By.CSS_SELECTOR, "span.qqcom-comment-user-nick.main-user")
                    #         commenter_name = commenter_name_element.text
                    #         comment['commenter_name'] = commenter_name
                    #         # 提取评论内容
                    #         comment_content_element = item.find_all(By.CSS_SELECTOR, "div.qnc-comment__content-container")
                    #         comment_content = comment_content_element.text
                    #         comment['comment_content'] = comment_content
                    #         # 提取评论时间
                    #         comment_time_element = item.find_all(By.CSS_SELECTOR, "div.qnc-comment__time-location:not([class*='qnc-comment__time-location-text'])")
                    #         comment_time = comment_time_element.text
                    #         comment['comment_time'] = comment_time
                    #     except Exception as e:
                    #         comment['commenter_name'] = None
                    #         comment['comment_content'] = None
                    #         comment['comment_time'] = None
                    #     comments.append(comment)
                    # result['comments'] = comments
                #将caseinfo类型转换为json格式 方便存储和处理
            #result=result.__json__()
            other_result=other_result.__json__()
            # all_results.append(result)
            other_results.append(other_result)
            logging.info("已爬取标题为"+title+"的信息")
    driver.quit()
    logging.info(f"新华网关键词{keyword}已爬取完毕")
    return all_results,other_results
