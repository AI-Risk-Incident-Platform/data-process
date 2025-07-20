#这个文件定义了一个函数，用于重试获取Selenium元素
#如果在指定的最大重试次数内未能获取到元素，将会等待一段时间后重试

from selenium.common.exceptions import NoSuchElementException
import time as tm
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
def get_element_with_retry(driver, locator, max_retries=3, retry_interval=60):
    retries = 0
    while retries < max_retries:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(locator)
            )
            return element
        except:
            print(f"第{retries + 1}次尝试获取元素失败，休眠{retry_interval}秒后重试...")
            tm.sleep(retry_interval)
            retries += 1
    print("达到最大重试次数，仍未获取到元素")