# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# 项目根目录
base_dir = os.path.abspath('.')

# 数据文件
added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('config.py', '.'),
    ('utils', 'utils'),
    ('database_init.sql', '.'),
]

a = Analysis(
    ['app_new.py'],
    pathex=[base_dir],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'pymysql',
        'pymysql.cursors',
        'DBUtils.PooledDB',
        'pandas',
        'pandas._libs.tslibs.base',
        'openpyxl',
        'openpyxl.cell._writer',
        'werkzeug',
        'werkzeug.middleware.proxy_fix',
        'flask_wtf',
        'wtforms',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='智慧宿舍管理系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/icon.ico' if os.path.exists('static/icon.ico') else None,
)
