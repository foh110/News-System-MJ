-- ====================================
-- 数据库表结构检查与修复脚本
-- ====================================

-- 1. 检查 dormitory 表结构
SHOW COLUMNS FROM dormitory;

-- 2. 检查 student 表结构  
SHOW COLUMNS FROM student;

-- 3. 检查 sys_user 表结构
SHOW COLUMNS FROM sys_user;

-- 4. 查看表的创建语句（重要！可以看到字段名和字符集）
SHOW CREATE TABLE dormitory;
SHOW CREATE TABLE student;
SHOW CREATE TABLE sys_user;

-- ====================================
-- 修复方案（根据上面检查结果选择执行）
-- ====================================

-- 【方案 A】如果 dormitory 表只有 building 字段，没有 building_no：
-- ALTER TABLE dormitory CHANGE building building_no VARCHAR(20) NOT NULL COMMENT '楼栋编号';

-- 【方案 B】如果 dormitory 表同时有 building 和 building_no，删除 building：
-- ALTER TABLE dormitory DROP COLUMN building;

-- 【方案 C】如果 student 表只有 building 字段，没有 building_no：
-- ALTER TABLE student CHANGE building building_no VARCHAR(20) COMMENT '楼栋号';

-- 【方案 D】如果 student 表同时有 building 和 building_no，删除 building：
-- ALTER TABLE student DROP COLUMN building;

-- 【方案 E】添加缺失的字段（如果完全没有这些字段）
-- ALTER TABLE dormitory ADD COLUMN building_no VARCHAR(20) AFTER id;
-- UPDATE dormitory SET building_no = building WHERE building_no IS NULL;

-- 【方案 F】修复 sys_user 表缺失的字段
-- ALTER TABLE sys_user ADD COLUMN real_name VARCHAR(50) AFTER password;
-- ALTER TABLE sys_user ADD COLUMN role ENUM('admin', 'manager', 'staff') DEFAULT 'staff' AFTER real_name;
-- ALTER TABLE sys_user ADD COLUMN avatar VARCHAR(255) AFTER email;
-- ALTER TABLE sys_user ADD COLUMN status TINYINT DEFAULT 1 AFTER avatar;
-- ALTER TABLE sys_user ADD COLUMN last_login DATETIME AFTER status;

-- ====================================
-- 字符集修复（解决 collation 冲突）
-- ====================================

-- 检查数据库字符集
SHOW VARIABLES LIKE 'character_set%%';
SHOW VARIABLES LIKE 'collation%%';

-- 修复表的字符集（如果需要）
-- ALTER TABLE dormitory CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE student CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE sys_user CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ====================================
-- 测试插入（验证修复是否成功）
-- ====================================

-- 测试插入 dormitory
-- INSERT INTO dormitory (building_no, dormitory_no, capacity, deleted) VALUES ('TEST001', '999', 4, 0);
-- DELETE FROM dormitory WHERE building_no = 'TEST001' AND dormitory_no = '999';

-- 测试插入 student
-- INSERT INTO student (student_no, name, gender, deleted) VALUES ('TEST999', '测试学生', '男', 0);
-- DELETE FROM student WHERE student_no = 'TEST999';
