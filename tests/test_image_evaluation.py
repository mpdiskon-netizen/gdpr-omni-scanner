import json
from pathlib import Path

import pytest

from gdpr_scanner import image_evaluate_cli
from gdpr_scanner.image_evaluation import (
    count_character_errors,
    evaluate_image_cases,
    load_image_cases,
    normalise_characters,
)


def test_character_normalisation_collapses_formatting() -> None:
    assert normalise_characters("  ALEX\nMorgan  ") == "alex morgan"


def test_exact_ocr_text_has_zero_cer() -> None:
    counts = count_character_errors("Alex Morgan", "alex  Morgan")
    assert counts.to_dict() == {
        "edit_distance": 0,
        "reference_characters": 11,
        "hypothesis_characters": 11,
        "character_error_rate": 0.0,
    }


def test_character_edit_distance_counts_changes() -> None:
    assert count_character_errors("abc", "axc").edit_distance == 1
    assert count_character_errors("abc", "ac").edit_distance == 1
    assert count_character_errors("ac", "abc").edit_distance == 1


def test_empty_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="no comparable characters"):
        count_character_errors(" \n ", "some text")


def test_manifest_paths_are_resolved_and_unlabelled_cases_rejected(tmp_path) -> None:
    image = tmp_path / "form.png"
    image.write_bytes(b"image")
    manifest = tmp_path / "cases.jsonl"
    row = {
        "id": "form-1",
        "image_path": "form.png",
        "reference_text": "reference",
        "annotation_status": "labelled",
    }
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert load_image_cases(manifest)[0]["_resolved_image_path"] == image.resolve()

    row["annotation_status"] = "unlabelled"
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not labelled"):
        load_image_cases(manifest)


def test_duplicate_image_ids_are_rejected(tmp_path) -> None:
    image = tmp_path / "form.png"
    image.write_bytes(b"image")
    row = json.dumps(
        {
            "id": "same",
            "image_path": "form.png",
            "reference_text": "reference",
            "annotation_status": "labelled",
        }
    )
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(row + "\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_image_cases(manifest)


def test_image_evaluation_aggregates_without_storing_transcriptions(tmp_path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"image")
    second.write_bytes(b"image")
    cases = [
        {
            "id": "first",
            "dataset": "test set",
            "image_path": "first.png",
            "reference_text": "abcd",
            "_resolved_image_path": first,
        },
        {
            "id": "second",
            "dataset": "test set",
            "image_path": "second.png",
            "reference_text": "wxyz",
            "_resolved_image_path": second,
        },
    ]
    hypotheses = {first: "abxd", second: "wxyz"}
    times = iter([0.0, 1.0, 1.0, 3.0])
    result = evaluate_image_cases(
        cases,
        ocr=lambda path: (hypotheses[Path(path)], "tesseract:test"),
        clock=lambda: next(times),
    )

    assert result["aggregate"]["edit_distance"] == 1
    assert result["aggregate"]["reference_characters"] == 8
    assert result["aggregate"]["character_error_rate"] == 0.125
    assert result["aggregate"]["total_processing_seconds"] == 3.0
    assert result["models"] == ["tesseract:test"]
    assert "reference_text" not in result["per_case"][0]
    assert "hypothesis_text" not in result["per_case"][0]


def test_image_evaluation_counts_empty_ocr_as_full_error(tmp_path) -> None:
    image = tmp_path / "blank.png"
    image.write_bytes(b"image")
    result = evaluate_image_cases(
        [
            {
                "id": "blank",
                "image_path": "blank.png",
                "reference_text": "visible",
                "_resolved_image_path": image,
            }
        ],
        ocr=lambda _path: ("", "tesseract:test"),
        clock=lambda: 0.0,
    )
    assert result["aggregate"]["character_error_rate"] == 1.0


def test_image_evaluate_cli_writes_metrics(monkeypatch, tmp_path, capsys) -> None:
    summary = {
        "case_count": 1,
        "per_case": [
            {
                "id": "form-1",
                "reference_characters": 10,
                "hypothesis_characters": 9,
                "edit_distance": 1,
                "character_error_rate": 0.1,
                "processing_seconds": 0.2,
            }
        ],
        "aggregate": {
            "reference_characters": 10,
            "hypothesis_characters": 9,
            "edit_distance": 1,
            "character_error_rate": 0.1,
            "total_processing_seconds": 0.2,
        },
    }
    monkeypatch.setattr(image_evaluate_cli, "load_image_cases", lambda _path: [{}])
    monkeypatch.setattr(image_evaluate_cli, "evaluate_image_cases", lambda _cases: summary)
    output = tmp_path / "metrics.json"
    assert image_evaluate_cli.main(
        ["--dataset", "cases.jsonl", "--json-out", str(output)]
    ) == 0
    assert "AGGREGATE" in capsys.readouterr().out
    assert json.loads(output.read_text(encoding="utf-8"))["case_count"] == 1


def test_image_evaluate_cli_reports_invalid_dataset(tmp_path, capsys) -> None:
    assert image_evaluate_cli.main(["--dataset", str(tmp_path / "missing.jsonl")]) == 2
    assert "could not be read" in capsys.readouterr().err
