"""Text scanning, export and input validation."""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from gdpr_scanner.audio import SUPPORTED_AUDIO_SUFFIXES, transcribe_audio
from gdpr_scanner.detectors import detect_all, load_spacy_model
from gdpr_scanner.models import ScanResult
from gdpr_scanner.ocr import SUPPORTED_IMAGE_SUFFIXES, extract_image_text
from gdpr_scanner.scoring import assess_exposure

MAX_TEXT_CHARACTERS = 1_000_000


def scan_text(text: str, source_name: str = "direct-text", nlp: Any | None = None) -> ScanResult:
    if not text or not text.strip():
        raise ValueError("Input text is empty.")
    if len(text) > MAX_TEXT_CHARACTERS:
        raise ValueError(f"Input exceeds the {MAX_TEXT_CHARACTERS:,}-character limit.")

    nlp = nlp or load_spacy_model()
    findings = detect_all(text, nlp)
    metadata = getattr(nlp, "meta", {})
    model_name = metadata.get("name", "en_core_web_sm")
    model_language = metadata.get("lang", "en")
    if not model_name.startswith(f"{model_language}_"):
        model_name = f"{model_language}_{model_name}"
    model_version = metadata.get("version", "unknown")
    return ScanResult(
        schema_version="1.0",
        scan_id=str(uuid4()),
        created_at=datetime.now(UTC).isoformat(),
        source_name=source_name,
        text=text,
        findings=findings,
        assessment=assess_exposure(findings),
        models=(f"spacy:{model_name}:{model_version}", "deterministic-identifiers:v1"),
    )


def scan_text_file(path: str | Path, nlp: Any | None = None) -> ScanResult:
    input_path = Path(path)
    if input_path.suffix.casefold() != ".txt":
        raise ValueError("Text input must be a .txt file.")
    try:
        text = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("The text file must use UTF-8 encoding.") from error
    return scan_text(text, source_name=input_path.name, nlp=nlp)


def scan_image_file(path: str | Path, nlp: Any | None = None) -> ScanResult:
    input_path = Path(path)
    extracted_text, ocr_model = extract_image_text(input_path)
    result = scan_text(extracted_text, source_name=input_path.name, nlp=nlp)
    return replace(result, models=(ocr_model, *result.models))


def scan_audio_file(
    path: str | Path,
    nlp: Any | None = None,
    whisper_model: Any | None = None,
) -> ScanResult:
    input_path = Path(path)
    transcript, audio_model = transcribe_audio(input_path, model=whisper_model)
    result = scan_text(transcript, source_name=input_path.name, nlp=nlp)
    return replace(result, models=(audio_model, *result.models))


def scan_file(
    path: str | Path,
    nlp: Any | None = None,
    whisper_model: Any | None = None,
) -> ScanResult:
    input_path = Path(path)
    if not input_path.is_file():
        raise ValueError(f"Input file does not exist: {input_path}")
    suffix = input_path.suffix.casefold()
    if suffix == ".txt":
        return scan_text_file(input_path, nlp=nlp)
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return scan_image_file(input_path, nlp=nlp)
    if suffix in SUPPORTED_AUDIO_SUFFIXES:
        return scan_audio_file(input_path, nlp=nlp, whisper_model=whisper_model)
    raise ValueError("Supported files are .txt, .png, .jpg, .jpeg, .wav and .mp3.")


def export_json(result: ScanResult, path: str | Path, include_text: bool = True) -> Path:
    output_path = Path(path)
    if output_path.suffix.casefold() != ".json":
        raise ValueError("JSON export path must end in .json.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(include_text), indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def export_csv(result: ScanResult, path: str | Path) -> Path:
    output_path = Path(path)
    if output_path.suffix.casefold() != ".csv":
        raise ValueError("CSV export path must end in .csv.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["finding_type", "value", "normalized_value", "start", "end", "detector", "validated"]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(finding.to_dict() for finding in result.findings)
    return output_path
