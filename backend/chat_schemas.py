from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MessageBase(BaseModel):
    role: str
    content: str


class ConversationCreate(BaseModel):
    messages: List[MessageBase]
    title: Optional[str] = None


class MessageResponse(MessageBase):
    id: int
    order: int
    timestamp: datetime

    class Config:
        orm_mode = True


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True


class ConversationListItem(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
