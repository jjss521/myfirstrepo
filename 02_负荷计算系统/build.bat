@echo off
chcp 65001 >nul
title 打包污水厂负荷计算系统 v3.0

echo ================================================
echo   污水厂负荷计算系统 v3.0 - 打包EXE
echo ================================================
echo.

cd /d "%~dp0"

REM 删除旧构建
if exist "dist\污水厂负荷计算系统_v3.0" rmdir /s /q "dist\污水厂负荷计算系统_v3.0"
if exist "build" rmdir /s /q "build"

echo 正在打包（可能需要3-5分钟）...
echo.

pyinstaller --onedir ^
    --name "污水厂负荷计算系统_v3.0" ^
    --noconsole ^
    --clean ^
    --hidden-import openpyxl ^
    --hidden-import openpyxl.cell._writer ^
    --hidden-import matplotlib ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import ttkbootstrap ^
    --hidden-import tkinterdnd2 ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module PySide2 ^
    --exclude-module PySide6 ^
    run_load_calc.py

echo.
if %errorlevel% equ 0 (
    echo ================================================
    echo   ✅ 打包成功！
    echo.
    echo   输出目录: dist\污水厂负荷计算系统_v3.0\
    echo   运行文件: dist\污水厂负荷计算系统_v3.0\污水厂负荷计算系统_v3.0.exe
    echo ================================================
    explorer dist\污水厂负荷计算系统_v3.0
) else (
    echo ❌ 打包失败，请检查错误信息
    pause
)
