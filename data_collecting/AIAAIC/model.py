from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CaseType(str, Enum):
    news = "news"
    # 可以添加更多的类型
class VideoBase(BaseModel):
    pass
class TextCommentBase(BaseModel):
    pass
# 图片模型
class ImageBase(BaseModel):
    image_name: Optional[str] = Field(
        None, 
        description="The name of the image. Can be left empty if not provided."
    )
    image_url: str = Field(
        ..., 
        description="The URL of the image. This field is required."
    )
    base64_encoding: Optional[str] = Field(
        None, 
        description="The Base64 encoding of the image. Can be left empty if not available."
    )

# 视频表模型
class VideoBase(BaseModel):
    video_url: str = Field(
        ..., 
        max_length=255, 
        description="The URL of the video. This field is required and has a maximum length of 255 characters."
    )

# 文本评论表模型
class TextCommentBase(BaseModel):
    comment_content: str = Field(
        ..., 
        max_length=500, 
        description="The content of the text comment. This field is required and has a maximum length of 500 characters."
    )

# 风险案例表模型
class RiskCaseBase(BaseModel):
    title: str = Field(
        ..., 
        max_length=255, 
        description="The title of the risk case, with a maximum length of 255 characters."
    )
    description: Optional[str] = Field(
        None, 
        description="A detailed description of the risk case. Can be left empty."
    )
    platform: Optional[str] = Field(
        None, 
        description="The platform where the risk case is sourced from. Can be left empty."
    )
    source: Optional[str] = Field(
        None, 
        description="The specific source of the risk case. Can be left empty."
    )
    case_link: Optional[str] = Field(
        None, 
        description="The link to the risk case. Can be left empty."
    )
    release_date: Optional[date] = Field(
        None, 
        description="The release date of the risk case. Can be left empty."
    )
    location: Optional[str] = Field(
        None, 
        description="The location related to the risk case. Can be left empty."
    )
    involved_subject: Optional[str] = Field(
        None, 
        description="The subject involved in the risk case. Can be left empty."
    )
    views: Optional[int] = Field(
        0, 
        description="The number of views of the risk case. Defaults to 0."
    )
    likes: Optional[int] = Field(
        0, 
        description="The number of likes of the risk case. Defaults to 0."
    )
    comments: Optional[int] = Field(
        0, 
        description="The number of comments of the risk case. Defaults to 0."
    )
    case_type: CaseType = Field(
        CaseType.news, 
        description="The type of the risk case. Defaults to 'news'."
    )
    summary: Optional[str] = Field(
        None, 
        description="A summary of the risk case. Can be left empty."
    )
    tags: Optional[str] = Field(
        None, 
        description="Tags associated with the risk case. Can be left empty."
    )
    search_keywords: Optional[str] = Field(
        None, 
        description="Search keywords for the risk case. Can be left empty."
    )

class RiskCaseCreate(RiskCaseBase):
    uploaded_by: int = Field(
        ..., 
        description="The ID of the user who uploaded the risk case."
    )
    images: Optional[List[ImageBase]] = Field(
        None, 
        description="A list containing image information related to the risk case. Can be left empty."
    )
    videos: Optional[List[VideoBase]] = Field(
        None, 
        description="A list containing video information related to the risk case. Can be left empty."
    )
    text_comments: Optional[List[TextCommentBase]] = Field(
        None, 
        description="A list containing text comment information related to the risk case. Can be left empty."
    )