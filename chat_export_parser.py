from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from image_describer import (
    DEFAULT_OLLAMA_URL,
    DEFAULT_VISION_MODEL,
    ImageDescriptionError,
    describe_image,
)


MEDIA_DIRS = {"voice_messages", "round_video_messages"}
IMAGE_DIRS = {"photos", "stickers"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
TRANSCRIPTION_START = "<!-- transcriber:start -->"
TRANSCRIPTION_END = "<!-- transcriber:end -->"
DESCRIPTION_START = "<!-- image-description:start -->"
DESCRIPTION_END = "<!-- image-description:end -->"

ANCHOR_RE = re.compile(
    r"(?P<anchor><a\b[^>]*>.*?</a>)"
    r"(?:\s*<!-- transcriber:start -->.*?<!-- transcriber:end -->)?",
    re.IGNORECASE | re.DOTALL,
)
IMAGE_ANCHOR_RE = re.compile(
    r"(?P<anchor><a\b[^>]*>.*?</a>)"
    r"(?:\s*<!-- image-description:start -->.*?<!-- image-description:end -->)?",
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
MESSAGE_START_RE = re.compile(
    r'<div\b[^>]*class=["\'][^"\']*\bmessage\b[^"\']*["\'][^>]*>',
    re.IGNORECASE,
)
MESSAGE_TEXT_RE = re.compile(
    r'<div\b[^>]*class=["\']text["\'][^>]*>(?P<text>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
MESSAGE_DATE_RE = re.compile(
    r'<div\b[^>]*class=["\'][^"\']*\bdate\b[^"\']*["\'][^>]*'
    r'title=["\'](?P<title>.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)

STYLE = """<style id="transcriber-styles">
.transcriber-transcription {
  clear: both;
  margin: 10px 0 2px 0;
  padding: 10px 12px;
  max-width: 560px;
  border-left: 3px solid #4ea4f6;
  border-radius: 6px;
  background: rgba(78, 164, 246, 0.10);
  color: #a1a1a1;
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
.transcriber-image-description {
  clear: both;
  margin: 8px 0 2px 0;
  padding: 9px 12px;
  max-width: 560px;
  border-left: 3px solid #b37c57;
  border-radius: 6px;
  background: rgba(179, 124, 87, 0.10);
  color: #444;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.transcriber-image-description .transcriber-title {
  margin-bottom: 5px;
  color: #9a603e;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: .03em;
}
body.dark .transcriber-image-description {
  background: rgba(179, 124, 87, 0.16);
  color: #ddd;
}
</style>"""


@dataclass(frozen=True)
class MediaReference:
    href: str
    media_path: Path


@dataclass
class Transcript:
    message: str
    timestamped: list[dict[str, str]]


@dataclass(frozen=True)
class ImageReference:
    href: str
    image_path: Path
    caption: str | None = None


@dataclass
class ChatMessage:
    message_id: str
    sent_at: datetime
    sender: str
    parts: list[str]
    reply_to: str | None = None
    reactions: list[tuple[str, int]] | None = None


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


def image_reference(anchor: str, export_root: Path) -> ImageReference | None:
    attributes = attributes_from_anchor(anchor)
    classes = set(attributes.get("class", "").split())
    href = attributes.get("href")
    if not href or not ({"photo_wrap", "sticker_wrap"} & classes):
        return None

    relative = PurePosixPath(unquote(urlsplit(href).path))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        return None
    media_dir = relative.parts[0]
    if media_dir not in IMAGE_DIRS or "_thumb" in relative.name.lower():
        return None
    if media_dir == "stickers" and relative.suffix.lower() != ".webp":
        return None
    if media_dir == "photos" and relative.suffix.lower() not in IMAGE_EXTENSIONS:
        return None
    return ImageReference(href=href, image_path=export_root.joinpath(*relative.parts))


def collect_image_references(html_text: str, export_root: Path) -> list[ImageReference]:
    references: list[ImageReference] = []
    seen: set[Path] = set()
    candidates: list[tuple[ImageReference, str | None, str | None]] = []
    starts = list(MESSAGE_START_RE.finditer(html_text))

    # Keep supporting small HTML fragments that contain an image anchor without
    # the outer Telegram message container.
    if not starts:
        for match in IMAGE_ANCHOR_RE.finditer(html_text):
            reference = image_reference(match.group("anchor"), export_root)
            if reference and reference.image_path not in seen:
                references.append(reference)
                seen.add(reference.image_path)
        return references

    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(html_text)
        message_block = html_text[start.start():end]
        block_references = []
        for match in IMAGE_ANCHOR_RE.finditer(message_block):
            reference = image_reference(match.group("anchor"), export_root)
            if reference:
                block_references.append(reference)
        if not block_references:
            continue

        text_match = MESSAGE_TEXT_RE.search(message_block)
        caption = None
        if text_match:
            plain_text = TAG_RE.sub(" ", text_match.group("text"))
            caption = " ".join(html.unescape(plain_text).split()) or None
        date_match = MESSAGE_DATE_RE.search(message_block)
        timestamp = html.unescape(date_match.group("title")) if date_match else None
        for reference in block_references:
            candidates.append((reference, caption, timestamp))

    timestamp_counts: dict[str, int] = {}
    for _, _, timestamp in candidates:
        if timestamp:
            timestamp_counts[timestamp] = timestamp_counts.get(timestamp, 0) + 1

    for reference, caption, timestamp in candidates:
        if reference.image_path in seen:
            continue
        is_album = bool(timestamp and timestamp_counts.get(timestamp, 0) > 1)
        references.append(
            ImageReference(
                href=reference.href,
                image_path=reference.image_path,
                caption=None if is_album else caption,
            )
        )
        seen.add(reference.image_path)
    return references


def description_path(image_path: Path, export_root: Path) -> Path:
    return export_root / "image_descriptions" / image_path.parent.name / f"{image_path.stem}.json"


def load_image_description(image_path: Path, export_root: Path) -> str | None:
    path = description_path(image_path, export_root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"[WARN] Не удалось прочитать {path}: {exc}")
        return None
    description = str(data.get("description", "")).strip()
    return description or None


def generate_image_descriptions(
    export_root: Path,
    references: list[ImageReference],
    args: argparse.Namespace,
) -> tuple[int, int]:
    generated = 0
    failed = 0
    pending = [
        reference for reference in references
        if args.force or not description_path(reference.image_path, export_root).is_file()
    ]
    if not pending:
        print("[VISION] Все описания изображений уже существуют.")
        return generated, failed

    print(f"[VISION] Модель: {args.vision_model}; изображений: {len(pending)}")
    for index, reference in enumerate(pending, start=1):
        source = reference.image_path
        print(f"[VISION {index}/{len(pending)}] {source.name}")
        if not source.is_file():
            print(f"[WARN] Изображение не найдено: {source}")
            failed += 1
            continue
        try:
            description = describe_image(
                source,
                model=args.vision_model,
                ollama_url=args.ollama_url,
                log=args.log,
                context=reference.caption,
            )
            target = description_path(source, export_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(
                    {
                        "source": str(source.relative_to(export_root)).replace("\\", "/"),
                        "model": args.vision_model,
                        "caption_context": reference.caption,
                        "description": description,
                    },
                    ensure_ascii=False,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
            print(f"[DESCRIPTION] {description}")
            generated += 1
        except ImageDescriptionError as exc:
            print(f"[WARN] Не удалось описать {source.name}: {exc}")
            failed += 1
            continue
        except OSError as exc:
            print(f"[WARN] Не удалось прочитать {source.name}: {exc}")
            failed += 1
    return generated, failed


def render_image_description(description: str) -> str:
    escaped = html.escape(description).replace("\n", "<br/>\n")
    return (
        f"\n{DESCRIPTION_START}\n"
        '<div class="transcriber-image-description">\n'
        ' <div class="transcriber-title">Описание изображения</div>\n'
        f' <div class="transcriber-text">{escaped}</div>\n'
        "</div>\n"
        f"{DESCRIPTION_END}"
    )


def html_fragment_to_text(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.IGNORECASE)
    fragment = TAG_RE.sub("", fragment)
    lines = [" ".join(line.split()) for line in html.unescape(fragment).splitlines()]
    return "\n".join(line for line in lines if line).strip()


def extract_chat_messages(
    html_files: list[Path], export_root: Path
) -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    last_sender = "Неизвестный отправитель"

    for html_path in html_files:
        source = html_path.read_text(encoding="utf-8-sig")
        starts = list(MESSAGE_START_RE.finditer(source))
        for index, start in enumerate(starts):
            end = starts[index + 1].start() if index + 1 < len(starts) else len(source)
            block = source[start.start():end]
            id_match = re.search(r'\bid=["\']message(?P<id>-?\d+)["\']', start.group(0), re.IGNORECASE)
            message_id = id_match.group("id") if id_match else f"seq-{len(messages) + 1:06d}"
            date_match = MESSAGE_DATE_RE.search(block)
            if not date_match:
                continue
            try:
                sent_at = datetime.strptime(
                    html.unescape(date_match.group("title"))[:19], "%d.%m.%Y %H:%M:%S"
                )
            except ValueError:
                continue

            sender_match = re.search(
                r'<div\b[^>]*class=["\']from_name["\'][^>]*>(.*?)</div>',
                block,
                re.IGNORECASE | re.DOTALL,
            )
            if sender_match:
                sender = html_fragment_to_text(sender_match.group(1))
                if sender:
                    last_sender = sender

            parts: list[str] = []
            reply_match = re.search(
                r'<div\b[^>]*class=["\'][^"\']*\breply_to\b[^"\']*["\'][^>]*>.*?'
                r'href=["\']#go_to_message(?P<id>-?\d+)["\']',
                block,
                re.IGNORECASE | re.DOTALL,
            )
            reply_to = reply_match.group("id") if reply_match else None
            text_match = MESSAGE_TEXT_RE.search(block)
            if text_match:
                text_fragment = text_match.group("text")
                animated_sticker = re.fullmatch(
                    r'\s*<a\b[^>]*href\s*=\s*["\'](?P<href>[^"\']+)["\'][^>]*>'
                    r'(?P<label>.*?)</a>\s*',
                    text_fragment,
                    re.IGNORECASE | re.DOTALL,
                )
                sticker_href = animated_sticker.group("href") if animated_sticker else ""
                sticker_path = PurePosixPath(unquote(urlsplit(sticker_href).path))
                if (
                    animated_sticker
                    and sticker_path.suffix.lower() in {".webm", ".tgs"}
                    and "sticker" in sticker_path.name.lower()
                ):
                    label = html_fragment_to_text(animated_sticker.group("label"))
                    suffix = f" {label}" if label else ""
                    parts.append(f"**Анимированный стикер:**{suffix} (`{sticker_path.name}`)")
                else:
                    text = html_fragment_to_text(text_fragment)
                    if text:
                        parts.append(text)

            recognized_anchors: set[str] = set()
            for match in ANCHOR_RE.finditer(block):
                anchor = match.group("anchor")
                reference = media_reference(anchor, export_root)
                if not reference:
                    continue
                recognized_anchors.add(anchor)
                transcript = load_transcript(reference.media_path, export_root)
                classes = set(attributes_from_anchor(anchor).get("class", "").split())
                label = "Видеосообщение" if "media_video" in classes else "Голосовое сообщение"
                if transcript and transcript.message:
                    parts.append(f"**{label}:** {transcript.message.strip()}")
                else:
                    parts.append(f"**{label}:** _транскрипция отсутствует_")

            for match in IMAGE_ANCHOR_RE.finditer(block):
                anchor = match.group("anchor")
                reference = image_reference(anchor, export_root)
                if not reference:
                    continue
                recognized_anchors.add(anchor)
                is_sticker = reference.image_path.parent.name.lower() == "stickers"
                label = "Стикер" if is_sticker else "Фото"
                description = load_image_description(reference.image_path, export_root)
                if description:
                    parts.append(f"**{label}:** {description}")
                else:
                    parts.append(f"**{label}:** `{reference.image_path.name}`")

            for match in re.finditer(r"<a\b[^>]*>.*?</a>", block, re.IGNORECASE | re.DOTALL):
                anchor = match.group(0)
                if anchor in recognized_anchors:
                    continue
                attrs = attributes_from_anchor(anchor)
                classes = set(attrs.get("class", "").split())
                if "media_photo" in classes:
                    name = Path(unquote(urlsplit(attrs.get("href", "")).path)).name
                    parts.append(f"**Видео:** `{name}`")

            reactions: list[tuple[str, int]] = []
            reaction_starts = list(re.finditer(
                r'<span\b[^>]*class=["\'][^"\']*\breaction\b[^"\']*["\'][^>]*>',
                block,
                re.IGNORECASE,
            ))
            for reaction_index, reaction_start in enumerate(reaction_starts):
                reaction_end = (
                    reaction_starts[reaction_index + 1].start()
                    if reaction_index + 1 < len(reaction_starts)
                    else len(block)
                )
                reaction_block = block[reaction_start.start():reaction_end]
                emoji_match = re.search(
                    r'<span\b[^>]*class=["\']emoji["\'][^>]*>(.*?)</span>',
                    reaction_block,
                    re.IGNORECASE | re.DOTALL,
                )
                if not emoji_match:
                    continue
                emoji = html_fragment_to_text(emoji_match.group(1))
                count = len(re.findall(
                    r'<div\b[^>]*class=["\'][^"\']*\buserpic\b',
                    reaction_block,
                    re.IGNORECASE,
                ))
                if emoji:
                    reactions.append((emoji, max(count, 1)))

            if parts:
                messages.append(
                    ChatMessage(
                        message_id=message_id,
                        sent_at=sent_at,
                        sender=last_sender,
                        parts=parts,
                        reply_to=reply_to,
                        reactions=reactions,
                    )
                )
    return messages


def markdown_navigation(part: int, total: int) -> str:
    links = []
    if part > 1:
        links.append(f"[[chat-part-{part - 1:03d}|← Предыдущая часть]]")
    if part < total:
        links.append(f"[[chat-part-{part + 1:03d}|Следующая часть →]]")
    return " · ".join(links)


def export_markdown_chat(
    export_root: Path,
    html_files: list[Path],
    chunk_size: int,
    output_dir: Path | None = None,
) -> list[Path]:
    messages = extract_chat_messages(html_files, export_root)
    destination = output_dir or export_root / "markdown_export"
    destination.mkdir(parents=True, exist_ok=True)
    chunks = [messages[index:index + chunk_size] for index in range(0, len(messages), chunk_size)]
    written: list[Path] = []
    message_parts = {
        message.message_id: part
        for part, chunk in enumerate(chunks, start=1)
        for message in chunk
    }
    expected_names = {f"chat-part-{part:03d}.md" for part in range(1, len(chunks) + 1)}
    for stale in destination.glob("chat-part-*.md"):
        if stale.name not in expected_names:
            stale.unlink()

    for part, chunk in enumerate(chunks, start=1):
        navigation = markdown_navigation(part, len(chunks))
        lines = [f"# Чат — часть {part} из {len(chunks)}", ""]
        if navigation:
            lines.extend([navigation, "", "---", ""])
        current_day = None
        for message in chunk:
            day = message.sent_at.date()
            if day != current_day:
                lines.extend([f"# {day:%Y-%m-%d}", ""])
                current_day = day
            lines.extend([
                f"**{message.sent_at:%H:%M} — {message.sender}**",
                f"Message ID: `{message.message_id}`",
                "",
            ])
            if message.reply_to:
                target_part = message_parts.get(message.reply_to)
                if target_part:
                    lines.extend([
                        f"Reply to: [[chat-part-{target_part:03d}#^message-{message.reply_to}|message {message.reply_to}]]",
                        "",
                    ])
                else:
                    lines.extend([f"Reply to: `message {message.reply_to}`", ""])
            lines.extend([*message.parts, ""])
            if message.reactions:
                rendered_reactions = ", ".join(
                    f"{emoji} x{count}" for emoji, count in message.reactions
                )
                lines.extend([f"Reactions: {rendered_reactions}", ""])
            lines.extend([f"^message-{message.message_id}", ""])
        if navigation:
            lines.extend(["---", "", navigation, ""])
        target = destination / f"chat-part-{part:03d}.md"
        target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        written.append(target)

    print(f"[MARKDOWN] Сообщений: {len(messages)}; частей: {len(written)}; папка: {destination}")
    return written

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


def update_html(html_path: Path, export_root: Path) -> tuple[int, int, int, int]:
    original = html_path.read_text(encoding="utf-8-sig")
    inserted = 0
    missing = 0
    descriptions_inserted = 0
    descriptions_missing = 0

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

    def replace_image_anchor(match: re.Match[str]) -> str:
        nonlocal descriptions_inserted, descriptions_missing
        anchor = match.group("anchor")
        reference = image_reference(anchor, export_root)
        if not reference:
            return match.group(0)

        description = load_image_description(reference.image_path, export_root)
        if not description:
            descriptions_missing += 1
            return anchor

        descriptions_inserted += 1
        return anchor + render_image_description(description)

    updated = ANCHOR_RE.sub(replace_anchor, original)
    updated = IMAGE_ANCHOR_RE.sub(replace_image_anchor, updated)
    if inserted or descriptions_inserted:
        updated = inject_styles(updated)

    if updated != original:
        backup = html_path.with_suffix(html_path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(html_path, backup)
        html_path.write_text(updated, encoding="utf-8")

    return inserted, missing, descriptions_inserted, descriptions_missing

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


def telegram_html_sort_key(path: Path) -> tuple[str, str, int, str]:
    match = re.fullmatch(r"(?P<prefix>.*?)(?P<number>\d+)?", path.stem)
    prefix = match.group("prefix") if match else path.stem
    number = int(match.group("number")) if match and match.group("number") else 1
    return str(path.parent).lower(), prefix.lower(), number, path.suffix.lower()


def find_html_files(paths: list[Path]) -> dict[Path, list[Path]]:
    groups: dict[Path, list[Path]] = {}
    for path in paths:
        resolved = path.resolve()
        if resolved.is_file() and resolved.suffix.lower() in {".html", ".htm"}:
            groups.setdefault(resolved.parent, []).append(resolved)
        elif resolved.is_dir():
            files = sorted(
                (
                    item for item in resolved.rglob("*")
                    if item.is_file() and item.suffix.lower() in {".html", ".htm"}
                ),
                key=telegram_html_sort_key,
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
    parser.add_argument("--force", action="store_true", help="Перезаписывать существующие транскрипции и описания")
    parser.add_argument("--describe-images", action="store_true", help="Создавать описания фото и стикеров через Ollama")
    parser.add_argument("--vision-model", default=DEFAULT_VISION_MODEL, help="Vision-модель Ollama")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Адрес Ollama API")
    parser.add_argument("--log", action="store_true", help="Подробная диагностика ошибок Ollama")
    parser.add_argument("--export-md", action="store_true", help="Экспортировать чат в Markdown для Obsidian")
    parser.add_argument("--md-chunk-size", type=int, default=500, help="Количество сообщений в одной Markdown-части")
    parser.add_argument("--md-output-dir", type=Path, help="Папка для Markdown (по умолчанию markdown_export)")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--language", default="ru")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--compute-type", default="float16")
    args = parser.parse_args()
    if args.md_chunk_size < 1:
        parser.error("--md-chunk-size должен быть больше нуля")

    groups = find_html_files(args.paths)
    if not groups or not any(groups.values()):
        print("Подходящие HTML-файлы не найдены.")
        raise SystemExit(1)

    total_inserted = 0
    total_missing = 0
    total_descriptions = 0
    total_description_missing = 0
    total_description_failed = 0

    for export_root, html_files in groups.items():
        print(f"\n[EXPORT] {export_root}")
        references: list[MediaReference] = []
        seen: set[Path] = set()
        image_references: list[ImageReference] = []
        image_seen: set[Path] = set()
        for html_path in html_files:
            text = html_path.read_text(encoding="utf-8-sig")
            for reference in collect_references(text, export_root):
                if reference.media_path not in seen:
                    references.append(reference)
                    seen.add(reference.media_path)
            for reference in collect_image_references(text, export_root):
                if reference.image_path not in image_seen:
                    image_references.append(reference)
                    image_seen.add(reference.image_path)

        print(f"[MEDIA] Аудио/видео: {len(references)}; изображения: {len(image_references)}")
        if not args.no_transcribe:
            transcribe_missing(export_root, references, args)
        if args.describe_images:
            _, failed = generate_image_descriptions(export_root, image_references, args)
            total_description_failed += failed

        for html_path in html_files:
            inserted, missing, described, description_missing = update_html(
                html_path, export_root
            )
            total_inserted += inserted
            total_missing += missing
            total_descriptions += described
            if args.describe_images:
                total_description_missing += description_missing
            print(
                f"[HTML] {html_path.name}: расшифровок {inserted}, "
                f"описаний {described}, без текста {missing}, "
                f"без описания {description_missing}"
            )

        if args.export_md:
            md_output_dir = args.md_output_dir.resolve() if args.md_output_dir else None
            export_markdown_chat(
                export_root,
                html_files,
                args.md_chunk_size,
                md_output_dir,
            )

    print(f"\n[OK] Добавлено расшифровок: {total_inserted}")
    print(f"[OK] Добавлено описаний изображений: {total_descriptions}")
    if total_missing:
        print(f"[WARN] Не найдена расшифровка для {total_missing} сообщений")
    if total_description_missing:
        print(f"[WARN] Не найдено описание для {total_description_missing} изображений")
    if total_description_failed:
        print(f"[WARN] Ошибок генерации описаний: {total_description_failed}")


if __name__ == "__main__":
    main()
