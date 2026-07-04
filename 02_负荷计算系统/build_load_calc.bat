@echo off
chcp 65001 >nul 2>&1
title 污水厂负荷计算系统 - EXE打包
color 0B

echo.
echo  ============================================================
echo     污水厂负荷计算系统 v2.0 - EXE 打包脚本
echo  ============================================================
echo.

:: 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo  [信息] Python 版本:
python --version
echo.

:: 步骤1: 安装打包工具和依赖
echo  [步骤1/4] 安装打包工具和项目依赖...
echo  -----------------------------------------------------------
pip install pyinstaller --quiet
pip install -r "%~dp0requirements.txt" --quiet
echo.
echo  依赖安装完成！
echo.

:: 步骤2: 清理旧构建
echo  [步骤2/4] 清理旧构建文件...
echo  -----------------------------------------------------------
if exist "%~dp0build" rmdir /s /q "%~dp0build"
if exist "%~dp0dist" rmdir /s /q "%~dp0dist"
echo  已清理
echo.

:: 步骤3: 执行打包
echo  [步骤3/4] 开始 PyInstaller 打包（需要几分钟）...
echo  -----------------------------------------------------------
echo  [提示] 这可能需要 3-5 分钟，请耐心等待...
echo.

cd /d "%~dp0"
pyinstaller load_calc.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo.
    echo  [错误] 打包失败！请检查上方错误信息。
    echo.
    echo  常见解决方案:
    echo    1. 确所有依赖已安装: pip install -r requirements.txt
    echo    2. 尝试: pip install pyinstaller --upgrade
    echo    3. 确保 ttkbootstrap 已安装
    echo.
    pause
    exit /b 1
)
echo.

:: 步骤4: 后处理
echo  [步骤4/4] 后处理...
echo  -----------------------------------------------------------

:: 创建启动快捷方式
(
echo @echo off
echo cd /d "%%~dp0"
echo start LoadCalc.exe
) > "%~dp0dist\LoadCalc\启动程序.bat"

echo.
echo  ============================================================
echo    打包完成!
echo  ============================================================
echo.
echo  输出目录: %~dp0dist\LoadCalc\
echo  可执行文件: %~dp0dist\LoadCalc\LoadCalc.exe
echo.
echo  你可以将整个 dist\LoadCalc 文件夹复制到其他
echo  Windows 电脑上直接运行，无需安装 Python。
echo.

:: 打开输出目录
explorer "%~dp0dist\LoadCalc"

pause
