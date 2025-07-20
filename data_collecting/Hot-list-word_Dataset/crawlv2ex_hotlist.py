#这个文件是用来爬取v2ex热搜榜单的

import asyncio
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
import re
import json

async def search_v2ex_dayhotlist(date):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"https://github.com/lonnyzhang423/v2ex-hot-hub/blob/main/archives/{date}.md",
        )
        #print(result.markdown)
        if result.success:
            
            pattern = r"# v2ex热议话题\n(.*?)(?=## Footer)"
            match = re.search(pattern, result.markdown, re.DOTALL)
            #print(match)
            if match:
                v2ex_hottalk_list = match.group(1).strip().split("\n")
                v2ex_hottalk = v2ex_hottalk_list[2:]
                #print(v2ex_hottalk)
                v2ex_hottalk = [
                    {
                        "title": re.search(r"\[(.*?)\]", item).group(1) if re.search(r"\[(.*?)\]", item) else item.strip().split(". ", 1)[-1],
                        "url": re.search(r"\<(.*?)\>", item).group(1) if re.search(r"\<(.*?)\>", item) else ""
                    }
                    for item in v2ex_hottalk
                ]
                #print(v2ex_hottalk)
            else:
                v2ex_hottalk=[]
            return v2ex_hottalk 
        else:
            print(type(result.markdown))
            print(f"{date}爬取Error:", result.error_message)
async def fetch_v2ex_hotlist(start_date, end_date):
    start_year = start_date.year
    start_month = start_date.month
    start_day = start_date.day
    end_year = end_date.year
    end_month = end_date.month
    end_day = end_date.day
    start_date = datetime(start_year, start_month, start_day)
    end_date = datetime(end_year, end_month, end_day)
    current_date = start_date
    hotlist_dict = {}

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(type(date_str))
        print(f"Fetching hotlist for {date_str}")
        hotlist = await search_v2ex_dayhotlist(date_str)
        if hotlist:
            hotlist_dict[date_str]=[]
            for title in hotlist:
                hotlist_dict[date_str].append({"title": title, "is_AIGC": False})
        current_date += timedelta(days=1)
    
    return hotlist_dict

# 调用函数获取去年的微博热搜榜单
start_date = datetime(2021, 1, 6)
end_date = datetime(2025, 3, 5)
hotlist_dict = asyncio.run(fetch_v2ex_hotlist(start_date, end_date))
# hotlist_dict = asyncio.run(search_douyin_dayhotlist("2024-01-01"))

# 将结果保存为JSON文件
with open(f"v2ex_hotlist.json", "w", encoding="utf-8") as json_file:
    json.dump(hotlist_dict, json_file, ensure_ascii=False, indent=4)

print(f"v2ex热搜榜单已保存为 v2ex_hotlist.json")