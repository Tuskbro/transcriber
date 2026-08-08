@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "APP_DIR=%~dp0"
set "OUTPUT_FORMAT=%~2"

if "%~1"=="" (
    echo [ERROR] Не указан файл или папка.
    pause
    exit /b 1
)

if "%OUTPUT_FORMAT%"=="" set "OUTPUT_FORMAT=md"
if /i not "%OUTPUT_FORMAT%"=="md" if /i not "%OUTPUT_FORMAT%"=="json" (
    echo [ERROR] Неизвестный формат: %OUTPUT_FORMAT%
    pause
    exit /b 1
)

"%APP_DIR%.venv\Scripts\python.exe" "%APP_DIR%main.py" --format "%OUTPUT_FORMAT%" --force "%~1"
set "EXIT_CODE=%errorlevel%"

echo.
if not "%EXIT_CODE%"=="0" echo [ERROR] Программа завершилась с кодом %EXIT_CODE%.
pause
exit /b %EXIT_CODE%