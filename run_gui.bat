@echo off
setlocal
chcp 65001 >nul
set "APP_DIR=%~dp0"
"%APP_DIR%.venv\Scripts\python.exe" "%APP_DIR%gui.py"
if errorlevel 1 pause