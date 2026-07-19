"""Prepare deterministic, roughly one-minute AMI speech composites.

The AMI processed dataset contains short utterance segments. This helper joins
segments from the same meeting, speaker and headset until each output contains
about one minute of speech. The outputs are evaluation inputs, not training data.
"""

from __future__ import annotations

import argparse
from array import array
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys
import wave


DATASET_NAME = "edinburghcstr/ami"
DATASET_CONFIG = "ihm"
DATASET_SPLIT = "test"
SOURCE_URL = "https://groups.inf.ed.ac.uk/ami/corpus/"
PROCESSED_URL = "https://huggingface.co/datasets/edinburghcstr/ami"


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _to_pcm16(samples: object) -> array:
    values = samples.tolist() if hasattr(samples, "tolist") else list(samples)  # type: ignore[arg-type]
    if values and isinstance(values[0], list):
        values = values[0]
    pcm = array("h")
    for sample in values:
        clipped = max(-1.0, min(1.0, float(sample)))
        pcm.append(int(clipped * 32767))
    return pcm


def _write_wav(path: Path, pcm: array, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm.tobytes())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare three roughly one-minute AMI evaluation composites."
    )
    parser.add_argument("--out", type=Path, default=Path("evaluation_private/ami_minute"))
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=60.0)
    parser.add_argument("--force", action="store_true")
    return parser


def _new_group(row: dict[str, object], row_index: int) -> dict[str, object]:
    return {
        "meeting_id": str(row["meeting_id"]),
        "speaker_id": str(row["speaker_id"]),
        "microphone_id": str(row["microphone_id"]),
        "first_source_row_index": row_index,
        "sample_rate": None,
        "pcm": array("h"),
        "reference_parts": [],
        "segments": [],
        "complete": False,
    }


def _append_row(group: dict[str, object], row: dict[str, object], row_index: int) -> None:
    audio = row["audio"]
    if not isinstance(audio, dict) or "array" not in audio or "sampling_rate" not in audio:
        raise ValueError("Unexpected AMI audio format.")
    sample_rate = int(audio["sampling_rate"])
    if group["sample_rate"] is None:
        group["sample_rate"] = sample_rate
    elif group["sample_rate"] != sample_rate:
        raise ValueError("AMI sample rate changed inside one composite.")

    pcm = group["pcm"]
    reference_parts = group["reference_parts"]
    segments = group["segments"]
    assert isinstance(pcm, array)
    assert isinstance(reference_parts, list)
    assert isinstance(segments, list)
    pcm.extend(_to_pcm16(audio["array"]))
    text = str(row["text"]).strip()
    reference_parts.append(text)
    segments.append(
        {
            "source_row_index": row_index,
            "audio_id": str(row["audio_id"]),
            "begin_time_seconds": float(row["begin_time"]),
            "end_time_seconds": float(row["end_time"]),
        }
    )


def _duration(group: dict[str, object]) -> float:
    pcm = group["pcm"]
    sample_rate = group["sample_rate"]
    assert isinstance(pcm, array)
    assert isinstance(sample_rate, int)
    return len(pcm) / sample_rate


def select_composites(
    rows: object,
    limit: int,
    target_seconds: float,
) -> list[dict[str, object]]:
    """Select the first speaker streams and accumulate source-ordered speech."""

    groups: dict[tuple[str, str, str], dict[str, object]] = {}
    for row_index, row in enumerate(rows):  # type: ignore[arg-type]
        text = str(row["text"]).strip()
        if not text:
            continue
        key = (
            str(row["meeting_id"]),
            str(row["speaker_id"]),
            str(row["microphone_id"]),
        )
        if key not in groups:
            if len(groups) == limit:
                continue
            groups[key] = _new_group(row, row_index)
        group = groups[key]
        if group["complete"]:
            continue
        _append_row(group, row, row_index)
        if _duration(group) >= target_seconds:
            group["complete"] = True
            print(
                f"Completed {sum(bool(item['complete']) for item in groups.values())}/{limit}: "
                f"{key[0]} {key[1]} ({_duration(group):.2f}s)"
            )
        if len(groups) == limit and all(bool(item["complete"]) for item in groups.values()):
            break
    return list(groups.values())


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.limit < 1 or args.target_seconds <= 0:
        print("Error: --limit and --target-seconds must be positive.", file=sys.stderr)
        return 2

    manifest_path = args.out / "ami_minute_cases.jsonl"
    provenance_path = args.out / "ami_minute_provenance.json"
    if not args.force and (manifest_path.exists() or provenance_path.exists()):
        print(f"Error: {args.out} already contains a sample; use --force to replace it.", file=sys.stderr)
        return 2

    try:
        from datasets import load_dataset
        import librosa  # noqa: F401
        import soundfile  # noqa: F401
    except ImportError:
        print(
            "Error: install datasets==2.21.0, soundfile==0.12.1 and "
            "librosa==0.10.2.post1 in the AMI helper environment.",
            file=sys.stderr,
        )
        return 2

    print("Streaming the AMI individual-headset test split...")
    rows = load_dataset(DATASET_NAME, DATASET_CONFIG, split=DATASET_SPLIT, streaming=True)
    try:
        groups = select_composites(rows, args.limit, args.target_seconds)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    if len(groups) != args.limit or not all(bool(group["complete"]) for group in groups):
        print("Error: the requested composites could not be completed.", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    selected: list[dict[str, object]] = []
    for index, group in enumerate(groups, start=1):
        identifier = (
            f"AMI_{group['meeting_id']}_{group['speaker_id']}_{group['microphone_id']}_minute"
        )
        filename = f"{index:02d}_{_safe_name(identifier)}.wav"
        clip_path = args.out / "clips" / filename
        pcm = group.pop("pcm")
        sample_rate = group["sample_rate"]
        reference_parts = group.pop("reference_parts")
        assert isinstance(pcm, array)
        assert isinstance(sample_rate, int)
        assert isinstance(reference_parts, list)
        _write_wav(clip_path, pcm, sample_rate)
        duration_seconds = round(len(pcm) / sample_rate, 4)
        manifest.append(
            {
                "id": identifier,
                "audio_path": f"clips/{filename}",
                "reference_text": " ".join(reference_parts),
                "duration_seconds": duration_seconds,
            }
        )
        selected.append(
            {
                "selection_index": index,
                **group,
                "duration_seconds": duration_seconds,
                "segment_count": len(group["segments"]),
                "wav_sha256": _sha256(clip_path),
            }
        )

    manifest_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in manifest),
        encoding="utf-8",
    )
    provenance = {
        "schema_version": "1.0",
        "source_corpus": "AMI Meeting Corpus",
        "source_url": SOURCE_URL,
        "processed_distribution": DATASET_NAME,
        "processed_url": PROCESSED_URL,
        "licence": "CC BY 4.0",
        "configuration": DATASET_CONFIG,
        "split": DATASET_SPLIT,
        "datasets_package_version": version("datasets"),
        "selection_rule": (
            "Source order; first distinct meeting/speaker/headset streams; concatenate "
            "their utterance segments until each reaches the configured speech duration."
        ),
        "important_limitation": (
            "Each output is a same-speaker speech composite, not an uninterrupted "
            "one-minute section of the original meeting."
        ),
        "criteria": {"limit": args.limit, "target_seconds": args.target_seconds},
        "selected": selected,
    }
    provenance_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")
    print(f"Provenance: {provenance_path}")
    print("Keep this directory private because it contains reference transcripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
