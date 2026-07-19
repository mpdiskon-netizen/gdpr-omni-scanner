from types import SimpleNamespace

import pytest

from gdpr_scanner.image_pipeline_evaluation import evaluate_image_pipeline_cases
from gdpr_scanner.models import Finding, FindingType


def _scan(text: str):
    findings = ()
    if "alex@example.test" in text:
        findings = (
            Finding(
                FindingType.EMAIL_ADDRESS,
                "alex@example.test",
                "alex@example.test",
                0,
                18,
                "test",
                True,
            ),
        )
    return SimpleNamespace(
        findings=findings,
        models=("spacy:test", "deterministic-identifiers:v1"),
        assessment=SimpleNamespace(score=10, band="low"),
    )


def test_image_pipeline_combines_cer_and_finding_metrics(tmp_path) -> None:
    image = tmp_path / "badge.png"
    image.write_bytes(b"image")
    case = {
        "id": "badge",
        "document_class": "employee_badge",
        "reference_text": "alex@example.test",
        "expected": [{"finding_type": "EMAIL_ADDRESS", "value": "alex@example.test"}],
        "_resolved_image_path": image,
    }
    times = iter((0.0, 0.5))
    result = evaluate_image_pipeline_cases(
        [case],
        ocr=lambda _path: ("alex@example.test", "tesseract:test"),
        scan=_scan,
        clock=lambda: next(times),
    )
    assert result["ocr"]["character_error_rate"] == 0.0
    assert result["findings"]["micro"]["f1"] == 1.0
    assert result["per_case"][0]["exposure_score"] == 10
    assert "reference_text" not in result["per_case"][0]


def test_image_pipeline_counts_empty_ocr_as_missed_label(tmp_path) -> None:
    image = tmp_path / "note.png"
    image.write_bytes(b"image")
    case = {
        "id": "note",
        "reference_text": "alex@example.test",
        "expected": [{"finding_type": "EMAIL_ADDRESS", "value": "alex@example.test"}],
        "_resolved_image_path": image,
    }
    result = evaluate_image_pipeline_cases(
        [case], ocr=lambda _path: ("", "ocr:test"), scan=_scan, clock=lambda: 0.0
    )
    assert result["findings"]["micro"]["false_negatives"] == 1
    assert result["ocr"]["character_error_rate"] == 1.0


def test_image_pipeline_requires_expected_labels(tmp_path) -> None:
    with pytest.raises(ValueError, match="requires expected labels"):
        evaluate_image_pipeline_cases(
            [{"id": "bad", "reference_text": "text", "_resolved_image_path": tmp_path}],
            ocr=lambda _path: ("text", "ocr:test"),
        )
