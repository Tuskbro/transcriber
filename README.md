# Transcriber

Локальное Windows-приложение для расшифровки аудио и видео с помощью `faster-whisper`. Поддерживает обычные медиафайлы, пакетную обработку папок и автоматическое добавление расшифровок в HTML-выгрузки Telegram Chat Export.

## Возможности

- графический интерфейс PyQt5 со светлой и тёмной темами;
- drag-and-drop файлов и папок;
- вывод в Markdown, JSON или оба формата;
- цельный текст и сегменты с тайм-кодами;
- обработка голосовых и круглых видеосообщений Telegram;
- встраивание расшифровок в HTML с резервной копией `.html.bak`;
- контекстное меню Проводника для файлов, папок и Chat Export;
- CUDA и CPU режимы;
- пропуск готовых результатов или принудительная перезапись через `--force`.

## Быстрый запуск из исходников

Требуется Windows и Python 3.10–3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run_gui.bat
```

При первом запуске выбранная модель Whisper загружается из Hugging Face. Модель не входит в репозиторий и установщик.

## GUI

Запустите `run_gui.bat`. Во вкладке «Транскрипция» можно выбрать медиа, формат и папку результата. Во вкладке «Chat Export» выбирается отдельный HTML-файл либо корневая папка выгрузки Telegram.

Строки `[EXPORT]` и `[OK]` содержат кликабельные имена файлов и папок. Кнопка «Открыть папку результата» открывает результат в Проводнике.

## Командная строка

Markdown по умолчанию:

```powershell
.\.venv\Scripts\python.exe main.py audio.ogg
```

JSON и Markdown в отдельную папку:

```powershell
.\.venv\Scripts\python.exe main.py voice_messages --format both --output-dir transcriptions
```

Принудительная перезапись:

```powershell
.\.venv\Scripts\python.exe main.py audio.ogg --format json --force
```

Обработка Telegram Chat Export:

```powershell
.\.venv\Scripts\python.exe chat_export_parser.py "C:\Chats\ChatExport_2026-08-08"
```

Парсер ищет готовые `.json`/`.md` сначала в `transcriptions`, затем рядом с медиа. При отсутствии результатов он создаёт `transcriptions`, транскрибирует нужные папки без `--force` и обновляет HTML.

## Контекстное меню

Для режима разработки запустите `install_context_menu.bat`. Удаление выполняется через `uninstall_context_menu.bat`. В Windows 11 команды могут находиться в «Показать дополнительные параметры».

Установщик предлагает такую же интеграцию отдельной опцией.

## Поддерживаемые форматы

`.mp3`, `.wav`, `.ogg`, `.opus`, `.m4a`, `.aac`, `.flac`, `.mp4`, `.mkv`, `.webm`.

## Сборка EXE и установщика

Инструкции находятся в [BUILDING.md](BUILDING.md). Кратко:

```powershell
build.bat
```

PyInstaller создаёт папку `dist\Transcriber`. Если установлен Inno Setup 6, дополнительно создаётся `installer\output\Transcriber-Setup-0.5.0.exe`.

## Примечания

- Для CUDA нужны совместимая NVIDIA GPU, драйвер и библиотеки, требуемые CTranslate2.
- При CPU обычно следует выбрать `device=cpu` и `compute-type=int8`.
- Кэш Hugging Face располагается в профиле пользователя и не удаляется вместе с приложением.

## Лицензия

GNU General Public License v3.0 — см. [LICENSE](LICENSE).
