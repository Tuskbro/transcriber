from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel


SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".opus",
    ".m4a",
    ".aac",
    ".flac",
    ".mp4",
    ".mkv",
    ".webm",
}


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours:
        return f"{hours:02}:{minutes:02}:{secs:02}"

    return f"{minutes:02}:{secs:02}"


def find_media_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []

    for path in paths:

        if not path.exists():
            print(f"[!] Не найдено: {path}")
            continue

        if path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
            else:
                print(f"[!] Неподдерживаемый файл: {path}")

            continue

        if path.is_dir():
            for item in path.rglob("*"):
                if (
                    item.is_file()
                    and item.suffix.lower() in SUPPORTED_EXTENSIONS
                ):
                    files.append(item)

    # удаляем дубликаты
    unique_files = list(dict.fromkeys(files))

    return unique_files


def transcribe_file(
    model: WhisperModel,
    source: Path,
    language: str | None,
    force: bool,
    output_format: str,
    output_dir: Path | None,
):
    destination = output_dir or source.parent
    output = destination / f"{source.stem}.md"
    json_output = destination / f"{source.stem}.json"

    selected_outputs = {
        "md": [output],
        "json": [json_output],
        "both": [output, json_output],
    }[output_format]

    if all(path.exists() for path in selected_outputs) and not force:
        names = ", ".join(path.name for path in selected_outputs)
        print(f"[SKIP] Уже существует: {names}")
        return

    print()
    print("=" * 70)
    print(f"[FILE] {source}")
    print("=" * 70)

    started = time.time()

    try:
        destination.mkdir(parents=True, exist_ok=True)
        segments, info = model.transcribe(
            str(source),
            language=language,
            vad_filter=True,
            beam_size=5,
        )

        messages: list[dict[str, str]] = []

        print(
            f"[LANG] {info.language} "
            f"({info.language_probability:.2%})"
        )

        for segment in segments:
            text = segment.text.strip()

            if not text:
                continue

            timestamp = format_timestamp(segment.start)
            line = f"[{timestamp}] {text}"

            print(line)

            messages.append({
                "timestamp": timestamp,
                "text": text,
            })

        if output_format in {"md", "both"}:
            markdown = create_markdown(
                source=source,
                language=info.language,
                messages=messages,
            )
            output.write_text(markdown, encoding="utf-8")

        if output_format in {"json", "both"}:
            json_data = create_json(
                source=source,
                language=info.language,
                messages=messages,
            )
            json_output.write_text(
                json.dumps(json_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        elapsed = time.time() - started

        print()
        for saved_output in selected_outputs:
            print(f"[OK] {saved_output}")
        print(f"[TIME] {elapsed:.1f} сек.")

    except Exception as exc:
        print()
        print(f"[ERROR] {source}")
        print(exc)


def create_markdown(
    source: Path,
    language: str,
    messages: list[dict[str, str]],
) -> str:
    text = " ".join(message["text"] for message in messages)
    text_with_timestamps = "\n\n".join(
        f'[{message["timestamp"]}] {message["text"]}'
        for message in messages
    )

    return f"""# {source.stem}

**Source:** `{source.name}`

**Language:** `{language}`

---

## Текст

{text}

## Текст с тайм-кодами

{text_with_timestamps}
"""


def create_json(
    source: Path,
    language: str,
    messages: list[dict[str, str]],
) -> dict:
    return {
        "source": source.name,
        "language": language,
        "message": " ".join(
            message["text"] for message in messages
        ),
        "messages_with_timestamps": messages,
    }

def main():
    parser = argparse.ArgumentParser(
        description="Local audio/video transcriber"
    )

    parser.add_argument(
        "paths",
        nargs="+",
        help="Файлы или папки",
    )

    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model",
    )

    parser.add_argument(
        "--language",
        default="ru",
        help="Язык. Например ru, en. auto = автоопределение",
    )

    parser.add_argument(
        "--device",
        default="cuda",
        choices=["cuda", "cpu"],
    )

    parser.add_argument(
        "--compute-type",
        default="float16",
    )

    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["md", "json", "both"],
        default="md",
        help="Формат результата: md, json или оба (по умолчанию md)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Папка для сохранения результатов",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Перезаписывать существующие выходные файлы",
    )

    args = parser.parse_args()

    paths = [Path(p).resolve() for p in args.paths]

    files = find_media_files(paths)

    if not files:
        print("Подходящих аудио/видео файлов не найдено.")
        sys.exit(1)

    print(f"Найдено файлов: {len(files)}")
    print(f"Модель: {args.model}")
    print(f"Устройство: {args.device}")
    print(f"Формат: {args.output_format}")
    print()

    print("[MODEL] Загрузка модели...")

    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
    )

    language = None if args.language == "auto" else args.language

    print("[MODEL] Готово.")

    for index, source in enumerate(files, start=1):

        print()
        print(f"[{index}/{len(files)}]")

        transcribe_file(
            model=model,
            source=source,
            language=language,
            force=args.force,
            output_format=args.output_format,
            output_dir=args.output_dir.resolve() if args.output_dir else None,
        )

    print()
    print("=" * 70)
    print("Готово.")
    print("=" * 70)


if __name__ == "__main__":
    main()