from sqlmodel import Field, Session, SQLModel, create_engine, select, JSON, Column
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

# Create SQLite database file in the current directory
sqlite_file_name = "legal_consultation.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Create the SQLite engine
engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})

# Define User model
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True


# Define ChatMessage model
class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="chatconversation.id")
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    order: int  # To maintain the order of messages in a conversation


# Define ChatConversation model
class ChatConversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Create the database tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Get a database session
def get_session():
    with Session(engine) as session:
        yield session
