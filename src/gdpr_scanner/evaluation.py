"""Reproducible value-level evaluation for labelled text cases."""

from __future__ import annotations

import ipaddress
import json
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gdpr_scanner.models import FindingType, ScanResult
from gdpr_scanner.scanner import scan_text


@dataclass(frozen=True, slots=True)
class MetricCounts:
    true_positives: int
    false_positives: int
    false_negatives: int

    def to_dict(self) -> dict[str, int | float]:
        precision = _safe_divide(self.true_positives, self.true_positives + self.false_positives)
        recall = _safe_divide(self.true_positives, self.true_positives + self.false_negatives)
        f1 = _safe_divide(2 * precision * recall, precision + recall)
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def normalise_expected(finding_type: FindingType, value: str) -> str:
    """Normalise an annotation in the same way as the matching detector."""
    if finding_type == FindingType.EMAIL_ADDRESS:
        return value.casefold()
    if finding_type == FindingType.IBAN:
        return re.sub(r"[^A-Z0-9]", "", value.upper())
    if finding_type == FindingType.PAYMENT_CARD_NUMBER:
        return "".join(character for character in value if character.isdigit())
    if finding_type == FindingType.PHONE_NUMBER:
        digits = "".join(character for character in value if character.isdigit())
        return ("+" if value.lstrip().startswith("+") else "") + digits
    if finding_type == FindingType.IP_ADDRESS:
        return str(ipaddress.ip_address(value))
    return " ".join(value.split()).casefold()


def load_text_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load and minimally validate JSON Lines text-evaluation cases."""

    dataset_path = Path(path)
    cases: list[dict[str, Any]] = []
    try:
        lines = dataset_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"Evaluation dataset could not be read: {dataset_path}") from error

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on evaluation line {line_number}.") from error
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError(f"Evaluation line {line_number} requires a string id.")
        if not isinstance(case.get("text"), str) or not case["text"].strip():
            raise ValueError(f"Evaluation line {line_number} requires non-empty text.")
        if not isinstance(case.get("expected"), list):
            raise ValueError(f"Evaluation line {line_number} requires an expected list.")
        if case.get("annotation_status", "labelled") != "labelled":
            raise ValueError(
                f"Evaluation line {line_number} is not labelled; complete annotation first."
            )
        for item in case["expected"]:
            if not isinstance(item, dict) or not isinstance(item.get("value"), str):
                raise ValueError(f"Evaluation line {line_number} has an invalid expected item.")
            try:
                FindingType(item.get("finding_type"))
            except ValueError as error:
                raise ValueError(
                    f"Evaluation line {line_number} has an unsupported finding type."
                ) from error
        cases.append(case)
    if not cases:
        raise ValueError("Evaluation dataset contains no cases.")
    return cases


def evaluate_text_cases(
    cases: Iterable[dict[str, Any]],
    scan: Callable[[str], ScanResult] = scan_text,
) -> dict[str, Any]:
    """Calculate micro and per-type exact-value precision, recall and F1."""

    totals: Counter[str] = Counter()
    per_type: dict[str, Counter[str]] = {}
    case_count = 0

    for case in cases:
        case_count += 1
        expected = Counter()
        for item in case["expected"]:
            finding_type = FindingType(item["finding_type"])
            expected[(finding_type.value, normalise_expected(finding_type, item["value"]))] += 1

        result = scan(case["text"])
        predicted = Counter(
            (finding.finding_type.value, finding.normalized_value)
            for finding in result.findings
        )

        keys = set(expected) | set(predicted)
        for key in keys:
            finding_type = key[0]
            true_positives = min(expected[key], predicted[key])
            false_positives = max(predicted[key] - expected[key], 0)
            false_negatives = max(expected[key] - predicted[key], 0)
            counts = per_type.setdefault(finding_type, Counter())
            counts["true_positives"] += true_positives
            counts["false_positives"] += false_positives
            counts["false_negatives"] += false_negatives
            totals["true_positives"] += true_positives
            totals["false_positives"] += false_positives
            totals["false_negatives"] += false_negatives

    def metric_dict(counts: Counter[str]) -> dict[str, int | float]:
        return MetricCounts(
            counts["true_positives"],
            counts["false_positives"],
            counts["false_negatives"],
        ).to_dict()

    return {
        "evaluation_schema_version": "1.0",
        "matching": "exact finding type and normalized value; occurrence-aware",
        "case_count": case_count,
        "micro": metric_dict(totals),
        "per_type": {
            finding_type: metric_dict(per_type[finding_type])
            for finding_type in sorted(per_type)
        },
    }
