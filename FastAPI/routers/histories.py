from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from schemas.users import HistoryRequest
from crud import histories as history_crud
from routers.users import get_current_user_id

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/add")
async def add_history(
    hist_data: HistoryRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """添加浏览历史"""
    success = await history_crud.add_history(db, user_id, hist_data.newsId)
    await db.commit()  # 提交事务
    
    if success:
        return {
            "code": 200,
            "message": "记录浏览历史成功",
            "data": None
        }
    else:
        return {
            "code": 400,
            "message": "记录浏览历史失败",
            "data": None
        }


@router.delete("/delete/{news_id}")
async def remove_history(
    news_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除单条浏览历史"""
    success = await history_crud.remove_history(db, user_id, news_id)
    await db.commit()
    
    if success:
        return {
            "code": 200,
            "message": "删除浏览历史成功",
            "data": None
        }
    else:
        return {
            "code": 404,
            "message": "浏览历史不存在",
            "data": None
        }


@router.delete("/clear")
async def clear_history(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """清空所有浏览历史"""
    count = await history_crud.clear_user_history(db, user_id)
    await db.commit()
    
    return {
        "code": 200,
        "message": f"已清空{count}条浏览历史",
        "data": None
    }


@router.get("/list")
async def get_history_list(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """获取浏览历史列表"""
    # 默认获取最近50条
    histories = await history_crud.get_user_history(db, user_id, skip=0, limit=50)
    
    return {
        "code": 200,
        "message": "获取浏览历史成功",
        "data": {
            "list": histories,
            "total": len(histories)
        }
    }
