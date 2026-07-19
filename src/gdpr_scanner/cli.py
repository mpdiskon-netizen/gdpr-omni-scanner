"""Command-line interface for text, document-image and audio scans."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gdpr_scanner import __version__
from gdpr_scanner.audio import AudioUnavailableError
from gdpr_scanner.detectors import ModelUnavailableError
from gdpr_scanner.models import Finding
from gdpr_scanner.ocr import OcrUnavailableError
from gdpr_scanner.scanner import export_csv, export_json, scan_file, scan_text


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * min(len(value) - 4, 12)}{value[-2:]}"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-scan",
        description="Highlight possible personal-data exposure in local English text, document images or speech.",
        epilog="This tool does not determine GDPR compliance or provide legal advice.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Text to scan")
    source.add_argument("--file", type=Path, help="UTF-8 TXT, PNG/JPG image, or WAV/MP3 audio")
    parser.add_argument("--json-out", type=Path, help="Optional JSON export path")
    parser.add_argument("--csv-out", type=Path, help="Optional findings CSV export path")
    parser.add_argument("--show-values", action="store_true", help="Show unmasked finding values")
    parser.add_argument(
        "--show-extracted-text",
        action="store_true",
        help="Display text supplied directly, extracted by OCR or transcribed from audio",
    )
    return parser


def _finding_line(finding: Finding, show_values: bool) -> str:
    value = finding.value if show_values else _mask(finding.value)
    return f"- {finding.finding_type.value:<22} {value} [{finding.detector}]"


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = scan_text(args.text) if args.text is not None else scan_file(args.file)
    except (
        OSError,
        ValueError,
        ModelUnavailableError,
        OcrUnavailableError,
        AudioUnavailableError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(f"GDPR Omni-Scanner {__version__} - text, image and audio scanner")
    print(f"Source: {result.source_name}")
    print(f"Models: {', '.join(result.models)}")
    if args.show_extracted_text:
        print("Extracted text:")
        print(result.text)
    print(f"Findings: {len(result.findings)}")
    for finding in result.findings:
        print(_finding_line(finding, args.show_values))

    print(f"Exposure indicator: {result.assessment.score}/100 ({result.assessment.band})")
    if result.assessment.contributions:
        print("Breakdown:")
        for item in result.assessment.contributions:
            print(
                f"- {item.finding_type.value}: {item.capped_count} x "
                f"{item.weight} = {item.points}"
            )
    print(result.assessment.disclaimer)

    try:
        if args.json_out:
            print(f"JSON written: {export_json(result, args.json_out)}")
        if args.csv_out:
            print(f"CSV written: {export_csv(result, args.csv_out)}")
    except (OSError, ValueError) as error:
        print(f"Export error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
