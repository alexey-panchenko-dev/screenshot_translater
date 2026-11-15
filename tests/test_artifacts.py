from pathlib import Path

from screen_translator.core.artifacts import remove_capture, remove_stale_captures


def test_removes_only_generated_captures(tmp_path: Path) -> None:
    captures = tmp_path / "screenshots"
    captures.mkdir()
    old_capture = captures / "capture_20260101.png"
    unrelated = captures / "keep.png"
    outside = tmp_path / "capture_outside.png"
    for path in (old_capture, unrelated, outside):
        path.write_bytes(b"png")

    assert remove_stale_captures(captures) == 1
    assert not old_capture.exists()
    assert unrelated.exists()
    assert outside.exists()
    assert not remove_capture(outside, captures)
    assert outside.exists()
