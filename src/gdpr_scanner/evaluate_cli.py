"""Command-line entry point for labelled text evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gdpr_scanner.detectors import ModelUnavailableError
from gdpr_scanner.evaluation import evaluate_text_cases, load_text_cases


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-evaluate-text",
        description="Evaluate text findings against a labelled JSON Lines dataset.",
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Labelled JSONL dataset")
    parser.add_argument("--json-out", type=Path, help="Optional metrics JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        summary = evaluate_text_cases(load_text_cases(args.dataset))
    except (ValueError, ModelUnavailableError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(f"Cases: {summary['case_count']}")
    print("Matching: exact finding type and normalized value")
    print("Type                         TP   FP   FN  Precision  Recall     F1")
    for finding_type, metrics in summary["per_type"].items():
        print(
            f"{finding_type:<27} {metrics['true_positives']:>3} "
            f"{metrics['false_positives']:>4} {metrics['false_negatives']:>4} "
            f"{metrics['precision']:>10.4f} {metrics['recall']:>7.4f} "
            f"{metrics['f1']:>7.4f}"
        )
    micro = summary["micro"]
    print(
        f"{'MICRO':<27} {micro['true_positives']:>3} {micro['false_positives']:>4} "
        f"{micro['false_negatives']:>4} {micro['precision']:>10.4f} "
        f"{micro['recall']:>7.4f} {micro['f1']:>7.4f}"
    )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Metrics written: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
