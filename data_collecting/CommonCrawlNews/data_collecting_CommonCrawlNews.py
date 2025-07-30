#该文件是为了获取CommonCrawl的新闻数据 文件为wrac格式，下载指定年份，下载至指定文件夹
#注意根据实际情况 修改并添加数据保存地址和新闻获取年份 这一版已将其注释

import requests
import os
import time
import gzip
from io import BytesIO
import random
import configparser

def download_file(url, local_path, retry_interval):
    while True:
        try:
            local_file_size = 0
            if os.path.exists(local_path):
                local_file_size = os.path.getsize(local_path)
                # 发送一个 HEAD 请求来获取远程文件的大小
                head_response = requests.head(url)
                head_response.raise_for_status()
                remote_file_size = int(head_response.headers.get('Content-Length', 0))

                if local_file_size == remote_file_size:
                    print(f"文件 {local_path} 已经完整下载，跳过。")
                    break
                else:
                    print(f"文件 {local_path} 未完整下载，继续下载。")
                    headers = {'Range': f'bytes={local_file_size}-'}
            else:
                headers = {}

            print(f"开始下载文件 {url} 到 {local_path} ...")
            response = requests.get(url, stream=True, headers=headers)
            response.raise_for_status()
                        # 处理不同响应状态码
            if response.status_code == 206:
                print(f"从字节 {local_file_size} 处继续下载...")
            elif response.status_code == 200 and local_file_size == 0:
                print("从头开始下载...")
            else:
                print(f"不支持的响应状态码: {response.status_code}")
                break
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            with open(local_path, 'ab' if headers else 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            print(f"文件 {local_path} 下载成功。")
            break
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP 错误发生: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"请求错误发生: {req_err}")
        except Exception as e:
            print(f"发生未知错误: {e}")

        print(f"将在 {retry_interval} 秒后重试下载 {url} ...")
        time.sleep(retry_interval)

def get_warc_file_paths(index_url):
    """获取所有 WARC 文件路径"""
    while True:
        try:
            print(f"正在下载索引文件 {index_url} ...")
            response = requests.get(index_url)
            response.raise_for_status()
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                file_paths = [line.decode('utf-8').strip() for line in gz]
            print(f"索引文件下载完成，共 {len(file_paths)} 个文件路径。")
            return file_paths
        except Exception as e:
            print(f"获取 WARC 文件路径失败: {e}")
            retry_interval = random.randint(10, 30)
            print(f"将在 {retry_interval} 秒后重试下载索引文件 {index_url} ...")
            time.sleep(retry_interval)

if __name__ == "__main__":
    # 读取配置文件
    config = configparser.ConfigParser()
    config.read("config.ini")
    cc_config = config["CommonCrawl"]
    year = cc_config.get("year", "2022")
    months_str = cc_config.get("months", "1,2,3,4,5,6,7,8,9,10,11,12")
    months = [int(m.strip()) for m in months_str.split(",")]
    download_dir = cc_config.get("download_dir", "/data3/downloads")
    base_url = cc_config.get("base_url", "https://data.commoncrawl.org/")

    for month in months:
        url = f"{base_url}crawl-data/CC-NEWS/{year}/{month:02d}/warc.paths.gz"
        file_paths = get_warc_file_paths(url)
        for file_path in file_paths:
            time1 = time.time()
            file_url = base_url + file_path
            local_path = os.path.join(download_dir, year, f"{month:02d}", os.path.basename(file_path))
            retry_interval = random.randint(10, 30)
            download_file(file_url, local_path, retry_interval)
            time2 = time.time()
            print(f"下载 {file_path} 完成，耗时 {time2 - time1:.2f} 秒。")