"""
用户相关CRUD操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.users import User
from utils.auth import get_password_hash, verify_password


async def get_user_by_username(db: AsyncSession, username: str):
    """根据用户名获取用户"""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    """根据ID获取用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, password: str):
    """创建新用户"""
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        password=hashed_password
    )
    db.add(db_user)
    await db.flush()  # 刷新以获取ID
    return db_user


async def update_user_bio(db: AsyncSession, user_id: int, bio: str):
    """更新用户个人简介"""
    user = await get_user_by_id(db, user_id)
    if user:
        user.bio = bio
        await db.flush()
        return user
    return None


async def update_user_password(db: AsyncSession, user_id: int, new_password: str):
    """更新用户密码"""
    user = await get_user_by_id(db, user_id)
    if user:
        user.password = get_password_hash(new_password)
        await db.flush()
        return user
    return None


async def verify_user_password(db: AsyncSession, username: str, password: str):
    """验证用户密码"""
    user = await get_user_by_username(db, username)
    if user and verify_password(password, user.password):
        return user
    return None
