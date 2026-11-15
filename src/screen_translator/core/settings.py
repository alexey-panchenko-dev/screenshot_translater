from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _user_data_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "ScreenTranslator"
    return Path.home() / ".screen-translator"


@dataclass(frozen=True, slots=True)
class AppSettings:
    app_name: str = "Screen Translator"
    hotkey_label: str = "Alt+Q"
    minimum_selection_size: int = 8
    compositor_delay_ms: int = 120
    popup_timeout_ms: int = 5_000
    debug_screenshot_directory: Path = field(
        default_factory=lambda: _user_data_root() / "screenshots"
    )
    ocr_model_cache_directory: Path = PROJECT_ROOT / "data" / "models" / "paddlex"
    database_path: Path = field(
        default_factory=lambda: _user_data_root() / "history.db"
    )
    dictionary_path: Path = field(
        default_factory=lambda: _user_data_root() / "dictionary.md"
    )
    icon_path: Path = PROJECT_ROOT / "assets" / "screen_translator.ico"
    log_directory: Path = field(default_factory=lambda: _user_data_root() / "logs")


def migrate_legacy_history(settings: AppSettings) -> int:
    """Copy old install-local history once, without replacing persistent data."""
    migrated = 0
    legacy_directory = PROJECT_ROOT / "data"
    for source, destination in (
        (legacy_directory / "history.db", settings.database_path),
        (legacy_directory / "dictionary.md", settings.dictionary_path),
    ):
        if destination.exists() or not source.is_file():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        migrated += 1
    return migrated
