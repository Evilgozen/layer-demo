from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import List
import uvicorn

from database import create_db_and_tables, get_session, User
from schemas import UserCreate, UserResponse, Token
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str
from auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user
)
from ai_service import ChatMessage, ChatRequest, ChatResponse, generate_ai_response, generate_mock_response
from datetime import timedelta

# Create FastAPI app
app = FastAPI(title="Legal Consultation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom headers middleware to help with debugging
@app.middleware("http")
async def add_custom_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Server-Status"] = "Running"
    return response

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Legal Consultation API"}

# User registration endpoint
@app.post("/users/", response_model=UserResponse)
@app.post("/register", response_model=UserResponse)  # Alternative endpoint for registration
async def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Check if user with same email exists
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username is taken
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# JSON login endpoint for authentication
@app.post("/login", response_model=Token)
async def login_json(login_data: LoginRequest, session: Session = Depends(get_session)):
    user = authenticate_user(session, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user info
@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# AI consultation endpoint
@app.post("/ai/chat", response_model=ChatResponse)
async def consult_ai(request: ChatRequest, current_user: User = Depends(get_current_active_user)):
    return await generate_ai_response(request)

# Alternative AI consultation endpoint (keeping for backward compatibility)
@app.post("/ai/consult/", response_model=ChatResponse)
async def consult_ai_alt(request: ChatRequest, current_user: User = Depends(get_current_active_user)):
    return await generate_ai_response(request)

# Mock AI response endpoint (for testing)
@app.post("/ai/mock-chat")
@app.post("/ai/mock-consult/")
async def mock_consult(messages: List[ChatMessage], current_user: User = Depends(get_current_active_user)):
    response = generate_mock_response(messages)
    return {"response": response}

# Run the application
if __name__ == "__main__":
    # Use port 8000 to match your frontend configuration
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)