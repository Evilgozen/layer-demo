from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class LegalArticleBase(BaseModel):
    """法条基础模型"""
    title: str
    content: str
    source: str  # 法律来源，如《民法典》、《劳动法》等
    article_number: str  # 条文编号
    category: str  # 分类，如民法、刑法、劳动法等


class LegalArticleCreate(LegalArticleBase):
    """创建法条的请求模型"""
    pass


class LegalArticleResponse(LegalArticleBase):
    """法条响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class DiscussionBase(BaseModel):
    """讨论基础模型"""
    title: str
    content: str
    legal_article_id: Optional[int] = None  # 关联的法条ID，可选


class DiscussionCreate(DiscussionBase):
    """创建讨论的请求模型"""
    pass


class DiscussionResponse(DiscussionBase):
    """讨论响应模型"""
    id: int
    user_id: int
    username: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments_count: int = 0

    class Config:
        orm_mode = True


class CommentBase(BaseModel):
    """评论基础模型"""
    content: str
    discussion_id: int


class CommentCreate(CommentBase):
    """创建评论的请求模型"""
    pass


class CommentResponse(CommentBase):
    """评论响应模型"""
    id: int
    user_id: int
    username: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserProfileResponse(BaseModel):
    """用户个人资料响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    discussions_count: int = 0
    comments_count: int = 0
    created_at: datetime

    class Config:
        orm_mode = True


class UserProfileUpdate(BaseModel):
    """更新用户个人资料的请求模型"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None