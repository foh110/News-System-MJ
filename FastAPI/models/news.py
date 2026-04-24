

from datetime import datetime
from typing import Optional

from sqlalchemy import DATETIME, TIMESTAMP, Index, Integer, Text, ForeignKey, DateTime, INTEGER

# 导入 ORM 核心组件
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import INTEGER, String


# ========== 声明式基类 ==========
# DeclarativeBase 是 SQLAlchemy 2.0 的声明式基类
# 所有模型类都继承自它，用于将 Python 类映射到数据库表
class Base(DeclarativeBase):

    pass


# ========== 新闻分类模型 ==========
class Category(Base):

    # 指定数据库表名
    __tablename__ = "news_category"

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
        autoincrement=True,
        comment="分类id"
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="分类名称"
    )
    
    # sort_order 字段 - 排序顺序
    # default=0 - 默认值为0
    sort_order: Mapped[int] = mapped_column(
        INTEGER,
        default=0,
        nullable=False,
        comment="排序"
    )
    
    # created_at 字段 - 创建时间
    # TIMESTAMP - 时间戳类型（对应 MySQL 的 TIMESTAMP）
    # nullable=True - 允许为空
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="创建时间"
    )
    
    # updated_at 字段 - 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="更新时间"
    )
    
    # ========== 魔法方法 ==========
    def __repr__(self):

        return f"<Category(id={self.id}, name={self.name}, sort_order={self.sort_order})>"

class News(Base):
    __tablename__ = "news"

    # 创建索引：提升查询速度
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'),  # 分类外键索引（高频查询）
        Index('idx_publish_time', 'publish_time'),     # 发布时间索引（按时间排序）
    )

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True, comment="新闻ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")
    description: Mapped[Optional[str]] = mapped_column(String(500), comment="新闻简介")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")
    image: Mapped[Optional[str]] = mapped_column(String(255), comment="封面图片URL")
    author: Mapped[Optional[str]] = mapped_column(String(50), comment="作者")
    category_id: Mapped[int] = mapped_column(INTEGER, ForeignKey('news_category.id'), nullable=False)
    views: Mapped[int] = mapped_column(INTEGER, default=0, nullable=False, comment="浏览量")
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")

    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', views={self.views})>"

