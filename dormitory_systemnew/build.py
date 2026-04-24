"""
智慧宿舍管理系统 - 打包脚本
用于将系统打包为可执行文件
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__', '.pytest_cache']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name}...")
            shutil.rmtree(dir_name)
    
    # 清理 .pyc 文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
        for dir in dirs:
            if dir == '__pycache__':
                shutil.rmtree(os.path.join(root, dir))


def install_dependencies():
    """安装依赖"""
    print("安装依赖...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])


def build_exe():
    """构建可执行文件"""
    print("构建可执行文件...")
    
    # 确保目录存在
    os.makedirs('dist', exist_ok=True)
    
    # 使用 PyInstaller 打包
    cmd = [
        'pyinstaller',
        '--name=智慧宿舍管理系统',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--add-data=config.py;.',
        '--add-data=utils;utils',
        '--add-data=database_init.sql;.',
        '--hidden-import=pymysql',
        '--hidden-import=pymysql.cursors',
        '--hidden-import=DBUtils.PooledDB',
        '--hidden-import=pandas',
        '--hidden-import=pandas._libs.tslibs.base',
        '--hidden-import=openpyxl',
        '--hidden-import=openpyxl.cell._writer',
        '--hidden-import=werkzeug',
        '--hidden-import=flask_wtf',
        '--hidden-import=wtforms',
        'app_new.py'
    ]
    
    subprocess.check_call(cmd)


def create_installer():
    """创建安装程序"""
    print("创建安装程序...")
    
    # 创建发布目录
    release_dir = 'release/智慧宿舍管理系统_v2.0.0'
    os.makedirs(release_dir, exist_ok=True)
    
    # 复制文件
    shutil.copy('dist/智慧宿舍管理系统.exe', release_dir)
    shutil.copy('database_init.sql', release_dir)
    shutil.copy('README.md', release_dir)
    shutil.copy('requirements.txt', release_dir)
    
    # 创建启动脚本
    with open(os.path.join(release_dir, '启动系统.bat'), 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('echo 正在启动智慧宿舍管理系统...\n')
        f.write('start "" "智慧宿舍管理系统.exe"\n')
        f.write('echo 系统已启动，请在浏览器访问 http://localhost:8080\n')
        f.write('pause\n')
    
    # 创建初始化数据库脚本
    with open(os.path.join(release_dir, '初始化数据库.bat'), 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('echo 请确保已安装MySQL并创建了数据库\n')
        f.write('echo 按任意键开始初始化数据库...\n')
        f.write('pause\n')
        f.write('mysql -u root -p dormitory_db < database_init.sql\n')
        f.write('echo 数据库初始化完成！\n')
        f.write('pause\n')
    
    # 创建使用说明
    with open(os.path.join(release_dir, '使用说明.txt'), 'w', encoding='utf-8') as f:
        f.write('智慧宿舍管理系统 v2.0.0\n')
        f.write('=' * 50 + '\n\n')
        f.write('【安装步骤】\n')
        f.write('1. 确保已安装 MySQL 5.7+ 数据库\n')
        f.write('2. 运行"初始化数据库.bat"初始化数据库\n')
        f.write('3. 运行"启动系统.bat"启动系统\n')
        f.write('4. 浏览器访问 http://localhost:8080\n\n')
        f.write('【默认账号】\n')
        f.write('用户名: admin\n')
        f.write('密码: admin123\n\n')
        f.write('【技术支持】\n')
        f.write('邮箱: support@dormitory-system.com\n')
    
    print(f"安装程序已创建: {release_dir}")


def main():
    """主函数"""
    print("=" * 60)
    print("智慧宿舍管理系统 - 打包工具")
    print("=" * 60)
    
    # 检查是否在正确目录
    if not os.path.exists('app_new.py'):
        print("错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 清理
    clean_build()
    
    # 安装依赖
    try:
        install_dependencies()
    except Exception as e:
        print(f"安装依赖失败: {e}")
        print("请手动安装依赖: pip install -r requirements.txt pyinstaller")
    
    # 构建
    try:
        build_exe()
    except Exception as e:
        print(f"构建失败: {e}")
        sys.exit(1)
    
    # 创建安装程序
    try:
        create_installer()
    except Exception as e:
        print(f"创建安装程序失败: {e}")
    
    print("=" * 60)
    print("打包完成！")
    print("发布文件位于: release/智慧宿舍管理系统_v2.0.0/")
    print("=" * 60)


if __name__ == '__main__':
    main()
