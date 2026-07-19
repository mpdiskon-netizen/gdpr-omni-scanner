import json
from types import SimpleNamespace

import pytest

from gdpr_scanner.evaluation import evaluate_text_cases, load_text_cases
from gdpr_scanner.scanner import scan_text


class EmptyNlp:
    def __call__(self, text: str):
        return SimpleNamespace(ents=())


def _deterministic_scan(text: str):
    return scan_text(text, nlp=EmptyNlp())


def test_text_metrics_count_true_false_and_missed_findings() -> None:
    cases = [
        {
            "id": "mixed",
            "text": "Email alex@example.test and IP 192.0.2.1",
            "expected": [
                {"finding_type": "EMAIL_ADDRESS", "value": "alex@example.test"},
                {"finding_type": "PERSON_NAME", "value": "Alex Morgan"},
            ],
        }
    ]
    result = evaluate_text_cases(cases, scan=_deterministic_scan)
    assert result["micro"]["true_positives"] == 1
    assert result["micro"]["false_positives"] == 1
    assert result["micro"]["false_negatives"] == 1
    assert result["micro"]["f1"] == 0.5


def test_expected_phone_is_normalized_like_scanner_output() -> None:
    cases = [
        {
            "id": "phone",
            "text": "Call +356 2123 4567",
            "expected": [{"finding_type": "PHONE_NUMBER", "value": "+356 2123 4567"}],
        }
    ]
    assert evaluate_text_cases(cases, scan=_deterministic_scan)["micro"]["f1"] == 1.0


def test_load_text_cases_reads_json_lines(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps({"id": "negative", "text": "Nothing to report.", "expected": []}),
        encoding="utf-8",
    )
    assert load_text_cases(path)[0]["id"] == "negative"


def test_load_text_cases_rejects_unsupported_type(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "invalid",
                "text": "Example",
                "expected": [{"finding_type": "UNKNOWN", "value": "Example"}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported finding type"):
        load_text_cases(path)
