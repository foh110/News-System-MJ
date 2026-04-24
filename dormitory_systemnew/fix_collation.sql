-- 紧急修复：字符集冲突问题
-- ====================================

-- 1. 修改数据库默认字符集
ALTER DATABASE dormitory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 修改所有表的字符集（逐个执行）
ALTER TABLE dormitory CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE student CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE sys_user CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE building CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE repair CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE fee CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE notice CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. 验证修复结果
SHOW TABLE STATUS FROM dormitory_db WHERE Collation LIKE '%utf8mb4%';

-- 4. 查看每个表的字符集
SELECT table_name, table_collation 
FROM information_schema.tables 
WHERE table_schema = 'dormitory_db';
