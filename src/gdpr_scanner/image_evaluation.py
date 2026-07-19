"""Character-error-rate evaluation for English document-image OCR."""

from __future__ import annotations

import json
import time
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gdpr_scanner.ocr import SUPPORTED_IMAGE_SUFFIXES, extract_image_text


@dataclass(frozen=True, slots=True)
class CharacterErrorCounts:
    edit_distance: int
    reference_characters: int
    hypothesis_characters: int

    @property
    def cer(self) -> float:
        return self.edit_distance / self.reference_characters

    def to_dict(self) -> dict[str, int | float]:
        return {
            "edit_distance": self.edit_distance,
            "reference_characters": self.reference_characters,
            "hypothesis_characters": self.hypothesis_characters,
            "character_error_rate": round(self.cer, 4),
        }


def normalise_characters(text: str) -> str:
    """Apply the documented formatting normalisation used before CER."""

    normalised = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalised.split())


def count_character_errors(reference: str, hypothesis: str) -> CharacterErrorCounts:
    """Calculate Levenshtein edit distance using one row of working memory."""

    reference_text = normalise_characters(reference)
    hypothesis_text = normalise_characters(hypothesis)
    if not reference_text:
        raise ValueError("Reference transcription contains no comparable characters.")

    previous = list(range(len(hypothesis_text) + 1))
    for row, reference_character in enumerate(reference_text, start=1):
        current = [row]
        for column, hypothesis_character in enumerate(hypothesis_text, start=1):
            substitution_cost = int(reference_character != hypothesis_character)
            current.append(
                min(
                    current[column - 1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + substitution_cost,
                )
            )
        previous = current

    return CharacterErrorCounts(
        edit_distance=previous[-1],
        reference_characters=len(reference_text),
        hypothesis_characters=len(hypothesis_text),
    )


def load_image_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load labelled image cases and resolve paths relative to the manifest."""

    dataset_path = Path(path)
    try:
        lines = dataset_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"Image evaluation dataset could not be read: {dataset_path}") from error

    cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on image evaluation line {line_number}.") from error
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError(f"Image evaluation line {line_number} requires a string id.")
        if case["id"] in seen_ids:
            raise ValueError(f"Duplicate image evaluation id: {case['id']}")
        if case.get("annotation_status") != "labelled":
            raise ValueError(
                f"Image evaluation line {line_number} is not labelled; reference text is required."
            )
        if not isinstance(case.get("image_path"), str) or not case["image_path"].strip():
            raise ValueError(f"Image evaluation line {line_number} requires image_path.")
        if not isinstance(case.get("reference_text"), str) or not case["reference_text"].strip():
            raise ValueError(f"Image evaluation line {line_number} requires reference_text.")

        resolved = (dataset_path.parent / case["image_path"]).resolve()
        if resolved.suffix.casefold() not in SUPPORTED_IMAGE_SUFFIXES:
            raise ValueError(f"Unsupported image evaluation file: {resolved}")
        if not resolved.is_file():
            raise ValueError(f"Image evaluation file does not exist: {resolved}")
        seen_ids.add(case["id"])
        cases.append({**case, "_resolved_image_path": resolved})

    if not cases:
        raise ValueError("Image evaluation dataset contains no cases.")
    return cases


def evaluate_image_cases(
    cases: Iterable[dict[str, Any]],
    ocr: Callable[[str | Path], tuple[str, str]] | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """Run OCR and calculate per-document and aggregate character error rate."""

    extractor = ocr or (lambda path: extract_image_text(path, allow_empty=True))
    per_case: list[dict[str, Any]] = []
    models: list[str] = []
    datasets: list[str] = []
    total_edit_distance = 0
    total_reference_characters = 0
    total_hypothesis_characters = 0
    total_processing_seconds = 0.0

    for case in cases:
        started = clock()
        hypothesis, model = extractor(case["_resolved_image_path"])
        elapsed = max(0.0, clock() - started)
        counts = count_character_errors(case["reference_text"], hypothesis)
        if model not in models:
            models.append(model)
        dataset_name = str(case.get("dataset", "unspecified"))
        if dataset_name not in datasets:
            datasets.append(dataset_name)
        total_edit_distance += counts.edit_distance
        total_reference_characters += counts.reference_characters
        total_hypothesis_characters += counts.hypothesis_characters
        total_processing_seconds += elapsed
        per_case.append(
            {
                "id": case["id"],
                "image_path": case["image_path"],
                "document_class": case.get("document_class"),
                **counts.to_dict(),
                "processing_seconds": round(elapsed, 4),
            }
        )

    aggregate_cer = total_edit_distance / total_reference_characters
    return {
        "evaluation_schema_version": "1.0",
        "metric": "character error rate = Levenshtein edit distance / reference characters",
        "normalisation": "Unicode NFKC; case-folding; whitespace collapsed",
        "timing": "Wall-clock OCR time",
        "case_count": len(per_case),
        "datasets": datasets,
        "models": models,
        "aggregate": {
            "edit_distance": total_edit_distance,
            "reference_characters": total_reference_characters,
            "hypothesis_characters": total_hypothesis_characters,
            "character_error_rate": round(aggregate_cer, 4),
            "total_processing_seconds": round(total_processing_seconds, 4),
            "mean_processing_seconds": round(total_processing_seconds / len(per_case), 4),
        },
        "per_case": per_case,
    }
