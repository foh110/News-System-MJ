"""
密码修复脚本
用于更新现有数据库中的用户密码，使其与系统密码加密方式一致

使用方法：
1. 确保数据库配置正确（config.py）
2. 运行此脚本：python fix_password.py
3. 按照提示输入要更新的用户名和新密码
"""
import sys
import os
import hashlib

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from pymysql.cursors import DictCursor
from config import Config

# 密码盐值（必须与 security.py 中的一致）
PASSWORD_SALT = 'dorm_system_2026'


def pwd_hash_sha256(password):
    """
    使用 SHA256 + 盐值加密密码
    与 security.py 中的 pwd_hash 函数保持一致（当没有 bcrypt 时）
    """
    return hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest()


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(
            host=Config.DB_CONFIG['host'],
            port=Config.DB_CONFIG['port'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database'],
            charset=Config.DB_CONFIG['charset'],
            cursorclass=DictCursor
        )
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return None


def list_users(conn):
    """列出所有用户"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username, real_name FROM sys_user WHERE deleted = 0")
        users = cursor.fetchall()
    
    print("\n📋 当前用户列表：")
    print("-" * 60)
    print(f"{'ID':<6} {'用户名':<15} {'姓名':<15}")
    print("-" * 60)
    for user in users:
        print(f"{user['id']:<6} {user['username']:<15} {user['real_name'] or '-':<15}")
    print("-" * 60)
    return users


def update_password(conn, username, new_password):
    """更新用户密码"""
    hashed_password = pwd_hash_sha256(new_password)
    
    with conn.cursor() as cursor:
        # 检查用户是否存在
        cursor.execute("SELECT id FROM sys_user WHERE username = %s AND deleted = 0", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ 用户 '{username}' 不存在")
            return False
        
        # 更新密码
        cursor.execute(
            "UPDATE sys_user SET password = %s WHERE username = %s",
            (hashed_password, username)
        )
        conn.commit()
        
        print(f"✅ 用户 '{username}' 密码已更新")
        print(f"   新密码哈希: {hashed_password[:20]}...")
        return True


def reset_admin_password(conn):
    """重置管理员密码为默认值 admin123"""
    default_password = 'admin123'
    hashed = pwd_hash_sha256(default_password)
    
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE sys_user SET password = %s WHERE username = 'admin' AND deleted = 0",
            (hashed,)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ 管理员密码已重置为: {default_password}")
            print(f"   密码哈希: {hashed}")
        else:
            print("⚠️ 未找到管理员账号，尝试创建...")
            cursor.execute(
                """INSERT INTO sys_user (username, password, real_name, status) 
                   VALUES ('admin', %s, '系统管理员', 1)""",
                (hashed,)
            )
            conn.commit()
            print(f"✅ 已创建管理员账号，密码: {default_password}")


def main():
    print("=" * 60)
    print("🔐 智慧宿舍管理系统 - 密码修复工具")
    print("=" * 60)
    
    # 连接数据库
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        while True:
            print("\n请选择操作：")
            print("1. 查看用户列表")
            print("2. 更新指定用户密码")
            print("3. 重置管理员密码为 admin123")
            print("4. 批量更新所有用户密码（交互式）")
            print("0. 退出")
            
            choice = input("\n请输入选项 [0-4]: ").strip()
            
            if choice == '1':
                list_users(conn)
            
            elif choice == '2':
                list_users(conn)
                username = input("请输入用户名: ").strip()
                if not username:
                    print("❌ 用户名不能为空")
                    continue
                new_password = input("请输入新密码: ").strip()
                if not new_password:
                    print("❌ 密码不能为空")
                    continue
                if len(new_password) < 6:
                    print("❌ 密码长度至少6位")
                    continue
                update_password(conn, username, new_password)
            
            elif choice == '3':
                confirm = input("确认重置管理员密码为 admin123？[y/N]: ").strip().lower()
                if confirm == 'y':
                    reset_admin_password(conn)
            
            elif choice == '4':
                users = list_users(conn)
                default_pwd = input("请输入统一设置的密码（留空则逐个输入）: ").strip()
                
                for user in users:
                    if default_pwd:
                        new_pwd = default_pwd
                    else:
                        new_pwd = input(f"请输入用户 '{user['username']}' 的新密码: ").strip()
                        if not new_pwd or len(new_pwd) < 6:
                            print(f"⚠️ 跳过用户 '{user['username']}'")
                            continue
                    
                    update_password(conn, user['username'], new_pwd)
            
            elif choice == '0':
                print("\n👋 再见！")
                break
            
            else:
                print("❌ 无效选项，请重新输入")
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()
