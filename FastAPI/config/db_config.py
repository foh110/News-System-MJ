"""
数据库配置文件 - db_config.py

功能：配置数据库连接，创建异步引擎和会话

SQLAlchemy 异步数据库连接说明：
- 异步引擎：用于执行 SQL 语句
- 会话工厂：用于创建数据库会话
- 依赖注入：FastAPI 自动管理会话的生命周期

学习要点：
1. 数据库连接字符串格式：
   mysql+aiomysql://用户名:密码@主机:端口/数据库名?参数
   
   组成部分：
   - mysql+aiomysql : 数据库类型 + 异步驱动
   - root:lyp82ndlf : 用户名:密码
   - localhost:3307 : 主机:端口
   - news_app       : 数据库名
   - charset=utf8mb4: 字符集参数

2. 连接池概念：
   - pool_size: 基础连接数
   - max_overflow: 最大溢出连接数
   - 总连接数 = pool_size + max_overflow
"""

# 导入 SQLAlchemy 异步数据库组件
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine


# ========== 数据库连接配置 ==========

# 导入os模块以读取环境变量
import os

# 数据库连接 URL
# 优先从环境变量 DATABASE_URL 读取，兼容云平台部署
# 格式：mysql+aiomysql://用户名:密码@主机:端口/数据库名?参数
#
# 参数说明：
#   mysql          - 数据库类型（MySQL）
#   aiomysql       - 异步驱动（用于异步操作）
#   root           - 数据库用户名
#   lyp82ndlf      - 数据库密码
#   localhost      - 数据库主机（127.0.0.1）
#   3307           - 数据库端口（默认3306，这里使用3307）
#   news_app       - 数据库名称
#   charset=utf8mb4 - 字符集（支持中文和emoji）
ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:lyp82ndlf@localhost:3307/news_app?charset=utf8mb4"
)


# ========== 创建异步引擎 ==========

# create_async_engine() 创建异步数据库引擎
# 引擎是 SQLAlchemy 的核心组件，负责：
# - 管理数据库连接
# - 执行 SQL 语句
# - 连接池管理
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,     # 数据库连接 URL
    
    # 开发配置
    echo=True,              # 是否打印 SQL 语句（开发时设为True，生产环境设为False）
    
    # 连接池配置
    pool_size=10,           # 连接池基础大小（保持10个持久连接）
    max_overflow=20,        # 最大溢出连接数（允许额外创建20个连接）
    
    # 其他可选参数：
    # pool_timeout=30,      # 获取连接的超时时间（秒）
    # pool_recycle=3600,    # 连接回收时间（秒，防止连接过期）
    # pool_pre_ping=True,   # 使用前检查连接是否有效
)


# ========== 创建异步会话工厂 ==========

# async_sessionmaker() 创建会话工厂
# 会话（Session）是 SQLAlchemy 的工作单元，用于：
# - 管理数据库事务
# - 跟踪对象状态
# - 执行查询和更新
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,          # 绑定的引擎
    class_=AsyncSession,        # 使用异步会话类
    expire_on_commit=False      # 提交后不使对象过期（推荐设为False）
    
    # expire_on_commit 说明：
    # - True  : 提交后对象属性变为过期状态，下次访问会重新查询
    # - False : 提交后对象保持可用（推荐，避免额外的查询）
)


# ========== 数据库会话依赖注入 ==========

# FastAPI 依赖注入函数
# 作用：自动为每个请求创建和关闭数据库会话
#
# FastAPI 工作流程：
# 1. 请求到达时，创建新的数据库会话
# 2. 将 session 注入到路由函数
# 3. 请求处理完成后，自动关闭会话
#
# 使用方式：
#   db: AsyncSession = Depends(get_db)
async def get_db():
    """
    数据库会话依赖注入
    
    这是一个生成器函数（使用 yield）
    
    工作流程：
    1. 创建数据库会话
    2. yield 返回 session（给路由函数使用）
    3. 请求完成后执行后续代码
    4. 提交事务 / 回滚 / 关闭会话
    
    FastAPI 自动管理：
    - 成功响应 → commit() → close()
    - 异常错误 → rollback() → close()
    """
    
    # 创建异步会话上下文
    # async with 自动管理会话的生命周期
    async with AsyncSessionLocal() as session:
        try:
            # yield 返回 session 给路由函数使用
            # 此时路由函数执行数据库操作
            yield session
            
            # 路由函数执行完成后，提交事务
            # 将所有数据库操作持久化
            await session.commit()
            
        except Exception:
            # 如果发生异常，回滚事务
            # 撤销所有未提交的数据库操作
            await session.rollback()
            raise  # 重新抛出异常
            
        finally:
            # 无论成功或失败，最终都关闭会话
            # 释放数据库连接回连接池
            await session.close()


# ========== 其他配置示例（供参考） ==========
"""
# 1. 同步数据库连接（非异步）
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SYNC_DATABASE_URL = "mysql+pymysql://root:lyp82ndlf@localhost:3307/news_app?charset=utf8mb4"
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def get_sync_db():
    '''同步数据库会话（用于非异步场景）'''
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# 2. SQLite 数据库连接
# SQLite 连接字符串格式：sqlite+aiosqlite:///数据库文件路径
# SQLite 不需要用户名密码

SQLITE_DATABASE_URL = "sqlite+aiosqlite:///./news_app.db"
sqlite_engine = create_async_engine(SQLITE_DATABASE_URL, echo=True)


# 3. PostgreSQL 数据库连接
# 格式：postgresql+asyncpg://用户名:密码@主机:端口/数据库名

POSTGRES_DATABASE_URL = "postgresql+asyncpg://root:lyp82ndlf@localhost:5432/news_app"
postgres_engine = create_async_engine(POSTGRES_DATABASE_URL, echo=True)


# 4. 数据库表自动创建（开发环境）
# 使用 Base.metadata.create_all() 自动创建所有模型对应的表

from sqlalchemy import MetaData
from models.news import Base

async def init_db():
    '''初始化数据库（创建所有表）'''
    async with async_engine.begin() as conn:
        # create_all() 创建所有不存在的表
        # 不会覆盖已存在的表
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表初始化完成")


# 5. 测试数据库连接
async def test_connection():
    '''测试数据库连接是否正常'''
    try:
        async with AsyncSessionLocal() as session:
            # 执行简单查询测试连接
            result = await session.execute("SELECT 1")
            print("数据库连接成功！")
            return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False
"""
