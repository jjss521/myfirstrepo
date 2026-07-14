@echo off
title 电气自控生成器
cd /d "%~dp0"
set PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PY%" set PY=python
start "" "%PY%" "%~dp0gui.py"
