@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Не найдено виртуальное окружение .venv
    echo Создайте его командой: python -m venv .venv
    pause
    exit /b 1
)

echo [1/3] Установка зависимостей сборки...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto :error

echo [2/3] Сборка EXE...
".venv\Scripts\pyinstaller.exe" --noconfirm --clean transcriber.spec
if errorlevel 1 goto :error

echo [3/3] Поиск Inno Setup...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"

if defined ISCC (
    "%ISCC%" "installer\transcriber.iss"
    if errorlevel 1 goto :error
    echo [OK] EXE и установщик собраны.
) else (
    echo [WARN] Inno Setup 6 не найден. EXE собраны в dist\Transcriber.
    echo Для установщика установите Inno Setup и снова запустите build.bat.
)

pause
exit /b 0

:error
echo.
echo [ERROR] Сборка завершилась с ошибкой.
pause
exit /b 1