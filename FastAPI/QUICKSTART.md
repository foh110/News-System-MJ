# 快速启动指南

## 前置要求

1. Python 3.8+
2. MySQL 数据库

## 步骤1: 安装依赖

```bash
cd FastAPI
pip install -r requirements.txt
```

如果安装缓慢，可以使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 步骤2: 配置数据库

1. 创建MySQL数据库：
```sql
CREATE DATABASE news_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 修改 `config/db_config.py` 中的数据库连接信息：
```python
ASYNC_DATABASE_URL = "mysql+aiomysql://用户名:密码@localhost:3306/news_app?charset=utf8mb4"
```

## 步骤3: 初始化数据库

```bash
python init_database.py
```

这将创建所有必需的表：
- news_category (新闻分类)
- news (新闻内容)
- users (用户)
- favorites (收藏)
- histories (浏览历史)

## 步骤4: 插入测试数据（可选）

在数据库中执行以下SQL插入一些测试数据：

```sql
-- 插入新闻分类
INSERT INTO news_category (name, sort_order) VALUES 
('头条', 1),
('社会', 2),
('国内', 3),
('国际', 4),
('娱乐', 5),
('体育', 6),
('军事', 7),
('科技', 8),
('财经', 9);

-- 插入测试新闻（示例）
INSERT INTO news (title, description, content, image, author, category_id, views, publish_time) VALUES
('测试新闻标题1', '这是测试新闻简介', '这是测试新闻内容...', 'https://picsum.photos/200/200', '测试作者', 1, 0, NOW()),
('测试新闻标题2', '这是测试新闻简介', '这是测试新闻内容...', 'https://picsum.photos/200/200', '测试作者', 2, 0, NOW());
```

## 步骤5: 启动后端服务

```bash
python main.py
```

服务将在 http://127.0.0.1:8000 启动

访问 http://127.0.0.1:8000/docs 查看API文档

## 步骤6: 测试API

运行测试脚本验证API是否正常工作：

```bash
python test_api.py
```

## 步骤7: 启动前端（如果需要）

```bash
cd ../xwzx-news
npm install
npm run dev
```

## 常见问题

### 1. 模块导入错误
确保在项目根目录下运行命令，或者将FastAPI目录添加到Python路径。

### 2. 数据库连接失败
- 检查MySQL服务是否启动
- 检查数据库用户名和密码是否正确
- 检查端口号是否正确（默认3306）

### 3. 依赖安装失败
尝试逐个安装：
```bash
pip install fastapi uvicorn sqlalchemy aiomysql pydantic PyJWT passlib[bcrypt]
```

### 4. bcrypt编译错误
Windows用户可能需要安装Visual C++ Build Tools，或使用预编译版本：
```bash
pip install bcrypt --only-binary :all:
```

## API测试示例

使用curl测试注册接口：
```bash
curl -X POST "http://127.0.0.1:8000/api/user/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "123456"}'
```

使用curl测试登录接口：
```bash
curl -X POST "http://127.0.0.1:8000/api/user/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "123456"}'
```

## 下一步

1. 查看 `README.md` 了解完整的API文档
2. 根据实际需求修改数据库配置
3. 在生产环境中修改SECRET_KEY
4. 配置合适的CORS策略
