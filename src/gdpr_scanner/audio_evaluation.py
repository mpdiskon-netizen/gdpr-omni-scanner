"""Word-error-rate evaluation for English Whisper transcripts."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gdpr_scanner.audio import WHISPER_MODEL_NAME, transcribe_audio


@dataclass(frozen=True, slots=True)
class WordErrorCounts:
    substitutions: int
    deletions: int
    insertions: int
    reference_words: int
    hypothesis_words: int

    @property
    def errors(self) -> int:
        return self.substitutions + self.deletions + self.insertions

    @property
    def wer(self) -> float:
        return self.errors / self.reference_words if self.reference_words else 0.0

    def to_dict(self) -> dict[str, int | float]:
        return {
            "substitutions": self.substitutions,
            "deletions": self.deletions,
            "insertions": self.insertions,
            "reference_words": self.reference_words,
            "hypothesis_words": self.hypothesis_words,
            "word_error_rate": round(self.wer, 4),
        }


def normalise_words(text: str) -> list[str]:
    """Apply a small, documented English normalisation before WER matching."""

    # Capitalisation and punctuation are formatting differences rather than word errors.
    folded = text.casefold().replace("’", "'").replace("'", "")
    return re.findall(r"[a-z0-9]+", folded)


def count_word_errors(reference: str, hypothesis: str) -> WordErrorCounts:
    """Count substitutions, deletions and insertions using edit distance."""

    reference_words = normalise_words(reference)
    hypothesis_words = normalise_words(hypothesis)
    if not reference_words:
        raise ValueError("Reference transcript contains no comparable words.")

    # Each cell stores total cost plus S, D and I counts for the best alignment.
    rows = len(reference_words) + 1
    columns = len(hypothesis_words) + 1
    table: list[list[tuple[int, int, int, int]]] = [
        [(0, 0, 0, 0) for _ in range(columns)] for _ in range(rows)
    ]
    for row in range(1, rows):
        table[row][0] = (row, 0, row, 0)
    for column in range(1, columns):
        table[0][column] = (column, 0, 0, column)

    for row in range(1, rows):
        for column in range(1, columns):
            if reference_words[row - 1] == hypothesis_words[column - 1]:
                table[row][column] = table[row - 1][column - 1]
                continue

            diagonal = table[row - 1][column - 1]
            above = table[row - 1][column]
            left = table[row][column - 1]
            candidates = (
                (diagonal[0] + 1, diagonal[1] + 1, diagonal[2], diagonal[3]),
                (above[0] + 1, above[1], above[2] + 1, above[3]),
                (left[0] + 1, left[1], left[2], left[3] + 1),
            )
            table[row][column] = min(candidates, key=lambda item: item[0])

    _, substitutions, deletions, insertions = table[-1][-1]
    return WordErrorCounts(
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
        reference_words=len(reference_words),
        hypothesis_words=len(hypothesis_words),
    )


def load_audio_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON Lines manifest and resolve audio paths relative to the manifest."""

    dataset_path = Path(path)
    try:
        lines = dataset_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"Audio evaluation dataset could not be read: {dataset_path}") from error

    cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on audio evaluation line {line_number}.") from error
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError(f"Audio evaluation line {line_number} requires a string id.")
        if case["id"] in seen_ids:
            raise ValueError(f"Duplicate audio evaluation id: {case['id']}")
        if not isinstance(case.get("audio_path"), str) or not case["audio_path"].strip():
            raise ValueError(f"Audio evaluation line {line_number} requires audio_path.")
        if not isinstance(case.get("reference_text"), str) or not case["reference_text"].strip():
            raise ValueError(f"Audio evaluation line {line_number} requires reference_text.")
        duration = case.get("duration_seconds")
        if duration is not None and (not isinstance(duration, (int, float)) or duration <= 0):
            raise ValueError(
                f"Audio evaluation line {line_number} has invalid duration_seconds."
            )

        resolved = (dataset_path.parent / case["audio_path"]).resolve()
        if not resolved.is_file():
            raise ValueError(f"Audio evaluation file does not exist: {resolved}")
        seen_ids.add(case["id"])
        cases.append({**case, "_resolved_audio_path": resolved})

    if not cases:
        raise ValueError("Audio evaluation dataset contains no cases.")
    return cases


def evaluate_audio_cases(
    cases: Iterable[dict[str, Any]],
    transcribe: Callable[[str | Path], tuple[str, str]] | None = None,
    model_name: str = WHISPER_MODEL_NAME,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """Transcribe audio cases and calculate WER plus elapsed processing time."""

    per_case: list[dict[str, Any]] = []
    models: list[str] = []
    total = WordErrorCounts(0, 0, 0, 0, 0)
    total_processing_seconds = 0.0
    total_audio_seconds = 0.0
    durations_complete = True
    transcriber = transcribe or (
        lambda path: transcribe_audio(path, model_name=model_name)
    )

    for case in cases:
        started = clock()
        hypothesis, model = transcriber(case["_resolved_audio_path"])
        elapsed = max(0.0, clock() - started)
        counts = count_word_errors(case["reference_text"], hypothesis)
        duration = case.get("duration_seconds")
        duration_value = float(duration) if isinstance(duration, (int, float)) else None
        if duration_value is None:
            durations_complete = False
        else:
            total_audio_seconds += duration_value
        total_processing_seconds += elapsed
        if model not in models:
            models.append(model)
        result = {
            "id": case["id"],
            "audio_path": case["audio_path"],
            **counts.to_dict(),
            "processing_seconds": round(elapsed, 4),
        }
        if duration_value is not None:
            result["audio_duration_seconds"] = round(duration_value, 4)
            result["real_time_factor"] = round(elapsed / duration_value, 4)
        per_case.append(result)
        total = WordErrorCounts(
            substitutions=total.substitutions + counts.substitutions,
            deletions=total.deletions + counts.deletions,
            insertions=total.insertions + counts.insertions,
            reference_words=total.reference_words + counts.reference_words,
            hypothesis_words=total.hypothesis_words + counts.hypothesis_words,
        )

    aggregate = {
        **total.to_dict(),
        "total_processing_seconds": round(total_processing_seconds, 4),
        "mean_processing_seconds": round(total_processing_seconds / len(per_case), 4),
    }
    if durations_complete:
        aggregate["total_audio_seconds"] = round(total_audio_seconds, 4)
        aggregate["real_time_factor"] = round(
            total_processing_seconds / total_audio_seconds, 4
        )

    return {
        "evaluation_schema_version": "1.1",
        "metric": "word error rate = (substitutions + deletions + insertions) / reference words",
        "normalisation": "English case-folding; punctuation ignored; apostrophes removed",
        "timing": "Wall-clock transcription time; first case includes model loading",
        "case_count": len(per_case),
        "models": models,
        "aggregate": aggregate,
        "per_case": per_case,
    }
