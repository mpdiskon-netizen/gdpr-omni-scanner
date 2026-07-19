"""Command-line entry point for document-image OCR evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gdpr_scanner.easyocr_adapter import EasyOcrUnavailableError, extract_easyocr_text
from gdpr_scanner.image_evaluation import evaluate_image_cases, load_image_cases
from gdpr_scanner.ocr import OcrUnavailableError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-evaluate-image",
        description="Evaluate OCR output against reference text using CER.",
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Image JSONL manifest")
    parser.add_argument(
        "--engine", choices=("tesseract", "easyocr"), default="tesseract"
    )
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Allow the first EasyOCR run to fetch its English model weights",
    )
    parser.add_argument("--json-out", type=Path, help="Optional score-only JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        extractor = None
        if args.engine == "easyocr":
            extractor = lambda path: extract_easyocr_text(
                path, allow_model_download=args.allow_model_download
            )
        cases = load_image_cases(args.dataset)
        summary = (
            evaluate_image_cases(cases, ocr=extractor)
            if extractor is not None
            else evaluate_image_cases(cases)
        )
    except (ValueError, OcrUnavailableError, EasyOcrUnavailableError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(f"Cases: {summary['case_count']}")
    print("Case                         Ref   Hyp  Edit     CER   Seconds")
    for case in summary["per_case"]:
        print(
            f"{case['id']:<28} {case['reference_characters']:>5} "
            f"{case['hypothesis_characters']:>5} {case['edit_distance']:>5} "
            f"{case['character_error_rate']:>7.4f} "
            f"{case['processing_seconds']:>9.4f}"
        )
    aggregate = summary["aggregate"]
    print(
        f"{'AGGREGATE':<28} {aggregate['reference_characters']:>5} "
        f"{aggregate['hypothesis_characters']:>5} {aggregate['edit_distance']:>5} "
        f"{aggregate['character_error_rate']:>7.4f} "
        f"{aggregate['total_processing_seconds']:>9.4f}"
    )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Metrics written: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
