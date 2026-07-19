from pathlib import Path

import pytest

from gdpr_scanner.models import FindingType
from gdpr_scanner.ocr import extract_image_text
from gdpr_scanner.scanner import scan_file

SAMPLE_IMAGE = Path(__file__).parent.parent / "sample_data" / "synthetic_document.png"


def test_invalid_png_is_rejected(tmp_path) -> None:
    path = tmp_path / "invalid.png"
    path.write_bytes(b"this is not an image")
    with pytest.raises(ValueError, match="not a readable"):
        extract_image_text(path)


def test_unsupported_image_extension_is_rejected(tmp_path) -> None:
    path = tmp_path / "document.bmp"
    path.write_bytes(b"not used")
    with pytest.raises(ValueError, match="formats"):
        extract_image_text(path)


@pytest.mark.ocr
def test_real_tesseract_image_pipeline() -> None:
    result = scan_file(SAMPLE_IMAGE)
    finding_types = {finding.finding_type for finding in result.findings}
    assert FindingType.PERSON_NAME in finding_types
    assert FindingType.EMAIL_ADDRESS in finding_types
    assert FindingType.IBAN in finding_types
    assert any(model.startswith("tesseract:eng:") for model in result.models)
    assert "Alex Morgan" in result.text
    assert "alex@example.test" in result.text
