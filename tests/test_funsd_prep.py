import json
from pathlib import Path

import pytest
from PIL import Image

from gdpr_scanner.funsd_prep import prepare_funsd_subset


def _make_dataset(root: Path, count: int = 22) -> None:
    images = root / "dataset" / "testing_data" / "images"
    annotations = root / "dataset" / "testing_data" / "annotations"
    images.mkdir(parents=True)
    annotations.mkdir(parents=True)
    for index in range(count):
        Image.new("L", (20, 20), color=255).save(images / f"form_{index:02}.png")
        annotation = {
            "form": [
                {"text": f"Answer {index}", "box": [10, 20, 80, 30]},
                {"text": "Question", "box": [5, 5, 60, 15]},
            ]
        }
        (annotations / f"form_{index:02}.json").write_text(
            json.dumps(annotation), encoding="utf-8"
        )


def test_funsd_selection_is_repeatable_and_uses_annotations(tmp_path) -> None:
    source = tmp_path / "source"
    _make_dataset(source)
    first = tmp_path / "first"
    second = tmp_path / "second"

    cases_one = prepare_funsd_subset(source, first, limit=20, seed=3070)
    cases_two = prepare_funsd_subset(source, second, limit=20, seed=3070)

    assert [case["source_ref"] for case in cases_one] == [
        case["source_ref"] for case in cases_two
    ]
    assert len(cases_one) == 20
    assert cases_one[0]["annotation_status"] == "labelled"
    assert cases_one[0]["reference_text"].startswith("Question\nAnswer")
    assert (first / "images" / Path(cases_one[0]["image_path"]).name).is_file()
    provenance = json.loads((first / "funsd_test_provenance.json").read_text())
    assert provenance["criteria"] == {"limit": 20, "seed": 3070}
    assert len(provenance["selected"]) == 20


def test_funsd_limit_must_match_frozen_range(tmp_path) -> None:
    with pytest.raises(ValueError, match="between 20 and 30"):
        prepare_funsd_subset(tmp_path, tmp_path / "out", limit=5)


def test_funsd_existing_sample_requires_force(tmp_path) -> None:
    source = tmp_path / "source"
    _make_dataset(source, count=20)
    output = tmp_path / "output"
    prepare_funsd_subset(source, output, limit=20)
    with pytest.raises(ValueError, match="--force"):
        prepare_funsd_subset(source, output, limit=20)
