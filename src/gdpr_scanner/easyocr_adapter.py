"""Optional EasyOCR adapter used for the image-model comparison."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from gdpr_scanner.ocr import MAX_IMAGE_BYTES, MAX_IMAGE_PIXELS, SUPPORTED_IMAGE_SUFFIXES

_reader: Any | None = None


class EasyOcrUnavailableError(RuntimeError):
    """Raised when EasyOCR or its local English weights are unavailable."""


def _load_reader(allow_model_download: bool) -> Any:
    global _reader
    if _reader is not None:
        return _reader
    try:
        import easyocr
    except Exception as error:
        raise EasyOcrUnavailableError(
            'EasyOCR is optional. Install it with: python -m pip install -e ".[image-comparison]"'
        ) from error
    try:
        _reader = easyocr.Reader(
            ["en"],
            gpu=False,
            download_enabled=allow_model_download,
            quantize=False,
            verbose=False,
        )
    except Exception as error:
        raise EasyOcrUnavailableError(
            "EasyOCR English weights are unavailable. Run once with "
            "--allow-model-download while online, then repeat offline."
        ) from error
    return _reader


def extract_easyocr_text(
    path: str | Path,
    *,
    allow_model_download: bool = False,
) -> tuple[str, str]:
    """Extract English text with EasyOCR on CPU."""

    input_path = Path(path)
    if input_path.suffix.casefold() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError("Supported document-image formats are .png, .jpg and .jpeg.")
    if not input_path.is_file():
        raise ValueError(f"Image file does not exist: {input_path}")
    if input_path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds the 20 MB size limit.")
    try:
        with Image.open(input_path) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image exceeds the 25-megapixel processing limit.")
            image.verify()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise ValueError("The file is not a readable PNG or JPEG document image.") from error

    reader = _load_reader(allow_model_download)
    try:
        lines = reader.readtext(str(input_path), detail=0, paragraph=False)
    except Exception as error:
        raise EasyOcrUnavailableError(f"EasyOCR failed: {error}") from error
    try:
        package_version = version("easyocr")
    except PackageNotFoundError:
        package_version = "unknown"
    return "\n".join(str(line).strip() for line in lines if str(line).strip()), (
        f"easyocr:en:{package_version}:cpu"
    )
