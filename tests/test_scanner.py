import csv
import json
from types import SimpleNamespace

import pytest

from gdpr_scanner.scanner import export_csv, export_json, scan_file, scan_text, scan_text_file


class EmptyNlp:
    def __call__(self, text: str):
        return SimpleNamespace(ents=())


def test_scan_text_builds_explainable_result() -> None:
    result = scan_text("Email alex@example.test", nlp=EmptyNlp())
    assert result.schema_version == "1.0"
    assert result.assessment.score == 10
    assert len(result.findings) == 1
    assert "does not determine GDPR compliance" in result.assessment.disclaimer


def test_empty_text_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        scan_text("   ", nlp=EmptyNlp())


def test_excessively_large_text_is_rejected() -> None:
    with pytest.raises(ValueError, match="character limit"):
        scan_text("x" * 1_000_001, nlp=EmptyNlp())


def test_text_file_must_be_txt(tmp_path) -> None:
    path = tmp_path / "input.csv"
    path.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a .txt"):
        scan_text_file(path, nlp=EmptyNlp())


def test_valid_text_file_is_scanned(tmp_path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("Email alex@example.test", encoding="utf-8")
    result = scan_text_file(path, nlp=EmptyNlp())
    assert result.source_name == "input.txt"
    assert result.assessment.score == 10


def test_file_router_rejects_unsupported_extension(tmp_path) -> None:
    path = tmp_path / "input.pdf"
    path.write_bytes(b"not a supported input")
    with pytest.raises(ValueError, match="Supported files"):
        scan_file(path, nlp=EmptyNlp())


def test_file_router_reports_a_missing_file(tmp_path) -> None:
    path = tmp_path / "missing.txt"
    with pytest.raises(ValueError, match="does not exist"):
        scan_file(path, nlp=EmptyNlp())


def test_audio_router_accepts_an_injected_model(tmp_path, monkeypatch) -> None:
    path = tmp_path / "speech.wav"
    path.write_bytes(b"synthetic audio placeholder")

    class FakeWhisper:
        def transcribe(self, *_args, **_kwargs):
            return {"text": "Email alex@example.test"}

    monkeypatch.setattr("gdpr_scanner.audio._require_ffmpeg", lambda: None)
    result = scan_file(path, nlp=EmptyNlp(), whisper_model=FakeWhisper())
    assert result.assessment.score == 10
    assert result.models[0].startswith("whisper:tiny.en:")


def test_json_and_csv_exports(tmp_path) -> None:
    result = scan_text("Email alex@example.test", nlp=EmptyNlp())
    json_path = export_json(result, tmp_path / "result.json")
    csv_path = export_csv(result, tmp_path / "result.csv")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["assessment"]["score"] == 10
    assert payload["findings"][0]["finding_type"] == "EMAIL_ADDRESS"

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["finding_type"] == "EMAIL_ADDRESS"


@pytest.mark.parametrize(
    ("exporter", "filename", "message"),
    [
        (export_json, "result.txt", "must end in .json"),
        (export_csv, "result.txt", "must end in .csv"),
    ],
)
def test_exports_reject_the_wrong_file_extension(
    tmp_path, exporter, filename: str, message: str
) -> None:
    result = scan_text("Email alex@example.test", nlp=EmptyNlp())
    with pytest.raises(ValueError, match=message):
        exporter(result, tmp_path / filename)
