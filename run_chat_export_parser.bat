@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "APP_DIR=%~dp0"

if "%~1"=="" (
    echo [ERROR] Не указан HTML-файл или папка экспорта.
    pause
    exit /b 1
)

"%APP_DIR%.venv\Scripts\python.exe" "%APP_DIR%chat_export_parser.py" "%~1"
set "EXIT_CODE=%errorlevel%"

echo.
if not "%EXIT_CODE%"=="0" echo [ERROR] Парсер завершился с кодом %EXIT_CODE%.
pause
exit /b %EXIT_CODE%