-- 检查并修复 admin 账号角色
-- 先查看当前 admin 账号信息
SELECT id, username, real_name, role, status FROM sys_user WHERE username = 'admin';

-- 修复 admin 角色
UPDATE sys_user SET role = 'admin' WHERE username = 'admin';

-- 验证修复结果
SELECT id, username, real_name, role, status FROM sys_user WHERE username = 'admin';
