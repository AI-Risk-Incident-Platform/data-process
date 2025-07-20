#该文件是为了获取CommonCrawl的新闻数据 文件为wrac格式，下载指定年份，下载至指定文件夹
#注意根据实际情况 修改并添加数据保存地址和新闻获取年份 这一版已将其注释
import requests
import os
import time
import gzip
from io import BytesIO
import random

def download_file(url, local_path, retry_interval):
    while True:
        try:
            local_file_size=0
            # 检查本地文件是否已经存在
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
                    # 设置请求头，从本地文件的末尾开始下载
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
    # 指定要下载到的新闻年份  注意修改 
    year = "2022"
    for month in range(1, 13):
        url = f"https://data.commoncrawl.org/crawl-data/CC-NEWS/{year}/{month:02d}/warc.paths.gz"
        file_paths = get_warc_file_paths(url)
        base_url = 'https://data.commoncrawl.org/'
        # 指定要下载到的特定硬盘挂载目录  注意修改 

        specific_mount_point = '/target_data'
        save_folder = 'downloads'

        for file_path in file_paths:
            time1 = time.time()
            file_url = base_url + file_path
            local_path = os.path.join(specific_mount_point, save_folder, year, str(month), os.path.basename(file_path))
            retry_interval = random.randint(10, 30)
            download_file(file_url, local_path,retry_interval)
            time2 = time.time()
            print(f"下载 {file_path} 完成，耗时 {time2 - time1:.2f} 秒。")