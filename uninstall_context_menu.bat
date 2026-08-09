@echo off
setlocal EnableExtensions
chcp 65001 >nul

for %%E in (.mp3 .wav .ogg .opus .m4a .aac .flac .mp4 .mkv .webm) do (
    reg delete "HKCU\Software\Classes\SystemFileAssociations\%%E\shell\TranscriberToMarkdown" /f >nul 2>&1
    reg delete "HKCU\Software\Classes\SystemFileAssociations\%%E\shell\TranscriberToJson" /f >nul 2>&1
)

for %%E in (.jpg .jpeg .png .webp .gif .bmp) do (
    reg delete "HKCU\Software\Classes\SystemFileAssociations\%%E\shell\TranscriberDescribeImage" /f >nul 2>&1
)
for %%E in (.html .htm) do (
    reg delete "HKCU\Software\Classes\SystemFileAssociations\%%E\shell\TranscriberChatExport" /f >nul 2>&1
)

reg delete "HKCU\Software\Classes\Directory\shell\TranscriberToMarkdown" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\TranscriberToJson" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\TranscriberChatExport" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\TranscriberDescribeImages" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\TranscriberToMarkdown" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\TranscriberToJson" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\TranscriberChatExport" /f >nul 2>&1

echo.
echo [OK] Команды Transcriber удалены из контекстного меню.
pause
exit /b 0
