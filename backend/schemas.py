from pydantic import BaseModel, EmailStr
from typing import Optional

# User registration schema
class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None

# User response schema (without password)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool

# Token response schema
class Token(BaseModel):
    access_token: str
    token_type: str

# Token data schema
class TokenData(BaseModel):
    username: Optional[str] = None
