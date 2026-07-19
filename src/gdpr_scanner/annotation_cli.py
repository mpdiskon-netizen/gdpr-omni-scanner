"""Private local annotation assistant for the Enron evaluation subset."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gdpr_scanner.models import FindingType

SUPPORTED_TYPES = tuple(finding_type.value for finding_type in FindingType)


def _load_cases(path: Path) -> list[dict[str, Any]]:
    try:
        cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Annotation dataset could not be read: {path}") from error
    if not cases:
        raise ValueError("Annotation dataset contains no cases.")
    return cases


def _save_cases(path: Path, cases: list[dict[str, Any]]) -> None:
    backup = path.with_name(path.name + ".original.bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _show_case(case: dict[str, Any], index: int, total: int, output: Callable[[str], None]) -> None:
    output(f"Case {index + 1}/{total}: {case['id']}")
    output(f"Source reference: {case.get('source_ref', 'unknown')}")
    output(f"Status: {case.get('annotation_status', 'unlabelled')}")
    output("--- PRIVATE EMAIL TEXT: DO NOT SCREENSHOT ---")
    output(case["text"])
    output("--- END PRIVATE EMAIL TEXT ---")
    if case["expected"]:
        output("Current labels:")
        for label_index, item in enumerate(case["expected"], start=1):
            output(f"  {label_index}. {item['finding_type']}: {item['value']}")
    else:
        output("Current labels: none")


def _add_label(case: dict[str, Any], finding_type: str, value: str) -> bool:
    """Add one occurrence when the exact value exists and is not already fully labelled."""

    if not value or value not in case["text"]:
        return False
    matching_labels = sum(
        1
        for item in case["expected"]
        if item["finding_type"] == finding_type and item["value"] == value
    )
    if matching_labels >= case["text"].count(value):
        return False
    case["expected"].append({"finding_type": finding_type, "value": value})
    return True


def _accept_suggestion(case: dict[str, Any], finding_type: str, value: str, count: int) -> int:
    added = 0
    for _ in range(count):
        if _add_label(case, finding_type, value):
            added += 1
    return added


def _assisted_review(
    case: dict[str, Any],
    cases: list[dict[str, Any]],
    path: Path,
    input_fn: Callable[[str], str],
    output: Callable[[str], None],
    scan: Callable[[str], Any],
) -> bool:
    """Review grouped scanner suggestions, then explicitly check for missed values."""

    output("Running the local scanner to create review suggestions...")
    result = scan(case["text"])
    grouped: dict[str, Counter[str]] = {finding_type: Counter() for finding_type in SUPPORTED_TYPES}
    for finding in result.findings:
        grouped[finding.finding_type.value][finding.value] += 1

    output("Suggestions are not ground truth. Reject mistakes and add missed values.")
    for finding_type in SUPPORTED_TYPES:
        suggestions = grouped[finding_type]
        output(f"\n{finding_type}")
        if suggestions:
            for suggestion_index, (value, count) in enumerate(suggestions.items(), start=1):
                suffix = f" (x{count})" if count > 1 else ""
                output(f"  {suggestion_index}. {value}{suffix}")
            while True:
                decision = input_fn(
                    "Suggestions [a=accept all, r=review each, n=reject all, q=quit]: "
                ).strip().casefold()
                if decision == "a":
                    for value, count in suggestions.items():
                        _accept_suggestion(case, finding_type, value, count)
                    _save_cases(path, cases)
                    break
                if decision == "r":
                    for value, count in suggestions.items():
                        answer = input_fn(f"Accept {value!r} x{count}? [y/n/q]: ").strip().casefold()
                        if answer == "q":
                            _save_cases(path, cases)
                            return False
                        if answer == "y":
                            _accept_suggestion(case, finding_type, value, count)
                    _save_cases(path, cases)
                    break
                if decision == "n":
                    break
                if decision == "q":
                    _save_cases(path, cases)
                    return False
                output("Choose a, r, n or q.")
        else:
            output("  Scanner suggested none.")

        output("Check the email for values the scanner missed.")
        while True:
            missed = input_fn("Missed exact value [Enter=none, q=quit]: ").strip()
            if not missed:
                break
            if missed.casefold() == "q":
                _save_cases(path, cases)
                return False
            if _add_label(case, finding_type, missed):
                _save_cases(path, cases)
                output("Missed value added.")
            else:
                output("Value is absent or every exact occurrence is already labelled.")

    while True:
        decision = input_fn("Mark this case fully reviewed? [y/n/q]: ").strip().casefold()
        if decision == "y":
            case["annotation_status"] = "labelled"
            case["annotation_method"] = "model_assisted_human_review"
            case["annotation_models"] = list(getattr(result, "models", ()))
            _save_cases(path, cases)
            output(f"Case marked labelled with {len(case['expected'])} labels.")
            return True
        if decision == "n":
            _save_cases(path, cases)
            output("Case remains unlabelled; saved progress is retained.")
            return True
        if decision == "q":
            _save_cases(path, cases)
            return False
        output("Choose y, n or q.")


def annotate_file(
    dataset_path: str | Path,
    case_number: int | None = None,
    assisted: bool = False,
    input_fn: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    scan: Callable[[str], Any] | None = None,
) -> int:
    """Interactively annotate one selected case or successive unlabelled cases."""

    path = Path(dataset_path)
    cases = _load_cases(path)
    if case_number is not None and not 1 <= case_number <= len(cases):
        raise ValueError(f"Case number must be between 1 and {len(cases)}.")

    output("This command displays private Enron email text locally.")
    output("Do not screenshot, copy into the report, or send the text to an external service.")
    selected_indices = (
        [case_number - 1]
        if case_number is not None
        else [
            index
            for index, case in enumerate(cases)
            if case.get("annotation_status") != "labelled"
        ]
    )
    if not selected_indices:
        output("All cases are already labelled.")
        return 0

    for index in selected_indices:
        case = cases[index]
        if assisted:
            if scan is None:
                from gdpr_scanner.scanner import scan_text

                scan = scan_text
            _show_case(case, index, len(cases), output)
            if not _assisted_review(case, cases, path, input_fn, output, scan):
                output("Annotation stopped; saved progress is retained.")
                return 0
            if case_number is not None:
                break
            continue
        while True:
            _show_case(case, index, len(cases), output)
            command = input_fn("Command [a=add, r=remove, d=done, s=skip, q=quit]: ").strip().casefold()
            if command == "a":
                output("Supported types: " + ", ".join(SUPPORTED_TYPES))
                finding_type = input_fn("Finding type: ").strip().upper()
                if finding_type not in SUPPORTED_TYPES:
                    output("Unsupported finding type; nothing saved.")
                    continue
                value = input_fn("Exact value copied from the email: ").strip()
                if not value or value not in case["text"]:
                    output("That exact value does not occur in the email; nothing saved.")
                    continue
                if not _add_label(case, finding_type, value):
                    output("Every exact occurrence is already labelled; nothing saved.")
                    continue
                _save_cases(path, cases)
                output("Label saved.")
            elif command == "r":
                try:
                    label_number = int(input_fn("Label number to remove: "))
                    if not 1 <= label_number <= len(case["expected"]):
                        raise IndexError
                    case["expected"].pop(label_number - 1)
                except (ValueError, IndexError):
                    output("Invalid label number; nothing removed.")
                    continue
                _save_cases(path, cases)
                output("Label removed.")
            elif command == "d":
                case["annotation_status"] = "labelled"
                _save_cases(path, cases)
                output(f"Case {index + 1} marked labelled with {len(case['expected'])} labels.")
                break
            elif command == "s":
                output("Case left unlabelled.")
                break
            elif command == "q":
                output("Annotation stopped; saved progress is retained.")
                return 0
            else:
                output("Unknown command.")
        if case_number is not None:
            break
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-annotate-enron",
        description="Annotate private Enron cases locally without editing JSON manually.",
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Private Enron JSONL file")
    parser.add_argument("--case", type=int, help="One-based case number; omit for all unlabelled cases")
    parser.add_argument(
        "--assisted",
        action="store_true",
        help="Review scanner suggestions by type, then add any missed values",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return annotate_file(args.dataset, args.case, assisted=args.assisted)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
