# 这个文件定义了一个DuplicateDataCase类，用于存储和处理重复数据的案例信息
# 该类包含新闻链接、标题和是否与AIGC风险相关的属性

class DuplicateDataCase:
    def __init__(self, news_link="", title="", is_AIGC=""):
        """
        初始化DuplicateDataCase类的实例

        参数:
        url (str): 数据对应的网址
        title (str): 数据的标题
        is_aigc_risk (bool): 表示该数据是否与AIGC风险相关，True表示相关，False表示不相关
        """
        self.url = news_link
        self.title = title
        self.is_AIGC = is_AIGC

    def __json__(self):
        """
        将类的实例转换为字典形式，方便后续进行序列化等操作

        返回:
        dict: 包含类实例属性的字典，键分别为'url'、'title'、'is_AIGC'
        """
        return {
            "news_link": self.news_link,
            "title": self.title,
            "is_AIGC": self.is_AIGC
        }

    def set_url(self, new_url):
        """
        设置新的网址

        参数:
        new_url (str): 要设置的新网址
        """
        self.news_link = new_url

    def get_url(self):
        """
        获取当前的网址

        返回:
        str: 当前实例的网址属性值
        """
        return self.news_link

    def set_title(self, new_title):
        """
        设置新的标题

        参数:
        new_title (str): 要设置的新标题
        """
        self.title = new_title

    def get_title(self):
        """
        获取当前的标题

        返回:
        str: 当前实例的标题属性值
        """
        return self.title

    def set_is_AIGC(self, is_AIGC):
        """
        设置是否与AIGC风险相关的状态

        参数:
        new_is_aigc_risk (bool): 要设置的新状态，True表示相关，False表示不相关
        """
        self.is_AIGC = is_AIGC

    def get_is_AIGC(self):
        """
        获取当前是否与AIGC风险相关的状态

        返回:
        bool: 当前实例的is_aigc_risk属性值
        """
        return self.is_AIGC