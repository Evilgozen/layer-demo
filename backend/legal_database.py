from sqlmodel import Field, SQLModel
from typing import Optional, List
from datetime import datetime
from database import User

# 法条模型
class LegalArticle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    source: str  # 法律来源，如《民法典》、《劳动法》等
    article_number: str  # 条文编号
    category: str  # 分类，如民法、刑法、劳动法等
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

# 讨论模型
class Discussion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    user_id: int = Field(foreign_key="user.id")
    legal_article_id: Optional[int] = Field(default=None, foreign_key="legalarticle.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

# 评论模型
class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    user_id: int = Field(foreign_key="user.id")
    discussion_id: int = Field(foreign_key="discussion.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

# 扩展用户模型，添加个人资料字段
class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)