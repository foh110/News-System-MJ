"""
收藏相关CRUD操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.users import Favorite
from models.news import News


async def get_user_favorites(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    """获取用户的收藏列表"""
    stmt = (
        select(Favorite, News)
        .join(News, Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    favorites = result.all()
    
    # 转换为字典列表
    return [{
        "id": news.id,
        "title": news.title,
        "description": news.description,
        "image": news.image,
        "author": news.author,
        "publishTime": news.publish_time.isoformat() if news.publish_time else None,
        "categoryId": news.category_id,
        "views": news.views,
        "favoriteTime": fav.created_at.isoformat() if fav.created_at else None
    } for fav, news in favorites]


async def check_favorite(db: AsyncSession, user_id: int, news_id: int):
    """检查用户是否已收藏某新闻"""
    stmt = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def add_favorite(db: AsyncSession, user_id: int, news_id: int):
    """添加收藏"""
    # 检查是否已存在
    existing = await check_favorite(db, user_id, news_id)
    if existing:
        return False
    
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.flush()
    return True


async def remove_favorite(db: AsyncSession, user_id: int, news_id: int):
    """取消收藏"""
    stmt = delete(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount > 0


async def clear_user_favorites(db: AsyncSession, user_id: int):
    """清空用户的所有收藏"""
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount
