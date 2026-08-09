from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from PyQt5.QtCore import QProcess, QProcessEnvironment, QSettings, QTimer, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


APP_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else APP_DIR
MEDIA_FILTER = (
    "Медиафайлы (*.mp3 *.wav *.ogg *.opus *.m4a *.aac *.flac "
    "*.mp4 *.mkv *.webm);;Все файлы (*)"
)
HTML_FILTER = "HTML-файлы (*.html *.htm);;Все файлы (*)"


class DropListWidget(QListWidget):
    paths_dropped = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)
        self.setDefaultDropAction(Qt.CopyAction)

    def dragEnterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

class PathSelector(QWidget):
    def __init__(self, file_filter: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.file_filter = file_filter
        self.paths = DropListWidget()
        self.paths.paths_dropped.connect(self.add_paths)
        self.paths.setAlternatingRowColors(True)
        self.paths.setSelectionMode(QListWidget.ExtendedSelection)
        self.paths.setMinimumHeight(125)

        add_files = QPushButton("Добавить файлы…")
        add_folder = QPushButton("Добавить папку…")
        remove = QPushButton("Убрать")
        clear = QPushButton("Очистить")

        add_files.clicked.connect(self.add_files)
        add_folder.clicked.connect(self.add_folder)
        remove.clicked.connect(self.remove_selected)
        clear.clicked.connect(self.paths.clear)

        buttons = QHBoxLayout()
        buttons.addWidget(add_files)
        buttons.addWidget(add_folder)
        buttons.addStretch(1)
        buttons.addWidget(remove)
        buttons.addWidget(clear)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.paths)
        layout.addLayout(buttons)

    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы",
            "",
            self.file_filter,
        )
        self.add_paths(files)

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths: list[str]) -> None:
        existing = {self.paths.item(i).text() for i in range(self.paths.count())}
        for value in paths:
            normalized = str(Path(value).resolve())
            if normalized not in existing:
                self.paths.addItem(normalized)
                existing.add(normalized)

    def remove_selected(self) -> None:
        for item in self.paths.selectedItems():
            self.paths.takeItem(self.paths.row(item))

    def values(self) -> list[str]:
        return [self.paths.item(i).text() for i in range(self.paths.count())]


class ModelOptions(QGroupBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__("Параметры модели", parent)

        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems(["large-v3", "medium", "small", "base"])

        self.language = QComboBox()
        self.language.setEditable(True)
        self.language.addItems(["ru", "auto", "en"])

        self.device = QComboBox()
        self.device.addItems(["cuda", "cpu"])

        self.compute_type = QComboBox()
        self.compute_type.setEditable(True)
        self.compute_type.addItems(["float16", "int8_float16", "int8", "float32"])

        form = QFormLayout(self)
        form.addRow("Модель:", self.model)
        form.addRow("Язык:", self.language)
        form.addRow("Устройство:", self.device)
        form.addRow("Тип вычислений:", self.compute_type)

    def arguments(self) -> list[str]:
        return [
            "--model", self.model.currentText().strip(),
            "--language", self.language.currentText().strip(),
            "--device", self.device.currentText(),
            "--compute-type", self.compute_type.currentText().strip(),
        ]

    def load_settings(self, settings: QSettings, prefix: str) -> None:
        self.model.setCurrentText(settings.value(f"{prefix}/model", "large-v3"))
        self.language.setCurrentText(settings.value(f"{prefix}/language", "ru"))
        self.device.setCurrentText(settings.value(f"{prefix}/device", "cuda"))
        self.compute_type.setCurrentText(
            settings.value(f"{prefix}/compute_type", "float16")
        )

    def save_settings(self, settings: QSettings, prefix: str) -> None:
        settings.setValue(f"{prefix}/model", self.model.currentText())
        settings.setValue(f"{prefix}/language", self.language.currentText())
        settings.setValue(f"{prefix}/device", self.device.currentText())
        settings.setValue(f"{prefix}/compute_type", self.compute_type.currentText())


class TranscriptionTab(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.path_selector = PathSelector(MEDIA_FILTER)
        self.options = ModelOptions()

        self.output_format = QComboBox()
        self.output_format.addItem("Markdown", "md")
        self.output_format.addItem("JSON", "json")
        self.output_format.addItem("Markdown + JSON", "both")

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Рядом с исходным файлом")
        browse_output = QPushButton("Обзор…")
        browse_output.clicked.connect(self.select_output_dir)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_dir)
        output_row.addWidget(browse_output)

        self.force = QCheckBox("Перезаписывать существующие результаты (--force)")

        output_group = QGroupBox("Результат")
        output_form = QFormLayout(output_group)
        output_form.addRow("Формат:", self.output_format)
        output_form.addRow("Папка:", output_row)
        output_form.addRow("", self.force)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Медиафайлы или папки:"))
        layout.addWidget(self.path_selector)
        layout.addWidget(output_group)
        layout.addWidget(self.options)
        layout.addStretch(1)

    def select_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Папка результатов")
        if folder:
            self.output_dir.setText(folder)

    def command(self) -> tuple[Path, list[str]]:
        paths = self.path_selector.values()
        if not paths:
            raise ValueError("Добавьте хотя бы один медиафайл или папку.")

        arguments = [
            *paths,
            "--format", self.output_format.currentData(),
            *self.options.arguments(),
        ]
        if self.output_dir.text().strip():
            arguments.extend(["--output-dir", self.output_dir.text().strip()])
        if self.force.isChecked():
            arguments.append("--force")
        return APP_DIR / "main.py", arguments

    def load_settings(self, settings: QSettings) -> None:
        self.options.load_settings(settings, "transcription")
        index = self.output_format.findData(settings.value("transcription/format", "md"))
        self.output_format.setCurrentIndex(max(index, 0))
        self.output_dir.setText(settings.value("transcription/output_dir", ""))
        self.force.setChecked(settings.value("transcription/force", False, type=bool))

    def save_settings(self, settings: QSettings) -> None:
        self.options.save_settings(settings, "transcription")
        settings.setValue("transcription/format", self.output_format.currentData())
        settings.setValue("transcription/output_dir", self.output_dir.text())
        settings.setValue("transcription/force", self.force.isChecked())


class ChatExportTab(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.path_selector = PathSelector(HTML_FILTER)
        self.options = ModelOptions()
        self.no_transcribe = QCheckBox(
            "Только встроить готовые JSON/MD, не запускать Whisper"
        )
        self.force = QCheckBox(
            "Перезаписать существующие транскрипции и описания (--force)"
        )

        self.describe_images = QCheckBox(
            "Создавать текстовые описания фото и стикеров через Ollama"
        )
        self.vision_model = QComboBox()
        self.vision_model.setEditable(True)
        self.vision_model.addItems(
            ["qwen3-vl-vision:latest", "qwen3-vl:8b", "qwen3-vl:4b", "qwen3-vl:2b"]
        )
        self.ollama_url = QLineEdit("http://127.0.0.1:11434")
        self.vision_log = QCheckBox("Подробный лог ошибок Ollama (--log)")

        self.export_md = QCheckBox("Создать текстовую Markdown-выгрузку для Obsidian")
        self.md_chunk_size = QSpinBox()
        self.md_chunk_size.setRange(50, 5000)
        self.md_chunk_size.setValue(500)
        self.md_chunk_size.setSuffix(" сообщений")
        self.md_chunk_size.setEnabled(False)
        self.export_md.toggled.connect(self.md_chunk_size.setEnabled)

        markdown_group = QGroupBox("Текстовая выгрузка чата")
        markdown_form = QFormLayout(markdown_group)
        markdown_form.addRow("", self.export_md)
        markdown_form.addRow("Размер одной части:", self.md_chunk_size)

        vision_group = QGroupBox("Описание изображений")
        vision_form = QFormLayout(vision_group)
        vision_form.addRow("", self.describe_images)
        vision_form.addRow("Vision-модель:", self.vision_model)
        vision_form.addRow("Ollama API:", self.ollama_url)
        vision_form.addRow("", self.vision_log)

        self.no_transcribe.toggled.connect(self.update_force_enabled)
        self.describe_images.toggled.connect(self.update_force_enabled)

        note = QLabel(
            "Расшифровки сохраняются в transcriptions, описания картинок — "
            "в image_descriptions. HTML перед первым изменением копируется в .bak."
        )
        note.setWordWrap(True)
        note.setObjectName("note")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("HTML-файлы или папка Telegram Chat Export:"))
        layout.addWidget(self.path_selector)
        layout.addWidget(self.no_transcribe)
        layout.addWidget(self.force)
        layout.addWidget(vision_group)
        layout.addWidget(markdown_group)
        layout.addWidget(note)
        layout.addWidget(self.options)
        layout.addStretch(1)

    def update_force_enabled(self) -> None:
        self.vision_log.setEnabled(self.describe_images.isChecked())
        self.force.setEnabled(
            not self.no_transcribe.isChecked() or self.describe_images.isChecked()
        )

    def command(self) -> tuple[Path, list[str]]:
        paths = self.path_selector.values()
        if not paths:
            raise ValueError("Добавьте HTML-файл или папку экспорта.")

        arguments = [*paths, *self.options.arguments()]
        if self.no_transcribe.isChecked():
            arguments.append("--no-transcribe")
        if self.describe_images.isChecked():
            arguments.extend([
                "--describe-images",
                "--vision-model", self.vision_model.currentText().strip(),
                "--ollama-url", self.ollama_url.text().strip(),
            ])
        if self.vision_log.isChecked() and self.describe_images.isChecked():
            arguments.append("--log")
        if self.export_md.isChecked():
            arguments.extend(["--export-md", "--md-chunk-size", str(self.md_chunk_size.value())])
        if self.force.isChecked() and self.force.isEnabled():
            arguments.append("--force")
        return APP_DIR / "chat_export_parser.py", arguments

    def load_settings(self, settings: QSettings) -> None:
        self.options.load_settings(settings, "chat_export")
        self.no_transcribe.setChecked(
            settings.value("chat_export/no_transcribe", False, type=bool)
        )
        self.force.setChecked(
            settings.value("chat_export/force", False, type=bool)
        )
        self.describe_images.setChecked(
            settings.value("chat_export/describe_images", False, type=bool)
        )
        self.vision_model.setCurrentText(
            settings.value("chat_export/vision_model", "qwen3-vl:8b")
        )
        self.ollama_url.setText(
            settings.value("chat_export/ollama_url", "http://127.0.0.1:11434")
        )
        self.vision_log.setChecked(
            settings.value("chat_export/vision_log", False, type=bool)
        )
        self.export_md.setChecked(
            settings.value("chat_export/export_md", False, type=bool)
        )
        self.md_chunk_size.setValue(
            settings.value("chat_export/md_chunk_size", 500, type=int)
        )
        self.update_force_enabled()

    def save_settings(self, settings: QSettings) -> None:
        self.options.save_settings(settings, "chat_export")
        settings.setValue("chat_export/no_transcribe", self.no_transcribe.isChecked())
        settings.setValue("chat_export/force", self.force.isChecked())
        settings.setValue("chat_export/describe_images", self.describe_images.isChecked())
        settings.setValue("chat_export/vision_model", self.vision_model.currentText())
        settings.setValue("chat_export/ollama_url", self.ollama_url.text())
        settings.setValue("chat_export/vision_log", self.vision_log.isChecked())
        settings.setValue("chat_export/export_md", self.export_md.isChecked())
        settings.setValue("chat_export/md_chunk_size", self.md_chunk_size.value())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcriber")
        self.resize(880, 900)

        self.settings = QSettings("LocalTools", "Transcriber")
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONUNBUFFERED", "1")
        environment.insert("PYTHONIOENCODING", "utf-8")
        environment.insert("PYTHONUTF8", "1")
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(str(APP_DIR))
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.started.connect(self.process_started)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)

        self.tabs = QTabWidget()
        self.transcription_tab = TranscriptionTab()
        self.chat_export_tab = ChatExportTab()
        self.tabs.addTab(self.transcription_tab, "Транскрипция")
        self.tabs.addTab(self.chat_export_tab, "Chat Export")

        self.log = QTextBrowser()
        self.log.setOpenLinks(False)
        self.log.setOpenExternalLinks(False)
        self.log.anchorClicked.connect(self.open_log_link)
        self.output_buffer = ""
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(190)
        log_font = QFont("Consolas")
        log_font.setStyleHint(QFont.Monospace)
        self.log.setFont(log_font)

        self.start_button = QPushButton("Запустить")
        self.start_button.setObjectName("startButton")
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)
        open_output_button = QPushButton("Открыть папку результата")
        clear_button = QPushButton("Очистить лог")
        self.dark_theme = QCheckBox("Тёмная тема")

        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        open_output_button.clicked.connect(self.open_result_folder)
        clear_button.clicked.connect(self.log.clear)
        self.dark_theme.toggled.connect(self.apply_theme)

        actions = QHBoxLayout()
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addWidget(open_output_button)
        actions.addStretch(1)
        actions.addWidget(self.dark_theme)
        actions.addWidget(clear_button)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.tabs, 3)
        layout.addWidget(QLabel("Вывод:"))
        layout.addWidget(self.log, 1)
        layout.addLayout(actions)
        self.setCentralWidget(central)

        self.dark_theme.setChecked(self.settings.value("window/dark_theme", False, type=bool))
        self.apply_theme(self.dark_theme.isChecked())

        self.transcription_tab.load_settings(self.settings)
        self.chat_export_tab.load_settings(self.settings)
        self.tabs.setCurrentIndex(self.settings.value("window/tab", 0, type=int))

    def active_command(self) -> tuple[Path, list[str]]:
        widget = self.tabs.currentWidget()
        if isinstance(widget, TranscriptionTab):
            return widget.command()
        if isinstance(widget, ChatExportTab):
            return widget.command()
        raise ValueError("Неизвестная вкладка.")

    def start_process(self) -> None:
        if self.process.state() != QProcess.NotRunning:
            return
        try:
            script, arguments = self.active_command()
        except ValueError as exc:
            QMessageBox.warning(self, "Не выбраны файлы", str(exc))
            return

        if not script.is_file():
            QMessageBox.critical(self, "Ошибка", f"Не найден файл: {script}")
            return

        self.output_buffer = ""
        if getattr(sys, "frozen", False):
            executable_name = (
                "TranscriberCLI.exe"
                if script.name == "main.py"
                else "ChatExportParser.exe"
            )
            program = RUNTIME_DIR / executable_name
            process_arguments = arguments
        else:
            program = Path(sys.executable)
            process_arguments = [str(script), *arguments]

        command_preview = " ".join([str(program), *process_arguments])
        self.append_log(f"\n> {command_preview}\n")
        self.process.start(str(program), process_arguments)

    def stop_process(self) -> None:
        if self.process.state() == QProcess.NotRunning:
            return
        self.append_log("\n[GUI] Остановка процесса…\n")
        self.process.terminate()
        QTimer.singleShot(3000, self.kill_if_running)

    def kill_if_running(self) -> None:
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()

    def read_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput())
        self.output_buffer += data.decode("utf-8", errors="replace")
        while "\n" in self.output_buffer:
            line, self.output_buffer = self.output_buffer.split("\n", 1)
            self.append_output_line(line.rstrip("\r"))

    def append_output_line(self, line: str) -> None:
        match = re.match(r"^\[(EXPORT|OK)\]\s+(.+)$", line)
        if match:
            candidate = Path(match.group(2).strip())
            if candidate.exists():
                resolved = candidate.resolve()
                url = QUrl.fromLocalFile(str(resolved)).toString()
                name = resolved.name or str(resolved)
                parent = "" if not resolved.name else str(resolved.parent) + "\\"
                prefix = html.escape(f"[{match.group(1)}] {parent}")
                label = html.escape(name)
                cursor = self.log.textCursor()
                cursor.movePosition(cursor.End)
                cursor.insertHtml(f'{prefix}<a href="{url}">{label}</a><br/>')
                self.log.setTextCursor(cursor)
                self.log.ensureCursorVisible()
                return
        self.append_log(line + "\n")

    def append_log(self, text: str) -> None:
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def open_log_link(self, url: QUrl) -> None:
        QDesktopServices.openUrl(url)

    def result_folder(self) -> Path | None:
        current = self.tabs.currentWidget()
        if isinstance(current, TranscriptionTab):
            configured = current.output_dir.text().strip()
            if configured:
                return Path(configured)
            paths = current.path_selector.values()
            if paths:
                first = Path(paths[0])
                return first if first.is_dir() else first.parent
        elif isinstance(current, ChatExportTab):
            paths = current.path_selector.values()
            if paths:
                first = Path(paths[0])
                root = first if first.is_dir() else first.parent
                transcriptions = root / "transcriptions"
                return transcriptions if transcriptions.exists() else root
        return None

    def open_result_folder(self) -> None:
        folder = self.result_folder()
        if folder is None:
            QMessageBox.information(self, "Папка результата", "Сначала выберите файл или папку.")
            return
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def apply_theme(self, dark: bool) -> None:
        if dark:
            colors = {
                "window": "#3c455c", "panel": "#3c455c", "field": "#433c5c",
                "text": "#dde2e3", "muted": "#9aacb8", "border": "#3c555c",
                "accent": "#b37c57", "disabled": "#60412b", "selection": "#60412b",
                "button_text": "#dde2e3", "hover": "#3c555c", "tab": "#3c555c",
                "positive": "#455c3c", "danger": "#5c3c45", "focus": "#b37c57",
                "link": "#b37c57",
            }
        else:
            colors = {
                "window": "#ebe3ce", "panel": "#c4d4d7", "field": "#ebe3ce",
                "text": "#145270", "muted": "#145270", "border": "#07b1cd",
                "accent": "#07b1cd", "disabled": "#c4d4d7", "selection": "#03e3e3",
                "button_text": "#ebe3ce", "hover": "#03e3e3", "tab": "#142470",
                "positive": "#147060", "danger": "#701452", "focus": "#527014",
                "link": "#701452",
            }
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {colors['window']}; color: {colors['text']}; }}
            QTabWidget::pane {{ border: 1px solid {colors['border']}; background: {colors['panel']}; }}
            QTabBar::tab {{ padding: 8px 18px; background: {colors['field']}; border: 1px solid {colors['border']}; }}
            QTabBar::tab:selected {{ background: {colors['tab']}; color: {colors['button_text']}; }}
            QGroupBox {{ font-weight: bold; border: 1px solid {colors['border']}; border-radius: 7px; margin-top: 10px; padding-top: 10px; background: {colors['panel']}; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {colors['accent']}; }}
            QLineEdit, QComboBox, QListWidget, QTextBrowser {{ border: 1px solid {colors['border']}; border-radius: 5px; padding: 5px; background: {colors['field']}; color: {colors['text']}; selection-background-color: {colors['selection']}; }}
            QComboBox QAbstractItemView {{ background: {colors['field']}; color: {colors['text']}; selection-background-color: {colors['selection']}; }}
            QLineEdit:focus, QComboBox:focus, QListWidget:focus, QTextBrowser:focus {{ border: 2px solid {colors['focus']}; }}
            QPushButton {{ padding: 7px 13px; border: 1px solid {colors['border']}; border-radius: 5px; background: {colors['field']}; }}
            QPushButton:hover {{ border-color: {colors['hover']}; background: {colors['hover']}; }}
            QPushButton#startButton {{ color: {colors['button_text']}; background: {colors['positive']}; border: none; font-weight: bold; }}
            QPushButton#startButton:disabled {{ background: {colors['disabled']}; }}
            QPushButton#stopButton {{ color: {colors['button_text']}; background: {colors['danger']}; border: none; font-weight: bold; }}
            QPushButton#stopButton:disabled {{ background: {colors['disabled']}; }}
            QLabel#note {{ color: {colors['muted']}; padding: 6px; }}
            QTextBrowser a {{ color: {colors['link']}; text-decoration: underline; }}
        """)
        self.log.document().setDefaultStyleSheet(
            f"a {{ color: {colors['link']}; text-decoration: underline; }}"
        )

    def process_started(self) -> None:
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.tabs.setEnabled(False)

    def process_finished(self, exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        self.read_output()
        if self.output_buffer:
            self.append_output_line(self.output_buffer.rstrip("\r"))
            self.output_buffer = ""
        self.append_log(f"\n[GUI] Процесс завершён, код: {exit_code}\n")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.tabs.setEnabled(True)

    def process_error(self, _error: QProcess.ProcessError) -> None:
        self.append_log(f"\n[GUI ERROR] {self.process.errorString()}\n")

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self.process.state() != QProcess.NotRunning:
            answer = QMessageBox.question(
                self,
                "Процесс выполняется",
                "Остановить процесс и закрыть приложение?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.process.kill()
            self.process.waitForFinished(2000)

        self.transcription_tab.save_settings(self.settings)
        self.chat_export_tab.save_settings(self.settings)
        self.settings.setValue("window/tab", self.tabs.currentIndex())
        self.settings.setValue("window/dark_theme", self.dark_theme.isChecked())
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Transcriber")
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec_())


if __name__ == "__main__":
    main()
