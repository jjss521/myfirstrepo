@echo off
setlocal
set PY=python
if exist "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" (
    set PY="C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
)
cd /d "%~dp0"
start "" %PY% gui.py
endlocal
