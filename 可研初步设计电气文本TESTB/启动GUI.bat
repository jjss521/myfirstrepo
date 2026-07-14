@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Find Python
set "PYTHON_EXE="
for %%p in (
    "%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
    "%USERPROFILE%\.workbuddy\binaries\python\versions\3.12.*\python.exe"
    "C:\Python\Python313\python.exe"
    "C:\Python\Python312\python.exe"
    "C:\Python\Python310\python.exe"
    "C:\Program Files\Python38\python.exe"
) do (
    if exist %%p if "!PYTHON_EXE!"=="" set "PYTHON_EXE=%%p"
)

if "%PYTHON_EXE%"=="" (
    set "PYTHON_EXE=python"
)

echo.
echo === Launching GUI ===
"%PYTHON_EXE%" "gui.py"

if %errorlevel% neq 0 (
    echo.
    echo === Error starting ===
    echo Please install dependencies:
    echo   pip install openpyxl xlrd python-docx
    echo.
    "%PYTHON_EXE%" -c "import tkinter" >nul 2>&1 || echo WARNING: tkinter not found
    "%PYTHON_EXE%" -c "import openpyxl" >nul 2>&1 || echo WARNING: openpyxl not found
    "%PYTHON_EXE%" -c "import xlrd" >nul 2>&1 || echo WARNING: xlrd not found
    pause
)
