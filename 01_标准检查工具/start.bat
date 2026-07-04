@echo off
chcp 65001 >nul 2>&1
title 工程建设标准有效性检查工具
color 0A

echo.
echo  ============================================================
echo        工程建设标准有效性检查工具 - 安装与启动
echo  ============================================================
echo.

:: 检查 Python 是否安装
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [错误] 未检测到 Python，请先安装 Python 3.8+
    echo  下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 显示 Python 版本
echo  [信息] 检测到 Python:
python --version
echo.

:: 安装/更新依赖
echo  [步骤1] 正在安装依赖包...
echo  -----------------------------------------------------------
pip install -r "%~dp0requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo.
    echo  [警告] 部分依赖安装失败，尝试逐个安装...
    echo.
    pip install paddlepaddle
    pip install paddleocr
    pip install requests
    pip install beautifulsoup4
    pip install lxml
    pip install customtkinter
)

echo.
echo  [步骤2] 依赖安装完成！
echo.

:: 检查 PaddleOCR 模型是否已下载（首次运行会自动下载）
echo  [步骤3] 正在初始化 PaddleOCR（首次运行需下载中文模型约1GB）...
echo  -----------------------------------------------------------
python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False); print('  PaddleOCR 初始化成功!')" 2>nul
if %errorlevel% neq 0 (
    echo  [提示] PaddleOCR 正在下载模型文件，请耐心等待...
    python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=True); print('  PaddleOCR 初始化完成!')"
)
echo.

:: 创建目录
if not exist "%~dp0screenshots" mkdir "%~dp0screenshots"
if not exist "%~dp0output" mkdir "%~dp0output"

echo  ============================================================
echo    准备就绪！正在启动图形界面...
echo  ============================================================
echo.

:: 启动 GUI
cd /d "%~dp0"
python gui_app.py

:: 如果 GUI 启动失败，提示用户
if %errorlevel% neq 0 (
    echo.
    echo  [错误] GUI 启动失败。请确认 customtkinter 已安装:
    echo    pip install customtkinter
    echo.
    echo  也可以使用命令行模式:
    echo    python main.py -i .\screenshots -o .\output
    echo.
)

pause
