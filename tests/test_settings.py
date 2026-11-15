from pathlib import Path

from screen_translator.core import settings as settings_module
from screen_translator.core.settings import AppSettings, migrate_legacy_history


def test_app_settings_store_history_in_local_app_data(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    settings = AppSettings()

    assert settings.database_path == tmp_path / "ScreenTranslator" / "history.db"
    assert settings.dictionary_path == tmp_path / "ScreenTranslator" / "dictionary.md"


def test_migrate_legacy_history_does_not_replace_existing_file(
    monkeypatch, tmp_path: Path
) -> None:
    project_root = tmp_path / "install"
    legacy = project_root / "data"
    legacy.mkdir(parents=True)
    (legacy / "history.db").write_text("legacy", encoding="utf-8")
    destination = tmp_path / "persistent" / "history.db"
    destination.parent.mkdir()
    destination.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(settings_module, "PROJECT_ROOT", project_root)
    settings = AppSettings(database_path=destination)

    assert migrate_legacy_history(settings) == 0
    assert destination.read_text(encoding="utf-8") == "keep"
