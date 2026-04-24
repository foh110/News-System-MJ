# 智慧宿舍管理系统 - 安装指南

## 系统要求

### 必需软件
1. **Python 3.8+** - [下载地址](https://www.python.org/downloads/)
2. **MySQL 5.7+** 或 **MariaDB 10.2+** - [下载地址](https://dev.mysql.com/downloads/mysql/)

### 硬件要求
- CPU: 双核以上
- 内存: 4GB+
- 硬盘: 10GB+ 可用空间

## 安装步骤

### 第一步：安装 Python

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.8 或更高版本
3. 安装时**务必勾选** "Add Python to PATH"
4. 完成安装

### 第二步：安装 MySQL

1. 访问 https://dev.mysql.com/downloads/mysql/
2. 下载 MySQL Installer
3. 运行安装程序，选择 "Server only" 或 "Full"
4. 设置 root 密码（请记住密码）
5. 完成安装

### 第三步：创建数据库

1. 打开 MySQL Command Line Client 或 MySQL Workbench
2. 执行以下命令创建数据库：

```sql
CREATE DATABASE dormitory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. 导入初始化脚本（在项目目录下执行）：

```bash
mysql -u root -p dormitory_db < database_init.sql
```

输入 root 密码后，数据库将自动初始化。

### 第四步：配置系统

编辑 `config.py` 文件，修改数据库连接信息：

```python
DB_CONFIG = {
    "host": "localhost",      # 数据库地址
    "port": 3306,             # 数据库端口
    "user": "root",           # 数据库用户名
    "password": "你的密码",    # 数据库密码
    "database": "dormitory_db",
    "charset": "utf8mb4"
}
```

### 第五步：启动系统

#### 方式一：使用启动脚本（推荐）

双击运行 `start.bat`

#### 方式二：手动启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动系统
python app_new.py
```

### 第六步：访问系统

打开浏览器，访问：

```
http://localhost:8080
```

## 默认账号

- **用户名**: `admin`
- **密码**: `admin123`

**首次登录后请立即修改密码！**

## 常见问题

### Q1: 启动时报错 "ModuleNotFoundError"

**解决方法**: 安装依赖
```bash
pip install -r requirements.txt
```

### Q2: 数据库连接失败

**解决方法**: 
1. 检查 MySQL 服务是否启动
2. 检查 config.py 中的数据库配置
3. 确认数据库已创建

### Q3: 端口被占用

**解决方法**: 修改 config.py 中的 PORT 配置：
```python
PORT = 8081  # 修改为其他端口
```

### Q4: 如何修改管理员密码？

**解决方法**: 
1. 登录系统
2. 点击右上角用户头像
3. 选择"修改密码"

### Q5: 忘记密码怎么办？

**解决方法**: 使用数据库重置密码
```sql
UPDATE sys_user SET password = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918' WHERE username = 'admin';
```
重置后的密码为: `admin123`

## 系统升级

### 从 v1.0 升级到 v2.0

1. 备份现有数据库
2. 下载新版本代码
3. 执行数据库升级脚本
4. 替换旧版本文件
5. 重启系统

## 技术支持

- 邮箱: support@dormitory-system.com
- 电话: 400-123-4567
- QQ群: 123456789

## 授权信息

本软件为商业软件，购买授权后可获得：
- 完整源代码
- 技术支持服务
- 免费版本升级
- 定制化开发服务

购买授权请联系: business@dormitory-system.com
