"""
CRUD 操作模块 - news.py

功能：封装数据库的增删改查操作（Create, Read, Update, Delete）

SQLAlchemy 异步查询说明：
- 所有数据库操作都是异步的，使用 async/await 语法
- select() 用于构建查询语句
- db.execute() 执行查询
- result.scalars().all() 获取结果列表

学习要点：
1. SQLAlchemy ORM 核心概念
   - Model: 数据模型类（对应数据库表）
   - Session: 数据库会话（管理事务）
   - Statement: SQL 语句（select/insert/update/delete）

2. 异步操作语法
   - async def: 定义异步函数
   - await: 等待异步操作完成
   - async with: 异步上下文管理器
"""

# 导入异步数据库会话类型
from sqlalchemy.ext.asyncio import AsyncSession
# 导入 SQLAlchemy 查询构建器
from sqlalchemy import select, func, update
# 导入数据模型（Category 类对应 news_category 表）
from models.news import Category,News


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()  # ✅ 补充 return 语句


async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    # 查询指定分类下的新闻
    stmt = select(News).where(News.category_id == category_id).order_by(News.publish_time.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_news_count(db: AsyncSession, category_id: int):
    # ✅ 修复拼写错误: cout -> count
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()

async def get_news_detail (db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def increase_news_views(db: AsyncSession, news_id: int):
    stmt=update(News).where(News.id == news_id).values(views=News.views+1)
    result=await db.execute(stmt)
    await db.commit()

    #更新 -> 检查数据库是否真的命中了数据 ->  命中返回true
    return result.rowcount > 0


async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):

    stmt = select(News).where(News.id != news_id, News.category_id == category_id).order_by(News.views.desc(),News.publish_time.desc()).limit(limit)
    result = await db.execute(stmt)
    # return result.scalars().all()
    related_news = result.scalars().all()

    #列表推导式 推导出新闻的核心数据。然后在return
    return [{
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views,
    } for news_detail in related_news]


async def get_news_by_title(db: AsyncSession, title_prefix: str):
    """根据标题前缀查找新闻（用于去重）"""
    stmt = select(News).where(News.title.like(f"{title_prefix}%"))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_news(
    db: AsyncSession,
    title: str,
    description: str,
    content: str,
    image: str = None,
    author: str = None,
    category_id: int = 1,
    publish_time = None
):
    """创建新新闻"""
    from datetime import datetime
    new_news = News(
        title=title,
        description=description,
        content=content,
        image=image,
        author=author,
        category_id=category_id,
        publish_time=publish_time or datetime.now()
    )
    db.add(new_news)
    await db.flush()
    return new_news