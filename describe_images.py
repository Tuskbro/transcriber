from __future__ import annotations

import argparse
import json
from pathlib import Path

from image_describer import (
    DEFAULT_OLLAMA_URL,
    DEFAULT_VISION_MODEL,
    ImageDescriptionError,
    describe_image,
)


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def is_source_image(path: Path) -> bool:
    """Exclude Telegram previews and accept only original WebP stickers."""
    if not path.is_file() or "_thumb" in path.name.lower():
        return False
    if path.parent.name.lower() == "stickers":
        return path.suffix.lower() == ".webp"
    return path.suffix.lower() in IMAGE_EXTENSIONS


def find_images(paths: list[Path]) -> list[Path]:
    images: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved.is_file() and is_source_image(resolved):
            images.append(resolved)
        elif resolved.is_dir():
            images.extend(
                item for item in resolved.rglob("*")
                if is_source_image(item)
            )
        else:
            print(f"[WARN] Изображение или папка не найдены: {path}")
    return list(dict.fromkeys(images))


def output_paths(image: Path, output_dir: Path | None) -> tuple[Path, Path]:
    destination = output_dir or image.parent
    base = destination / f"{image.stem}.description"
    return base.with_suffix(".description.json"), base.with_suffix(".description.md")


def save_description(
    image: Path,
    description: str,
    model: str,
    output_dir: Path | None,
) -> tuple[Path, Path]:
    json_path, markdown_path = output_paths(image, output_dir)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {"source": image.name, "model": model, "description": description},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        f"# Описание {image.name}\n\n{description}\n",
        encoding="utf-8",
    )
    return json_path, markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Локальное описание изображений через Ollama")
    parser.add_argument("paths", nargs="+", type=Path, help="Изображения или папки")
    parser.add_argument("--vision-model", default=DEFAULT_VISION_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--log", action="store_true", help="Подробная диагностика Ollama")
    args = parser.parse_args()

    images = find_images(args.paths)
    if not images:
        print("Подходящие изображения не найдены.")
        raise SystemExit(1)

    output_dir = args.output_dir.resolve() if args.output_dir else None
    print(f"[VISION] Модель: {args.vision_model}; изображений: {len(images)}")
    failed = 0

    for index, image in enumerate(images, start=1):
        json_path, markdown_path = output_paths(image, output_dir)
        if json_path.exists() and markdown_path.exists() and not args.force:
            print(f"[SKIP] Уже описано: {image.name}")
            continue

        print(f"[IMAGE {index}/{len(images)}] {image}")
        try:
            description = describe_image(
                image,
                model=args.vision_model,
                ollama_url=args.ollama_url,
                log=args.log,
            )
            json_path, markdown_path = save_description(
                image, description, args.vision_model, output_dir
            )
            print(f"[DESCRIPTION] {description}")
            print(f"[OK] {json_path}")
            print(f"[OK] {markdown_path}")
        except (OSError, ImageDescriptionError) as exc:
            print(f"[ERROR] {image.name}: {exc}")
            failed += 1

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
