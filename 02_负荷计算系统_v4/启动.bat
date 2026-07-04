@echo off
chcp 65001 >nul
title 污水厂负荷计算系统 v4.0
cd /d "%~dp0"
python run_load_calc.py
if %errorlevel% neq 0 (
    echo.
    echo 启动失败！错误码: %errorlevel%
    echo.
)
pause
