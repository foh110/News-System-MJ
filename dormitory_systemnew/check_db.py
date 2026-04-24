"""
数据库表结构检查和测试脚本
"""
import pymysql
from config import Config

# 连接数据库
conn = pymysql.connect(
    host=Config.DB_CONFIG['host'],
    port=Config.DB_CONFIG['port'],
    user=Config.DB_CONFIG['user'],
    password=Config.DB_CONFIG['password'],
    database=Config.DB_CONFIG['database'],
    charset=Config.DB_CONFIG['charset'],
    cursorclass=pymysql.cursors.DictCursor
)

print("=" * 60)
print("数据库表结构检查")
print("=" * 60)

with conn.cursor() as cursor:
    # 1. 检查 dormitory 表结构
    print("\n1. dormitory 表结构:")
    cursor.execute("SHOW COLUMNS FROM dormitory")
    for col in cursor.fetchall():
        print(f"   {col['Field']}: {col['Type']} (Null: {col['Null']}, Key: {col['Key']})")
    
    # 2. 检查 student 表结构
    print("\n2. student 表结构:")
    cursor.execute("SHOW COLUMNS FROM student")
    for col in cursor.fetchall():
        print(f"   {col['Field']}: {col['Type']} (Null: {col['Null']}, Key: {col['Key']})")
    
    # 3. 检查 sys_user 表结构
    print("\n3. sys_user 表结构:")
    cursor.execute("SHOW COLUMNS FROM sys_user")
    for col in cursor.fetchall():
        print(f"   {col['Field']}: {col['Type']} (Null: {col['Null']}, Key: {col['Key']})")
    
    # 4. 测试插入 dormitory
    print("\n4. 测试插入 dormitory:")
    try:
        cursor.execute("""
            INSERT INTO dormitory (building_no, dormitory_no, capacity, deleted) 
            VALUES (%s, %s, %s, %s)
        """, ('TEST001', '999', 4, 0))
        conn.commit()
        print(f"   ✅ 插入成功，lastrowid: {cursor.lastrowid}")
        
        # 删除测试数据
        cursor.execute("DELETE FROM dormitory WHERE building_no = 'TEST001' AND dormitory_no = '999'")
        conn.commit()
        print(f"   ✅ 测试数据已清理")
    except Exception as e:
        print(f"   ❌ 插入失败：{str(e)}")
    
    # 5. 测试插入 student
    print("\n5. 测试插入 student:")
    try:
        cursor.execute("""
            INSERT INTO student (student_no, name, gender, deleted) 
            VALUES (%s, %s, %s, %s)
        """, ('TEST999', '测试学生', '男', 0))
        conn.commit()
        print(f"   ✅ 插入成功，lastrowid: {cursor.lastrowid}")
        
        # 删除测试数据
        cursor.execute("DELETE FROM student WHERE student_no = 'TEST999'")
        conn.commit()
        print(f"   ✅ 测试数据已清理")
    except Exception as e:
        print(f"   ❌ 插入失败：{str(e)}")
    
    # 6. 检查字符集
    print("\n6. 数据库字符集:")
    cursor.execute("SHOW VARIABLES LIKE 'character_set%%'")
    for row in cursor.fetchall():
        print(f"   {row['Variable_name']}: {row['Value']}")
    
    cursor.execute("SHOW VARIABLES LIKE 'collation%%'")
    for row in cursor.fetchall():
        print(f"   {row['Variable_name']}: {row['Value']}")

conn.close()
print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
