from __future__ import annotations

from datetime import datetime
from pathlib import Path

from screen_translator.storage.models import TranslationRecord


def export_translations(path: Path, records: list[TranslationRecord]) -> None:
    """Write a portable, human- and AI-readable Markdown vocabulary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Screen Translator — экспорт словаря",
        "",
        f"Экспортировано: {datetime.now().astimezone():%d.%m.%Y %H:%M}",
        "",
        "Файл содержит исходный текст, перевод и статус изучения.",
        "Его можно загрузить в ИИ, чтобы создать упражнения по этим словам.",
        "",
    ]
    if not records:
        lines.extend(("_Словарь пока пуст._", ""))
    else:
        for source, target in (("en", "ru"), ("ru", "en")):
            matching = [record for record in records if record.source_language == source]
            if not matching:
                continue
            lines.extend(
                (
                    f"## {source.upper()} → {target.upper()}",
                    "",
                    "| Статус | Исходный текст | Перевод | Добавлено |",
                    "|---|---|---|---|",
                )
            )
            for record in matching:
                status = "Выучено" if record.is_learned else "Изучаю"
                created = record.created_at.astimezone().strftime("%d.%m.%Y %H:%M")
                lines.append(
                    f"| {status} | {_cell(record.original_text)} | "
                    f"{_cell(record.translated_text)} | {created} |"
                )
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")
