"""
智慧宿舍管理系统 - 配置文件
"""
import os
import logging
from datetime import timedelta

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """基础配置类"""
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dormitory_system_2026_secure_key'
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8080
    
    # 数据库配置
    DB_CONFIG = {
        "host": os.environ.get('DB_HOST') or "localhost",
        "port": int(os.environ.get('DB_PORT') or 3307),
        "user": os.environ.get('DB_USER') or "root",
        "password": os.environ.get('DB_PASSWORD') or "lyp82ndlf",
        "database": os.environ.get('DB_NAME') or "dormitory_db",
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "cursorclass": "pymysql.cursors.DictCursor"
    }
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    AVATAR_FOLDER = os.path.join(BASE_DIR, 'static', 'avatar')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'pdf', 'doc', 'docx'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 密码加密盐值
    PASSWORD_SALT = 'dorm_system_2026'
    
    # Session 配置
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 分页配置
    PER_PAGE = 10
    MAX_PER_PAGE = 100
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'system.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    
    # 备份配置
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    BACKUP_RETENTION_DAYS = 30
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 系统配置
    SYSTEM_NAME = '智慧宿舍管理系统'
    SYSTEM_VERSION = '2.0.0'
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = logging.WARNING


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    DB_CONFIG = {
        "host": "localhost",
        "port": 3307,
        "user": "root",
        "password": "lyp82ndlf",
        "database": "dormitory_test_db",
        "charset": "utf8mb4"
    }


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
