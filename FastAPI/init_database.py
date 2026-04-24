"""
数据库初始化脚本 - 创建所有表并插入初始数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config.db_config import async_engine
from models.news import Base as NewsBase
from models.users import Base as UserBase


async def init_db():
    """初始化数据库（创建所有表）"""
    print("开始初始化数据库...")
    
    async with async_engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(NewsBase.metadata.create_all)
        await conn.run_sync(UserBase.metadata.create_all)
    
    print("✓ 数据库表创建完成")
    print("\n已创建的表：")
    print("  - news_category (新闻分类)")
    print("  - news (新闻)")
    print("  - users (用户)")
    print("  - favorites (收藏)")
    print("  - histories (浏览历史)")
    print("\n提示：请手动在数据库中插入测试数据或运行其他初始化脚本")


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
        print("\n✓ 数据库初始化成功！")
    except Exception as e:
        print(f"\n✗ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
