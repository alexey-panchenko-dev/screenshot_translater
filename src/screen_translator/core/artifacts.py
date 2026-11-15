from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def remove_capture(path: Path, capture_directory: Path) -> bool:
    """Remove only a generated capture from the configured screenshot directory."""
    try:
        resolved_path = path.resolve()
        resolved_directory = capture_directory.resolve()
        if resolved_path.parent != resolved_directory or not resolved_path.name.startswith(
            "capture_"
        ):
            logger.warning("Refusing to remove non-capture path: %s", path)
            return False
        resolved_path.unlink(missing_ok=True)
        return True
    except OSError:
        logger.exception("Unable to remove screenshot %s", path)
        return False


def remove_stale_captures(capture_directory: Path) -> int:
    if not capture_directory.exists():
        return 0
    removed = 0
    for path in capture_directory.glob("capture_*.png"):
        removed += int(remove_capture(path, capture_directory))
    return removed
