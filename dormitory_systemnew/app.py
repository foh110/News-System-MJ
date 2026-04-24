from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
import pymysql
import secrets
import os
import hashlib
import logging
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from functools import wraps
import pandas as pd
from werkzeug.utils import secure_filename
import json


# -------------------------- 配置 --------------------------
class Config:
    SECRET_KEY = 'dormitory_system_2026_key'
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8080

    DB_CONFIG = {
        "host": "localhost",
        "port": 3307,
        "user": "root",
        "password": "lyp82ndlf",
        "database": "dormitory_db",
        "charset": "utf8mb4"
    }

    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'xlsx'}
    PASSWORD_SALT = 'dorm_system_2026'

    # 修复登录失效
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 30
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


# -------------------------- 初始化 --------------------------
app = Flask(__name__)
app.config.from_object(Config)  # 加载配置类
csrf = CSRFProtect(app)

# 自动创建目录（使用 Config 中的 UPLOAD_FOLDER）
for dirs in ['logs', 'backups', Config.UPLOAD_FOLDER]:
    os.makedirs(dirs, exist_ok=True)

# 日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('logs/system.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger('dorm')


# -------------------------- 工具函数 --------------------------
def get_db():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**app.config['DB_CONFIG'])
        conn.autocommit(True)
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return None


def pwd_hash(pwd):
    """密码加密"""
    return hashlib.sha256((pwd + app.config['PASSWORD_SALT']).encode()).hexdigest()


def login_required(f):
    """登录装饰器"""

    @wraps(f)
    def inner(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return inner


def allowed_file(filename):
    """验证文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_dormitories():
    """获取所有宿舍号"""
    conn = get_db()
    dorm_list = []
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT dormitory_no FROM dormitory WHERE deleted=0")
            dorm_list = [item[0] for item in c.fetchall()]
        except Exception as e:
            logger.error(f"获取宿舍列表失败: {str(e)}")
        finally:
            conn.close()
    return dorm_list


# -------------------------- 核心路由 --------------------------
@app.route('/')
@login_required
def index():
    """首页"""
    conn = get_db()
    total_stu = 0
    total_dorm = 0
    bed_rate = "0%"
    pending_tasks = 0
    male_count = 0
    female_count = 0

    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM student WHERE deleted=0")
            total_stu = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM dormitory WHERE deleted=0")
            total_dorm = c.fetchone()[0]

            c.execute("SELECT gender, COUNT(*) FROM student WHERE deleted=0 GROUP BY gender")
            gender_data = c.fetchall()
            for gender, count in gender_data:
                if gender == '男':
                    male_count = count
                elif gender == '女':
                    female_count = count

            c.execute("SELECT SUM(capacity), SUM(occupied) FROM dormitory WHERE deleted=0")
            capacity, occupied = c.fetchone()
            if capacity and capacity > 0:
                bed_rate = f"{round((occupied or 0) / capacity * 100, 1)}%"

        except Exception as e:
            logger.error(f"首页数据查询失败: {str(e)}")
        finally:
            conn.close()

    return render_template(
        'index.html',
        total_students=total_stu,
        total_dorms=total_dorm,
        bed_rate=bed_rate,
        pending_tasks=pending_tasks,
        male_count=male_count,
        female_count=female_count
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if 'username' in session:
        return redirect('/')
    err = ''
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '').strip()
        conn = get_db()
        if not conn:
            err = '数据库连接失败'
        else:
            try:
                c = conn.cursor(pymysql.cursors.DictCursor)
                c.execute("SELECT * FROM sys_user WHERE username=%s AND deleted=0", (u,))
                user = c.fetchone()
                if user and user['password'] == pwd_hash(p):
                    session.permanent = True
                    session['username'] = user['username']
                    flash('登录成功', 'success')
                    logger.info(f"用户 {u} 登录成功")
                    return redirect('/')
                else:
                    err = '账号或密码错误'
                    logger.warning(f"用户 {u} 登录失败: 账号或密码错误")
            except Exception as e:
                err = '系统异常'
                logger.error(f"登录异常: {str(e)}")
            finally:
                conn.close()
    return render_template('login.html', error_msg=err)


@app.route('/logout')
def logout():
    """退出登录"""
    logger.info(f"用户 {session.get('username')} 退出登录")
    session.clear()
    flash('已退出登录', 'success')
    return redirect('/login')


# -------------------------- 学生管理路由 --------------------------
@app.route('/students', methods=['GET'])
@login_required
def students():
    """学生列表"""
    keyword = request.args.get('keyword', '').strip()
    conn = get_db()
    students = []

    if conn:
        try:
            c = conn.cursor(pymysql.cursors.DictCursor)
            if keyword:
                sql = "SELECT * FROM student WHERE deleted=0 AND (student_no LIKE %s OR name LIKE %s)"
                c.execute(sql, (f"%{keyword}%", f"%{keyword}%"))
            else:
                c.execute("SELECT * FROM student WHERE deleted=0")
            students = c.fetchall()
        except Exception as e:
            logger.error(f"查询学生列表失败: {str(e)}")
        finally:
            conn.close()

    return render_template('students.html', students=students, keyword=keyword)


@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def student_add():
    """新增学生"""
    error_msg = ''
    dormitories = get_dormitories()

    if request.method == 'POST':
        student_no = request.form.get('student_no', '').strip()
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', '').strip()
        age = request.form.get('age', '')
        dormitory_no = request.form.get('dormitory_no', '').strip()
        phone = request.form.get('phone', '').strip()
        photo = request.files.get('photo')

        if not student_no or not name or not gender:
            error_msg = '学号、姓名、性别为必填项'
        elif len(student_no) != 11 or not student_no.isdigit():
            error_msg = '学号必须是11位数字'
        else:
            conn = get_db()
            if not conn:
                error_msg = '数据库连接失败'
            else:
                try:
                    c = conn.cursor()
                    # 检查学号重复
                    c.execute("SELECT id FROM student WHERE student_no=%s AND deleted=0", (student_no,))
                    if c.fetchone():
                        error_msg = '该学号已存在'
                    else:
                        # 校验宿舍存在性
                        if dormitory_no:
                            c.execute("SELECT id FROM dormitory WHERE dormitory_no=%s AND deleted=0", (dormitory_no,))
                            if not c.fetchone():
                                error_msg = '所选宿舍不存在，请重新选择'
                            else:
                                # 更新宿舍入住人数（先插入学生再更新，但这里先插入占位，后续再更新）
                                pass
                        if error_msg:
                            raise Exception(error_msg)

                        # 处理照片上传
                        photo_path = ''
                        if photo and allowed_file(photo.filename):
                            filename = secure_filename(f"{student_no}_{photo.filename}")
                            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            photo.save(photo_path)
                            photo_path = f"/{photo_path}"

                        # 插入学生
                        sql = """
                        INSERT INTO student (student_no, name, gender, age, dormitory_no, phone, photo_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        c.execute(sql, (student_no, name, gender, age or None, dormitory_no or None, phone or None, photo_path))

                        # 更新宿舍入住人数
                        if dormitory_no:
                            c.execute("UPDATE dormitory SET occupied = occupied + 1 WHERE dormitory_no=%s AND deleted=0", (dormitory_no,))

                        flash('学生添加成功', 'success')
                        logger.info(f"新增学生: {student_no} - {name}")
                        return redirect('/students')
                except Exception as e:
                    error_msg = f'添加失败: {str(e)}'
                    logger.error(f"新增学生失败: {str(e)}")
                finally:
                    conn.close()

    return render_template('student_add.html', error_msg=error_msg, dormitories=dormitories)


@app.route('/student/edit/<int:stu_id>', methods=['GET', 'POST'])
@login_required
def student_edit(stu_id):
    """编辑学生"""
    error_msg = ''
    conn = get_db()
    if not conn:
        flash('数据库连接失败', 'error')
        return redirect('/students')

    student = None
    c = conn.cursor(pymysql.cursors.DictCursor)
    try:
        c.execute("SELECT * FROM student WHERE id=%s AND deleted=0", (stu_id,))
        student = c.fetchone()
        if not student:
            flash('学生不存在', 'error')
            return redirect('/students')
    except Exception as e:
        logger.error(f"查询学生信息失败: {str(e)}")

    dormitories = get_dormitories()

    if request.method == 'POST':
        student_no = request.form.get('student_no', '').strip()
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', '').strip()
        age = request.form.get('age', '')
        dormitory_no = request.form.get('dormitory_no', '').strip()
        phone = request.form.get('phone', '').strip()
        photo = request.files.get('photo')

        if not student_no or not name or not gender:
            error_msg = '学号、姓名、性别为必填项'
        elif len(student_no) != 11 or not student_no.isdigit():
            error_msg = '学号必须是11位数字'
        else:
            try:
                # 检查学号是否重复（排除自身）
                c.execute("SELECT id FROM student WHERE student_no=%s AND deleted=0 AND id != %s", (student_no, stu_id))
                if c.fetchone():
                    error_msg = '该学号已被其他学生使用'
                else:
                    # 校验宿舍存在性
                    if dormitory_no:
                        c.execute("SELECT id FROM dormitory WHERE dormitory_no=%s AND deleted=0", (dormitory_no,))
                        if not c.fetchone():
                            error_msg = '所选宿舍不存在，请重新选择'
                    if error_msg:
                        raise Exception(error_msg)

                    # 处理照片上传
                    photo_path = student['photo_path']
                    if photo and allowed_file(photo.filename):
                        if photo_path and os.path.exists(photo_path.lstrip('/')):
                            os.remove(photo_path.lstrip('/'))
                        filename = secure_filename(f"{student_no}_{photo.filename}")
                        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        photo.save(photo_path)
                        photo_path = f"/{photo_path}"

                    # 更新宿舍入住人数（如果宿舍有变化）
                    old_dorm = student['dormitory_no']
                    if old_dorm != dormitory_no:
                        if old_dorm:
                            c.execute("UPDATE dormitory SET occupied = occupied - 1 WHERE dormitory_no=%s AND deleted=0", (old_dorm,))
                        if dormitory_no:
                            c.execute("UPDATE dormitory SET occupied = occupied + 1 WHERE dormitory_no=%s AND deleted=0", (dormitory_no,))

                    # 更新学生信息
                    sql = """
                    UPDATE student SET student_no=%s, name=%s, gender=%s, age=%s, dormitory_no=%s, phone=%s, photo_path=%s
                    WHERE id=%s AND deleted=0
                    """
                    c.execute(sql, (student_no, name, gender, age or None, dormitory_no or None, phone or None, photo_path, stu_id))

                    flash('学生信息更新成功', 'success')
                    logger.info(f"编辑学生: {stu_id} - {student_no}")
                    return redirect('/students')
            except Exception as e:
                error_msg = f'更新失败: {str(e)}'
                logger.error(f"编辑学生失败: {str(e)}")
            finally:
                conn.close()

    return render_template('student_edit.html', student=student, dormitories=dormitories, error_msg=error_msg)


@app.route('/student/delete/<int:stu_id>')
@login_required
def student_delete(stu_id):
    """删除学生（软删除）"""
    conn = get_db()
    if not conn:
        flash('数据库连接失败', 'error')
        return redirect('/students')

    try:
        c = conn.cursor()
        c.execute("SELECT dormitory_no, photo_path FROM student WHERE id=%s AND deleted=0", (stu_id,))
        student = c.fetchone()
        if student:
            if student[0]:
                c.execute("UPDATE dormitory SET occupied = occupied - 1 WHERE dormitory_no=%s AND deleted=0", (student[0],))
            c.execute("UPDATE student SET deleted=1 WHERE id=%s", (stu_id,))
            if student[1] and os.path.exists(student[1].lstrip('/')):
                os.remove(student[1].lstrip('/'))
            flash('学生删除成功', 'success')
            logger.info(f"删除学生: {stu_id}")
        else:
            flash('学生不存在', 'error')
    except Exception as e:
        flash(f'删除失败: {str(e)}', 'error')
        logger.error(f"删除学生失败: {str(e)}")
    finally:
        conn.close()

    return redirect('/students')


@app.route('/student/import', methods=['GET', 'POST'])
@login_required
def student_import():
    """批量导入学生"""
    error_msg = ''
    if request.method == 'POST':
        if 'file' not in request.files:
            error_msg = '请选择Excel文件'
        else:
            file = request.files['file']
            if file.filename == '':
                error_msg = '文件名为空'
            elif not allowed_file(file.filename):
                error_msg = '仅支持xlsx格式文件'
            else:
                try:
                    df = pd.read_excel(file)
                    required_cols = ['学号', '姓名', '性别']
                    if not all(col in df.columns for col in required_cols):
                        error_msg = f'Excel必须包含列：{",".join(required_cols)}'
                    else:
                        conn = get_db()
                        if not conn:
                            error_msg = '数据库连接失败'
                        else:
                            c = conn.cursor()
                            success_count = 0
                            fail_count = 0
                            fail_reasons = []

                            for idx, row in df.iterrows():
                                try:
                                    student_no = str(row.get('学号', '')).strip()
                                    name = str(row.get('姓名', '')).strip()
                                    gender = str(row.get('性别', '')).strip()
                                    age = row.get('年龄', '')
                                    dormitory_no = str(row.get('宿舍号', '')).strip()
                                    phone = str(row.get('电话', '')).strip()

                                    if not student_no or not name or not gender:
                                        fail_reasons.append(f'第{idx + 2}行：必填项缺失')
                                        fail_count += 1
                                        continue
                                    if len(student_no) != 11 or not student_no.isdigit():
                                        fail_reasons.append(f'第{idx + 2}行：学号必须是11位数字')
                                        fail_count += 1
                                        continue

                                    c.execute("SELECT id FROM student WHERE student_no=%s AND deleted=0", (student_no,))
                                    if c.fetchone():
                                        fail_reasons.append(f'第{idx + 2}行：学号{student_no}已存在')
                                        fail_count += 1
                                        continue

                                    # 校验宿舍存在性
                                    if dormitory_no:
                                        c.execute("SELECT id FROM dormitory WHERE dormitory_no=%s AND deleted=0", (dormitory_no,))
                                        if not c.fetchone():
                                            fail_reasons.append(f'第{idx + 2}行：宿舍号 {dormitory_no} 不存在')
                                            fail_count += 1
                                            continue

                                    # 插入学生
                                    sql = """
                                    INSERT INTO student (student_no, name, gender, age, dormitory_no, phone)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    """
                                    c.execute(sql, (student_no, name, gender, age or None, dormitory_no or None, phone or None))

                                    # 更新宿舍人数
                                    if dormitory_no:
                                        c.execute("UPDATE dormitory SET occupied = occupied + 1 WHERE dormitory_no=%s AND deleted=0", (dormitory_no,))

                                    success_count += 1
                                except Exception as e:
                                    fail_reasons.append(f'第{idx + 2}行：{str(e)}')
                                    fail_count += 1

                            conn.close()
                            flash(f'导入完成：成功{success_count}条，失败{fail_count}条', 'success')
                            if fail_reasons:
                                logger.warning(f"导入失败详情: {'; '.join(fail_reasons)}")
                            return redirect('/students')
                except Exception as e:
                    error_msg = f'导入失败: {str(e)}'
                    logger.error(f"批量导入学生失败: {str(e)}")

    return render_template('student_import.html', error_msg=error_msg)


@app.route('/student/export')
@login_required
def student_export():
    """导出学生数据为Excel"""
    conn = get_db()
    if not conn:
        flash('数据库连接失败', 'error')
        return redirect('/students')

    try:
        c = conn.cursor(pymysql.cursors.DictCursor)
        c.execute("SELECT student_no, name, gender, age, dormitory_no, phone FROM student WHERE deleted=0")
        students = c.fetchall()

        df = pd.DataFrame(students)
        filename = f"学生数据_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df.to_excel(filepath, index=False)

        logger.info(f"导出学生数据: {len(students)} 条")
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f'导出失败: {str(e)}', 'error')
        logger.error(f"导出学生数据失败: {str(e)}")
        return redirect('/students')
    finally:
        conn.close()


# -------------------------- 宿舍管理路由 --------------------------
@app.route('/dormitories', methods=['GET'])
@login_required
def dormitories():
    """宿舍列表"""
    keyword = request.args.get('keyword', '').strip()
    conn = get_db()
    dorms = []

    if conn:
        try:
            c = conn.cursor(pymysql.cursors.DictCursor)
            if keyword:
                sql = "SELECT * FROM dormitory WHERE deleted=0 AND (building LIKE %s OR dormitory_no LIKE %s)"
                c.execute(sql, (f"%{keyword}%", f"%{keyword}%"))
            else:
                c.execute("SELECT * FROM dormitory WHERE deleted=0")
            dorms = c.fetchall()
        except Exception as e:
            logger.error(f"查询宿舍列表失败: {str(e)}")
        finally:
            conn.close()

    return render_template('dormitories.html', dorms=dorms, keyword=keyword)


@app.route('/dormitory/add', methods=['GET', 'POST'])
@login_required
def dormitory_add():
    """新增宿舍"""
    error_msg = ''
    if request.method == 'POST':
        building = request.form.get('building', '').strip()
        dormitory_no = request.form.get('dormitory_no', '').strip()
        capacity = request.form.get('capacity', '')

        if not building or not dormitory_no or not capacity:
            error_msg = '楼栋号、宿舍号、可住人数为必填项'
        elif not capacity.isdigit() or int(capacity) <= 0:
            error_msg = '可住人数必须是正整数'
        else:
            conn = get_db()
            if not conn:
                error_msg = '数据库连接失败'
            else:
                try:
                    c = conn.cursor()
                    c.execute("SELECT id FROM dormitory WHERE dormitory_no=%s AND deleted=0", (dormitory_no,))
                    if c.fetchone():
                        error_msg = '该宿舍号已存在'
                    else:
                        sql = """
                        INSERT INTO dormitory (building, dormitory_no, capacity, occupied)
                        VALUES (%s, %s, %s, 0)
                        """
                        c.execute(sql, (building, dormitory_no, int(capacity)))
                        flash('宿舍添加成功', 'success')
                        logger.info(f"新增宿舍: {dormitory_no} (楼栋{building})")
                        return redirect('/dormitories')
                except Exception as e:
                    error_msg = f'添加失败: {str(e)}'
                    logger.error(f"新增宿舍失败: {str(e)}")
                finally:
                    conn.close()

    return render_template('dormitory_add.html', error_msg=error_msg)


# -------------------------- 系统管理路由 --------------------------
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    error_msg = ''
    if request.method == 'POST':
        old_pwd = request.form.get('old_pwd', '').strip()
        new_pwd = request.form.get('new_pwd', '').strip()
        confirm_pwd = request.form.get('confirm_pwd', '').strip()

        if new_pwd != confirm_pwd:
            error_msg = '两次输入的新密码不一致'
        elif len(new_pwd) < 6:
            error_msg = '新密码至少6位'
        else:
            conn = get_db()
            if not conn:
                error_msg = '数据库连接失败'
            else:
                try:
                    c = conn.cursor(pymysql.cursors.DictCursor)
                    username = session['username']
                    c.execute("SELECT password FROM sys_user WHERE username=%s AND deleted=0", (username,))
                    user = c.fetchone()
                    if not user or user['password'] != pwd_hash(old_pwd):
                        error_msg = '原密码错误'
                    else:
                        c.execute("UPDATE sys_user SET password=%s WHERE username=%s", (pwd_hash(new_pwd), username))
                        flash('密码修改成功，请重新登录', 'success')
                        logger.info(f"用户 {username} 修改密码")
                        return redirect('/logout')
                except Exception as e:
                    error_msg = f'修改失败: {str(e)}'
                    logger.error(f"修改密码失败: {str(e)}")
                finally:
                    conn.close()

    return render_template('change_password.html', error_msg=error_msg)


# -------------------------- 新增：数据备份 --------------------------
@app.route('/system/backup')
@login_required
def system_backup():
    """备份数据库关键表为JSON文件"""
    conn = get_db()
    if not conn:
        flash('数据库连接失败', 'error')
        return redirect('/')
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        tables = ['student', 'dormitory', 'sys_user']
        backup_data = {}
        for table in tables:
            cursor.execute(f"SELECT * FROM {table} WHERE deleted=0")
            backup_data[table] = cursor.fetchall()
        filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join('backups', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"系统备份完成: {filename}")
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f'备份失败: {str(e)}', 'error')
        logger.error(f"备份失败: {str(e)}")
        return redirect('/')
    finally:
        conn.close()


# -------------------------- 楼栋管理路由 --------------------------
@app.route('/buildings')
@login_required
def buildings():
    """楼栋列表"""
    conn = get_db()
    buildings = []
    if conn:
        try:
            c = conn.cursor(pymysql.cursors.DictCursor)
            c.execute("SELECT * FROM building WHERE deleted=0 ORDER BY building_no")
            buildings = c.fetchall()
        except Exception as e:
            logger.error(f"查询楼栋列表失败: {str(e)}")
        finally:
            conn.close()
    return render_template('buildings.html', buildings=buildings)


# -------------------------- 新增：入住管理（调宿） --------------------------
@app.route('/dormitory/occupancy', methods=['GET', 'POST'])
@login_required
def dormitory_occupancy():
    """入住管理：调整学生宿舍"""
    error_msg = ''
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        new_dorm_no = request.form.get('new_dorm_no')
        conn = get_db()
        if not conn:
            error_msg = '数据库连接失败'
        else:
            try:
                c = conn.cursor()
                c.execute("SELECT dormitory_no FROM student WHERE id=%s AND deleted=0", (student_id,))
                student = c.fetchone()
                if not student:
                    error_msg = '学生不存在'
                else:
                    old_dorm = student[0]
                    if old_dorm == new_dorm_no:
                        error_msg = '宿舍未变更，无需调整'
                    else:
                        c.execute("SELECT capacity, occupied FROM dormitory WHERE dormitory_no=%s AND deleted=0", (new_dorm_no,))
                        dorm = c.fetchone()
                        if not dorm:
                            error_msg = '新宿舍不存在'
                        elif dorm[1] >= dorm[0]:
                            error_msg = '新宿舍已满'
                        else:
                            c.execute("UPDATE student SET dormitory_no=%s WHERE id=%s", (new_dorm_no, student_id))
                            if old_dorm:
                                c.execute("UPDATE dormitory SET occupied=occupied-1 WHERE dormitory_no=%s", (old_dorm,))
                            c.execute("UPDATE dormitory SET occupied=occupied+1 WHERE dormitory_no=%s", (new_dorm_no,))
                            flash('调宿成功', 'success')
                            logger.info(f"学生 {student_id} 从 {old_dorm} 调至 {new_dorm_no}")
                            return redirect('/dormitory/occupancy')
            except Exception as e:
                error_msg = f'调宿失败: {str(e)}'
                logger.error(f"调宿失败: {str(e)}")
            finally:
                conn.close()

    # GET 请求：显示所有宿舍及占用情况，并提供学生搜索下拉框
    conn = get_db()
    dorms = []
    students = []
    if conn:
        try:
            c = conn.cursor(pymysql.cursors.DictCursor)
            c.execute("SELECT dormitory_no, building, capacity, occupied FROM dormitory WHERE deleted=0")
            dorms = c.fetchall()
            c.execute("SELECT id, student_no, name, dormitory_no FROM student WHERE deleted=0 ORDER BY student_no")
            students = c.fetchall()
        except Exception as e:
            logger.error(f"查询宿舍/学生失败: {str(e)}")
        finally:
            conn.close()
    return render_template('dormitory_occupancy.html', dorms=dorms, students=students, error_msg=error_msg)


# -------------------------- 启动 --------------------------
if __name__ == '__main__':
    logger.info("✅ 智慧宿舍管理系统已启动")
    logger.info(f"🌐 访问：http://127.0.0.1:{app.config['PORT']}")
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        extra_files=[],
        exclude_patterns=['*/.venv/*', '*\\venv\\*', '*\\site-packages\\*']
    )