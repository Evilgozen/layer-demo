from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Optional
import os

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

# Create the database tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Get a database session
def get_session():
    with Session(engine) as session:
        yield session
