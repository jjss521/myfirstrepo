@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Find Python from known locations
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
echo ===========================================
echo   市政工程电气自控设计说明书生成器
echo   macOS Style GUI v1.0.0
echo ===========================================
echo.

:: Step 1: Install/Update dependencies from backend/requirements.txt
echo [1/2] Checking dependencies...
echo.

if exist "backend\requirements.txt" (
    "%PYTHON_EXE%" -c "import customtkinter, tkinterdnd2" >nul 2>&1
    if !errorlevel! neq 0 (
        echo Installing dependencies from backend/requirements.txt...
        "%PYTHON_EXE%" -m pip install -r "backend\requirements.txt"
        if !errorlevel! neq 0 (
            echo.
            echo WARNING: pip install failed. Attempting manual fallback...
            "%PYTHON_EXE%" -m pip install customtkinter>=5.2.0 tkinterdnd2>=0.3.0 openpyxl>=3.1.0 xlrd>=2.0.0 python-docx>=0.8.11
        )
    ) else (
        echo All dependencies satisfied.
    )
) else (
    echo No requirements.txt found. Checking core dependencies...
    "%PYTHON_EXE%" -c "import customtkinter" >nul 2>&1
    if !errorlevel! neq 0 (
        echo Installing customtkinter...
        "%PYTHON_EXE%" -m pip install customtkinter>=5.2.0
    )
    "%PYTHON_EXE%" -c "import tkinterdnd2" >nul 2>&1
    if !errorlevel! neq 0 (
        echo Installing tkinterdnd2...
        "%PYTHON_EXE%" -m pip install tkinterdnd2>=0.3.0
    )
    "%PYTHON_EXE%" -c "import openpyxl" >nul 2>&1
    if !errorlevel! neq 0 (
        echo Installing openpyxl...
        "%PYTHON_EXE%" -m pip install openpyxl>=3.1.0
    )
    "%PYTHON_EXE%" -c "import xlrd" >nul 2>&1
    if !errorlevel! neq 0 (
        echo Installing xlrd...
        "%PYTHON_EXE%" -m pip install xlrd>=2.0.0
    )
    "%PYTHON_EXE%" -c "import docx" >nul 2>&1
    if !errorlevel! neq 0 (
        echo Installing python-docx...
        "%PYTHON_EXE%" -m pip install python-docx>=0.8.11
    )
)

echo.
echo [2/2] Launching macOS Style GUI...
echo.

:: Step 2: Launch the macOS-style GUI
"%PYTHON_EXE%" "src\macos_gui.py"

:: Handle errors after GUI exits
if %errorlevel% neq 0 (
    echo.
    echo ===========================================
    echo   启动失败 ^| Launch Failed
    echo ===========================================
    echo.
    echo Possible issues:
    echo   1. Missing dependencies — run:
    echo      pip install -r backend\requirements.txt
    echo.
    echo   2. Python not found — install Python 3.10+
    echo      or set PATH to include python.exe
    echo.
    echo   3. Missing source file — ensure src\macos_gui.py exists
    echo.
    pause
)

endlocal
