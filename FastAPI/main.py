"""
FastAPI 应用入口文件

项目结构说明：
├── main.py          - 应用入口，注册路由，启动服务
├── config/          - 配置文件（数据库连接等）
├── models/          - 数据模型（对应数据库表结构）
├── crud/            - 数据库操作（增删改查方法）
├── routers/         - 路由处理（API接口定义）
└── schemas/         - 数据验证（Pydantic模型，可选）

启动命令：
    python main.py
    或
    uvicorn main:app --reload
"""

from fastapi import FastAPI
import uvicorn
import os
from routers import news, users, favorites, histories, search, avatar, spider
from fastapi.middleware.cors import CORSMiddleware


# 创建 FastAPI 应用实例
# 可选参数：title="API名称", description="API描述", version="1.0.0"
app = FastAPI(
    title="新闻管理系统API",
    description="基于 FastAPI + SQLAlchemy 的新闻管理系统",
    version="1.0.0"
)

# 跨域中间件
# 从环境变量读取允许的源，支持云平台部署
cors_origins_str = os.getenv("CORS_ORIGINS", "*")
if cors_origins_str == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(CORSMiddleware,
                   allow_origins=cors_origins,  # 允许的来源列表
                   allow_methods=["*"],  # 允许所有方法访问
                   allow_headers=["*"],  # 允许所有头部访问
                   allow_credentials=True)

# 静态文件服务（用于访问上传的头像）
from fastapi.staticfiles import StaticFiles阿达
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ========== 根路径接口 ==========
@app.get("/")
def def_root():
    """
    根路径接口测试
    访问：http://127.0.0.1:8000/
    返回：{"message": "Hello World"}
    """
    return {"message": "Hello World"}


# ========== 挂载路由 ==========
# 将各模块中的路由注册到应用
app.include_router(users.router)
app.include_router(news.router)
app.include_router(favorites.router)
app.include_router(histories.router)
app.include_router(search.router)
app.include_router(avatar.router)
app.include_router(spider.router)


# ========== 启动服务器 ==========
if __name__ == "__main__":
    import os
    # 启动定时任务
    from tasks.scheduler import start_scheduler
    start_scheduler()
    
    # 从环境变量读取端口，兼容云平台部署
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # uvicorn.run() 启动 ASGI 服务器
    uvicorn.run("main:app", host=host, port=port, reload=False)