-- ============================================
-- 新闻管理系统 - 数据库初始化脚本
-- 在Aiven.io MySQL中执行此脚本
-- ============================================

-- 创建分类表
CREATE TABLE IF NOT EXISTS news_category (
    id INT NOT NULL AUTO_INCREMENT COMMENT '分类ID',
    name VARCHAR(100) NOT NULL COMMENT '分类名称',
    sort_order INT DEFAULT 0 COMMENT '排序',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻分类表';

-- 创建新闻表
CREATE TABLE IF NOT EXISTS news (
    id INT NOT NULL AUTO_INCREMENT COMMENT '新闻ID',
    title VARCHAR(255) NOT NULL COMMENT '标题',
    content TEXT COMMENT '内容',
    description VARCHAR(500) COMMENT '描述',
    image VARCHAR(500) COMMENT '封面图URL',
    author VARCHAR(100) COMMENT '作者',
    publish_time DATETIME COMMENT '发布时间',
    category_id INT COMMENT '分类ID',
    views INT DEFAULT 0 COMMENT '浏览量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_category (category_id),
    FOREIGN KEY (category_id) REFERENCES news_category(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻表';

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(加密)',
    bio VARCHAR(500) DEFAULT '这个人很懒，什么都没留下' COMMENT '个人简介',
    avatar VARCHAR(500) DEFAULT 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg' COMMENT '头像URL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 创建收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id INT NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
    user_id INT NOT NULL COMMENT '用户ID',
    news_id INT NOT NULL COMMENT '新闻ID',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    PRIMARY KEY (id),
    UNIQUE KEY idx_user_news (user_id, news_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏表';

-- 创建浏览历史表
CREATE TABLE IF NOT EXISTS histories (
    id INT NOT NULL AUTO_INCREMENT COMMENT '历史记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    news_id INT NOT NULL COMMENT '新闻ID',
    viewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
    PRIMARY KEY (id),
    KEY idx_user_news_history (user_id, news_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='浏览历史表';

-- 插入初始分类数据
INSERT INTO news_category (name, sort_order) VALUES 
('头条', 0),
('科技', 1),
('财经', 2),
('体育', 3),
('娱乐', 4)
ON DUPLICATE KEY UPDATE name=name;
