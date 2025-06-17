from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from database import get_session, User
from legal_database import LegalArticle, Discussion, Comment, UserProfile
from legal_schemas import (
    LegalArticleCreate, LegalArticleResponse,
    DiscussionCreate, DiscussionResponse,
    CommentCreate, CommentResponse,
    UserProfileResponse, UserProfileUpdate
)
from auth import get_current_active_user

# 创建路由器
router = APIRouter(prefix="/api", tags=["legal"])

# 法条相关路由
@router.post("/legal-articles/", response_model=LegalArticleResponse)
async def create_legal_article(article: LegalArticleCreate, current_user: User = Depends(get_current_active_user), session: Session = Depends(get_session)):
    # 只有管理员可以创建法条
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以创建法条")
    
    db_article = LegalArticle(
        title=article.title,
        content=article.content,
        source=article.source,
        article_number=article.article_number,
        category=article.category,
        created_at=datetime.now()
    )
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    return db_article

@router.get("/legal-articles/", response_model=List[LegalArticleResponse])
async def list_legal_articles(
    category: Optional[str] = None,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    query = select(LegalArticle)
    
    # 应用过滤条件
    if category:
        query = query.where(LegalArticle.category == category)
    if source:
        query = query.where(LegalArticle.source == source)
    if keyword:
        query = query.where(
            (LegalArticle.title.contains(keyword)) | 
            (LegalArticle.content.contains(keyword)) | 
            (LegalArticle.article_number.contains(keyword))
        )
    
    # 分页
    articles = session.exec(query.offset(skip).limit(limit)).all()
    return articles

@router.get("/legal-articles/{article_id}", response_model=LegalArticleResponse)
async def get_legal_article(article_id: int, session: Session = Depends(get_session)):
    article = session.exec(select(LegalArticle).where(LegalArticle.id == article_id)).first()
    if not article:
        raise HTTPException(status_code=404, detail="法条不存在")
    return article

# 讨论相关路由
@router.post("/discussions/", response_model=DiscussionResponse)
async def create_discussion(
    discussion: DiscussionCreate, 
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # 如果关联了法条，检查法条是否存在
    if discussion.legal_article_id:
        article = session.exec(select(LegalArticle).where(LegalArticle.id == discussion.legal_article_id)).first()
        if not article:
            raise HTTPException(status_code=404, detail="关联的法条不存在")
    
    db_discussion = Discussion(
        title=discussion.title,
        content=discussion.content,
        user_id=current_user.id,
        legal_article_id=discussion.legal_article_id,
        created_at=datetime.now()
    )
    session.add(db_discussion)
    session.commit()
    session.refresh(db_discussion)
    
    # 构建响应
    response = DiscussionResponse(
        id=db_discussion.id,
        title=db_discussion.title,
        content=db_discussion.content,
        legal_article_id=db_discussion.legal_article_id,
        user_id=current_user.id,
        username=current_user.username,
        created_at=db_discussion.created_at,
        updated_at=db_discussion.updated_at,
        comments_count=0
    )
    
    return response

@router.get("/discussions/", response_model=List[DiscussionResponse])
async def list_discussions(
    legal_article_id: Optional[int] = None,
    user_id: Optional[int] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    query = select(Discussion)
    
    # 应用过滤条件
    if legal_article_id:
        query = query.where(Discussion.legal_article_id == legal_article_id)
    if user_id:
        query = query.where(Discussion.user_id == user_id)
    if keyword:
        query = query.where(
            (Discussion.title.contains(keyword)) | 
            (Discussion.content.contains(keyword))
        )
    
    # 分页并按创建时间倒序排序
    discussions = session.exec(query.order_by(Discussion.created_at.desc()).offset(skip).limit(limit)).all()
    
    # 构建响应列表
    response_list = []
    for disc in discussions:
        # 获取用户名
        user = session.exec(select(User).where(User.id == disc.user_id)).first()
        username = user.username if user else "未知用户"
        
        # 获取评论数量
        comments_count = session.exec(select(Comment).where(Comment.discussion_id == disc.id)).count()
        
        response_list.append(DiscussionResponse(
            id=disc.id,
            title=disc.title,
            content=disc.content,
            legal_article_id=disc.legal_article_id,
            user_id=disc.user_id,
            username=username,
            created_at=disc.created_at,
            updated_at=disc.updated_at,
            comments_count=comments_count
        ))
    
    return response_list

@router.get("/discussions/{discussion_id}", response_model=DiscussionResponse)
async def get_discussion(discussion_id: int, session: Session = Depends(get_session)):
    discussion = session.exec(select(Discussion).where(Discussion.id == discussion_id)).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="讨论不存在")
    
    # 获取用户名
    user = session.exec(select(User).where(User.id == discussion.user_id)).first()
    username = user.username if user else "未知用户"
    
    # 获取评论数量
    comments_count = session.exec(select(Comment).where(Comment.discussion_id == discussion.id)).count()
    
    return DiscussionResponse(
        id=discussion.id,
        title=discussion.title,
        content=discussion.content,
        legal_article_id=discussion.legal_article_id,
        user_id=discussion.user_id,
        username=username,
        created_at=discussion.created_at,
        updated_at=discussion.updated_at,
        comments_count=comments_count
    )

# 评论相关路由
@router.post("/comments/", response_model=CommentResponse)
async def create_comment(
    comment: CommentCreate, 
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # 检查讨论是否存在
    discussion = session.exec(select(Discussion).where(Discussion.id == comment.discussion_id)).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="讨论不存在")
    
    db_comment = Comment(
        content=comment.content,
        user_id=current_user.id,
        discussion_id=comment.discussion_id,
        created_at=datetime.now()
    )
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    
    # 更新讨论的更新时间
    discussion.updated_at = datetime.now()
    session.add(discussion)
    session.commit()
    
    return CommentResponse(
        id=db_comment.id,
        content=db_comment.content,
        discussion_id=db_comment.discussion_id,
        user_id=current_user.id,
        username=current_user.username,
        created_at=db_comment.created_at,
        updated_at=db_comment.updated_at
    )

@router.get("/discussions/{discussion_id}/comments", response_model=List[CommentResponse])
async def list_comments(
    discussion_id: int,
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    # 检查讨论是否存在
    discussion = session.exec(select(Discussion).where(Discussion.id == discussion_id)).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="讨论不存在")
    
    # 获取评论列表
    comments = session.exec(
        select(Comment)
        .where(Comment.discussion_id == discussion_id)
        .order_by(Comment.created_at)
        .offset(skip)
        .limit(limit)
    ).all()
    
    # 构建响应列表
    response_list = []
    for comment in comments:
        # 获取用户名
        user = session.exec(select(User).where(User.id == comment.user_id)).first()
        username = user.username if user else "未知用户"
        
        response_list.append(CommentResponse(
            id=comment.id,
            content=comment.content,
            discussion_id=comment.discussion_id,
            user_id=comment.user_id,
            username=username,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        ))
    
    return response_list

# 用户个人资料相关路由
@router.get("/users/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user), session: Session = Depends(get_session)):
    # 获取用户个人资料
    profile = session.exec(select(UserProfile).where(UserProfile.user_id == current_user.id)).first()
    
    # 如果用户没有个人资料，创建一个默认的
    if not profile:
        profile = UserProfile(user_id=current_user.id, created_at=datetime.now())
        session.add(profile)
        session.commit()
        session.refresh(profile)
    
    # 获取用户的讨论和评论数量
    discussions_count = session.exec(select(Discussion).where(Discussion.user_id == current_user.id)).count()
    comments_count = session.exec(select(Comment).where(Comment.user_id == current_user.id)).count()
    
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        discussions_count=discussions_count,
        comments_count=comments_count,
        created_at=profile.created_at
    )

@router.put("/users/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    # 获取用户个人资料
    profile = session.exec(select(UserProfile).where(UserProfile.user_id == current_user.id)).first()
    
    # 如果用户没有个人资料，创建一个
    if not profile:
        profile = UserProfile(user_id=current_user.id, created_at=datetime.now())
        session.add(profile)
    
    # 更新个人资料字段
    if profile_update.full_name is not None:
        current_user.full_name = profile_update.full_name
    if profile_update.bio is not None:
        profile.bio = profile_update.bio
    if profile_update.avatar_url is not None:
        profile.avatar_url = profile_update.avatar_url
    
    profile.updated_at = datetime.now()
    
    session.add(current_user)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    session.refresh(current_user)
    
    # 获取用户的讨论和评论数量
    discussions_count = session.exec(select(Discussion).where(Discussion.user_id == current_user.id)).count()
    comments_count = session.exec(select(Comment).where(Comment.user_id == current_user.id)).count()
    
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        discussions_count=discussions_count,
        comments_count=comments_count,
        created_at=profile.created_at
    )