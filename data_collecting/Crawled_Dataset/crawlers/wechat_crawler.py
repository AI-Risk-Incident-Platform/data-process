#给定微信公众号url 进行爬取相关内容
#该文件使用Selenium库进行动态内容的爬取
#爬取内容包括作者、发布时间、文章内容、标签和图片等
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.webdriver.common.by import By
import logging
import time as tm
from crawlers.img_to_base64 import url_to_base64

#目前暂时没有爬取微信公众号中可能的视频 也不存在摘要和浏览量 点赞数 喜欢数 评论

def wechat_crawler(url):
    logging.basicConfig(level=logging.INFO)
    logging.info("程序开始运行")
    #print(url)
    service = Service()
    #注意下载谷歌浏览器驱动并将其添加到环境变量 或者直接复制到python下载界面
    # 创建ChromeOptions对象来设置浏览器相关选项
    wx_result = {}
    chrome_options = ChromiumOptions()
    # 添加无头模式的选项
    chrome_options.add_argument('--headless')
    # 创建Chrome驱动对象，并传入服务和选项
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    tm.sleep(5)
    author_element = driver.find_elements(By.ID, "js_name")
    #print(author_element if author_element else "2")
    source = author_element[0].text if author_element else ""
    wx_result['source'] = source
    #注意 这里的 事件实例中的location指的是事件发生的地点，而不是作者ip的地址 所以以下爬取内容暂不能用
    # location_element = driver.find_elements(By.ID,'js_ip_wording')
    # location=location_element[0].text if location_element else ""
    # wx_result['location'] = location
    release_date_element = driver.find_elements(By.ID, "publish_time")
    release_date = release_date_element[0].text if release_date_element else ""
    wx_result['release_date'] = release_date
    description_element = driver.find_elements(By.ID, "js_content")
    description=description_element[0].text if description_element else ""
    #print(content if content else "1")
    wx_result['description']=description
    tags=""
    tag_elements=driver.find_elements(By.CLASS_NAME,"article-tag__item")
    for index,tag_element in enumerate(tag_elements):
        tag=tag_element.text
        if index!= 0:
            tags += ", "
        tags += tag
    wx_result["tags"]=tags
    images = []
    img_elements = description_element[0].find_elements(By.TAG_NAME, "img")
    for img in img_elements:
        if img.get_attribute('alt') == '图片':
            img_link = img.get_attribute('src')
            if img_link.startswith('http'):
                single_img={"image_name": "",
                            "image_url": "",
                            "base64_encoding": ""
                            }
                base64_encoding=url_to_base64(img_link)
                single_img["image_url"]=img_link
                single_img["base64_encoding"]=base64_encoding
                images.append(single_img)
    
    wx_result['images'] = images  if images else []
    logging.info(f'{url}"对应的微信公众号已爬取完毕"')
    return wx_result