"""End-to-end evaluation for image OCR followed by personal-data detection."""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from gdpr_scanner.evaluation import MetricCounts, normalise_expected
from gdpr_scanner.image_evaluation import count_character_errors
from gdpr_scanner.models import FindingType, ScanResult
from gdpr_scanner.ocr import extract_image_text
from gdpr_scanner.scanner import scan_text


def _metric_dict(counts: Counter[str]) -> dict[str, int | float]:
    return MetricCounts(
        counts["true_positives"],
        counts["false_positives"],
        counts["false_negatives"],
    ).to_dict()


def evaluate_image_pipeline_cases(
    cases: Iterable[dict[str, Any]],
    ocr: Callable[[str | Path], tuple[str, str]] | None = None,
    scan: Callable[[str], ScanResult] = scan_text,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """Measure OCR CER and exact finding accuracy without saving extracted text."""

    extractor = ocr or (lambda path: extract_image_text(path, allow_empty=True))
    totals: Counter[str] = Counter()
    per_type: dict[str, Counter[str]] = {}
    per_case: list[dict[str, Any]] = []
    models: list[str] = []
    total_edits = total_reference = total_hypothesis = 0
    total_seconds = 0.0

    for case in cases:
        if not isinstance(case.get("expected"), list):
            raise ValueError(f"Image case {case.get('id', '<unknown>')} requires expected labels.")
        expected: Counter[tuple[str, str]] = Counter()
        for item in case["expected"]:
            try:
                finding_type = FindingType(item["finding_type"])
                value = item["value"]
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"Image case {case['id']} has an invalid expected label.") from error
            expected[(finding_type.value, normalise_expected(finding_type, value))] += 1

        started = clock()
        hypothesis, ocr_model = extractor(case["_resolved_image_path"])
        result = scan(hypothesis) if hypothesis.strip() else None
        elapsed = max(0.0, clock() - started)
        total_seconds += elapsed
        if ocr_model not in models:
            models.append(ocr_model)
        if result:
            for model in result.models:
                if model not in models:
                    models.append(model)
        predicted = Counter(
            (finding.finding_type.value, finding.normalized_value)
            for finding in (result.findings if result else ())
        )

        case_counts: Counter[str] = Counter()
        for key in set(expected) | set(predicted):
            true_positives = min(expected[key], predicted[key])
            false_positives = max(predicted[key] - expected[key], 0)
            false_negatives = max(expected[key] - predicted[key], 0)
            counts = per_type.setdefault(key[0], Counter())
            for name, amount in (
                ("true_positives", true_positives),
                ("false_positives", false_positives),
                ("false_negatives", false_negatives),
            ):
                counts[name] += amount
                totals[name] += amount
                case_counts[name] += amount

        character_counts = count_character_errors(case["reference_text"], hypothesis)
        total_edits += character_counts.edit_distance
        total_reference += character_counts.reference_characters
        total_hypothesis += character_counts.hypothesis_characters
        per_case.append(
            {
                "id": case["id"],
                "document_class": case.get("document_class"),
                "character_error_rate": round(character_counts.cer, 4),
                **_metric_dict(case_counts),
                "exposure_score": result.assessment.score if result else 0,
                "exposure_band": result.assessment.band if result else "none detected",
                "processing_seconds": round(elapsed, 4),
            }
        )

    if not per_case:
        raise ValueError("Image pipeline evaluation contains no cases.")
    return {
        "evaluation_schema_version": "1.0",
        "case_count": len(per_case),
        "models": models,
        "ocr": {
            "metric": "character error rate",
            "edit_distance": total_edits,
            "reference_characters": total_reference,
            "hypothesis_characters": total_hypothesis,
            "character_error_rate": round(total_edits / total_reference, 4),
        },
        "findings": {
            "matching": "exact finding type and normalized value; occurrence-aware",
            "micro": _metric_dict(totals),
            "per_type": {
                finding_type: _metric_dict(per_type[finding_type])
                for finding_type in sorted(per_type)
            },
        },
        "timing": {
            "total_processing_seconds": round(total_seconds, 4),
            "mean_processing_seconds": round(total_seconds / len(per_case), 4),
        },
        "per_case": per_case,
    }
