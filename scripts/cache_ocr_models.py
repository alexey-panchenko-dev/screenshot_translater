"""Download the two OCR models required by the packaged application."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    cache = Path("data/models/paddlex").resolve()
    cache.mkdir(parents=True, exist_ok=True)
    os.environ["PADDLE_PDX_CACHE_HOME"] = str(cache)

    from paddleocr import PaddleOCR

    PaddleOCR(
        device="cpu",
        enable_mkldnn=False,
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="eslav_PP-OCRv5_mobile_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    print(f"OCR models are ready in {cache}")


if __name__ == "__main__":
    main()
