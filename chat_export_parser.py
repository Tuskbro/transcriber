from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


MEDIA_DIRS = {"voice_messages", "round_video_messages"}
TRANSCRIPTION_START = "<!-- transcriber:start -->"
TRANSCRIPTION_END = "<!-- transcriber:end -->"

ANCHOR_RE = re.compile(
    r"(?P<anchor><a\b[^>]*>.*?</a>)"
    r"(?:\s*<!-- transcriber:start -->.*?<!-- transcriber:end -->)?",
    re.IGNORECASE | re.DOTALL,
)
OPENING_TAG_RE = re.compile(r"<a\b(?P<attrs>[^>]*)>", re.IGNORECASE | re.DOTALL)
ATTRIBUTE_RE = re.compile(
    r"(?P<name>[\w:-]+)\s*=\s*(?P<quote>['\"])(?P<value>.*?)(?P=quote)",
    re.DOTALL,
)
STYLE_RE = re.compile(
    r"<style\b[^>]*\bid=['\"]transcriber-styles['\"][^>]*>.*?</style>",
    re.IGNORECASE | re.DOTALL,
)

STYLE = """<style id="transcriber-styles">
.transcriber-transcription {
  clear: both;
  margin: 10px 0 2px 0;
  padding: 10px 12px;
  max-width: 560px;
  border-left: 3px solid #4ea4f6;
  border-radius: 6px;
  background: rgba(78, 164, 246, 0.10);
  color: #a1a1a1
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.transcriber-transcription .transcriber-title {
  margin-bottom: 5px;
  color: #168acd;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: .03em;
}
.transcriber-transcription .transcriber-text { white-space: normal; }
.transcriber-transcription details { margin-top: 7px; }
.transcriber-transcription summary {
  color: #168acd;
  cursor: pointer;
  user-select: none;
}
.transcriber-transcription .transcriber-timestamps {
  margin-top: 7px;
  color: #555;
  font-size: 12px;
  white-space: normal;
}
body.dark .transcriber-transcription {
  background: rgba(78, 164, 246, 0.14);
  color: #ddd;
}
body.dark .transcriber-transcription .transcriber-timestamps { color: #bbb; }
</style>"""


@dataclass(frozen=True)
class MediaReference:
    href: str
    media_path: Path


@dataclass
class Transcript:
    message: str
    timestamped: list[dict[str, str]]


def attributes_from_anchor(anchor: str) -> dict[str, str]:
    opening = OPENING_TAG_RE.search(anchor)
    if not opening:
        return {}

    return {
        match.group("name").lower(): html.unescape(match.group("value"))
        for match in ATTRIBUTE_RE.finditer(opening.group("attrs"))
    }


def media_reference(anchor: str, export_root: Path) -> MediaReference | None:
    attributes = attributes_from_anchor(anchor)
    classes = set(attributes.get("class", "").split())
    href = attributes.get("href")

    if not href:
        return None
    if "media_voice_message" not in classes and "media_video" not in classes:
        return None

    url_path = unquote(urlsplit(href).path)
    relative = PurePosixPath(url_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        return None
    if relative.parts[0] not in MEDIA_DIRS:
        return None

    return MediaReference(
        href=href,
        media_path=export_root.joinpath(*relative.parts),
    )


def collect_references(html_text: str, export_root: Path) -> list[MediaReference]:
    references: list[MediaReference] = []
    seen: set[Path] = set()

    for match in ANCHOR_RE.finditer(html_text):
        reference = media_reference(match.group("anchor"), export_root)
        if reference and reference.media_path not in seen:
            references.append(reference)
            seen.add(reference.media_path)

    return references


def transcript_candidates(media_path: Path, export_root: Path) -> list[Path]:
    transcription_dir = export_root / "transcriptions"
    return [
        transcription_dir / f"{media_path.stem}.json",
        media_path.with_suffix(".json"),
        transcription_dir / f"{media_path.stem}.md",
        media_path.with_suffix(".md"),
    ]


def transcript_exists(media_path: Path, export_root: Path) -> bool:
    return any(path.is_file() for path in transcript_candidates(media_path, export_root))


def normalize_timestamped(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        timestamp = str(item.get("timestamp", "")).strip()
        text = str(item.get("text", "")).strip()
        if text:
            result.append({"timestamp": timestamp, "text": text})
    return result


def read_json_transcript(path: Path) -> Transcript:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    timestamped = normalize_timestamped(data.get("messages_with_timestamps"))
    message = str(data.get("message", "")).strip()
    if not message:
        message = " ".join(item["text"] for item in timestamped)
    return Transcript(message=message, timestamped=timestamped)


def read_markdown_transcript(path: Path) -> Transcript:
    content = path.read_text(encoding="utf-8-sig")
    text_match = re.search(
        r"^##\s+Текст\s*$\s*(.*?)(?=^##\s+Текст с тайм-кодами\s*$|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    timed_match = re.search(
        r"^##\s+Текст с тайм-кодами\s*$\s*(.*)\Z",
        content,
        re.MULTILINE | re.DOTALL,
    )

    message = text_match.group(1).strip() if text_match else ""
    timed_text = timed_match.group(1).strip() if timed_match else ""
    timestamped = [
        {"timestamp": match.group("timestamp"), "text": match.group("text").strip()}
        for match in re.finditer(
            r"^\[(?P<timestamp>\d{2}(?::\d{2}){1,2})\]\s*(?P<text>.+)$",
            timed_text or content,
            re.MULTILINE,
        )
    ]

    if not message:
        message = " ".join(item["text"] for item in timestamped)
    return Transcript(message=message, timestamped=timestamped)


def load_transcript(media_path: Path, export_root: Path) -> Transcript | None:
    for candidate in transcript_candidates(media_path, export_root):
        if not candidate.is_file():
            continue
        try:
            if candidate.suffix.lower() == ".json":
                transcript = read_json_transcript(candidate)
            else:
                transcript = read_markdown_transcript(candidate)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"[WARN] Не удалось прочитать {candidate}: {exc}")
            continue

        if transcript.message or transcript.timestamped:
            return transcript

    return None


def render_transcript(transcript: Transcript) -> str:
    message = html.escape(transcript.message).replace("\n", "<br/>\n")
    timed_lines = []
    for item in transcript.timestamped:
        timestamp = html.escape(item["timestamp"])
        text = html.escape(item["text"])
        prefix = f"[{timestamp}] " if timestamp else ""
        timed_lines.append(f"{prefix}{text}")

    details = ""
    if timed_lines:
        details = (
            "\n <details>\n"
            "  <summary>Показать текст с тайм-кодами</summary>\n"
            f"  <div class=\"transcriber-timestamps\">{'<br/>'.join(timed_lines)}</div>\n"
            " </details>"
        )

    return (
        f"\n{TRANSCRIPTION_START}\n"
        '<div class="transcriber-transcription">\n'
        ' <div class="transcriber-title">Расшифровка</div>\n'
        f' <div class="transcriber-text">{message}</div>{details}\n'
        "</div>\n"
        f"{TRANSCRIPTION_END}"
    )


def inject_styles(html_text: str) -> str:
    if STYLE_RE.search(html_text):
        return STYLE_RE.sub(STYLE, html_text, count=1)

    head_end = re.search(r"</head\s*>", html_text, re.IGNORECASE)
    if head_end:
        return html_text[:head_end.start()] + STYLE + "\n" + html_text[head_end.start():]
    return STYLE + "\n" + html_text


def update_html(html_path: Path, export_root: Path) -> tuple[int, int]:
    original = html_path.read_text(encoding="utf-8-sig")
    inserted = 0
    missing = 0

    def replace_anchor(match: re.Match[str]) -> str:
        nonlocal inserted, missing
        anchor = match.group("anchor")
        reference = media_reference(anchor, export_root)
        if not reference:
            return match.group(0)

        transcript = load_transcript(reference.media_path, export_root)
        if not transcript:
            missing += 1
            return anchor

        inserted += 1
        return anchor + render_transcript(transcript)

    updated = ANCHOR_RE.sub(replace_anchor, original)
    if inserted:
        updated = inject_styles(updated)

    if updated != original:
        backup = html_path.with_suffix(html_path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(html_path, backup)
        html_path.write_text(updated, encoding="utf-8")

    return inserted, missing


def transcribe_missing(
    export_root: Path,
    references: list[MediaReference],
    args: argparse.Namespace,
) -> None:
    missing = references if args.force else [
        reference for reference in references
        if not transcript_exists(reference.media_path, export_root)
    ]
    if not missing:
        return

    media_dirs = sorted({reference.media_path.parent for reference in missing})
    existing_dirs = [path for path in media_dirs if path.is_dir()]
    if not existing_dirs:
        print(f"[WARN] Медиафайлы для транскрипции не найдены в {export_root}")
        return

    output_dir = export_root / "transcriptions"
    output_dir.mkdir(parents=True, exist_ok=True)
    main_script = Path(__file__).with_name("main.py")
    if getattr(sys, "frozen", False):
        command = [
            str(Path(sys.executable).resolve().with_name("TranscriberCLI.exe")),
            *(str(path) for path in existing_dirs),
        ]
    else:
        command = [
            sys.executable,
            str(main_script),
            *(str(path) for path in existing_dirs),
        ]
    command.extend([
        "--format", "both",
        "--output-dir", str(output_dir),
        "--model", args.model,
        "--language", args.language,
        "--device", args.device,
        "--compute-type", args.compute_type,
    ])
    if args.force:
        command.append("--force")

    print(f"[TRANSCRIBE] Результаты будут сохранены в {output_dir}")
    completed = subprocess.run(command, check=False)
    if completed.returncode:
        print(f"[WARN] Транскрипция завершилась с кодом {completed.returncode}")


def find_html_files(paths: list[Path]) -> dict[Path, list[Path]]:
    groups: dict[Path, list[Path]] = {}
    for path in paths:
        resolved = path.resolve()
        if resolved.is_file() and resolved.suffix.lower() in {".html", ".htm"}:
            groups.setdefault(resolved.parent, []).append(resolved)
        elif resolved.is_dir():
            files = sorted(
                item for item in resolved.rglob("*")
                if item.is_file() and item.suffix.lower() in {".html", ".htm"}
            )
            groups.setdefault(resolved, []).extend(files)
        else:
            print(f"[WARN] HTML-файл или папка не найдены: {path}")

    for root, files in groups.items():
        groups[root] = list(dict.fromkeys(files))
    return groups


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Добавляет транскрипции в HTML-выгрузку Telegram"
    )
    parser.add_argument("paths", nargs="+", type=Path, help="HTML-файл или папка выгрузки")
    parser.add_argument("--no-transcribe", action="store_true", help="Не запускать Whisper для отсутствующих транскрипций")
    parser.add_argument("--force", action="store_true", help="Перезаписывать существующие транскрипции")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--language", default="ru")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--compute-type", default="float16")
    args = parser.parse_args()

    groups = find_html_files(args.paths)
    if not groups or not any(groups.values()):
        print("Подходящие HTML-файлы не найдены.")
        raise SystemExit(1)

    total_inserted = 0
    total_missing = 0

    for export_root, html_files in groups.items():
        print(f"\n[EXPORT] {export_root}")
        references: list[MediaReference] = []
        seen: set[Path] = set()
        for html_path in html_files:
            text = html_path.read_text(encoding="utf-8-sig")
            for reference in collect_references(text, export_root):
                if reference.media_path not in seen:
                    references.append(reference)
                    seen.add(reference.media_path)

        print(f"[MEDIA] Найдено ссылок: {len(references)}")
        if not args.no_transcribe:
            transcribe_missing(export_root, references, args)

        for html_path in html_files:
            inserted, missing = update_html(html_path, export_root)
            total_inserted += inserted
            total_missing += missing
            print(f"[HTML] {html_path.name}: добавлено {inserted}, без текста {missing}")

    print(f"\n[OK] Добавлено расшифровок: {total_inserted}")
    if total_missing:
        print(f"[WARN] Не найдена расшифровка для {total_missing} сообщений")


if __name__ == "__main__":
    main()