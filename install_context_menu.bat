@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "APP_DIR=%~dp0"
set "RUNNER=%APP_DIR%run_transcriber.bat"
set "CHAT_RUNNER=%APP_DIR%run_chat_export_parser.bat"

if not exist "%APP_DIR%.venv\Scripts\python.exe" (
    echo [ERROR] Не найден .venv\Scripts\python.exe
    echo Сначала создайте виртуальное окружение и установите зависимости.
    pause
    exit /b 1
)

if not exist "%APP_DIR%main.py" (
    echo [ERROR] Не найден файл main.py
    pause
    exit /b 1
)

if not exist "%RUNNER%" (
    echo [ERROR] Не найден файл run_transcriber.bat
    pause
    exit /b 1
)

if not exist "%APP_DIR%chat_export_parser.py" (
    echo [ERROR] Не найден файл chat_export_parser.py
    pause
    exit /b 1
)

if not exist "%CHAT_RUNNER%" (
    echo [ERROR] Не найден файл run_chat_export_parser.bat
    pause
    exit /b 1
)

for %%E in (.mp3 .wav .ogg .opus .m4a .aac .flac .mp4 .mkv .webm) do (
    call :AddFileMenu "HKCU\Software\Classes\SystemFileAssociations\%%E\shell\TranscriberToMarkdown" "Транскрибировать в Markdown" "md"
    if errorlevel 1 goto :error
    call :AddFileMenu "HKCU\Software\Classes\SystemFileAssociations\%%E\shell\TranscriberToJson" "Транскрибировать в JSON" "json"
    if errorlevel 1 goto :error
)

for %%E in (.html .htm) do (
    call :AddChatFileMenu "HKCU\Software\Classes\SystemFileAssociations\%%E\shell\TranscriberChatExport"
    if errorlevel 1 goto :error
)

call :AddFolderMenu "HKCU\Software\Classes\Directory\shell\TranscriberToMarkdown" "Транскрибировать в Markdown" "md"
if errorlevel 1 goto :error
call :AddFolderMenu "HKCU\Software\Classes\Directory\shell\TranscriberToJson" "Транскрибировать в JSON" "json"
if errorlevel 1 goto :error
call :AddChatFolderMenu "HKCU\Software\Classes\Directory\shell\TranscriberChatExport"
if errorlevel 1 goto :error

call :AddBackgroundMenu "HKCU\Software\Classes\Directory\Background\shell\TranscriberToMarkdown" "Транскрибировать в Markdown" "md"
if errorlevel 1 goto :error
call :AddBackgroundMenu "HKCU\Software\Classes\Directory\Background\shell\TranscriberToJson" "Транскрибировать в JSON" "json"
if errorlevel 1 goto :error
call :AddChatBackgroundMenu "HKCU\Software\Classes\Directory\Background\shell\TranscriberChatExport"
if errorlevel 1 goto :error

echo.
echo [OK] Команды транскрипции и обработки экспорта чата установлены.
echo В Windows 11 они могут находиться в меню "Показать дополнительные параметры".
pause
exit /b 0

:AddFileMenu
reg add "%~1" /ve /d "%~2" /f >nul
reg add "%~1" /v "Icon" /d "%APP_DIR%.venv\Scripts\python.exe" /f >nul
reg add "%~1\command" /ve /d "\"%RUNNER%\" \"%%1\" \"%~3\"" /f >nul
exit /b %errorlevel%

:AddFolderMenu
reg add "%~1" /ve /d "%~2" /f >nul
reg add "%~1" /v "Icon" /d "%APP_DIR%.venv\Scripts\python.exe" /f >nul
reg add "%~1\command" /ve /d "\"%RUNNER%\" \"%%1\" \"%~3\"" /f >nul
exit /b %errorlevel%

:AddBackgroundMenu
reg add "%~1" /ve /d "%~2" /f >nul
reg add "%~1" /v "Icon" /d "%APP_DIR%.venv\Scripts\python.exe" /f >nul
reg add "%~1\command" /ve /d "\"%RUNNER%\" \"%%V\" \"%~3\"" /f >nul
exit /b %errorlevel%

:AddChatFileMenu
reg add "%~1" /ve /d "Добавить транскрипции в экспорт чата" /f >nul
reg add "%~1" /v "Icon" /d "%APP_DIR%.venv\Scripts\python.exe" /f >nul
reg add "%~1\command" /ve /d "\"%CHAT_RUNNER%\" \"%%1\"" /f >nul
exit /b %errorlevel%

:AddChatFolderMenu
reg add "%~1" /ve /d "Добавить транскрипции в экспорт чата" /f >nul
reg add "%~1" /v "Icon" /d "%APP_DIR%.venv\Scripts\python.exe" /f >nul
reg add "%~1\command" /ve /d "\"%CHAT_RUNNER%\" \"%%1\"" /f >nul
exit /b %errorlevel%

:AddChatBackgroundMenu
reg add "%~1" /ve /d "Добавить транскрипции в экспорт чата" /f >nul
reg add "%~1" /v "Icon" /d "%APP_DIR%.venv\Scripts\python.exe" /f >nul
reg add "%~1\command" /ve /d "\"%CHAT_RUNNER%\" \"%%V\"" /f >nul
exit /b %errorlevel%

:error
echo.
echo [ERROR] Не удалось установить контекстное меню.
pause
exit /b 1