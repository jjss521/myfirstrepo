@echo off
chcp 65001 >nul
title 配电系统接线图生成工具
cd /d "%~dp0"
python -u power_distribution_generator/main.py
if %errorlevel% neq 0 (
    echo.
    echo 启动失败！请确认已安装 Python 3.8+ 和依赖：
    echo   pip install PySide6 openpyxl comtypes pywin32
    echo.
    pause
)
