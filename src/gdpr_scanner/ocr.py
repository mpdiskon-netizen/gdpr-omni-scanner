"""Local Tesseract adapter for printed English document images."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000


class OcrUnavailableError(RuntimeError):
    """Raised when the local Tesseract executable or English data is unavailable."""


def _configure_tesseract() -> None:
    if shutil.which("tesseract"):
        return
    if sys.platform == "win32":
        default_executable = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if default_executable.exists():
            pytesseract.pytesseract.tesseract_cmd = str(default_executable)


def _tesseract_version() -> str:
    _configure_tesseract()
    try:
        return str(pytesseract.get_tesseract_version()).splitlines()[0]
    except pytesseract.TesseractNotFoundError as error:
        raise OcrUnavailableError(
            "Tesseract OCR is unavailable. Install Tesseract 5 with English data "
            "and restart PowerShell."
        ) from error


def extract_image_text(
    path: str | Path,
    *,
    allow_empty: bool = False,
) -> tuple[str, str]:
    """Extract printed English text and return it with a model identifier."""

    input_path = Path(path)
    if input_path.suffix.casefold() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError("Supported document-image formats are .png, .jpg and .jpeg.")
    if not input_path.is_file():
        raise ValueError(f"Image file does not exist: {input_path}")
    if input_path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds the 20 MB size limit.")

    try:
        with Image.open(input_path) as image:
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                raise ValueError("Image exceeds the 25-megapixel processing limit.")
            prepared_image = image.convert("RGB")
            _configure_tesseract()
            text = pytesseract.image_to_string(
                prepared_image,
                lang="eng",
                config="--oem 1 --psm 6",
            ).strip()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise ValueError("The file is not a readable PNG or JPEG document image.") from error
    except pytesseract.TesseractNotFoundError as error:
        raise OcrUnavailableError(
            "Tesseract OCR is unavailable. Install Tesseract 5 with English data "
            "and restart PowerShell."
        ) from error
    except pytesseract.TesseractError as error:
        raise OcrUnavailableError(f"Tesseract OCR failed: {error}") from error

    if not text and not allow_empty:
        raise ValueError("Tesseract did not extract any text from the image.")
    return text, f"tesseract:eng:{_tesseract_version()}"
