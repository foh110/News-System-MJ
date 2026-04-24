from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserRequest(BaseModel):
    """用户注册/登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    bio: Optional[str] = "这个人很懒，什么都没留下"
    avatar: Optional[str] = "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
    
    class Config:
        from_attributes = True


class UpdateBioRequest(BaseModel):
    """更新用户资料请求（支持简介、头像、用户名）"""
    bio: Optional[str] = None
    avatar: Optional[str] = None
    username: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    """修改密码请求"""
    oldPassword: str
    newPassword: str


class FavoriteRequest(BaseModel):
    """收藏请求"""
    newsId: int


class HistoryRequest(BaseModel):
    """浏览历史请求"""
    newsId: int