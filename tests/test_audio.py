from pathlib import Path

import pytest

from gdpr_scanner.audio import load_whisper_model, transcribe_audio
from gdpr_scanner.models import FindingType
from gdpr_scanner.scanner import scan_file

SAMPLE_DATA = Path(__file__).parent.parent / "sample_data"


def test_unsupported_audio_extension_is_rejected(tmp_path) -> None:
    path = tmp_path / "recording.flac"
    path.write_bytes(b"not used")
    with pytest.raises(ValueError, match="audio formats"):
        transcribe_audio(path)


def test_unsupported_whisper_model_is_rejected() -> None:
    with pytest.raises(ValueError, match="Supported Whisper models"):
        load_whisper_model("large")


@pytest.mark.audio
@pytest.mark.parametrize("filename", ["synthetic_speech.wav", "synthetic_speech.mp3"])
def test_real_whisper_audio_pipeline(filename: str) -> None:
    result = scan_file(SAMPLE_DATA / filename)
    finding_types = {finding.finding_type for finding in result.findings}
    assert FindingType.PERSON_NAME in finding_types
    assert FindingType.LOCATION_REFERENCE in finding_types
    assert any(model.startswith("whisper:tiny.en:") for model in result.models)
    assert "Alex Morgan" in result.text
    assert "Malta" in result.text
