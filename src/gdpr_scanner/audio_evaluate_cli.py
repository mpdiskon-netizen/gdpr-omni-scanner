"""Command-line entry point for Whisper word-error-rate evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gdpr_scanner.audio import (
    AudioUnavailableError,
    SUPPORTED_WHISPER_MODELS,
    WHISPER_MODEL_NAME,
)
from gdpr_scanner.audio_evaluation import evaluate_audio_cases, load_audio_cases


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-evaluate-audio",
        description="Evaluate Whisper transcripts against reference text using WER.",
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Audio JSONL manifest")
    parser.add_argument(
        "--model",
        choices=SUPPORTED_WHISPER_MODELS,
        default=WHISPER_MODEL_NAME,
        help=f"Whisper model to evaluate (default: {WHISPER_MODEL_NAME})",
    )
    parser.add_argument("--json-out", type=Path, help="Optional score-only JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        summary = evaluate_audio_cases(
            load_audio_cases(args.dataset), model_name=args.model
        )
    except (ValueError, AudioUnavailableError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(f"Cases: {summary['case_count']}")
    print("Case                         Ref  Hyp    S    D    I     WER")
    for case in summary["per_case"]:
        print(
            f"{case['id']:<28} {case['reference_words']:>3} "
            f"{case['hypothesis_words']:>4} {case['substitutions']:>4} "
            f"{case['deletions']:>4} {case['insertions']:>4} "
            f"{case['word_error_rate']:>7.4f}"
        )
    aggregate = summary["aggregate"]
    print(
        f"{'AGGREGATE':<28} {aggregate['reference_words']:>3} "
        f"{aggregate['hypothesis_words']:>4} {aggregate['substitutions']:>4} "
        f"{aggregate['deletions']:>4} {aggregate['insertions']:>4} "
        f"{aggregate['word_error_rate']:>7.4f}"
    )
    print(f"Processing time: {aggregate['total_processing_seconds']:.2f} seconds")
    if "total_audio_seconds" in aggregate:
        print(f"Audio duration: {aggregate['total_audio_seconds']:.2f} seconds")
        print(f"Real-time factor: {aggregate['real_time_factor']:.4f}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Metrics written: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
