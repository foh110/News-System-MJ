"""
安全工具模块 - 密码加密、权限验证等
"""
import hashlib
import secrets
import re
from functools import wraps
from flask import session, flash, redirect, url_for, request
import logging

logger = logging.getLogger('dorm')

# 密码盐值（用于 SHA256 兼容旧数据）
PASSWORD_SALT = 'dorm_system_2026'

# 尝试导入 bcrypt，优先使用 BCrypt 加密
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    logger.warning("bcrypt 未安装，使用 SHA256 加密")


def pwd_hash(password):
    """
    密码加密（优先使用 BCrypt，兼容 SHA256）
    :param password: 明文密码
    :return: 加密后的密码
    """
    if HAS_BCRYPT:
        # BCrypt 加密（推荐，更安全）
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    else:
        # SHA256 加密（兼容旧数据）
        return hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest()


def verify_password(password, hashed):
    """
    验证密码（支持 BCrypt 和 SHA256）
    :param password: 明文密码
    :param hashed: 数据库中的密码哈希
    :return: 是否匹配
    """
    if not hashed:
        return False
    
    # 判断是否为 BCrypt 格式（$2b$ 或 $2a$ 开头）
    if hashed.startswith('$2'):
        if HAS_BCRYPT:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        else:
            logger.error("数据库使用 BCrypt 加密，但未安装 bcrypt 库")
            return False
    else:
        # SHA256 格式
        return hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest() == hashed


def generate_token(length=32):
    """
    生成随机令牌
    :param length: 令牌长度
    :return: 随机字符串
    """
    return secrets.token_hex(length)


def validate_password(password):
    """
    验证密码强度
    :param password: 密码
    :return: (是否有效, 错误信息)
    """
    if len(password) < 6:
        return False, '密码长度至少6位'
    if len(password) > 20:
        return False, '密码长度不能超过20位'
    return True, ''


def validate_phone(phone):
    """
    验证手机号格式
    :param phone: 手机号
    :return: 是否有效
    """
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_email(email):
    """
    验证邮箱格式
    :param email: 邮箱
    :return: 是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_id_card(id_card):
    """
    验证身份证号格式
    :param id_card: 身份证号
    :return: 是否有效
    """
    pattern = r'(\d{15}$)|(\d{17}([0-9]|X)$)'
    return bool(re.match(pattern, id_card))


def sanitize_filename(filename):
    """
    清理文件名，防止路径遍历攻击
    :param filename: 原始文件名
    :return: 安全的文件名
    """
    # 移除路径分隔符和危险字符
    filename = re.sub(r'[\\/:*?"<>|]', '', filename)
    # 限制长度
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:95] + '.' + ext if ext else name[:100]
    return filename


def login_required(f):
    """
    登录验证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return {'success': False, 'message': '请先登录'}, 401
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    管理员权限验证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return {'success': False, 'message': '请先登录'}, 401
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        # 兼容旧数据库：如果没有 role 字段或 role 为 admin，则允许访问
        user_role = session.get('role', 'staff')
        if user_role != 'admin':
            if request.is_json:
                return {'success': False, 'message': '权限不足'}, 403
            flash('权限不足', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    """
    管理员或宿管权限验证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return {'success': False, 'message': '请先登录'}, 401
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        # 兼容旧数据库：如果没有 role 字段，默认允许访问
        user_role = session.get('role', 'staff')
        if user_role not in ['admin', 'manager', 'staff']:
            if request.is_json:
                return {'success': False, 'message': '权限不足'}, 403
            flash('权限不足', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def log_operation(module, action, description=''):
    """
    记录操作日志的装饰器
    :param module: 操作模块
    :param action: 操作类型
    :param description: 操作描述
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from utils.database import execute_update
            import time
            
            start_time = time.time()
            user_id = session.get('user_id')
            username = session.get('username', 'anonymous')
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')[:500]
            
            try:
                result = f(*args, **kwargs)
                status = 1
                error_msg = ''
            except Exception as e:
                status = 0
                error_msg = str(e)
                raise
            finally:
                execution_time = int((time.time() - start_time) * 1000)
                
                # 异步记录日志，不阻塞主流程
                try:
                    sql = """
                        INSERT INTO operation_log 
                        (user_id, username, action, module, description, 
                         request_method, request_url, ip_address, user_agent, 
                         execution_time, status, error_msg)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    execute_update(sql, (
                        user_id, username, action, module, description,
                        request.method, request.url, ip_address, user_agent,
                        execution_time, status, error_msg
                    ))
                except Exception as log_e:
                    logger.error(f"记录操作日志失败: {str(log_e)}")
            
            return result
        return decorated_function
    return decorator
