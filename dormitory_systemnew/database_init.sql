-- 智慧宿舍管理系统数据库初始化脚本
-- 创建数据库
CREATE DATABASE IF NOT EXISTS dormitory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dormitory_db;

-- 系统用户表
CREATE TABLE IF NOT EXISTS sys_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    real_name VARCHAR(50) COMMENT '真实姓名',
    role ENUM('admin', 'manager', 'staff') DEFAULT 'staff' COMMENT '角色：admin-超级管理员, manager-宿舍管理员, staff-普通员工',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '邮箱',
    avatar VARCHAR(255) COMMENT '头像路径',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用, 0-禁用',
    last_login DATETIME COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0 COMMENT '软删除标记'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 宿舍楼栋表
CREATE TABLE IF NOT EXISTS building (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_no VARCHAR(20) NOT NULL UNIQUE COMMENT '楼栋编号',
    building_name VARCHAR(50) NOT NULL COMMENT '楼栋名称',
    building_type ENUM('male', 'female', 'mixed') DEFAULT 'male' COMMENT '楼栋类型：male-男生楼, female-女生楼, mixed-混合楼',
    floors INT DEFAULT 6 COMMENT '楼层数',
    description TEXT COMMENT '楼栋描述',
    manager_name VARCHAR(50) COMMENT '宿管姓名',
    manager_phone VARCHAR(20) COMMENT '宿管电话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='宿舍楼栋表';

-- 宿舍信息表
CREATE TABLE IF NOT EXISTS dormitory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_no VARCHAR(20) NOT NULL COMMENT '楼栋编号',
    dormitory_no VARCHAR(20) NOT NULL COMMENT '宿舍号',
    dormitory_type ENUM('male', 'female') DEFAULT 'male' COMMENT '宿舍类型',
    capacity INT NOT NULL DEFAULT 4 COMMENT '可容纳人数',
    occupied INT DEFAULT 0 COMMENT '已入住人数',
    floor INT COMMENT '所在楼层',
    area DECIMAL(5,2) COMMENT '面积(平方米)',
    has_balcony TINYINT DEFAULT 1 COMMENT '是否有阳台',
    has_bathroom TINYINT DEFAULT 1 COMMENT '是否有独立卫生间',
    has_aircon TINYINT DEFAULT 0 COMMENT '是否有空调',
    has_heater TINYINT DEFAULT 0 COMMENT '是否有热水器',
    status ENUM('normal', 'repairing', 'full') DEFAULT 'normal' COMMENT '状态：normal-正常, repairing-维修中, full-已满',
    remark TEXT COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_building_dorm (building_no, dormitory_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='宿舍信息表';

-- 学生信息表
CREATE TABLE IF NOT EXISTS student (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_no VARCHAR(20) NOT NULL UNIQUE COMMENT '学号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    gender ENUM('男', '女') NOT NULL COMMENT '性别',
    id_card VARCHAR(18) COMMENT '身份证号',
    age INT COMMENT '年龄',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '邮箱',
    college VARCHAR(100) COMMENT '学院',
    major VARCHAR(100) COMMENT '专业',
    class_name VARCHAR(50) COMMENT '班级',
    grade VARCHAR(10) COMMENT '年级',
    building_no VARCHAR(20) COMMENT '楼栋号',
    dormitory_no VARCHAR(20) COMMENT '宿舍号',
    bed_no VARCHAR(10) COMMENT '床位号',
    check_in_date DATE COMMENT '入住日期',
    check_out_date DATE COMMENT '退宿日期',
    photo_path VARCHAR(255) COMMENT '照片路径',
    emergency_contact VARCHAR(50) COMMENT '紧急联系人',
    emergency_phone VARCHAR(20) COMMENT '紧急联系人电话',
    address TEXT COMMENT '家庭地址',
    status ENUM('checked_in', 'checked_out', 'suspended') DEFAULT 'checked_in' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生信息表';

-- 费用管理表
CREATE TABLE IF NOT EXISTS fee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fee_type ENUM('rent', 'water', 'electricity', 'network', 'other') NOT NULL COMMENT '费用类型',
    building_no VARCHAR(20) COMMENT '楼栋号',
    dormitory_no VARCHAR(20) COMMENT '宿舍号',
    student_id INT COMMENT '学生ID（个人费用时填写）',
    amount DECIMAL(10,2) NOT NULL COMMENT '金额',
    month VARCHAR(7) NOT NULL COMMENT '费用月份，格式：2024-01',
    start_date DATE COMMENT '计费开始日期',
    end_date DATE COMMENT '计费结束日期',
    usage_amount DECIMAL(10,2) COMMENT '用量（水电费）',
    unit_price DECIMAL(10,4) COMMENT '单价',
    status ENUM('unpaid', 'paid', 'overdue') DEFAULT 'unpaid' COMMENT '状态',
    pay_time DATETIME COMMENT '支付时间',
    pay_method VARCHAR(20) COMMENT '支付方式',
    remark TEXT COMMENT '备注',
    created_by INT COMMENT '创建人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='费用管理表';

-- 报修管理表
CREATE TABLE IF NOT EXISTS repair (
    id INT AUTO_INCREMENT PRIMARY KEY,
    repair_no VARCHAR(20) NOT NULL UNIQUE COMMENT '报修单号',
    building_no VARCHAR(20) NOT NULL COMMENT '楼栋号',
    dormitory_no VARCHAR(20) NOT NULL COMMENT '宿舍号',
    student_id INT COMMENT '报修学生ID',
    student_name VARCHAR(50) COMMENT '报修人姓名',
    student_phone VARCHAR(20) COMMENT '报修人电话',
    repair_type ENUM('electric', 'water', 'furniture', 'door_window', 'appliance', 'other') NOT NULL COMMENT '报修类型',
    description TEXT NOT NULL COMMENT '问题描述',
    images TEXT COMMENT '图片路径，JSON格式',
    urgency ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium' COMMENT '紧急程度',
    status ENUM('pending', 'assigned', 'processing', 'completed', 'cancelled') DEFAULT 'pending' COMMENT '状态',
    handler_id INT COMMENT '处理人ID',
    handler_name VARCHAR(50) COMMENT '处理人姓名',
    assign_time DATETIME COMMENT '分配时间',
    start_time DATETIME COMMENT '开始处理时间',
    complete_time DATETIME COMMENT '完成时间',
    solution TEXT COMMENT '解决方案',
    material_cost DECIMAL(10,2) DEFAULT 0 COMMENT '材料费用',
    labor_cost DECIMAL(10,2) DEFAULT 0 COMMENT '人工费用',
    total_cost DECIMAL(10,2) DEFAULT 0 COMMENT '总费用',
    satisfaction INT COMMENT '满意度评分 1-5',
    feedback TEXT COMMENT '评价反馈',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报修管理表';

-- 通知公告表
CREATE TABLE IF NOT EXISTS notice (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    notice_type ENUM('system', 'notice', 'warning', 'activity') DEFAULT 'notice' COMMENT '类型',
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' COMMENT '优先级',
    target_type ENUM('all', 'building', 'dormitory', 'student') DEFAULT 'all' COMMENT '目标类型',
    target_ids TEXT COMMENT '目标ID列表，JSON格式',
    attachment VARCHAR(255) COMMENT '附件路径',
    view_count INT DEFAULT 0 COMMENT '浏览次数',
    publish_time DATETIME COMMENT '发布时间',
    expire_time DATETIME COMMENT '过期时间',
    is_top TINYINT DEFAULT 0 COMMENT '是否置顶',
    status ENUM('draft', 'published', 'withdrawn') DEFAULT 'draft' COMMENT '状态',
    created_by INT COMMENT '创建人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知公告表';

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT COMMENT '用户ID',
    username VARCHAR(50) COMMENT '用户名',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    module VARCHAR(50) COMMENT '操作模块',
    description TEXT COMMENT '操作描述',
    request_method VARCHAR(10) COMMENT '请求方法',
    request_url VARCHAR(500) COMMENT '请求URL',
    request_params TEXT COMMENT '请求参数',
    response_data TEXT COMMENT '响应数据',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '浏览器信息',
    execution_time INT COMMENT '执行时间(毫秒)',
    status TINYINT DEFAULT 1 COMMENT '状态：1-成功, 0-失败',
    error_msg TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- 系统配置表
CREATE TABLE IF NOT EXISTS sys_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(255) COMMENT '描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 插入默认管理员账号
-- 密码: admin123
-- 哈希方式: SHA256(password + PASSWORD_SALT), 其中 PASSWORD_SALT = 'dorm_system_2026'
-- 计算: SHA256('admin123' + 'dorm_system_2026') = SHA256('admin123dorm_system_2026')
-- 注意: 如果系统安装了 bcrypt，建议使用 bcrypt 格式的密码（以 $2b$ 开头）
INSERT INTO sys_user (username, password, real_name, role, status) VALUES 
('admin', '240be518fabd2724ddb6f04eeb1da5967448d68e824d4daedce9cd5f1b6ef53d', '系统管理员', 'admin', 1)
ON DUPLICATE KEY UPDATE password = '240be518fabd2724ddb6f04eeb1da5967448d68e824d4daedce9cd5f1b6ef53d';

-- 插入默认系统配置
INSERT INTO sys_config (config_key, config_value, description) VALUES
('system_name', '智慧宿舍管理系统', '系统名称'),
('system_version', '2.0.0', '系统版本'),
('water_price', '3.50', '水费单价(元/吨)'),
('electricity_price', '0.60', '电费单价(元/度)'),
('rent_price', '800.00', '住宿费(元/学期)'),
('network_price', '50.00', '网费(元/月)')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- 创建索引优化查询性能
CREATE INDEX idx_student_dormitory ON student(building_no, dormitory_no);
CREATE INDEX idx_student_status ON student(status);
CREATE INDEX idx_fee_status ON fee(status, month);
CREATE INDEX idx_repair_status ON repair(status, repair_type);
CREATE INDEX idx_notice_status ON notice(status, publish_time);
CREATE INDEX idx_log_user ON operation_log(user_id, created_at);
CREATE INDEX idx_log_time ON operation_log(created_at);
