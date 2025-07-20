#这个文件定义了一个函数，用于从给定的URL中提取基本的URL（协议和域名）

from urllib.parse import urlparse

def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url