#爬取澎湃网新闻的异步爬虫
#该爬虫使用aiohttp库进行异步请求，使用Selenium处理动态

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time as tm
import logging
import requests
from bs4 import BeautifulSoup
import json
from crawlers.caseinfo import CaseInfo  # 假设 CaseInfo 类定义在名为 your_module.py 的文件中
from crawlers.DuplicateDataCase import DuplicateDataCase
from crawlers.img_to_base64 import url_to_base64
from crawlers.check_AIGCrisk_title import check_AIGCrisk_news
from crawlers.time_convert import convert_date_format

# 假设这里已经有了新闻的soup，以下是获取body标签id属性的示例代码

def judge_video(soup):
        body_tag = soup.find('div', class_='header_videoWrap__TJQwg')  # 查找body标签
        if body_tag:
            # body_id = body_tag.get('id')  # 获取body标签的id属性
            return True  # 如果找到body标签则返回True
        else: 
            return False  # 如果未找到body标签则返回False
    

def scrape_thepaper_news(url, keyword, max_pages=5):
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
    search_url = f"{url}/searchResult?id={keyword}"
    driver.get(search_url)
    tm.sleep(5)
    for i in range(max_pages):
        # 滚动到页面底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 等待新内容加载（可以根据实际情况调整等待时间或使用显式等待）
        tm.sleep(2)  # 固定等待 2 秒
        print(f"已下划{i}次")
    #等待一段时间 用以使内容全部显示
    tm.sleep(8)
    # 定位新闻卡片
    news_cards = driver.find_elements(By.XPATH, "//div[@class='index_searchresult__KNmSI']//ul//li")
    if news_cards!="":
        print("news_cards")
    for card in news_cards:
        # 创建 CaseInfo 对象
        result = CaseInfo()
        # 添加平台信息 搜索关键词和案例类型
        result.set_attribute('platform','澎湃新闻')  
        result.set_attribute('case_type','news')
        result.set_attribute('search_keywords',keyword)
        #暂时用用户id=3做测试
        result.set_attribute('uploaded_by',3)
        # 获取新闻标题（class为title的元素内容）
        title_element = card.find_element(By.XPATH, "./div/a/h2")
        title = title_element.text 
        print(title)
        result.set_attribute('title' , title)
        # 获取超链接
        case_link = card.find_element(By.XPATH, "./div/a").get_attribute('href')
        #case_link=url+case_link
        result.set_attribute('case_link' , case_link)
        print(case_link)
        # 获取新闻描述（如果有）注意 创建的数据库类中 描述是指案例内容 而案例内容的类型名多为content 而在腾讯新闻中 描述是指 案例简介 或是摘要 注意概念的
        try:
            summary = card.find_element(By.XPATH, ".//p[1]").text
            result.set_attribute('summary' , summary)
        except Exception as e:
            result.set_attribute('summary' , "")
        #使用大模型对新闻标题判断一次是否与AI风险相关 返回是，就正常爬取
        AIGC_check=check_AIGCrisk_news(title)
        if AIGC_check:
            is_AIGC=1
        else:
            is_AIGC=0
        other_result=DuplicateDataCase()
        other_result.set_is_AIGC(is_AIGC)
        other_result.set_title(title)
        other_result.set_url(case_link)
        
        # 查看是否为AI相关内容
        if AIGC_check:
        #澎湃新闻不会由有关微信公众号的相关内容 因此可以不用判断
            # info_box = card.find_element(By.CLASS_NAME, "info-box")
            # if info_box:
            #     try:
            #         wx_logo_span = info_box.find_element(By.CLASS_NAME, "wxLogo")
            #         if wx_logo_span is not None:
            #             # print(wx_logo_span.text)
            #             # print(case_link)
            #             fromwx = True
            #     except NoSuchElementException as e:
            #         #print(f"未找到微信公众号标识元素，具体错误: {e}")
            #         fromwx = False
            # else:
            #     fromwx = False
            # 获取微信页面内容
            # if fromwx==True:
            #     wx_result=wechat_crawler(case_link)
            #     result.set_attribute("source",wx_result['source'])
            #     result.set_attribute('description',wx_result["description"])
            #     #注意 这里的 事件实例中的location指的是事件发生的地点，而不是作者ip的地址 所以以下爬取内容暂不能用
            #     # result.set_attribute('location',wx_result['location'])
            #     release_date=convert_date_format(wx_result['release_date'])#将时间格式统一起来
            #     result.set_attribute('release_date',release_date)
            #     result.set_attribute("tags",wx_result["tags"])
            #     result.set_attribute('images',wx_result['images'])
            
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
            response = requests.get(case_link,headers=headers)
            response.raise_for_status()  # 检查请求是否成功，若不成功抛出异常
            soup = BeautifulSoup(response.text, 'html.parser')
            #print(soup.prettify())
            # 判断是否为视频
            judgevideo = judge_video(soup)
            if judgevideo==False:
            #如果不是视频 提取其中的body的信息
                #提取新闻内容
                description_element=soup.select('div.index_cententWrap__Jv8jK')
                #print( description_element if  description_element else "3")
                # content_element=content_divs[0].find_all('div', class_="rich_media_content") if content_divs else None
                # 提取所有子标签的文本内容，并用换行符连接
                if description_element:
                    texts = []
                    for child in description_element[0].children:
                        if child.name:  # 确保是标签
                            texts.append(child.get_text(strip=True))
                    description = "\n".join(texts)
                if description==None:
                    print("1")
                result.set_attribute('description',description)
                
                #提取新闻内容中的图片
                #提取图片链接
                img_elements = description_element[0].select("img")
                #print(img_elements if img_elements else "1")
                images = []
                for img in img_elements:
                    #print(img if img else "1")
                    if  'alt' in img.attrs :
                        img_link = img['src']
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
                target_script = None
                target_script = soup.find('script',id="__NEXT_DATA__")
                # for script_tag in script_tags:
                #     target_script = script_tag
                            
                if target_script:
                    content = target_script.string
                    #澎湃新闻中不需要去除了
                    # content = content.replace('window.DATA = ', '')  # 去掉前面的定义部分，只保留类似JSON格式的内容
                    content=str(content)#在获取内容前后加单引号 使其成为字符串
                    # 去掉末尾分号
                    content = content.strip()
                    # content=content.rstrip(';')
                    #print(content)
                    try:
                        data_dict = json.loads(content)
                        #注意 这里的 事件实例中的location指的是事件发生的地点，而不是作者ip的地址 所以以下爬取内容暂不能用
                        #result.set_attribute('location', data_dict['userAddress'])

                        #得到新闻时间
                        release_date=convert_date_format(data_dict.get('props', {}).get('pageProps', {}).get('detailData', {}).get('contentDetail', {}).get('pubTime', ""))
                        result.set_attribute('release_date' ,release_date)
                        #得到新闻来源
                        result.set_attribute('source' ,data_dict.get('props', {}).get('pageProps', {}).get('detailData', {}).get('contentDetail', {}).get('nodeInfo', {}).get("name",""))
                        #得到新闻标签
                        result.set_attribute('tags',data_dict.get('props', {}).get('pageProps', {}).get('detailData', {}).get('contentDetail', {}).get('tags', '')) 
                    except json.JSONDecodeError as e:
                        print(f"解析JSON数据出现问题: {e}")
                        #result.set_attribute('location', "")
                        result.set_attribute('release_date', "")
                        result.set_attribute('source', "")
                        result.set_attribute('tags',"")
                else:
                    #result.set_attribute('location', "")
                    result.set_attribute('release_date', "")
                    result.set_attribute('source', "")
                    result.set_attribute('tags',"")
                #获取新闻的url 通过其最后的新闻标识号来获取新闻 使用反斜杠 获取url最后一部分 随后再通过_分割来获取新闻id
                parts = case_link.split('/')
                comment_part = parts[-1] if len(parts) > 1 else ""
                # 进一步提取数字部分
                if comment_part:
                    comment_id = comment_part.split('_')[-1]
                
                #获取新闻评论 初始化评论数和评论内容
                commentssort=[1,2]
                comments_count=0
                text_comments=[]
                #"commentSort":1表示爬取热评论 2表示爬取新评论 将两个评论合并 并爬取前10页的评论
                for page in range(1,11):
                    comments_count_hot_page,text_comments_hot_page=get_thepaper_news_comments(comment_id,commentssort[0],page)
                    comments_count_new_page,text_comments_new_page=get_thepaper_news_comments(comment_id,commentssort[1],page)
                    comments_count+=comments_count_hot_page+comments_count_new_page
                    text_comments+=text_comments_hot_page+text_comments_new_page
                result.set_attribute("comments",comments_count)
                print(comments_count)
                result.set_attribute("text_comments",text_comments)
            else:
            #如果是视频 提取其中的script的信息
                target_script = None
                target_script = soup.find('script',id="__NEXT_DATA__")
                # result.set_attribute('images',[])
                if target_script:
                    content = target_script.string
                    content=str(content)#在获取内容前后加单引号 使其成为字符串
                    # 去掉末尾分号
                    content = content.strip()
                    #print(content)
                    try:
                        data_dict = json.loads(content)
                        result.set_attribute('source' ,data_dict['props']['pageProps']['detailData']['contentDetail']['nodeInfo']['name'])
                        release_date=convert_date_format(data_dict['props']['pageProps']['detailData']['contentDetail']['pubTime'])
                        description=data_dict['props']['pageProps']['detailData']['contentDetail']['summary']
                        images = []
                        img_link=data_dict['props']['pageProps']['detailData']['contentDetail']['pic']
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
                        result.set_attribute('description',description)
                        tags=data_dict['props']['pageProps']['detailData']['contentDetail']['tags']
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
                    result.set_attribute('images',[])
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
    logging.info(f"澎湃新闻关键词{keyword}已爬取完毕")
    return all_results,other_results
def get_thepaper_news_comments(comment_id,hot_or_new,pageNum=1):
    #目前获取评论只考虑正常新闻内容 来源是微信公众号和视频内容暂不考虑爬取评论

    #考虑到新闻的评论数较少 只爬取澎湃新闻的显示出来的新评论和热评论 查看全部评论似乎需要登录
    #只爬取两层评论 也即爬取评论 子评论 不再继续爬取子评论的子评论
    #注意 有些评论的url中没有新闻id 他们的新闻id在负载中
    comment_url="https://api.thepaper.cn/comment/news/comment/talkList"
    headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "content-type":"application/json"
            }
    data = {"contId":comment_id,"pageSize":20,"commentSort":hot_or_new,"contType":1,"pageNum":pageNum}

    response = requests.post(comment_url, headers=headers, json=data)
    
    # data=response.json()
    # print(response.json())
    # print(data.get("data",{}).get("list",[]))
    if response.status_code == 200:
        try:
            comments = response.json()
            if comments.get("code") == 200:
                comments_list = comments.get("data", {}).get("list", [])
                if comments_list==[]:
                    return 0,[]
                    #空列表表示没有评论
            else:
                print("获取评论失败，错误信息:", comments.get("msg"))
        except ValueError:
            print("响应数据格式错误")
    else:
        print("请求失败，状态码:", response.status_code)
    #这里注意，如果有子评论 我们只爬取一级子评论，对更多的子评论不做爬取 实际发现 total的统计数量只有一级评论 不包括子评论 因此评论数量通过计数获取。  此外 爬取评论时 由于数据库的格式设置和对接问题 我们不保留评论之间的结构 全部平铺到一个列表中
    #comment_count=int(comment_data["comments"]["count"])
    response.raise_for_status()  # 如果状态码不是200，抛出HTTPError异常
    comments = response.json()
    comment_count=0
    text_comments=[]
    comment_list=comments.get("data",{}).get("list",[])
    for comment_element in comment_list:#爬取的每一个一级评论
        comment_content = comment_element.get("content", "")
        if  comment_content!="":
            text_comment={"comment_content":comment_content}
            text_comments.append(text_comment)
            comment_count+=1
        comment_replycomments=comment_element.get("commentReply",[])#获取爬取的子评论
        if comment_replycomments!=[] and comment_replycomments!=None:
            for comment_replycomment in comment_replycomments:
                replycomment_content=comment_replycomment.get("content","")
                if replycomment_content!="":
                    text_comment={"comment_content":replycomment_content}
                    text_comments.append(text_comment)
                    comment_count+=1
    return comment_count,text_comments