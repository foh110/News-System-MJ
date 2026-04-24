# FastAPI 新闻管理系统后端

## 项目结构

```
FastAPI/
├── config/              # 配置文件
│   └── db_config.py    # 数据库配置
├── models/             # 数据模型
│   ├── news.py        # 新闻和分类模型
│   └── users.py       # 用户、收藏、历史模型
├── crud/              # 数据库操作
│   ├── news.py       # 新闻CRUD
│   ├── users.py      # 用户CRUD
│   ├── favorites.py  # 收藏CRUD
│   └── histories.py  # 浏览历史CRUD
├── routers/           # API路由
│   ├── news.py       # 新闻相关接口
│   ├── users.py      # 用户相关接口
│   ├── favorites.py  # 收藏相关接口
│   └── histories.py  # 浏览历史接口
├── schemas/           # 数据验证
│   └── users.py      # 用户相关Schema
├── utils/             # 工具函数
│   └── auth.py       # JWT认证和密码加密
├── main.py           # 应用入口
├── requirements.txt  # 依赖包
└── init_database.py  # 数据库初始化脚本
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 数据库配置

在 `config/db_config.py` 中修改数据库连接信息：

```python
ASYNC_DATABASE_URL = "mysql+aiomysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4"
```

## 初始化数据库

```bash
python init_database.py
```

这将创建以下表：
- `news_category` - 新闻分类
- `news` - 新闻内容
- `users` - 用户信息
- `favorites` - 用户收藏
- `histories` - 浏览历史

## 启动服务

```bash
python main.py
```

或

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

访问 http://127.0.0.1:8000/docs 查看API文档

## API接口列表

### 新闻模块 (/api/news)

#### 1. 获取新闻分类列表
- **接口**: `GET /api/news/categories`
- **参数**: 
  - `skip`: 跳过数量 (默认0)
  - `limit`: 返回数量 (默认100)
- **响应**:
```json
{
  "code": 200,
  "message": "获取分类成功",
  "data": [
    {"id": 1, "name": "头条", "sort_order": 0}
  ]
}
```

#### 2. 获取新闻列表
- **接口**: `GET /api/news/list`
- **参数**:
  - `categoryId`: 分类ID (必需)
  - `page`: 页码 (默认1)
  - `pageSize`: 每页数量 (默认10, 最大100)
- **响应**:
```json
{
  "code": 200,
  "message": "获取新闻列表成功",
  "data": {
    "list": [...],
    "total": 100,
    "hasMore": true
  }
}
```

#### 3. 获取新闻详情
- **接口**: `GET /api/news/detail`
- **参数**:
  - `id`: 新闻ID (必需)
- **响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "新闻标题",
    "content": "新闻内容",
    "image": "图片URL",
    "author": "作者",
    "publishTime": "2024-01-01T00:00:00",
    "categoryId": 1,
    "views": 100,
    "relatedNews": [...]
  }
}
```

### 用户模块 (/api/user)

#### 1. 用户注册
- **接口**: `POST /api/user/register`
- **请求体**:
```json
{
  "username": "testuser",
  "password": "123456"
}
```
- **响应**:
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userInfo": {
      "id": 1,
      "username": "testuser",
      "bio": "这个人很懒，什么都没留下",
      "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
    }
  }
}
```

#### 2. 用户登录
- **接口**: `POST /api/user/login`
- **请求体**:
```json
{
  "username": "testuser",
  "password": "123456"
}
```
- **响应**: 同注册

#### 3. 获取用户信息
- **接口**: `GET /api/user/info`
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
```json
{
  "code": 200,
  "message": "获取用户信息成功",
  "data": {
    "id": 1,
    "username": "testuser",
    "bio": "个人简介",
    "avatar": "头像URL"
  }
}
```

#### 4. 更新个人简介
- **接口**: `PUT /api/user/update`
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
  "bio": "新的个人简介"
}
```

#### 5. 修改密码
- **接口**: `PUT /api/user/password`
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
  "oldPassword": "123456",
  "newPassword": "654321"
}
```

### 收藏模块 (/api/favorite)

所有收藏接口都需要在请求头中携带Token：
`Authorization: Bearer <token>`

#### 1. 检查是否已收藏
- **接口**: `GET /api/favorite/check?newsId=1`
- **响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "isFavorite": true
  }
}
```

#### 2. 添加收藏
- **接口**: `POST /api/favorite/add`
- **请求体**:
```json
{
  "newsId": 1
}
```

#### 3. 取消收藏
- **接口**: `DELETE /api/favorite/remove?newsId=1`

#### 4. 清空所有收藏
- **接口**: `DELETE /api/favorite/clear`

#### 5. 获取收藏列表
- **接口**: `GET /api/favorite/list?page=1&pageSize=10`
- **响应**:
```json
{
  "code": 200,
  "message": "获取收藏列表成功",
  "data": {
    "list": [...],
    "total": 10,
    "page": 1,
    "pageSize": 10
  }
}
```

### 浏览历史模块 (/api/history)

所有浏览历史接口都需要在请求头中携带Token。

#### 1. 添加浏览历史
- **接口**: `POST /api/history/add`
- **请求体**:
```json
{
  "newsId": 1
}
```

#### 2. 删除单条浏览历史
- **接口**: `DELETE /api/history/delete/1`

#### 3. 清空所有浏览历史
- **接口**: `DELETE /api/history/clear`

#### 4. 获取浏览历史列表
- **接口**: `GET /api/history/list`
- **响应**:
```json
{
  "code": 200,
  "message": "获取浏览历史成功",
  "data": {
    "list": [...],
    "total": 50
  }
}
```

## 认证机制

使用JWT (JSON Web Token) 进行身份验证：

1. 用户登录/注册后获得Token
2. 后续请求在Header中携带Token
3. Token有效期为7天
4. 支持两种格式：
   - `Authorization: Bearer <token>`
   - `Authorization: <token>`

## 密码安全

- 使用bcrypt算法对密码进行哈希加密
- 原始密码不会存储在数据库中
- 登录时验证哈希后的密码

## 注意事项

1. **生产环境配置**：
   - 修改 `utils/auth.py` 中的 `SECRET_KEY`
   - 关闭 `db_config.py` 中的 `echo=True`
   - 设置合适的CORS策略

2. **数据库连接池**：
   - 默认连接池大小：10
   - 最大溢出连接数：20
   - 可根据实际情况调整

3. **跨域配置**：
   - 当前允许所有源访问（开发环境）
   - 生产环境应限制具体的域名

## 常见问题

### 1. 数据库连接失败
检查 `db_config.py` 中的连接字符串是否正确

### 2. Token验证失败
确保请求头中正确携带了Token

### 3. 导入错误
确保已安装所有依赖包：`pip install -r requirements.txt`

### 4. 表不存在
运行 `python init_database.py` 创建数据库表
