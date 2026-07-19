"""CLI for the controlled end-to-end image evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gdpr_scanner.easyocr_adapter import EasyOcrUnavailableError, extract_easyocr_text
from gdpr_scanner.image_evaluation import load_image_cases
from gdpr_scanner.image_pipeline_evaluation import evaluate_image_pipeline_cases
from gdpr_scanner.ocr import OcrUnavailableError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-evaluate-image-pipeline",
        description="Evaluate OCR and personal-data findings on labelled images.",
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--engine", choices=("tesseract", "easyocr"), default="tesseract")
    parser.add_argument("--allow-model-download", action="store_true")
    parser.add_argument("--json-out", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    ocr = None
    if args.engine == "easyocr":
        ocr = lambda path: extract_easyocr_text(
            path, allow_model_download=args.allow_model_download
        )
    try:
        summary = evaluate_image_pipeline_cases(load_image_cases(args.dataset), ocr=ocr)
    except (ValueError, OcrUnavailableError, EasyOcrUnavailableError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(f"Cases: {summary['case_count']}")
    print(f"OCR character error rate: {summary['ocr']['character_error_rate']:.4f}")
    findings = summary["findings"]["micro"]
    print("Finding TP  FP  FN  Precision  Recall     F1")
    print(
        f"MICRO   {findings['true_positives']:>3} {findings['false_positives']:>3} "
        f"{findings['false_negatives']:>3} {findings['precision']:>10.4f} "
        f"{findings['recall']:>7.4f} {findings['f1']:>7.4f}"
    )
    print(f"Processing time: {summary['timing']['total_processing_seconds']:.2f} seconds")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Metrics written: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
