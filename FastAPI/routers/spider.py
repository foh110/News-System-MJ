"""
爬虫路由接口
提供手动触发爬虫和定时任务管理
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from crud import news as news_crud
from spider.news_spider import NewsCrawlerManager
from datetime import datetime

router = APIRouter(prefix="/api/spider", tags=["spider"])

crawler_manager = NewsCrawlerManager()


@router.post("/crawl")
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    category_ids: str = "1,2,3",
    db: AsyncSession = Depends(get_db)
):
    """
    手动触发新闻爬取
    category_ids: 分类ID列表，逗号分隔，如 "1,2,3"
    """
    # 解析分类ID
    ids = [int(x.strip()) for x in category_ids.split(',') if x.strip().isdigit()]
    
    # 后台任务执行爬虫
    background_tasks.add_task(crawl_and_save_news, ids)
    
    return {
        "code": 200,
        "message": "爬虫任务已启动，正在后台执行",
        "data": {"category_ids": ids}
    }


@router.get("/status")
async def get_crawl_status(db: AsyncSession = Depends(get_db)):
    """获取爬虫状态和统计信息"""
    # 统计各分类新闻数量
    stats = []
    for cat_id in range(1, 6):
        count = await news_crud.get_news_count(db, cat_id)
        stats.append({"category_id": cat_id, "count": count})
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "stats": stats,
            "last_crawl": "待实现"  # 可记录最后一次爬取时间
        }
    }


async def crawl_and_save_news(category_ids: list):
    """后台执行爬虫并保存数据"""
    try:
        print(f"开始爬取新闻，分类: {category_ids}")
        
        # 执行爬取
        result = await crawler_manager.crawl_all(category_ids)
        news_list = result['news']
        
        print(f"爬取完成，共获取 {result['total']} 条新闻，去重后 {result['unique']} 条")
        
        # 保存到数据库（需要创建异步数据库会话）
        from config.db_config import async_session_local
        async with async_session_local() as db:
            saved_count = 0
            for news_item in news_list:
                try:
                    # 检查是否已存在（基于标题去重）
                    existing = await news_crud.get_news_by_title(db, news_item['title'][:100])
                    if existing:
                        print(f"跳过重复新闻: {news_item['title'][:50]}")
                        continue
                    
                    # 创建新闻
                    new_news = await news_crud.create_news(
                        db,
                        title=news_item['title'],
                        description=news_item['description'],
                        content=news_item['content'],
                        image=news_item['image'],
                        author=news_item['author'],
                        category_id=news_item['category_id'],
                        publish_time=news_item['publish_time']
                    )
                    
                    if new_news:
                        saved_count += 1
                        print(f"已保存: {news_item['title'][:50]}")
                    
                except Exception as e:
                    print(f"保存新闻失败 {news_item['title']}: {e}")
                    continue
            
            await db.commit()
            print(f"爬虫任务完成，成功保存 {saved_count}/{len(news_list)} 条新闻")
    
    except Exception as e:
        print(f"爬虫任务执行失败: {e}")
