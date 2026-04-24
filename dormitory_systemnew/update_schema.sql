-- 修改 dormitory 表结构
ALTER TABLE dormitory ADD COLUMN building_no VARCHAR(20) AFTER id;
UPDATE dormitory SET building_no = building WHERE building_no IS NULL AND building IS NOT NULL;
ALTER TABLE dormitory ADD COLUMN floor INT AFTER capacity;
ALTER TABLE dormitory ADD COLUMN area DECIMAL(5,2) AFTER floor;
ALTER TABLE dormitory ADD COLUMN has_balcony TINYINT DEFAULT 1 AFTER area;
ALTER TABLE dormitory ADD COLUMN has_bathroom TINYINT DEFAULT 1 AFTER has_balcony;
ALTER TABLE dormitory ADD COLUMN has_aircon TINYINT DEFAULT 0 AFTER has_bathroom;
ALTER TABLE dormitory ADD COLUMN has_heater TINYINT DEFAULT 0 AFTER has_aircon;
ALTER TABLE dormitory ADD COLUMN remark TEXT AFTER has_heater;
ALTER TABLE dormitory ADD COLUMN status ENUM('normal', 'repairing', 'full') DEFAULT 'normal' AFTER remark;
ALTER TABLE dormitory ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- 修改 sys_user 表结构
ALTER TABLE sys_user ADD COLUMN real_name VARCHAR(50) AFTER password;
ALTER TABLE sys_user ADD COLUMN role ENUM('admin', 'manager', 'staff') DEFAULT 'staff' AFTER real_name;
ALTER TABLE sys_user ADD COLUMN avatar VARCHAR(255) AFTER email;
ALTER TABLE sys_user ADD COLUMN status TINYINT DEFAULT 1 AFTER avatar;
ALTER TABLE sys_user ADD COLUMN last_login DATETIME AFTER status;
ALTER TABLE sys_user ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- 修改 student 表结构
ALTER TABLE student ADD COLUMN building_no VARCHAR(20) AFTER grade;
ALTER TABLE student ADD COLUMN bed_no VARCHAR(10) AFTER dormitory_no;
ALTER TABLE student ADD COLUMN check_in_date DATE AFTER bed_no;
ALTER TABLE student ADD COLUMN check_out_date DATE AFTER check_in_date;
ALTER TABLE student ADD COLUMN photo_path VARCHAR(255) AFTER check_out_date;
ALTER TABLE student ADD COLUMN emergency_contact VARCHAR(50) AFTER photo_path;
ALTER TABLE student ADD COLUMN emergency_phone VARCHAR(20) AFTER emergency_contact;
ALTER TABLE student ADD COLUMN address TEXT AFTER emergency_phone;
ALTER TABLE student ADD COLUMN status ENUM('checked_in', 'checked_out', 'suspended') DEFAULT 'checked_in' AFTER address;
ALTER TABLE student ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- 修改 repair 表结构
ALTER TABLE repair ADD COLUMN student_id INT AFTER dormitory_no;
ALTER TABLE repair ADD COLUMN images TEXT AFTER description;
ALTER TABLE repair ADD COLUMN handler_id INT AFTER status;
ALTER TABLE repair ADD COLUMN assign_time DATETIME AFTER handler_name;
ALTER TABLE repair ADD COLUMN start_time DATETIME AFTER assign_time;
ALTER TABLE repair ADD COLUMN complete_time DATETIME AFTER start_time;
ALTER TABLE repair ADD COLUMN solution TEXT AFTER complete_time;
ALTER TABLE repair ADD COLUMN material_cost DECIMAL(10,2) DEFAULT 0 AFTER solution;
ALTER TABLE repair ADD COLUMN labor_cost DECIMAL(10,2) DEFAULT 0 AFTER material_cost;
ALTER TABLE repair ADD COLUMN total_cost DECIMAL(10,2) DEFAULT 0 AFTER labor_cost;
ALTER TABLE repair ADD COLUMN satisfaction INT AFTER total_cost;
ALTER TABLE repair ADD COLUMN feedback TEXT AFTER satisfaction;
ALTER TABLE repair ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- 修改 fee 表结构
ALTER TABLE fee ADD COLUMN start_date DATE AFTER month;
ALTER TABLE fee ADD COLUMN end_date DATE AFTER start_date;
ALTER TABLE fee ADD COLUMN usage_amount DECIMAL(10,2) AFTER end_date;
ALTER TABLE fee ADD COLUMN unit_price DECIMAL(10,4) AFTER usage_amount;
ALTER TABLE fee ADD COLUMN pay_time DATETIME AFTER status;
ALTER TABLE fee ADD COLUMN pay_method VARCHAR(20) AFTER pay_time;
ALTER TABLE fee ADD COLUMN remark TEXT AFTER pay_method;
ALTER TABLE fee ADD COLUMN created_by INT AFTER remark;
ALTER TABLE fee ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- 修改 notice 表结构
ALTER TABLE notice ADD COLUMN target_type ENUM('all', 'building', 'dormitory', 'student') DEFAULT 'all' AFTER priority;
ALTER TABLE notice ADD COLUMN target_ids TEXT AFTER target_type;
ALTER TABLE notice ADD COLUMN attachment VARCHAR(255) AFTER target_ids;
ALTER TABLE notice ADD COLUMN view_count INT DEFAULT 0 AFTER attachment;
ALTER TABLE notice ADD COLUMN publish_time DATETIME AFTER view_count;
ALTER TABLE notice ADD COLUMN expire_time DATETIME AFTER publish_time;
ALTER TABLE notice ADD COLUMN is_top TINYINT DEFAULT 0 AFTER expire_time;
ALTER TABLE notice ADD COLUMN created_by INT AFTER status;
ALTER TABLE notice ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;
