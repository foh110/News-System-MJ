"""
检查并修复 admin 账号角色
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "lyp82ndlf",
    "database": "dormitory_db",
    "charset": "utf8mb4"
}

try:
    # 连接数据库
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 查询 admin 账号
    cursor.execute("SELECT id, username, real_name, role, status FROM sys_user WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if admin_user:
        print(f"找到 admin 账号:")
        print(f"  ID: {admin_user['id']}")
        print(f"  用户名：{admin_user['username']}")
        print(f"  真实姓名：{admin_user['real_name']}")
        print(f"  角色：{admin_user['role']}")
        print(f"  状态：{'正常' if admin_user['status'] == 1 else '禁用'}")
        
        # 如果角色不是 admin，则修复
        if admin_user['role'] != 'admin':
            print(f"\n⚠️  角色不正确，当前为：{admin_user['role']}")
            print("正在修复为 admin 角色...")
            
            cursor.execute("UPDATE sys_user SET role = 'admin' WHERE username = 'admin'")
            conn.commit()
            
            print("✅ 修复完成！admin 账号现在具有管理员权限")
            print("请重新登录系统")
        else:
            print("\n✅ admin 账号角色正确")
    else:
        print("❌ 未找到 admin 账号")
        print("正在创建 admin 账号...")
        
        # 创建 admin 账号（密码：admin123）
        import hashlib
        password_hash = hashlib.sha256('admin123dorm_system_2026'.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO sys_user (username, password, real_name, role, status)
            VALUES ('admin', %s, '系统管理员', 'admin', 1)
        """, (password_hash,))
        conn.commit()
        
        print("✅ admin 账号创建成功！")
        print("用户名：admin")
        print("密码：admin123")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 错误：{e}")
    input("按回车键退出...")
