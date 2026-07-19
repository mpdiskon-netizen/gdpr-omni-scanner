"""Prepare a small deterministic Enron pilot subset for manual annotation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from email import policy
from email.parser import BytesParser
from pathlib import Path

DEFAULT_LIMIT = 20
DEFAULT_SEED = 3070
MAX_MESSAGE_BYTES = 5 * 1024 * 1024


def _io_path(path: Path, platform_name: str | None = None) -> str:
    """Return a Windows extended path so trailing-period filenames remain addressable."""

    path_text = str(path.absolute())
    if (platform_name or os.name) != "nt" or path_text.startswith("\\\\?\\"):
        return path_text
    if path_text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path_text.lstrip("\\")
    return "\\\\?\\" + path_text


def _plain_text(message) -> str:
    if message.is_multipart():
        parts: list[str] = []
        for part in message.walk():
            if part.get_content_type() != "text/plain":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            try:
                parts.append(part.get_content())
            except (KeyError, UnicodeDecodeError):
                continue
        return "\n".join(parts)
    try:
        return message.get_content()
    except (KeyError, UnicodeDecodeError):
        payload = message.get_payload(decode=True) or b""
        return payload.decode("utf-8", errors="replace")


def _case_from_message(path: Path, corpus_root: Path, max_characters: int) -> dict | None:
    try:
        file_stat = os.stat(_io_path(path))
    except OSError:
        return None
    if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size > MAX_MESSAGE_BYTES:
        return None
    try:
        with open(_io_path(path), "rb") as handle:
            raw = handle.read()
    except OSError:
        return None
    message = BytesParser(policy=policy.default).parsebytes(raw)
    body = _plain_text(message).strip()
    headers = [
        f"Subject: {message.get('Subject', '')}",
        f"From: {message.get('From', '')}",
        f"To: {message.get('To', '')}",
        f"Cc: {message.get('Cc', '')}",
    ]
    text = "\n".join(headers + ["", body]).strip()[:max_characters]
    if not text:
        return None

    relative_path = path.relative_to(corpus_root).as_posix()
    content_hash = hashlib.sha256(raw).hexdigest()
    return {
        "id": f"enron-{content_hash[:12]}",
        "dataset": "CMU Enron Email Dataset, May 7 2015 version",
        "source_ref": relative_path,
        "source_sha256": content_hash,
        "annotation_status": "unlabelled",
        "text": text,
        "expected": [],
    }


def prepare_enron_subset(
    corpus_root: str | Path,
    output_path: str | Path,
    limit: int = DEFAULT_LIMIT,
    seed: int = DEFAULT_SEED,
    max_characters: int = 10_000,
) -> list[dict]:
    """Select reproducible messages and write unlabelled JSON Lines cases."""

    root = Path(corpus_root).resolve()
    if not root.is_dir():
        raise ValueError(f"Enron corpus directory does not exist: {root}")
    if not 1 <= limit <= 200:
        raise ValueError("Pilot limit must be between 1 and 200.")
    if not 500 <= max_characters <= 100_000:
        raise ValueError("Maximum characters must be between 500 and 100,000.")

    ranked_paths: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        try:
            is_file = stat.S_ISREG(os.stat(_io_path(path)).st_mode)
        except OSError:
            is_file = False
        if is_file:
            relative = path.relative_to(root).as_posix()
            rank = hashlib.sha256(f"{seed}:{relative}".encode()).hexdigest()
            ranked_paths.append((rank, path))
    ranked_paths.sort(key=lambda item: item[0])

    cases: list[dict] = []
    for _rank, path in ranked_paths:
        try:
            case = _case_from_message(path, root, max_characters)
        except (OSError, ValueError):
            continue
        if case is not None:
            cases.append(case)
        if len(cases) == limit:
            break
    if len(cases) < limit:
        raise ValueError(f"Only {len(cases)} readable messages were found; {limit} required.")

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )
    return cases


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-prepare-enron",
        description="Select a deterministic local Enron pilot subset for manual annotation.",
    )
    parser.add_argument("--corpus", type=Path, required=True, help="Extracted Enron maildir root")
    parser.add_argument("--out", type=Path, required=True, help="Private unlabelled JSONL output")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Messages to select")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Reproducible selection seed")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        cases = prepare_enron_subset(args.corpus, args.out, args.limit, args.seed)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"Selected {len(cases)} Enron messages.")
    print(f"Unlabelled pilot written: {args.out}")
    print("Next: follow evaluation/enron/ANNOTATION_GUIDE.md before evaluation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
