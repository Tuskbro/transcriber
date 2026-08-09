@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "APP_DIR=%~dp0"
if "%~1"=="" (
    echo [ERROR] Не указано изображение или папка.
    pause
    exit /b 1
)

"%APP_DIR%.venv\Scripts\python.exe" "%APP_DIR%describe_images.py" "%~1"
set "EXIT_CODE=%errorlevel%"
echo.
if not "%EXIT_CODE%"=="0" echo [ERROR] Генератор завершился с кодом %EXIT_CODE%.
pause
exit /b %EXIT_CODE%