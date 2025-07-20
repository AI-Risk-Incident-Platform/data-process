#这个文件定义了一个函数，用于将图片URL转换为Base64编码

import requests
import base64

def url_to_base64(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        img_data = response.content
        base64_data = base64.b64encode(img_data).decode('utf-8')
        return base64_data
    except requests.RequestException as e:
        print(f"请求图片出错: {e}")
        return None

