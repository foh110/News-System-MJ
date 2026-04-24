"""
定时任务调度器
使用 APScheduler 实现定时新闻爬取
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from spider.news_spider import NewsCrawlerManager
from config.db_config import AsyncSessionLocal
from crud import news as news_crud
from datetime import datetime
import asyncio
import threading

scheduler = None


def save_news_to_db_sync(news_list):
    """同步方式保存新闻到数据库（用于定时任务）"""
    import asyncio
    
    async def _save():
        async with AsyncSessionLocal() as db:
            saved_count = 0
            for news_item in news_list:
                try:
                    existing = await news_crud.get_news_by_title(db, news_item['title'][:100])
                    if existing:
                        print(f"[定时任务] 跳过重复新闻: {news_item['title'][:50]}")
                        continue
                    
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
                        print(f"[定时任务] 已保存: {news_item['title'][:50]}")
                    
                except Exception as e:
                    print(f"[定时任务] 保存新闻失败 {news_item['title']}: {e}")
                    continue
            
            await db.commit()
            return saved_count
    
    # 创建新的事件循环来执行异步任务
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        saved_count = loop.run_until_complete(_save())
        print(f"[定时任务] 成功保存 {saved_count} 条新新闻到数据库")
    finally:
        loop.close()


def scheduled_crawl():
    """定时执行的爬虫任务（同步版本）"""
    print("[定时任务] 开始自动爬取新闻...")
    
    # 在同步环境中运行异步爬虫
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        crawler_manager = NewsCrawlerManager()
        result = loop.run_until_complete(crawler_manager.crawl_all([1, 2, 3]))
        
        print(f"[定时任务] 爬取完成，获取 {result['total']} 条，去重后 {result['unique']} 条")
        
        # 保存到数据库
        if result['news']:
            save_news_to_db_sync(result['news'])
        else:
            print("[定时任务] 没有新新闻需要保存")
    finally:
        loop.close()


def start_scheduler():
    """启动定时任务"""
    global scheduler
    
    # 使用 BackgroundScheduler（同步版本）
    scheduler = BackgroundScheduler()
    
    # 每天早上 8 点、12 点、18 点执行
    scheduler.add_job(
        scheduled_crawl,
        'cron',
        hour='8,12,18',
        minute='0',
        id='news_crawl',
        name='自动爬取新闻',
        replace_existing=True
    )
    
    # 启动调度器（后台线程）
    scheduler.start()
    print("[定时任务] 调度器已启动，将在每天 8:00, 12:00, 18:00 自动爬取新闻")


def stop_scheduler():
    """停止定时任务"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
