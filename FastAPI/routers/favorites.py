from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from schemas.users import FavoriteRequest
from crud import favorites as favorite_crud
from routers.users import get_current_user_id

router = APIRouter(prefix="/api/favorite", tags=["favorite"])


@router.get("/check")
async def check_favorite(
    newsId: int = Query(description="新闻ID"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """检查是否已收藏"""
    is_favorited = await favorite_crud.check_favorite(db, user_id, newsId)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "isFavorite": is_favorited
        }
    }


@router.post("/add")
async def add_favorite(
    fav_data: FavoriteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """添加收藏"""
    success = await favorite_crud.add_favorite(db, user_id, fav_data.newsId)
    
    if success:
        return {
            "code": 200,
            "message": "收藏成功",
            "data": None
        }
    else:
        return {
            "code": 400,
            "message": "已收藏该新闻",
            "data": None
        }


@router.delete("/remove")
async def remove_favorite(
    newsId: int = Query(description="新闻ID"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """取消收藏"""
    success = await favorite_crud.remove_favorite(db, user_id, newsId)
    
    if success:
        return {
            "code": 200,
            "message": "取消收藏成功",
            "data": None
        }
    else:
        return {
            "code": 404,
            "message": "收藏不存在",
            "data": None
        }


@router.delete("/clear")
async def clear_favorites(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """清空所有收藏"""
    count = await favorite_crud.clear_user_favorites(db, user_id)
    
    return {
        "code": 200,
        "message": f"已清空{count}条收藏",
        "data": None
    }


@router.get("/list")
async def get_favorite_list(
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取收藏列表"""
    skip = (page - 1) * pageSize
    
    favorites = await favorite_crud.get_user_favorites(db, user_id, skip, pageSize)
    
    return {
        "code": 200,
        "message": "获取收藏列表成功",
        "data": {
            "list": favorites,
            "total": len(favorites),
            "page": page,
            "pageSize": pageSize
        }
    }
