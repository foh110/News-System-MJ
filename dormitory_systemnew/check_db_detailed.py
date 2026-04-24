"""
数据库表结构详细检查脚本
"""
import pymysql
from config import Config

conn = pymysql.connect(
    host=Config.DB_CONFIG['host'],
    port=Config.DB_CONFIG['port'],
    user=Config.DB_CONFIG['user'],
    password=Config.DB_CONFIG['password'],
    database=Config.DB_CONFIG['database'],
    charset=Config.DB_CONFIG['charset'],
    cursorclass=pymysql.cursors.DictCursor
)

print("=" * 80)
print("数据库表结构详细检查报告")
print("=" * 80)

with conn.cursor() as cursor:
    # 1. 检查 dormitory 表
    print("\n【1】dormitory 表结构")
    print("-" * 80)
    cursor.execute("SHOW COLUMNS FROM dormitory")
    cols = cursor.fetchall()
    print(f"字段列表:")
    for col in cols:
        print(f"  - {col['Field']:20s} {col['Type']:25s} Null:{col['Null']:5s} Key:{col['Key']:5s}")
    
    # 2. 检查 student 表
    print("\n【2】student 表结构")
    print("-" * 80)
    cursor.execute("SHOW COLUMNS FROM student")
    cols = cursor.fetchall()
    print(f"字段列表:")
    for col in cols:
        print(f"  - {col['Field']:20s} {col['Type']:25s} Null:{col['Null']:5s} Key:{col['Key']:5s}")
    
    # 3. 检查 building 表
    print("\n【3】building 表结构")
    print("-" * 80)
    cursor.execute("SHOW COLUMNS FROM building")
    cols = cursor.fetchall()
    print(f"字段列表:")
    for col in cols:
        print(f"  - {col['Field']:20s} {col['Type']:25s} Null:{col['Null']:5s} Key:{col['Key']:5s}")
    
    # 4. 检查 dormitory 表中是否有重复的 building_no
    print("\n【4】检查 dormitory 表是否有重复字段")
    print("-" * 80)
    cursor.execute("""
        SELECT COLUMN_NAME, COUNT(*) as cnt 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'dormitory'
        GROUP BY COLUMN_NAME 
        HAVING cnt > 1
    """, (Config.DB_CONFIG['database'],))
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"❌ 发现重复字段:")
        for dup in duplicates:
            print(f"   - {dup['COLUMN_NAME']} (出现{dup['cnt']}次)")
    else:
        print("✅ 无重复字段")
    
    # 5. 检查 student 表中是否有重复的 building_no
    print("\n【5】检查 student 表是否有重复字段")
    print("-" * 80)
    cursor.execute("""
        SELECT COLUMN_NAME, COUNT(*) as cnt 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'student'
        GROUP BY COLUMN_NAME 
        HAVING cnt > 1
    """, (Config.DB_CONFIG['database'],))
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"❌ 发现重复字段:")
        for dup in duplicates:
            print(f"   - {dup['COLUMN_NAME']} (出现{dup['cnt']}次)")
    else:
        print("✅ 无重复字段")
    
    # 6. 查看 dormitory 表实际数据
    print("\n【6】dormitory 表实际数据（前 5 条）")
    print("-" * 80)
    cursor.execute("SELECT * FROM dormitory LIMIT 5")
    rows = cursor.fetchall()
    if rows:
        print(f"列名：{list(rows[0].keys())}")
        for row in rows:
            print(f"  {row}")
    else:
        print("  (空表)")
    
    # 7. 查看 student 表实际数据
    print("\n【7】student 表实际数据（前 5 条）")
    print("-" * 80)
    cursor.execute("SELECT * FROM student LIMIT 5")
    rows = cursor.fetchall()
    if rows:
        print(f"列名：{list(rows[0].keys())}")
        for row in rows:
            print(f"  {row}")
    else:
        print("  (空表)")
    
    # 8. 查看 building 表实际数据
    print("\n【8】building 表实际数据（前 5 条）")
    print("-" * 80)
    cursor.execute("SELECT * FROM building LIMIT 5")
    rows = cursor.fetchall()
    if rows:
        print(f"列名：{list(rows[0].keys())}")
        for row in rows:
            print(f"  {row}")
    else:
        print("  (空表)")
    
    # 9. 测试插入 dormitory
    print("\n【9】测试插入 dormitory")
    print("-" * 80)
    try:
        cursor.execute("""
            INSERT INTO dormitory (building_no, dormitory_no, capacity, deleted) 
            VALUES (%s, %s, %s, %s)
        """, ('TEST_DORM', '999', 4, 0))
        conn.commit()
        print(f"✅ 插入成功")
        cursor.execute("DELETE FROM dormitory WHERE building_no = 'TEST_DORM' AND dormitory_no = '999'")
        conn.commit()
        print(f"✅ 测试数据已清理")
    except Exception as e:
        print(f"❌ 插入失败：{str(e)}")
    
    # 10. 测试插入 student
    print("\n【10】测试插入 student")
    print("-" * 80)
    try:
        cursor.execute("""
            INSERT INTO student (student_no, name, gender, deleted) 
            VALUES (%s, %s, %s, %s)
        """, ('TEST_STU', '测试', '男', 0))
        conn.commit()
        print(f"✅ 插入成功")
        cursor.execute("DELETE FROM student WHERE student_no = 'TEST_STU'")
        conn.commit()
        print(f"✅ 测试数据已清理")
    except Exception as e:
        print(f"❌ 插入失败：{str(e)}")
    
    # 11. 检查字符集
    print("\n【11】表和列的字符集")
    print("-" * 80)
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME IN ('dormitory', 'student', 'building')
        ORDER BY TABLE_NAME, COLUMN_NAME
    """, (Config.DB_CONFIG['database'],))
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row['TABLE_NAME']:15s} {row['COLUMN_NAME']:20s} "
              f"charset:{row['CHARACTER_SET_NAME'] or 'NULL':15s} "
              f"collation:{row['COLLATION_NAME'] or 'NULL':15s}")

conn.close()
print("\n" + "=" * 80)
print("检查完成")
print("=" * 80)
