
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 导入数据库会话依赖
from config.db_config import get_db
# 导入 CRUD 操作模块
from crud import news


# ========== 创建路由器实例 ==========
# APIRouter 是 FastAPI 的路由分组工具，用于模块化组织接口
# 参数说明：
#   prefix="/api/news" - 路由前缀，所有该路由器的接口都以 /api/news 开头
#   tags=["news"] - 标签，用于 Swagger 文档分组显示
router = APIRouter(prefix="/api/news", tags=["news"])



# ========== GET 接口：获取新闻分类列表 ==========
@router.get("/categories")
async def get_categories(
    skip: int = 0,              # 查询参数：跳过前N条（分页偏移量）
    limit: int = 100,           # 查询参数：返回条数（分页大小）
    db: AsyncSession = Depends(get_db)  # 依赖注入：自动获取数据库会话
):
    categories = await news.get_categories(db, skip=skip, limit=limit)
    return {
        "code": 200,              # 状态码：200表示成功
        "message": "获取分类成功",   # 提示信息
        "data": categories        # 数据：分类列表
    }

@router.get("/list")
async def get_news_list(
        categoryId: int = Query(description="分类ID"),
        page: int = 1,
        pageSize: int = Query(le=100, default=10, description="每页条数"),
        db: AsyncSession = Depends(get_db)
):
    # 思路：处理分页规则 -> 查询新闻列表 -> 计算总量 -> 计算是否还有更多
    offset = (page - 1) * pageSize
    news_list = await news.get_news_list(db, categoryId, offset, pageSize)
    total = await news.get_news_count(db, categoryId)
    has_more = (offset + len(news_list)) < total  # ✅ 计算布尔值
    
    # 字段转换：将下划线命名转换为驼峰命名
    formatted_list = []
    for n in news_list:
        formatted_list.append({
            "id": n.id,
            "title": n.title,
            "description": n.description,
            "image": n.image,
            "author": n.author,
            "publishTime": n.publish_time.strftime("%Y-%m-%d %H:%M:%S") if n.publish_time else "",
            "views": n.views,
            "categoryId": n.category_id
        })
    
    return {
        "code": 200,
        "message": "获取新闻列表成功",
        "data": {
            "list": formatted_list,
            "total": total,
            "hasMore": has_more
        }
    }

@router.get("/detail")
async def get_news_detail(news_id: int = Query(alias="id", description="新闻ID"), db: AsyncSession = Depends(get_db)):

    # 获取新闻详情+浏览次数加一+相关新闻
    news_detail = await news.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail="新闻不存在")

    views_res=await news.increase_news_views(db, news_detail.id)
    if not views_res:
        raise HTTPException(status_code=404, detail="新闻不存在")

    related_news = await news.get_related_news(db, news_detail.id, news_detail.category_id)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time,
            "categoryId": news_detail.category_id,
            "views": news_detail.views,
            "relatedNews": related_news
        }
    }

