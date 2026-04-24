"""
通用工具函数模块
"""
import os
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from werkzeug.utils import secure_filename
from config import Config, BASE_DIR
import logging

logger = logging.getLogger('dorm')


def allowed_file(filename, allowed_extensions=None):
    """
    检查文件扩展名是否允许
    :param filename: 文件名
    :param allowed_extensions: 允许的扩展名集合
    :return: 是否允许
    """
    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def allowed_image(filename):
    """
    检查是否为允许的图片文件
    :param filename: 文件名
    :return: 是否允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS


def generate_filename(original_filename, prefix=''):
    """
    生成安全的唯一文件名
    :param original_filename: 原始文件名
    :param prefix: 前缀
    :return: 新文件名
    """
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_name = f"{prefix}_{uuid.uuid4().hex[:16]}.{ext}" if prefix else f"{uuid.uuid4().hex[:16]}.{ext}"
    return secure_filename(unique_name)


def save_upload_file(file, folder=None, prefix=''):
    """
    保存上传的文件
    :param file: 文件对象
    :param folder: 保存目录
    :param prefix: 文件名前缀
    :return: (是否成功, 文件路径或错误信息)
    """
    if folder is None:
        folder = Config.UPLOAD_FOLDER
    
    try:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        
        filename = generate_filename(file.filename, prefix)
        filepath = os.path.join(folder, filename)
        file.save(filepath)
        
        # 返回相对路径
        rel_path = os.path.relpath(filepath, BASE_DIR).replace('\\', '/')
        return True, f"/{rel_path}"
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        return False, str(e)


def delete_file(filepath):
    """
    删除文件
    :param filepath: 文件路径
    :return: 是否成功
    """
    try:
        # 处理相对路径
        if filepath.startswith('/'):
            filepath = filepath[1:]
        full_path = os.path.join(BASE_DIR, filepath)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        return False


def format_datetime(dt, fmt='%Y-%m-%d %H:%M:%S'):
    """
    格式化日期时间
    :param dt: 日期时间对象
    :param fmt: 格式字符串
    :return: 格式化后的字符串
    """
    if dt is None:
        return ''
    if isinstance(dt, str):
        return dt
    return dt.strftime(fmt)


def format_date(d, fmt='%Y-%m-%d'):
    """
    格式化日期
    :param d: 日期对象
    :param fmt: 格式字符串
    :return: 格式化后的字符串
    """
    if d is None:
        return ''
    if isinstance(d, str):
        return d
    return d.strftime(fmt)


def format_decimal(value, decimal_places=2):
    """
    格式化小数
    :param value: 数值
    :param decimal_places: 小数位数
    :return: 格式化后的字符串
    """
    if value is None:
        return '0.00'
    return f"{float(value):.{decimal_places}f}"


def json_serial(obj):
    """
    JSON序列化辅助函数
    :param obj: 对象
    :return: 可序列化的值
    """
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def to_json(data):
    """
    将数据转换为JSON字符串
    :param data: 数据
    :return: JSON字符串
    """
    return json.dumps(data, default=json_serial, ensure_ascii=False)


def parse_json(json_str):
    """
    解析JSON字符串
    :param json_str: JSON字符串
    :return: 解析后的数据
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"解析JSON失败: {str(e)}")
        return None


def generate_repair_no():
    """
    生成报修单号
    :return: 报修单号
    """
    return f"BX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"


def get_age_from_id_card(id_card):
    """
    从身份证号获取年龄
    :param id_card: 身份证号
    :return: 年龄
    """
    try:
        if len(id_card) == 18:
            birth_year = int(id_card[6:10])
        elif len(id_card) == 15:
            birth_year = int('19' + id_card[6:8])
        else:
            return None
        return datetime.now().year - birth_year
    except:
        return None


def calculate_bed_rate(occupied, capacity):
    """
    计算床位使用率
    :param occupied: 已入住人数
    :param capacity: 总容量
    :return: 使用率字符串
    """
    if not capacity or capacity <= 0:
        return '0.0%'
    rate = (occupied or 0) / capacity * 100
    return f"{rate:.1f}%"


def truncate_string(s, length=50, suffix='...'):
    """
    截断字符串
    :param s: 字符串
    :param length: 最大长度
    :param suffix: 后缀
    :return: 截断后的字符串
    """
    if not s:
        return ''
    if len(s) <= length:
        return s
    return s[:length - len(suffix)] + suffix


def get_client_ip():
    """
    获取客户端真实IP
    :return: IP地址
    """
    from flask import request
    
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def build_query_conditions(base_sql, conditions, params):
    """
    构建查询条件
    :param base_sql: 基础SQL
    :param conditions: 条件列表 [(field, operator, value), ...]
    :param params: 参数列表
    :return: 完整SQL和参数
    """
    where_clauses = []
    
    for field, operator, value in conditions:
        if value is None or value == '':
            continue
        
        if operator == 'like':
            where_clauses.append(f"{field} LIKE %s")
            params.append(f"%{value}%")
        elif operator == 'eq':
            where_clauses.append(f"{field} = %s")
            params.append(value)
        elif operator == 'in':
            placeholders = ','.join(['%s'] * len(value))
            where_clauses.append(f"{field} IN ({placeholders})")
            params.extend(value)
        elif operator == 'gt':
            where_clauses.append(f"{field} > %s")
            params.append(value)
        elif operator == 'lt':
            where_clauses.append(f"{field} < %s")
            params.append(value)
        elif operator == 'gte':
            where_clauses.append(f"{field} >= %s")
            params.append(value)
        elif operator == 'lte':
            where_clauses.append(f"{field} <= %s")
            params.append(value)
    
    if where_clauses:
        if 'WHERE' in base_sql.upper():
            sql = base_sql + ' AND ' + ' AND '.join(where_clauses)
        else:
            sql = base_sql + ' WHERE ' + ' AND '.join(where_clauses)
    else:
        sql = base_sql
    
    return sql, params
