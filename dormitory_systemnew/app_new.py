"""
智慧宿舍管理系统 v2.0
企业级宿舍管理解决方案
"""
from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file, jsonify
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import pandas as pd
import json
from dbutils.pooled_db import PooledDB

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, config
from utils.database import get_db, execute_query, execute_update, execute_transaction, paginate
from utils.security import (
    pwd_hash, verify_password, validate_password, validate_phone, validate_email, 
    login_required, admin_required, manager_required, log_operation
)
from utils.helpers import (
    allowed_file, allowed_image, save_upload_file, delete_file,
    format_datetime, format_date, format_decimal, to_json, parse_json,
    generate_repair_no, calculate_bed_rate, get_client_ip, build_query_conditions
)

# 创建 Flask 应用
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化 CSRF 保护
    csrf = CSRFProtect(app)
    # 注意：登录页面已包含CSRF token，无需额外豁免
    
    # 创建必要目录
    for folder in ['logs', 'backups', Config.UPLOAD_FOLDER, Config.AVATAR_FOLDER]:
        os.makedirs(folder, exist_ok=True)
    
    # 配置日志
    setup_logging(app)
    
    # 初始化数据库连接池（启动时预创建连接，避免首次请求卡顿）
    from utils.database import _db_pool
    _db_pool.init()
    if _db_pool._pool:
        app.logger.info("✅ 数据库连接池已就绪")
    else:
        app.logger.warning("⚠️ 数据库连接池未启用，使用普通连接模式")
    
    return app


def setup_logging(app):
    """配置日志系统"""
    if not app.debug:
        # 文件日志
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(Config.LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        
        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        
        # 配置根日志记录器
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(Config.LOG_LEVEL)


# 创建应用实例
app = create_app()
logger = logging.getLogger('dorm')


# ==================== 上下文处理器 ====================
@app.context_processor
def inject_globals():
    """注入全局变量到模板"""
    return {
        'system_name': Config.SYSTEM_NAME,
        'system_version': Config.SYSTEM_VERSION,
        'now': datetime.now(),
        'format_datetime': format_datetime,
        'format_date': format_date,
        'format_decimal': format_decimal
    }


# ==================== 错误处理 ====================
@app.errorhandler(404)
def not_found_error(error):
    if request.is_json:
        return jsonify({'success': False, 'message': '页面不存在'}), 404
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器错误: {str(error)}")
    if request.is_json:
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    if request.is_json:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    flash('权限不足', 'error')
    return redirect(url_for('index'))


# ==================== 认证路由 ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    error_msg = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            error_msg = '请输入用户名和密码'
        else:
            user = execute_query(
                "SELECT * FROM sys_user WHERE username = %s AND deleted = 0",
                (username,), fetchone=True
            )
            
            # 使用统一的密码验证函数（支持 BCrypt 和 SHA256）
            if user and verify_password(password, user['password']):
                # 设置 session
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['real_name'] = user.get('real_name', '')
                session['role'] = user.get('role', 'staff')
                session['avatar'] = user.get('avatar', '')
                
                # 更新最后登录时间（兼容旧数据库，如果字段不存在则忽略）
                try:
                    execute_update(
                        "UPDATE sys_user SET last_login = NOW() WHERE id = %s",
                        (user['id'],)
                    )
                except Exception as e:
                    logger.debug(f"未更新最后登录时间：{str(e)}")
                
                logger.info(f"用户 {username} 登录成功")
                flash('登录成功', 'success')
                return redirect(url_for('index'))
            else:
                error_msg = '用户名或密码错误'
                logger.warning(f"用户 {username} 登录失败")
    
    return render_template('login_s.html', error_msg=error_msg)


@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    logger.info(f"用户 {session.get('username')} 退出登录")
    session.clear()
    flash('已退出登录', 'success')
    return redirect(url_for('login'))


# ==================== 首页路由 ====================
@app.route('/')
@login_required
def index():
    """系统首页 - 数据仪表盘（优化版：单次连接批量查询）"""
    from utils.database import get_db
    
    stats = {
        'total_students': 0, 'total_dorms': 0, 'total_buildings': 0,
        'bed_rate': '0%', 'male_count': 0, 'female_count': 0,
        'pending_repairs': 0, 'unpaid_fees': 0, 'new_notices': 0
    }
    notices = []
    recent_repairs = []
    trend_data = {'months': [], 'male': [], 'female': [], 'total': []}
    
    conn = get_db()
    if not conn:
        return render_template('index_new.html', stats=stats, notices=notices, recent_repairs=recent_repairs)
    
    try:
        with conn.cursor() as cursor:
            # 1. 学生总数
            cursor.execute("SELECT COUNT(*) as c FROM student WHERE deleted = 0")
            stats['total_students'] = cursor.fetchone()['c']
            
            # 2. 宿舍总数
            cursor.execute("SELECT COUNT(*) as c FROM dormitory WHERE deleted = 0")
            stats['total_dorms'] = cursor.fetchone()['c']
            
            # 3. 楼栋总数
            cursor.execute("SELECT COUNT(*) as c FROM building WHERE deleted = 0")
            stats['total_buildings'] = cursor.fetchone()['c']
            
            # 4. 性别统计（单次查询，避免字符集冲突）
            try:
                cursor.execute("SELECT gender, COUNT(*) as c FROM student WHERE deleted = 0 GROUP BY gender")
                for row in cursor.fetchall():
                    if row['gender'] == '男':
                        stats['male_count'] = row['c']
                    elif row['gender'] == '女':
                        stats['female_count'] = row['c']
            except Exception as e:
                logger.debug(f"性别统计失败：{str(e)}")
            
            # 5. 床位使用率
            cursor.execute("SELECT SUM(capacity) as cap, SUM(occupied) as occ FROM dormitory WHERE deleted = 0")
            row = cursor.fetchone()
            if row and row['cap']:
                stats['bed_rate'] = calculate_bed_rate(row['occ'] or 0, row['cap'])
            
            # 6. 待处理报修
            cursor.execute("SELECT COUNT(*) as c FROM repair WHERE status IN ('pending','assigned','processing') AND deleted = 0")
            stats['pending_repairs'] = cursor.fetchone()['c']
            
            # 7. 未缴费账单
            cursor.execute("SELECT COUNT(*) as c FROM fee WHERE status = 'unpaid' AND deleted = 0")
            stats['unpaid_fees'] = cursor.fetchone()['c']
            
            # 8. 最新公告
            cursor.execute("""SELECT id, title, notice_type, created_at FROM notice 
                WHERE status = 'published' AND deleted = 0 AND (expire_time IS NULL OR expire_time > NOW())
                ORDER BY is_top DESC, publish_time DESC LIMIT 5""")
            notices = cursor.fetchall()
            
            # 9. 最近报修
            cursor.execute("""SELECT r.*, d.building_no, d.dormitory_no FROM repair r
                LEFT JOIN dormitory d ON r.dormitory_no = d.dormitory_no
                WHERE r.deleted = 0 ORDER BY r.created_at DESC LIMIT 5""")
            recent_repairs = cursor.fetchall()
            
            # 10. 入住趋势（最近 6 个月）
            try:
                cursor.execute("""
                    SELECT DATE_FORMAT(create_time, '%Y-%m') as month, 
                           SUM(CASE WHEN gender = '男' THEN 1 ELSE 0 END) as male_count,
                           SUM(CASE WHEN gender = '女' THEN 1 ELSE 0 END) as female_count,
                           COUNT(*) as total
                    FROM student 
                    WHERE deleted = 0 
                    AND create_time >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                    GROUP BY DATE_FORMAT(create_time, '%Y-%m')
                    ORDER BY month
                """)
                trend_rows = cursor.fetchall()
                for row in trend_rows:
                    trend_data['months'].append(row['month'])
                    trend_data['male'].append(row['male_count'] or 0)
                    trend_data['female'].append(row['female_count'] or 0)
                    trend_data['total'].append(row['total'] or 0)
            except Exception as e:
                logger.debug(f"入住趋势查询失败：{str(e)}")
            
    except Exception as e:
        logger.error(f"首页数据加载失败：{str(e)}")
    finally:
        conn.close()
        
    return render_template('index_new.html', stats=stats, notices=notices, recent_repairs=recent_repairs, trend_data=trend_data)


# ==================== 学生管理路由 ====================
@app.route('/students')
@login_required
def students():
    """学生列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    building_no = request.args.get('building_no', '').strip()
    dormitory_no = request.args.get('dormitory_no', '').strip()
    status = request.args.get('status', '').strip()
    gender = request.args.get('gender', '').strip()
    
    # 构建查询条件
    base_sql = """
        SELECT s.student_no, s.name, s.gender, s.age, s.phone, s.email,
               s.college, s.major, s.class_name, s.grade,
               s.building_no, s.dormitory_no, s.bed_no,
               s.status, s.create_time, s.id,
               b.building_name, d.capacity, d.occupied
        FROM student s
        LEFT JOIN building b ON s.building_no = b.building_no
        LEFT JOIN dormitory d ON s.dormitory_no = d.dormitory_no AND d.building_no = s.building_no
        WHERE s.deleted = 0
    """
    conditions = []
    params = []
    
    if keyword:
        conditions.append("(s.student_no LIKE %s OR s.name LIKE %s OR s.phone LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    
    if building_no:
        conditions.append("s.building_no = %s")
        params.append(building_no)
    
    if dormitory_no:
        conditions.append("s.dormitory_no = %s")
        params.append(dormitory_no)
    
    if status:
        conditions.append("s.status = %s")
        params.append(status)
    
    if gender:
        conditions.append("s.gender = %s")
        params.append(gender)
    
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)
    
    base_sql += " ORDER BY s.create_time DESC"
    
    # 分页查询
    pagination = paginate(base_sql, params, page, per_page)
    
    # 获取楼栋列表（用于筛选）
    buildings = execute_query("SELECT building_no, building_name FROM building WHERE deleted = 0 ORDER BY building_no")
    
    # 获取所有宿舍号（用于下拉框）
    dorms = execute_query(
        "SELECT dormitory_no, building_no FROM dormitory WHERE deleted = 0 AND status != 'full' ORDER BY building_no, dormitory_no"
    )
    # 格式化宿舍号显示：楼栋号 + 宿舍号
    dormitory_nos = []
    for d in dorms:
        dormitory_nos.append(f"{d['building_no']}-{d['dormitory_no']}")
    
    return render_template('students.html', 
                         students=pagination['items'],
                         pagination=pagination,
                         buildings=buildings,
                         keyword=keyword,
                         building_no=building_no,
                         dormitory_no=dormitory_no,
                         status=status,
                         gender=gender)


@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def student_add():
    """新增学生"""
    if request.method == 'POST':
        # 获取表单数据
        data = {
            'student_no': request.form.get('student_no', '').strip(),
            'name': request.form.get('name', '').strip(),
            'gender': request.form.get('gender', '').strip(),
            'id_card': request.form.get('id_card', '').strip(),
            'age': request.form.get('age', type=int),
            'phone': request.form.get('phone', '').strip(),
            'email': request.form.get('email', '').strip(),
            'college': request.form.get('college', '').strip(),
            'major': request.form.get('major', '').strip(),
            'class_name': request.form.get('class_name', '').strip(),
            'grade': request.form.get('grade', '').strip(),
            'building_no': request.form.get('building_no', '').strip(),
            'dormitory_no': request.form.get('dormitory_no', '').strip(),
            'bed_no': request.form.get('bed_no', '').strip(),
            'emergency_contact': request.form.get('emergency_contact', '').strip(),
            'emergency_phone': request.form.get('emergency_phone', '').strip(),
            'address': request.form.get('address', '').strip()
        }
        
        # 数据验证
        if not data['student_no'] or not data['name'] or not data['gender']:
            return jsonify({'success': False, 'message': '学号、姓名、性别为必填项'})
        
        if len(data['student_no']) < 5 or len(data['student_no']) > 20:
            return jsonify({'success': False, 'message': '学号长度应在5-20位之间'})
        
        if data['phone'] and not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': '手机号格式不正确'})
        
        if data['email'] and not validate_email(data['email']):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})
        
        # 检查学号是否已存在
        existing = execute_query(
            "SELECT id FROM student WHERE student_no = %s AND deleted = 0",
            (data['student_no'],), fetchone=True
        )
        if existing:
            return jsonify({'success': False, 'message': '该学号已存在'})
        
        # 检查宿舍是否存在且有空位
        if data['dormitory_no']:
            dorm = execute_query(
                """SELECT d.*, b.building_type 
                   FROM dormitory d 
                   JOIN building b ON d.building_no = b.building_no
                   WHERE d.dormitory_no = %s AND d.building_no = %s AND d.deleted = 0""",
                (data['dormitory_no'], data['building_no']), fetchone=True
            )
            
            if not dorm:
                return jsonify({'success': False, 'message': '所选宿舍不存在'})
            
            if dorm['occupied'] >= dorm['capacity']:
                return jsonify({'success': False, 'message': '该宿舍已满'})
            
            # 检查性别是否匹配
            if (dorm['building_type'] == 'male' and data['gender'] != '男') or \
               (dorm['building_type'] == 'female' and data['gender'] != '女'):
                return jsonify({'success': False, 'message': '学生性别与宿舍类型不匹配'})
        
        # 处理照片上传
        photo = request.files.get('photo')
        photo_path = ''
        if photo and allowed_image(photo.filename):
            success, result = save_upload_file(photo, prefix=f"stu_{data['student_no']}")
            if success:
                photo_path = result
        
        # 插入学生数据
        sql = """
            INSERT INTO student (
                student_no, name, gender, age, phone, email,
                college, major, class_name, grade, building_no, dormitory_no, bed_no,
                emergency_contact, emergency_phone, address, photo_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['student_no'], data['name'], data['gender'],
            data['age'], data['phone'], data['email'], data['college'],
            data['major'], data['class_name'], data['grade'], data['building_no'],
            data['dormitory_no'], data['bed_no'],
            data['emergency_contact'], data['emergency_phone'], data['address'], photo_path
        )
        
        success, student_id = execute_update(sql, params)
        
        if success:
            # 更新宿舍入住人数
            if data['dormitory_no']:
                execute_update(
                    "UPDATE dormitory SET occupied = occupied + 1 WHERE dormitory_no = %s AND building_no = %s",
                    (data['dormitory_no'], data['building_no'])
                )
            
            logger.info(f"新增学生: {data['student_no']} - {data['name']}")
            return jsonify({'success': True, 'message': '学生添加成功', 'id': student_id})
        else:
            return jsonify({'success': False, 'message': '添加失败，请重试'})
    
    buildings = execute_query("SELECT * FROM building WHERE deleted = 0 ORDER BY building_no")
    
    # 获取所有宿舍号（用于下拉框）
    dorms = execute_query(
        "SELECT dormitory_no FROM dormitory WHERE deleted = 0 AND status != 'full' ORDER BY dormitory_no"
    )
    dormitory_nos = [d['dormitory_no'] for d in dorms]
    
    return render_template('student_add.html', buildings=buildings, dormitories=dormitory_nos)


@app.route('/student/edit/<int:stu_id>', methods=['GET', 'POST'])
@login_required
def student_edit(stu_id):
    """编辑学生"""
    if request.method == 'POST':
        # 获取表单数据
        data = {
            'name': request.form.get('name', '').strip(),
            'gender': request.form.get('gender', '').strip(),
            'id_card': request.form.get('id_card', '').strip(),
            'age': request.form.get('age', type=int),
            'phone': request.form.get('phone', '').strip(),
            'email': request.form.get('email', '').strip(),
            'college': request.form.get('college', '').strip(),
            'major': request.form.get('major', '').strip(),
            'class_name': request.form.get('class_name', '').strip(),
            'grade': request.form.get('grade', '').strip(),
            'building_no': request.form.get('building_no', '').strip(),
            'dormitory_no': request.form.get('dormitory_no', '').strip(),
            'bed_no': request.form.get('bed_no', '').strip(),
            'status': request.form.get('status', '').strip(),
            'emergency_contact': request.form.get('emergency_contact', '').strip(),
            'emergency_phone': request.form.get('emergency_phone', '').strip(),
            'address': request.form.get('address', '').strip()
        }
        
        # 验证
        if not data['name'] or not data['gender']:
            return jsonify({'success': False, 'message': '姓名和性别为必填项'})
        
        # 获取原学生信息
        old_student = execute_query(
            "SELECT * FROM student WHERE id = %s AND deleted = 0",
            (stu_id,), fetchone=True
        )
        
        if not old_student:
            return jsonify({'success': False, 'message': '学生不存在'})
        
        # 检查宿舍变更
        old_dorm = old_student['dormitory_no']
        old_building = old_student['building_no']
        new_dorm = data['dormitory_no']
        new_building = data['building_no']
        
        if new_dorm and (old_dorm != new_dorm or old_building != new_building):
            # 检查新宿舍
            dorm = execute_query(
                """SELECT d.*, b.building_type 
                   FROM dormitory d 
                   JOIN building b ON d.building_no = b.building_no
                   WHERE d.dormitory_no = %s AND d.building_no = %s AND d.deleted = 0""",
                (new_dorm, new_building), fetchone=True
            )
            
            if not dorm:
                return jsonify({'success': False, 'message': '所选宿舍不存在'})
            
            if dorm['occupied'] >= dorm['capacity']:
                return jsonify({'success': False, 'message': '该宿舍已满'})
            
            # 检查性别匹配
            if (dorm['building_type'] == 'male' and data['gender'] != '男') or \
               (dorm['building_type'] == 'female' and data['gender'] != '女'):
                return jsonify({'success': False, 'message': '学生性别与宿舍类型不匹配'})
        
        # 处理照片
        photo = request.files.get('photo')
        photo_path = old_student['photo_path']
        if photo and allowed_image(photo.filename):
            # 删除旧照片
            if photo_path:
                delete_file(photo_path)
            # 保存新照片
            success, result = save_upload_file(photo, prefix=f"stu_{old_student['student_no']}")
            if success:
                photo_path = result
        
        # 更新学生信息（兼容旧数据库字段）
        sql = """
            UPDATE student SET
                name = %s, gender = %s, age = %s,
                phone = %s, email = %s, college = %s, major = %s,
                class_name = %s, grade = %s, building_no = %s,
                dormitory_no = %s, bed_no = %s, status = %s,
                emergency_contact = %s,
                emergency_phone = %s, address = %s
            WHERE id = %s
        """
        params = (
            data['name'], data['gender'], data['age'],
            data['phone'], data['email'], data['college'], data['major'],
            data['class_name'], data['grade'], data['building_no'],
            data['dormitory_no'], data['bed_no'], data['status'],
            data['emergency_contact'], data['emergency_phone'],
            data['address'], stu_id
        )
        
        success, _ = execute_update(sql, params)
        
        if success:
            # 更新宿舍人数
            if old_dorm and (old_dorm != new_dorm or old_building != new_building):
                # 减少原宿舍人数
                execute_update(
                    "UPDATE dormitory SET occupied = occupied - 1 WHERE dormitory_no = %s AND building_no = %s",
                    (old_dorm, old_building)
                )
            
            if new_dorm and (old_dorm != new_dorm or old_building != new_building):
                # 增加新宿舍人数
                execute_update(
                    "UPDATE dormitory SET occupied = occupied + 1 WHERE dormitory_no = %s AND building_no = %s",
                    (new_dorm, new_building)
                )
            
            logger.info(f"编辑学生: {stu_id}")
            return jsonify({'success': True, 'message': '学生信息更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'})
    
    # GET 请求
    student = execute_query(
        """SELECT s.*, b.building_name 
           FROM student s
           LEFT JOIN building b ON s.building_no = b.building_no
           WHERE s.id = %s AND s.deleted = 0""",
        (stu_id,), fetchone=True
    )
    
    if not student:
        flash('学生不存在', 'error')
        return redirect(url_for('students'))
    
    buildings = execute_query("SELECT * FROM building WHERE deleted = 0 ORDER BY building_no")
    
    # 获取当前楼栋的宿舍列表
    dorms = []
    if student['building_no']:
        dorms = execute_query(
            """SELECT d.*, (d.capacity - d.occupied) as available 
               FROM dormitory d 
               WHERE d.building_no = %s AND d.deleted = 0
               ORDER BY d.dormitory_no""",
            (student['building_no'],)
        )
    
    return render_template('student_edit.html', student=student, buildings=buildings, dorms=dorms)


@app.route('/student/delete/<int:stu_id>', methods=['POST'])
@login_required
def student_delete(stu_id):
    """删除学生（软删除）"""
    student = execute_query(
        "SELECT * FROM student WHERE id = %s AND deleted = 0",
        (stu_id,), fetchone=True
    )
    
    if not student:
        return jsonify({'success': False, 'message': '学生不存在'})
    
    # 软删除
    success, _ = execute_update(
        "UPDATE student SET deleted = 1, status = 'checked_out', check_out_date = CURDATE() WHERE id = %s",
        (stu_id,)
    )
    
    if success:
        # 减少宿舍人数
        if student['dormitory_no']:
            execute_update(
                "UPDATE dormitory SET occupied = occupied - 1 WHERE dormitory_no = %s AND building_no = %s",
                (student['dormitory_no'], student['building_no'])
            )
        
        # 删除照片
        if student['photo_path']:
            delete_file(student['photo_path'])
        
        logger.info(f"删除学生: {stu_id}")
        return jsonify({'success': True, 'message': '学生删除成功'})
    
    return jsonify({'success': False, 'message': '删除失败'})


@app.route('/student/import', methods=['GET', 'POST'])
@login_required
def student_import():
    """批量导入学生"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'})
        
        if not allowed_file(file.filename, {'xlsx', 'xls'}):
            return jsonify({'success': False, 'message': '仅支持 Excel 文件'})
        
        try:
            df = pd.read_excel(file)
            
            # 检查必需列
            required_cols = ['学号', '姓名', '性别']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return jsonify({'success': False, 'message': f'缺少必需列: {", ".join(missing_cols)}'})
            
            success_count = 0
            fail_count = 0
            fail_reasons = []
            
            for idx, row in df.iterrows():
                try:
                    student_no = str(row.get('学号', '')).strip()
                    name = str(row.get('姓名', '')).strip()
                    gender = str(row.get('性别', '')).strip()
                    
                    if not student_no or not name or not gender:
                        fail_reasons.append(f'第{idx + 2}行：必填项缺失')
                        fail_count += 1
                        continue
                    
                    # 检查学号是否已存在
                    existing = execute_query(
                        "SELECT id FROM student WHERE student_no = %s AND deleted = 0",
                        (student_no,), fetchone=True
                    )
                    if existing:
                        fail_reasons.append(f'第{idx + 2}行：学号 {student_no} 已存在')
                        fail_count += 1
                        continue
                    
                    # 获取其他字段
                    id_card = str(row.get('身份证号', '')).strip()
                    age = row.get('年龄') if pd.notna(row.get('年龄')) else None
                    phone = str(row.get('电话', '')).strip()
                    email = str(row.get('邮箱', '')).strip()
                    college = str(row.get('学院', '')).strip()
                    major = str(row.get('专业', '')).strip()
                    class_name = str(row.get('班级', '')).strip()
                    grade = str(row.get('年级', '')).strip()
                    building_no = str(row.get('楼栋号', '')).strip()
                    dormitory_no = str(row.get('宿舍号', '')).strip()
                    bed_no = str(row.get('床位号', '')).strip()
                    
                    # 插入学生
                    sql = """
                        INSERT INTO student (
                            student_no, name, gender, id_card, age, phone, email,
                            college, major, class_name, grade, building_no, dormitory_no, bed_no
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    execute_update(sql, (
                        student_no, name, gender, id_card, age, phone, email,
                        college, major, class_name, grade, building_no, dormitory_no, bed_no
                    ))
                    
                    # 更新宿舍人数
                    if dormitory_no:
                        execute_update(
                            "UPDATE dormitory SET occupied = occupied + 1 WHERE dormitory_no = %s AND building_no = %s",
                            (dormitory_no, building_no)
                        )
                    
                    success_count += 1
                    
                except Exception as e:
                    fail_reasons.append(f'第{idx + 2}行：{str(e)}')
                    fail_count += 1
            
            logger.info(f"批量导入学生: 成功{success_count}条, 失败{fail_count}条")
            
            return jsonify({
                'success': True,
                'message': f'导入完成：成功 {success_count} 条，失败 {fail_count} 条',
                'fail_reasons': fail_reasons[:10]  # 只返回前10条错误
            })
            
        except Exception as e:
            logger.error(f"批量导入失败: {str(e)}")
            return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})
    
    return render_template('student_import.html')


@app.route('/student/export')
@login_required
def student_export():
    """导出学生数据"""
    try:
        students = execute_query("""
            SELECT student_no, name, gender, id_card, age, phone, email,
                   college, major, class_name, grade, building_no, dormitory_no,
                   bed_no, status, check_in_date, emergency_contact, emergency_phone
            FROM student WHERE deleted = 0
        """)
        
        df = pd.DataFrame(students)
        
        # 重命名列
        column_mapping = {
            'student_no': '学号',
            'name': '姓名',
            'gender': '性别',
            'id_card': '身份证号',
            'age': '年龄',
            'phone': '联系电话',
            'email': '邮箱',
            'college': '学院',
            'major': '专业',
            'class_name': '班级',
            'grade': '年级',
            'building_no': '楼栋号',
            'dormitory_no': '宿舍号',
            'bed_no': '床位号',
            'status': '状态',
            'check_in_date': '入住日期',
            'emergency_contact': '紧急联系人',
            'emergency_phone': '紧急联系电话'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        filename = f"学生数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        logger.info(f"导出学生数据: {len(students)} 条")
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"导出失败: {str(e)}")
        flash(f'导出失败: {str(e)}', 'error')
        return redirect(url_for('students'))


# ==================== 宿舍管理路由 ====================
@app.route('/dormitories')
@login_required
def dormitories():
    """宿舍列表"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '').strip()
    building_no = request.args.get('building_no', '').strip()
    status = request.args.get('status', '').strip()
    
    base_sql = """
        SELECT d.*, b.building_name, b.building_type
        FROM dormitory d
        LEFT JOIN building b ON d.building_no = b.building_no
        WHERE d.deleted = 0
    """
    conditions = []
    params = []
    
    if keyword:
        conditions.append("(d.dormitory_no LIKE %s OR d.building_no LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    if building_no:
        conditions.append("d.building_no = %s")
        params.append(building_no)
    
    if status:
        conditions.append("d.status = %s")
        params.append(status)
    
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)
    
    base_sql += " ORDER BY d.building_no, d.dormitory_no"
    
    pagination = paginate(base_sql, params, page)
    buildings = execute_query("SELECT * FROM building WHERE deleted = 0 ORDER BY building_no")
    
    return render_template('dormitories.html',
                         dorms=pagination['items'],
                         pagination=pagination,
                         buildings=buildings,
                         keyword=keyword,
                         building_no=building_no,
                         status=status)


@app.route('/dormitory/add', methods=['GET', 'POST'])
@manager_required
def dormitory_add():
    """新增宿舍"""
    if request.method == 'POST':
        building_no = request.form.get('building_no', '').strip()
        dormitory_no = request.form.get('dormitory_no', '').strip()
        capacity = request.form.get('capacity', type=int)
        floor = request.form.get('floor', type=int)
        area = request.form.get('area', type=float)
        has_balcony = 1 if request.form.get('has_balcony') else 0
        has_bathroom = 1 if request.form.get('has_bathroom') else 0
        has_aircon = 1 if request.form.get('has_aircon') else 0
        has_heater = 1 if request.form.get('has_heater') else 0
        remark = request.form.get('remark', '').strip()
        
        if not building_no or not dormitory_no or not capacity:
            return jsonify({'success': False, 'message': '楼栋、宿舍号和容量为必填项'})
        
        if capacity <= 0:
            return jsonify({'success': False, 'message': '容量必须大于0'})
        
        # 检查是否已存在
        existing = execute_query(
            "SELECT id FROM dormitory WHERE dormitory_no = %s AND building_no = %s AND deleted = 0",
            (dormitory_no, building_no), fetchone=True
        )
        if existing:
            return jsonify({'success': False, 'message': '该宿舍已存在'})
        
        sql = """
            INSERT INTO dormitory (
                building_no, dormitory_no, capacity, floor, area,
                has_balcony, has_bathroom, has_aircon, has_heater, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            building_no, dormitory_no, capacity, floor, area,
            has_balcony, has_bathroom, has_aircon, has_heater, remark
        )
        
        success, dorm_id = execute_update(sql, params)
        
        # 如果失败，尝试使用 building 字段名（兼容旧数据库）
        if not success:
            sql_old = """
                INSERT INTO dormitory (
                    building, dormitory_no, capacity
                ) VALUES (%s, %s, %s)
            """
            success, dorm_id = execute_update(sql_old, (building_no, dormitory_no, capacity))
        
        if success:
            logger.info(f"新增宿舍: {building_no} - {dormitory_no}")
            return jsonify({'success': True, 'message': '宿舍添加成功'})
        
        return jsonify({'success': False, 'message': '添加失败'})
    
    buildings = execute_query("SELECT * FROM building WHERE deleted = 0 ORDER BY building_no")
    return render_template('dormitory_add.html', buildings=buildings)


@app.route('/dormitory/detail/<int:dorm_id>')
@login_required
def dormitory_detail(dorm_id):
    """宿舍详情"""
    dorm = execute_query("""
        SELECT d.*, b.building_name, b.building_type, b.manager_name, b.manager_phone
        FROM dormitory d
        LEFT JOIN building b ON d.building_no = b.building_no
        WHERE d.id = %s AND d.deleted = 0
    """, (dorm_id,), fetchone=True)
    
    if not dorm:
        flash('宿舍不存在', 'error')
        return redirect(url_for('dormitories'))
    
    # 获取入住学生
    students = execute_query("""
        SELECT id, student_no, name, gender, phone, bed_no, check_in_date
        FROM student
        WHERE dormitory_no = %s AND building_no = %s AND deleted = 0 AND status = 'checked_in'
        ORDER BY bed_no
    """, (dorm['dormitory_no'], dorm['building_no']))
    
    return render_template('dormitory_detail.html', dorm=dorm, students=students)


# ==================== 楼栋管理路由 ====================
@app.route('/buildings')
@login_required
def buildings():
    """楼栋列表"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '').strip()
    
    base_sql = "SELECT * FROM building WHERE deleted = 0"
    params = []
    
    if keyword:
        base_sql += " AND (building_no LIKE %s OR building_name LIKE %s)"
        params = [f"%{keyword}%", f"%{keyword}%"]
    
    base_sql += " ORDER BY building_no"
    
    pagination = paginate(base_sql, params, page)
    
    return render_template('buildings.html',
                         buildings=pagination['items'],
                         pagination=pagination,
                         keyword=keyword)


@app.route('/building/add', methods=['GET', 'POST'])
@manager_required
def building_add():
    """新增楼栋"""
    if request.method == 'POST':
        building_no = request.form.get('building_no', '').strip()
        building_name = request.form.get('building_name', '').strip()
        building_type = request.form.get('building_type', '').strip()
        floors = request.form.get('floors', type=int)
        manager_name = request.form.get('manager_name', '').strip()
        manager_phone = request.form.get('manager_phone', '').strip()
        description = request.form.get('description', '').strip()
        
        if not building_no or not building_name:
            return jsonify({'success': False, 'message': '楼栋编号和名称为必填项'})
        
        # 检查是否已存在
        existing = execute_query(
            "SELECT id FROM building WHERE building_no = %s AND deleted = 0",
            (building_no,), fetchone=True
        )
        if existing:
            return jsonify({'success': False, 'message': '该楼栋已存在'})
        
        sql = """
            INSERT INTO building (
                building_no, building_name, building_type, floors,
                manager_name, manager_phone, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        success, _ = execute_update(sql, (
            building_no, building_name, building_type, floors,
            manager_name, manager_phone, description
        ))
        
        if success:
            logger.info(f"新增楼栋: {building_no}")
            return jsonify({'success': True, 'message': '楼栋添加成功'})
        
        return jsonify({'success': False, 'message': '添加失败'})
    
    return render_template('building_add.html')


# ==================== 报修管理路由 ====================
@app.route('/repairs')
@login_required
def repairs():
    """报修列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()
    repair_type = request.args.get('repair_type', '').strip()
    keyword = request.args.get('keyword', '').strip()
    
    base_sql = """
        SELECT r.id, r.repair_no, r.building_no, r.dormitory_no, r.student_name, r.student_phone,
               r.repair_type, r.urgency, r.description, r.status, r.handler_name,
               r.created_at, r.deleted,
               d.building_no as dorm_building_no
        FROM repair r
        LEFT JOIN dormitory d ON r.dormitory_no = d.dormitory_no AND r.building_no = d.building_no
        WHERE r.deleted = 0
    """
    conditions = []
    params = []
    
    if status:
        conditions.append("r.status = %s")
        params.append(status)
    
    if repair_type:
        conditions.append("r.repair_type = %s")
        params.append(repair_type)
    
    if keyword:
        conditions.append("(r.repair_no LIKE %s OR r.student_name LIKE %s OR r.dormitory_no LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)
    
    base_sql += " ORDER BY r.created_at DESC"
    
    pagination = paginate(base_sql, params, page)
    
    return render_template('repairs.html',
                         repairs=pagination['items'],
                         pagination=pagination,
                         status=status,
                         repair_type=repair_type,
                         keyword=keyword)


@app.route('/repair/add', methods=['GET', 'POST'])
@login_required
def repair_add():
    """新增报修"""
    if request.method == 'POST':
        building_no = request.form.get('building_no', '').strip()
        dormitory_no = request.form.get('dormitory_no', '').strip()
        student_name = request.form.get('student_name', '').strip()
        student_phone = request.form.get('student_phone', '').strip()
        repair_type = request.form.get('repair_type', '').strip()
        urgency = request.form.get('urgency', 'medium').strip()
        description = request.form.get('description', '').strip()
        
        if not building_no or not dormitory_no or not description:
            return jsonify({'success': False, 'message': '楼栋、宿舍号和问题描述为必填项'})
        
        repair_no = generate_repair_no()
        
        sql = """
            INSERT INTO repair (
                repair_no, building_no, dormitory_no, student_name, student_phone,
                repair_type, urgency, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        success, repair_id = execute_update(sql, (
            repair_no, building_no, dormitory_no, student_name, student_phone,
            repair_type, urgency, description
        ))
        
        if success:
            logger.info(f"新增报修: {repair_no}")
            return jsonify({'success': True, 'message': '报修提交成功', 'repair_no': repair_no})
        
        return jsonify({'success': False, 'message': '提交失败'})
    
    buildings = execute_query("SELECT * FROM building WHERE deleted = 0 ORDER BY building_no")
    return render_template('repair_add.html', buildings=buildings)


@app.route('/repair/handle/<int:repair_id>', methods=['POST'])
@manager_required
def repair_handle(repair_id):
    """处理报修"""
    action = request.form.get('action')
    
    if action == 'assign':
        handler_name = request.form.get('handler_name', '').strip()
        execute_update(
            "UPDATE repair SET status = 'assigned', handler_name = %s, assign_time = NOW() WHERE id = %s",
            (handler_name, repair_id)
        )
        return jsonify({'success': True, 'message': '已分配处理人'})
    
    elif action == 'start':
        execute_update(
            "UPDATE repair SET status = 'processing', start_time = NOW() WHERE id = %s",
            (repair_id,)
        )
        return jsonify({'success': True, 'message': '开始处理'})
    
    elif action == 'complete':
        solution = request.form.get('solution', '').strip()
        material_cost = request.form.get('material_cost', 0, type=float)
        labor_cost = request.form.get('labor_cost', 0, type=float)
        total_cost = material_cost + labor_cost
        
        execute_update("""
            UPDATE repair SET 
                status = 'completed', 
                complete_time = NOW(),
                solution = %s,
                material_cost = %s,
                labor_cost = %s,
                total_cost = %s
            WHERE id = %s
        """, (solution, material_cost, labor_cost, total_cost, repair_id))
        
        return jsonify({'success': True, 'message': '报修已完成'})
    
    return jsonify({'success': False, 'message': '无效的操作'})


# ==================== 费用管理路由 ====================
@app.route('/fees')
@login_required
def fees():
    """费用列表"""
    page = request.args.get('page', 1, type=int)
    month = request.args.get('month', '').strip()
    status = request.args.get('status', '').strip()
    fee_type = request.args.get('fee_type', '').strip()
    
    base_sql = """
        SELECT f.*, d.building_no, s.name as student_name, s.student_no
        FROM fee f
        LEFT JOIN dormitory d ON f.dormitory_no = d.dormitory_no AND f.building_no = d.building_no
        LEFT JOIN student s ON f.student_id = s.id
        WHERE f.deleted = 0
    """
    conditions = []
    params = []
    
    if month:
        conditions.append("f.month = %s")
        params.append(month)
    
    if status:
        conditions.append("f.status = %s")
        params.append(status)
    
    if fee_type:
        conditions.append("f.fee_type = %s")
        params.append(fee_type)
    
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)
    
    base_sql += " ORDER BY f.month DESC, f.created_at DESC"
    
    pagination = paginate(base_sql, params, page)
    
    # 统计信息
    stats = execute_query("""
        SELECT 
            SUM(CASE WHEN status = 'unpaid' THEN amount ELSE 0 END) as unpaid_amount,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as paid_amount,
            COUNT(CASE WHEN status = 'unpaid' THEN 1 END) as unpaid_count
        FROM fee WHERE deleted = 0
    """, fetchone=True)
    
    return render_template('fees.html',
                         fees=pagination['items'],
                         pagination=pagination,
                         stats=stats,
                         month=month,
                         status=status,
                         fee_type=fee_type)


@app.route('/fee/add', methods=['GET', 'POST'])
@manager_required
def fee_add():
    """新增费用"""
    if request.method == 'POST':
        fee_type = request.form.get('fee_type', '').strip()
        building_no = request.form.get('building_no', '').strip()
        dormitory_no = request.form.get('dormitory_no', '').strip()
        student_id = request.form.get('student_id', type=int) or None
        amount = request.form.get('amount', type=float)
        month = request.form.get('month', '').strip()
        usage_amount = request.form.get('usage_amount', type=float)
        unit_price = request.form.get('unit_price', type=float)
        remark = request.form.get('remark', '').strip()
        
        if not fee_type or not amount or not month:
            return jsonify({'success': False, 'message': '费用类型、金额和月份为必填项'})
        
        sql = """
            INSERT INTO fee (
                fee_type, building_no, dormitory_no, student_id, amount,
                month, usage_amount, unit_price, remark, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        success, fee_id = execute_update(sql, (
            fee_type, building_no, dormitory_no, student_id, amount,
            month, usage_amount, unit_price, remark, session.get('user_id')
        ))
        
        if success:
            logger.info(f"新增费用: {fee_id}")
            return jsonify({'success': True, 'message': '费用添加成功'})
        
        return jsonify({'success': False, 'message': '添加失败'})
    
    buildings = execute_query("SELECT * FROM building WHERE deleted = 0 ORDER BY building_no")
    return render_template('fee_add.html', buildings=buildings)


@app.route('/fee/pay/<int:fee_id>', methods=['POST'])
@login_required
def fee_pay(fee_id):
    """缴费"""
    pay_method = request.form.get('pay_method', '').strip()
    
    success, _ = execute_update("""
        UPDATE fee SET 
            status = 'paid', 
            pay_time = NOW(),
            pay_method = %s
        WHERE id = %s AND status = 'unpaid'
    """, (pay_method, fee_id))
    
    if success:
        return jsonify({'success': True, 'message': '缴费成功'})
    
    return jsonify({'success': False, 'message': '缴费失败'})


# ==================== 公告管理路由 ====================
@app.route('/notices')
@login_required
def notices():
    """公告列表"""
    page = request.args.get('page', 1, type=int)
    notice_type = request.args.get('notice_type', '').strip()
    status = request.args.get('status', '').strip()
    
    base_sql = """
        SELECT n.*, u.real_name as creator_name
        FROM notice n
        LEFT JOIN sys_user u ON n.created_by = u.id
        WHERE n.deleted = 0
    """
    conditions = []
    params = []
    
    if notice_type:
        conditions.append("n.notice_type = %s")
        params.append(notice_type)
    
    if status:
        conditions.append("n.status = %s")
        params.append(status)
    
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)
    
    base_sql += " ORDER BY n.is_top DESC, n.publish_time DESC"
    
    pagination = paginate(base_sql, params, page)
    
    return render_template('notices.html',
                         notices=pagination['items'],
                         pagination=pagination,
                         notice_type=notice_type,
                         status=status)


@app.route('/notice/add', methods=['GET', 'POST'])
@manager_required
def notice_add():
    """新增公告"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        notice_type = request.form.get('notice_type', 'notice').strip()
        priority = request.form.get('priority', 'normal').strip()
        target_type = request.form.get('target_type', 'all').strip()
        is_top = 1 if request.form.get('is_top') else 0
        publish_time = request.form.get('publish_time') or None
        expire_time = request.form.get('expire_time') or None
        
        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容为必填项'})
        
        sql = """
            INSERT INTO notice (
                title, content, notice_type, priority, target_type,
                is_top, publish_time, expire_time, status, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'published', %s)
        """
        success, notice_id = execute_update(sql, (
            title, content, notice_type, priority, target_type,
            is_top, publish_time, expire_time, session.get('user_id')
        ))
        
        if success:
            logger.info(f"新增公告: {notice_id}")
            return jsonify({'success': True, 'message': '公告发布成功'})
        
        return jsonify({'success': False, 'message': '发布失败'})
    
    return render_template('notice_add.html')


@app.route('/notice/detail/<int:notice_id>')
@login_required
def notice_detail(notice_id):
    """公告详情"""
    # 更新浏览次数
    execute_update(
        "UPDATE notice SET view_count = view_count + 1 WHERE id = %s",
        (notice_id,)
    )
    
    notice = execute_query("""
        SELECT n.*, u.real_name as creator_name
        FROM notice n
        LEFT JOIN sys_user u ON n.created_by = u.id
        WHERE n.id = %s AND n.deleted = 0
    """, (notice_id,), fetchone=True)
    
    if not notice:
        flash('公告不存在', 'error')
        return redirect(url_for('notices'))
    
    return render_template('notice_detail.html', notice=notice)


# ==================== 系统管理路由 ====================
@app.route('/users')
@admin_required
def users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '').strip()
    role = request.args.get('role', '').strip()
    
    base_sql = "SELECT * FROM sys_user WHERE deleted = 0"
    conditions = []
    params = []
    
    if keyword:
        conditions.append("(username LIKE %s OR real_name LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    if role:
        conditions.append("role = %s")
        params.append(role)
    
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)
    
    base_sql += " ORDER BY created_at DESC"
    
    pagination = paginate(base_sql, params, page)
    
    return render_template('users.html',
                         users=pagination['items'],
                         pagination=pagination,
                         keyword=keyword,
                         role=role)


@app.route('/user/add', methods=['GET', 'POST'])
@admin_required
def user_add():
    """新增用户"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        real_name = request.form.get('real_name', '').strip()
        role = request.form.get('role', 'staff').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        status = 1 if request.form.get('status') else 0
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码为必填项'})
        
        # 验证密码强度
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'success': False, 'message': msg})
        
        # 检查用户名是否已存在
        existing = execute_query(
            "SELECT id FROM sys_user WHERE username = %s AND deleted = 0",
            (username,), fetchone=True
        )
        if existing:
            return jsonify({'success': False, 'message': '用户名已存在'})
        
        sql = """
            INSERT INTO sys_user (username, password, real_name, role, phone, email, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        success, user_id = execute_update(sql, (
            username, pwd_hash(password), real_name, role, phone, email, status
        ))
        
        if success:
            logger.info(f"新增用户: {username}")
            return jsonify({'success': True, 'message': '用户添加成功'})
        
        return jsonify({'success': False, 'message': '添加失败'})
    
    return render_template('user_add.html')


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form.get('old_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的新密码不一致'})
        
        # 验证密码强度
        valid, msg = validate_password(new_password)
        if not valid:
            return jsonify({'success': False, 'message': msg})
        
        # 验证原密码
        user = execute_query(
            "SELECT password FROM sys_user WHERE id = %s",
            (session['user_id'],), fetchone=True
        )
        
        # 验证原密码（使用统一的密码验证函数）
        if not user or not verify_password(old_password, user['password']):
            return jsonify({'success': False, 'message': '原密码错误'})
        
        # 更新密码
        success, _ = execute_update(
            "UPDATE sys_user SET password = %s WHERE id = %s",
            (pwd_hash(new_password), session['user_id'])
        )
        
        if success:
            logger.info(f"用户 {session['username']} 修改密码")
            return jsonify({'success': True, 'message': '密码修改成功，请重新登录'})
        
        return jsonify({'success': False, 'message': '修改失败'})
    
    return render_template('change_password.html')


@app.route('/system/backup')
@admin_required
def system_backup():
    """系统备份"""
    try:
        tables = ['sys_user', 'building', 'dormitory', 'student', 'fee', 'repair', 'notice']
        backup_data = {}
        
        for table in tables:
            backup_data[table] = execute_query(f"SELECT * FROM {table} WHERE deleted = 0")
        
        # 添加备份信息
        backup_data['_backup_info'] = {
            'version': Config.SYSTEM_VERSION,
            'backup_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'table_count': len(tables)
        }
        
        filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(Config.BACKUP_FOLDER, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"系统备份完成: {filename}")
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"备份失败: {str(e)}")
        flash(f'备份失败: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/system/logs')
@admin_required
def system_logs():
    """系统日志"""
    page = request.args.get('page', 1, type=int)
    action = request.args.get('action', '').strip()
    module = request.args.get('module', '').strip()
    
    base_sql = """
        SELECT l.*, u.real_name
        FROM operation_log l
        LEFT JOIN sys_user u ON l.user_id = u.id
        WHERE 1=1
    """
    conditions = []
    params = []
    
    if action:
        conditions.append("l.action = %s")
        params.append(action)
    
    if module:
        conditions.append("l.module = %s")
        params.append(module)
    
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)
    
    base_sql += " ORDER BY l.created_at DESC"
    
    pagination = paginate(base_sql, params, page)
    
    return render_template('system_logs.html',
                         logs=pagination['items'],
                         pagination=pagination,
                         action=action,
                         module=module)


# ==================== API 路由 ====================
@app.route('/api/dormitories/<building_no>')
@login_required
def api_dormitories_by_building(building_no):
    """获取楼栋下的宿舍列表"""
    dorms = execute_query(
        """SELECT dormitory_no, capacity, occupied, (capacity - occupied) as available
           FROM dormitory 
           WHERE building_no = %s AND deleted = 0 AND status != 'full'
           ORDER BY dormitory_no""",
        (building_no,)
    )
    return jsonify({'success': True, 'data': dorms})


@app.route('/api/students/search')
@login_required
def api_students_search():
    """搜索学生"""
    keyword = request.args.get('q', '').strip()
    if not keyword or len(keyword) < 2:
        return jsonify({'success': True, 'data': []})
    
    students = execute_query(
        """SELECT id, student_no, name, dormitory_no, building_no
           FROM student 
           WHERE deleted = 0 AND status = 'checked_in'
           AND (student_no LIKE %s OR name LIKE %s)
           LIMIT 10""",
        (f"%{keyword}%", f"%{keyword}%")
    )
    return jsonify({'success': True, 'data': students})


@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """获取仪表盘统计数据"""
    stats = {}
    
    # 学生统计
    result = execute_query(
        "SELECT COUNT(*) as count FROM student WHERE deleted = 0",
        fetchone=True
    )
    stats['total_students'] = result['count'] if result else 0
    
    # 宿舍统计
    result = execute_query(
        "SELECT COUNT(*) as count FROM dormitory WHERE deleted = 0",
        fetchone=True
    )
    stats['total_dorms'] = result['count'] if result else 0
    
    # 床位使用率
    result = execute_query(
        "SELECT SUM(capacity) as cap, SUM(occupied) as occ FROM dormitory WHERE deleted = 0",
        fetchone=True
    )
    if result and result['cap']:
        stats['bed_rate'] = round((result['occ'] or 0) / result['cap'] * 100, 1)
    else:
        stats['bed_rate'] = 0
    
    # 待处理报修
    result = execute_query(
        "SELECT COUNT(*) as count FROM repair WHERE status IN ('pending', 'assigned') AND deleted = 0",
        fetchone=True
    )
    stats['pending_repairs'] = result['count'] if result else 0
    
    return jsonify({'success': True, 'data': stats})


# ==================== 启动应用 ====================
if __name__ == '__main__':
    logger.info(f"✅ {Config.SYSTEM_NAME} v{Config.SYSTEM_VERSION} 已启动")
    logger.info(f"🌐 访问地址: http://127.0.0.1:{Config.PORT}")
    # 禁用 use_reloader 防止监控 site-packages 导致卡顿
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
