from __future__ import annotations

from datetime import datetime
from pathlib import Path

import mss
import mss.tools

from screen_translator.capture.geometry import ScreenRegion


class ScreenshotService:
    def capture_to_file(self, region: ScreenRegion, output_directory: Path) -> Path:
        output_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = output_directory / f"capture_{timestamp}.png"

        with mss.MSS() as screen_capture:
            image = screen_capture.grab(region.as_mss_monitor())
            mss.tools.to_png(image.rgb, image.size, output=str(output_path))

        return output_path
