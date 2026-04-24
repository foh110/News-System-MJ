"""
浏览历史相关CRUD操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from models.users import History
from models.news import News


async def get_user_history(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 50):
    """获取用户的浏览历史列表"""
    stmt = (
        select(History, News)
        .join(News, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.viewed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    histories = result.all()
    
    # 转换为字典列表
    return [{
        "id": news.id,
        "title": news.title,
        "description": news.description,
        "image": news.image,
        "author": news.author,
        "publishTime": news.publish_time.strftime("%Y-%m-%d %H:%M") if news.publish_time else None,
        "categoryId": news.category_id,
        "views": news.views,
        "viewTime": hist.viewed_at.strftime("%Y-%m-%d %H:%M") if hist.viewed_at else None
    } for hist, news in histories]


async def add_history(db: AsyncSession, user_id: int, news_id: int):
    """添加浏览历史（如果已存在则更新浏览时间）"""
    # 检查是否已存在
    stmt = select(History).where(
        History.user_id == user_id,
        History.news_id == news_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # 如果已存在，删除旧记录
        await db.delete(existing)
        await db.flush()
    
    # 创建新记录
    history = History(user_id=user_id, news_id=news_id)
    db.add(history)
    await db.flush()
    return True


async def remove_history(db: AsyncSession, user_id: int, news_id: int):
    """删除单条浏览历史"""
    stmt = delete(History).where(
        History.user_id == user_id,
        History.news_id == news_id
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount > 0


async def clear_user_history(db: AsyncSession, user_id: int):
    """清空用户的所有浏览历史"""
    stmt = delete(History).where(History.user_id == user_id)
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount
