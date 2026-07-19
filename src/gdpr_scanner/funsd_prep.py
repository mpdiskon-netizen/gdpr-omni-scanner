"""Prepare a deterministic private FUNSD test subset for OCR evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

DEFAULT_LIMIT = 25
DEFAULT_SEED = 3070
MINIMUM_LIMIT = 20
MAXIMUM_LIMIT = 30
SOURCE_URL = "https://guillaumejaume.github.io/FUNSD/"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _find_test_directories(root: Path) -> tuple[Path, Path]:
    candidates = [root / "testing_data", root / "dataset" / "testing_data"]
    candidates.extend(root.rglob("testing_data"))
    for candidate in candidates:
        images = candidate / "images"
        annotations = candidate / "annotations"
        if images.is_dir() and annotations.is_dir():
            return images, annotations
    raise ValueError(
        "FUNSD testing_data/images and testing_data/annotations directories were not found."
    )


def _reference_text(annotation_path: Path) -> str:
    try:
        annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"FUNSD annotation could not be read: {annotation_path}") from error
    form = annotation.get("form")
    if not isinstance(form, list):
        raise ValueError(f"FUNSD annotation has no form list: {annotation_path}")

    entities: list[tuple[int, int, str]] = []
    for entity in form:
        if not isinstance(entity, dict):
            continue
        text = str(entity.get("text", "")).strip()
        box = entity.get("box")
        if not text or not isinstance(box, list) or len(box) != 4:
            continue
        entities.append((int(box[1]), int(box[0]), text))
    entities.sort(key=lambda item: (item[0], item[1]))
    reference = "\n".join(item[2] for item in entities).strip()
    if not reference:
        raise ValueError(f"FUNSD annotation contains no reference text: {annotation_path}")
    return reference


def prepare_funsd_subset(
    dataset_root: str | Path,
    output_directory: str | Path,
    limit: int = DEFAULT_LIMIT,
    seed: int = DEFAULT_SEED,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Select 20-30 traceable test forms and write a private JSONL manifest."""

    if not MINIMUM_LIMIT <= limit <= MAXIMUM_LIMIT:
        raise ValueError(f"Image evaluation limit must be between {MINIMUM_LIMIT} and {MAXIMUM_LIMIT}.")
    root = Path(dataset_root).resolve()
    if not root.is_dir():
        raise ValueError(f"FUNSD dataset directory does not exist: {root}")
    images_directory, annotations_directory = _find_test_directories(root)

    candidates: list[tuple[str, Path, Path]] = []
    for image_path in images_directory.glob("*.png"):
        annotation_path = annotations_directory / f"{image_path.stem}.json"
        if annotation_path.is_file():
            relative = image_path.relative_to(root).as_posix()
            rank = hashlib.sha256(f"{seed}:{relative}".encode()).hexdigest()
            candidates.append((rank, image_path, annotation_path))
    candidates.sort(key=lambda item: item[0])
    if len(candidates) < limit:
        raise ValueError(f"Only {len(candidates)} matched FUNSD test forms were found; {limit} required.")

    destination = Path(output_directory)
    manifest_path = destination / "funsd_test_cases.jsonl"
    provenance_path = destination / "funsd_test_provenance.json"
    if not force and (manifest_path.exists() or provenance_path.exists()):
        raise ValueError(f"{destination} already contains a sample; use --force to replace it.")
    images_output = destination / "images"
    images_output.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    for _rank, image_path, annotation_path in candidates[:limit]:
        image_hash = _sha256(image_path)
        annotation_hash = _sha256(annotation_path)
        output_name = f"{image_path.stem}.png"
        copied_image = images_output / output_name
        shutil.copy2(image_path, copied_image)
        case_id = f"funsd-{image_hash[:12]}"
        source_ref = image_path.relative_to(root).as_posix()
        cases.append(
            {
                "id": case_id,
                "dataset": "FUNSD 1.0 test split",
                "document_class": "form",
                "source_ref": source_ref,
                "source_sha256": image_hash,
                "annotation_sha256": annotation_hash,
                "annotation_status": "labelled",
                "annotation_method": "FUNSD supplied entity text ordered by box position",
                "image_path": f"images/{output_name}",
                "reference_text": _reference_text(annotation_path),
            }
        )
        selected.append(
            {
                "id": case_id,
                "source_ref": source_ref,
                "source_sha256": image_hash,
                "annotation_sha256": annotation_hash,
            }
        )

    manifest_path.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )
    provenance = {
        "schema_version": "1.0",
        "source_dataset": "FUNSD 1.0",
        "source_url": SOURCE_URL,
        "source_split": "test",
        "relationship_to_rvl_cdip": (
            "FUNSD forms were selected and annotated from the RVL-CDIP form collection."
        ),
        "selection_rule": (
            "Match test PNGs to supplied annotations, rank source paths by SHA-256 of "
            "seed:path, and take the first requested cases."
        ),
        "reference_rule": (
            "Use supplied FUNSD entity text ordered by top then left box coordinate."
        ),
        "criteria": {"limit": limit, "seed": seed},
        "selected": selected,
    }
    temporary = provenance_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    os.replace(temporary, provenance_path)
    return cases


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdpr-prepare-funsd",
        description="Prepare a deterministic 20-30 document FUNSD OCR evaluation subset.",
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Extracted FUNSD root")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evaluation_private/funsd"),
        help="Private output directory",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        cases = prepare_funsd_subset(
            args.dataset, args.out, args.limit, args.seed, args.force
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"Selected {len(cases)} FUNSD test documents.")
    print(f"Private manifest: {args.out / 'funsd_test_cases.jsonl'}")
    print(f"Provenance: {args.out / 'funsd_test_provenance.json'}")
    print("Next: run gdpr-evaluate-image with the private manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
