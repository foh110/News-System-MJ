@echo off
chcp 65001 >nul
title 智慧宿舍管理系统
color 0A

echo ============================================
echo     智慧宿舍管理系统 v2.0.0
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist ".venv" (
    echo [信息] 创建虚拟环境...
    python -m venv .venv
)

:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call .venv\Scripts\activate.bat

:: 安装依赖
echo [信息] 检查依赖...
pip install -q -r requirements.txt

:: 启动系统
echo.
echo [信息] 启动智慧宿舍管理系统...
echo [信息] 请在浏览器访问: http://localhost:8080
echo [信息] 按 Ctrl+C 停止服务
echo.

python app_new.py

:: 停用虚拟环境
call .venv\Scripts\deactivate.bat

echo.
echo [信息] 系统已停止
timeout /t 3 >nul
