from datetime import datetime
from typing import Optional
from sqlalchemy import INTEGER, String, Text, TIMESTAMP, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from models.news import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
        comment="用户ID"
    )
    
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名"
    )
    
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码（加密存储）"
    )
    
    bio: Mapped[Optional[str]] = mapped_column(
        String(500),
        default="这个人很懒，什么都没留下",
        comment="个人简介"
    )
    
    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),
        default="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
        comment="头像URL"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.now,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Favorite(Base):
    """收藏模型"""
    __tablename__ = "favorite"
    
    __table_args__ = (
        Index('idx_user_news', 'user_id', 'news_id', unique=True),
    )
    
    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
        comment="收藏ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="用户ID"
    )
    
    news_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey('news.id', ondelete='CASCADE'),
        nullable=False,
        comment="新闻ID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.now,
        comment="收藏时间"
    )
    
    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, news_id={self.news_id})>"


class History(Base):
    """浏览历史模型"""
    __tablename__ = "history"
    
    __table_args__ = (
        Index('idx_user_news_history', 'user_id', 'news_id'),
    )
    
    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
        comment="历史记录ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="用户ID"
    )
    
    news_id: Mapped[int] = mapped_column(
        INTEGER,
        ForeignKey('news.id', ondelete='CASCADE'),
        nullable=False,
        comment="新闻ID"
    )
    
    viewed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.now,
        comment="浏览时间"
    )
    
    def __repr__(self):
        return f"<History(user_id={self.user_id}, news_id={self.news_id})>"
