from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from schemas.users import UserRequest, UpdateBioRequest, UpdatePasswordRequest
from crud import users as user_crud
from utils.auth import create_access_token, decode_access_token
from typing import Optional

router = APIRouter(prefix="/api/user", tags=["user"])


def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """从请求头中获取当前用户ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权访问")
    
    # 支持 "Bearer token" 和直接 "token" 两种格式
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="无效的令牌")
    
    return int(payload["sub"])


@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查用户是否已存在
    existing_user = await user_crud.get_user_by_username(db, user_data.username)
    if existing_user:
        return {
            "code": 400,
            "message": "用户名已存在",
            "data": None
        }
    
    # 创建新用户
    new_user = await user_crud.create_user(db, user_data.username, user_data.password)
    
    # 生成Token
    token = create_access_token(data={"sub": str(new_user.id)})
    
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": token,
            "userInfo": {
                "id": new_user.id,
                "username": new_user.username,
                "bio": new_user.bio,
                "avatar": new_user.avatar
            }
        }
    }


@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    # 验证用户密码
    user = await user_crud.verify_user_password(db, user_data.username, user_data.password)
    if not user:
        return {
            "code": 401,
            "message": "用户名或密码错误",
            "data": None
        }
    
    # 生成Token
    token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": token,
            "userInfo": {
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar
            }
        }
    }


@router.get("/info")
async def get_user_info(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取当前用户信息"""
    user = await user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "code": 200,
        "message": "获取用户信息成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "bio": user.bio,
            "avatar": user.avatar
        }
    }


@router.put("/update")
async def update_user_profile(
    profile_data: UpdateBioRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新用户资料（支持简介、头像、用户名）"""
    user = await user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新个人简介
    if hasattr(profile_data, 'bio') and profile_data.bio:
        user.bio = profile_data.bio
    
    # 更新头像
    if hasattr(profile_data, 'avatar') and profile_data.avatar:
        user.avatar = profile_data.avatar
    
    # 更新用户名（可选）
    if hasattr(profile_data, 'username') and profile_data.username:
        # 检查用户名是否已存在
        existing_user = await user_crud.get_user_by_username(db, profile_data.username)
        if existing_user and existing_user.id != user_id:
            return {
                "code": 400,
                "message": "用户名已存在",
                "data": None
            }
        user.username = profile_data.username
    
    await db.flush()
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "bio": user.bio,
            "avatar": user.avatar
        }
    }


@router.put("/password")
async def update_password(
    password_data: UpdatePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """修改密码"""
    # 验证旧密码
    user = await user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    from utils.auth import verify_password
    if not verify_password(password_data.oldPassword, user.password):
        return {
            "code": 400,
            "message": "原密码错误",
            "data": None
        }
    
    # 更新密码
    await user_crud.update_user_password(db, user_id, password_data.newPassword)
    
    return {
        "code": 200,
        "message": "密码修改成功",
        "data": None
    }