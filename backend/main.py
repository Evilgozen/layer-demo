from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import List
import uvicorn
from datetime import datetime, timedelta

from database import create_db_and_tables, get_session, User, ChatConversation, ChatMessage
from schemas import UserCreate, UserResponse, Token
from chat_schemas import ConversationCreate, ConversationResponse, ConversationListItem
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
from ai_service import ChatRequest, ChatResponse, generate_ai_response, generate_mock_response

# Create FastAPI app
app = FastAPI(title="Legal Consultation API")

# Configure CORS - specifically allow the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Specifically allow the frontend origin
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list allowed methods
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Explicitly list allowed headers
    expose_headers=["Content-Type"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Add custom headers middleware to help with debugging
@app.middleware("http")
async def add_custom_headers(request, call_next):
    # For preflight OPTIONS requests, return a response immediately
    if request.method == "OPTIONS":
        # Create a response with appropriate headers
        from fastapi.responses import Response
        response = Response(
            content="",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "600",  # Cache preflight for 10 minutes
            },
        )
        return response
    
    # For non-OPTIONS requests, proceed normally
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

# Chat history endpoints
@app.post("/chat/conversations/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate, 
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # Create new conversation
    db_conversation = ChatConversation(
        user_id=current_user.id,
        title=conversation.title
    )
    session.add(db_conversation)
    session.commit()
    session.refresh(db_conversation)
    
    # Add messages to the conversation
    for i, msg in enumerate(conversation.messages):
        db_message = ChatMessage(
            conversation_id=db_conversation.id,
            role=msg.role,
            content=msg.content,
            order=i,
            timestamp=datetime.now()  # Add timestamp if not provided
        )
        session.add(db_message)
    
    session.commit()
    
    # Return the created conversation with messages
    return await get_conversation(db_conversation.id, current_user, session)


@app.get("/chat/conversations/", response_model=List[ConversationListItem])
async def list_conversations(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # Get all conversations for the current user
    conversations = session.exec(
        select(ChatConversation)
        .where(ChatConversation.user_id == current_user.id)
        .order_by(ChatConversation.updated_at.desc())
    ).all()
    
    return conversations


@app.get("/chat/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # Get conversation by ID
    conversation = session.exec(
        select(ChatConversation)
        .where(ChatConversation.id == conversation_id)
        .where(ChatConversation.user_id == current_user.id)
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get all messages for this conversation
    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.order)
    ).all()
    
    # Create response with conversation and messages
    response = ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages
    )
    
    return response


@app.put("/chat/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # Get conversation by ID
    db_conversation = session.exec(
        select(ChatConversation)
        .where(ChatConversation.id == conversation_id)
        .where(ChatConversation.user_id == current_user.id)
    ).first()
    
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update conversation title and timestamp
    if conversation.title is not None:
        db_conversation.title = conversation.title
    db_conversation.updated_at = datetime.now()
    
    # Delete existing messages
    messages_to_delete = session.exec(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
    ).all()
    
    for message in messages_to_delete:
        session.delete(message)
    
    # Add new messages
    for i, msg in enumerate(conversation.messages):
        db_message = ChatMessage(
            conversation_id=db_conversation.id,
            role=msg.role,
            content=msg.content,
            order=i,
            timestamp=datetime.now()  # Add timestamp if not provided
        )
        session.add(db_message)
    
    session.commit()
    session.refresh(db_conversation)
    
    # Return updated conversation
    return await get_conversation(conversation_id, current_user, session)


@app.delete("/chat/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # Get conversation by ID
    conversation = session.exec(
        select(ChatConversation)
        .where(ChatConversation.id == conversation_id)
        .where(ChatConversation.user_id == current_user.id)
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete all messages in the conversation
    session.exec(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
    ).delete()
    
    # Delete the conversation
    session.delete(conversation)
    session.commit()
    
    return {"message": "Conversation deleted successfully"}


# Run the application
if __name__ == "__main__":
    # Use port 8000 to match your frontend configuration
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)