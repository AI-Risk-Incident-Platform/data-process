#为了更好地处理新闻数据，定义了一个CaseInfo类来存储和管理新闻案件信息
#该类包含多个属性，如标题、描述、平台、来源、案件链接、发布日期

class CaseInfo:
    def __init__(self, title="", description="", platform="", source="", case_link="", release_date="", location="", involved_subject="", views=0, likes=0, comments=0, case_type="", summary="", tags="",search_keywords="",uploaded_by=0, images=[], videos=[], text_comments=[]):
        self.title = title if title is not None else ""
        self.description = description if description is not None else ""
        self.platform = platform if platform is not None else ""
        self.source = source if source is not None else ""
        self.case_link = case_link if case_link is not None else ""
        self.release_date = release_date if release_date is not None else None
        self.location = location if location is not None else ""
        self.involved_subject = involved_subject if involved_subject is not None else ""
        self.views = views
        self.likes = likes
        self.comments = comments if comments else 0
        self.case_type = case_type if case_type is not None else ""
        self.summary = summary if summary is not None else ""
        self.tags = tags if tags is not None else ""
        self.search_keywords=search_keywords if search_keywords is not None else ""
        self.uploaded_by = uploaded_by
        if images is None:
            self.images = []
        else:
            self.images = images
        if videos is None:
            self.videos = []
        else:
            self.videos = videos
        if text_comments is None:
            self.text_comments = []
        else:
            self.text_comments = text_comments

    def get_all_attributes(self):
        """获取所有属性的值"""
        return {
            "title": self.title,
            "description": self.description,
            "platform": self.platform,
            "source": self.source,
            "case_link": self.case_link,
            "release_date": self.release_date,
            "location": self.location,
            "involved_subject": self.involved_subject,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "case_type": self.case_type,
            "summary": self.summary,
            "tags": self.tags,
            "search_keywords":self.search_keywords,
            "uploaded_by": self.uploaded_by,
            "images": self.images,
            "videos": self.videos,
            "text_comments": self.text_comments
        }

    def set_attribute(self, attribute_name, value):
        """设置指定属性的值"""
        if hasattr(self, attribute_name):
            if value==None:
                setattr(self, attribute_name, getattr(self, attribute_name))
            else:
                setattr(self, attribute_name, value)
        else:
            print(f"不存在名为 {attribute_name} 的属性")
    def __json__(self):
        return {
            "title": self.title,
            "description": self.description,
            "platform": self.platform,
            "source": self.source,
            "case_link": self.case_link,
            "release_date": self.release_date,
            "location": self.location,
            "involved_subject": self.involved_subject,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "case_type": self.case_type,
            "summary": self.summary,
            "tags": self.tags,
            "search_keywords":self.search_keywords,
            "uploaded_by": self.uploaded_by,
            "images": self.images,
            "videos": self.videos,
            "text_comments": self.text_comments
        }