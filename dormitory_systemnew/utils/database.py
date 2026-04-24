"""
数据库工具模块 - 连接管理
"""
import pymysql
from pymysql.cursors import DictCursor
import logging
from config import Config

logger = logging.getLogger('dorm')

# 尝试导入连接池，如果失败则使用普通连接
try:
    from DBUtils.PooledDB import PooledDB
    HAS_DBUTILS = True
except ImportError:
    try:
        from dbutils.pooled_db import PooledDB
        HAS_DBUTILS = True
    except ImportError:
        HAS_DBUTILS = False
        logger.warning("DBUtils 未安装，使用普通连接模式")


class DatabasePool:
    """数据库连接池单例类"""
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def init(self):
        """ 延迟初始化，确保只初始化一次 """
        if self._initialized:
            return
        self._initialized = True
        if HAS_DBUTILS:
            self._init_pool()
    
    def _init_pool(self):
        """初始化连接池"""
        try:
            self._pool = PooledDB(
                creator=pymysql,
                mincached=2,
                maxcached=5,
                maxconnections=10,
                blocking=True,
                ping=1,
                host=Config.DB_CONFIG['host'],
                port=Config.DB_CONFIG['port'],
                user=Config.DB_CONFIG['user'],
                password=Config.DB_CONFIG['password'],
                database=Config.DB_CONFIG['database'],
                charset=Config.DB_CONFIG['charset'],
                cursorclass=DictCursor
            )
            logger.info("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {str(e)}")
            self._pool = None
    
    def get_connection(self):
        """获取数据库连接"""
        if HAS_DBUTILS and self._pool:
            try:
                return self._pool.connection()
            except Exception as e:
                logger.error(f"获取连接池连接失败: {str(e)}")
        
        try:
            return pymysql.connect(
                host=Config.DB_CONFIG['host'],
                port=Config.DB_CONFIG['port'],
                user=Config.DB_CONFIG['user'],
                password=Config.DB_CONFIG['password'],
                database=Config.DB_CONFIG['database'],
                charset=Config.DB_CONFIG['charset'],
                collation=Config.DB_CONFIG.get('collation', 'utf8mb4_unicode_ci'),
                cursorclass=DictCursor,
                autocommit=True,
                connect_timeout=5,
                read_timeout=30
            )
        except Exception as e:
            logger.error(f"获取数据库连接失败: {str(e)}")
            return None
    
    def close(self):
        """关闭连接池"""
        if HAS_DBUTILS and hasattr(self, '_pool') and self._pool:
            self._pool.close()
            logger.info("数据库连接池已关闭")


_db_pool = DatabasePool()

def get_db():
    """获取数据库连接"""
    _db_pool.init()
    return _db_pool.get_connection()


def execute_query(sql, params=None, fetchone=False):
    """执行查询语句"""
    conn = get_db()
    if not conn:
        return None if fetchone else []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if fetchone:
                return cursor.fetchone()
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"查询执行失败: {sql}, 错误: {str(e)}")
        return None if fetchone else []
    finally:
        conn.close()


def execute_update(sql, params=None):
    """
    执行更新语句（INSERT/UPDATE/DELETE）
    :return: (是否成功, lastrowid或影响行数)
    """
    conn = get_db()
    if not conn:
        return False, 0
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            # 对于INSERT语句返回lastrowid，对于UPDATE/DELETE返回影响行数
            # lastrowid在有自增主键的INSERT时>0，否则为0
            result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
            return True, result
    except Exception as e:
        conn.rollback()
        logger.error(f"更新执行失败: {sql}, 错误: {str(e)}")
        return False, 0
    finally:
        conn.close()


def execute_transaction(sql_list):
    """执行事务（多条SQL）"""
    conn = get_db()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            for sql, params in sql_list:
                cursor.execute(sql, params)
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"事务执行失败: {str(e)}")
        return False
    finally:
        conn.close()


def paginate(sql, params=None, page=1, per_page=10, count_sql=None):
    """分页查询"""
    conn = get_db()
    if not conn:
        return {'items': [], 'total': 0, 'pages': 0, 'page': page, 'per_page': per_page}
    
    try:
        # 获取总数
        if count_sql:
            with conn.cursor() as cursor:
                cursor.execute(count_sql, params)
                total = cursor.fetchone()['total']
        else:
            count_sql_base = f"SELECT COUNT(*) as total FROM ({sql}) as t"
            with conn.cursor() as cursor:
                cursor.execute(count_sql_base, params)
                total = cursor.fetchone()['total']
        
        # 计算分页
        pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # 执行分页查询
        paginated_sql = f"{sql} LIMIT {per_page} OFFSET {offset}"
        with conn.cursor() as cursor:
            cursor.execute(paginated_sql, params)
            items = cursor.fetchall()
        
        return {
            'items': items,
            'total': total,
            'pages': pages,
            'page': page,
            'per_page': per_page
        }
    except Exception as e:
        logger.error(f"分页查询失败: {str(e)}")
        return {'items': [], 'total': 0, 'pages': 0, 'page': page, 'per_page': per_page}
    finally:
        conn.close()
