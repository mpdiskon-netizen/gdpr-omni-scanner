import json
from pathlib import Path

import pytest

from gdpr_scanner import audio_evaluate_cli
from gdpr_scanner.audio_evaluation import (
    count_word_errors,
    evaluate_audio_cases,
    load_audio_cases,
    normalise_words,
)


def test_word_normalisation_ignores_case_punctuation_and_apostrophes() -> None:
    assert normalise_words("Don't STOP, Alex!") == ["dont", "stop", "alex"]


def test_exact_transcript_has_zero_wer() -> None:
    counts = count_word_errors("Alex lives in Malta.", "alex lives in malta")
    assert counts.to_dict() == {
        "substitutions": 0,
        "deletions": 0,
        "insertions": 0,
        "reference_words": 4,
        "hypothesis_words": 4,
        "word_error_rate": 0.0,
    }


def test_word_error_operations_are_counted() -> None:
    substitution = count_word_errors("one two three", "one four three")
    deletion = count_word_errors("one two three", "one three")
    insertion = count_word_errors("one three", "one two three")
    assert (substitution.substitutions, substitution.deletions, substitution.insertions) == (1, 0, 0)
    assert (deletion.substitutions, deletion.deletions, deletion.insertions) == (0, 1, 0)
    assert (insertion.substitutions, insertion.deletions, insertion.insertions) == (0, 0, 1)


def test_empty_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="no comparable words"):
        count_word_errors("...", "some words")


def test_manifest_paths_are_resolved_relative_to_manifest(tmp_path) -> None:
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"test")
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(
        json.dumps({"id": "case-1", "audio_path": "clip.wav", "reference_text": "test"}) + "\n",
        encoding="utf-8",
    )

    cases = load_audio_cases(manifest)
    assert cases[0]["_resolved_audio_path"] == audio.resolve()


def test_duplicate_manifest_ids_are_rejected(tmp_path) -> None:
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"test")
    row = json.dumps({"id": "same", "audio_path": "clip.wav", "reference_text": "test"})
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(row + "\n" + row + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate"):
        load_audio_cases(manifest)


def test_invalid_manifest_duration_is_rejected(tmp_path) -> None:
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"test")
    manifest = tmp_path / "cases.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "id": "case-1",
                "audio_path": "clip.wav",
                "reference_text": "test",
                "duration_seconds": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid duration"):
        load_audio_cases(manifest)


def test_audio_evaluation_aggregates_cases_without_storing_transcripts(tmp_path) -> None:
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    first.write_bytes(b"test")
    second.write_bytes(b"test")
    cases = [
        {
            "id": "first",
            "audio_path": "first.wav",
            "reference_text": "one two",
            "duration_seconds": 2.0,
            "_resolved_audio_path": first,
        },
        {
            "id": "second",
            "audio_path": "second.wav",
            "reference_text": "three four",
            "duration_seconds": 2.0,
            "_resolved_audio_path": second,
        },
    ]
    hypotheses = {first: "one two", second: "three five"}
    times = iter([0.0, 1.0, 1.0, 2.0])

    summary = evaluate_audio_cases(
        cases,
        transcribe=lambda path: (hypotheses[Path(path)], "whisper:test:cpu"),
        clock=lambda: next(times),
    )

    assert summary["aggregate"]["reference_words"] == 4
    assert summary["aggregate"]["substitutions"] == 1
    assert summary["aggregate"]["word_error_rate"] == 0.25
    assert summary["models"] == ["whisper:test:cpu"]
    assert "reference_text" not in summary["per_case"][0]
    assert summary["aggregate"]["total_processing_seconds"] == 2.0
    assert summary["aggregate"]["total_audio_seconds"] == 4.0
    assert summary["aggregate"]["real_time_factor"] == 0.5
    assert summary["per_case"][0]["processing_seconds"] == 1.0


def test_audio_evaluate_cli_prints_and_writes_metrics(monkeypatch, tmp_path, capsys) -> None:
    summary = {
        "case_count": 1,
        "per_case": [
            {
                "id": "clip-1",
                "reference_words": 4,
                "hypothesis_words": 4,
                "substitutions": 1,
                "deletions": 0,
                "insertions": 0,
                "word_error_rate": 0.25,
            }
        ],
        "aggregate": {
            "reference_words": 4,
            "hypothesis_words": 4,
            "substitutions": 1,
            "deletions": 0,
            "insertions": 0,
            "word_error_rate": 0.25,
            "total_processing_seconds": 1.25,
        },
    }
    monkeypatch.setattr(audio_evaluate_cli, "load_audio_cases", lambda _path: [{}])
    monkeypatch.setattr(
        audio_evaluate_cli,
        "evaluate_audio_cases",
        lambda _cases, model_name: {**summary, "models": [f"whisper:{model_name}:test:cpu"]},
    )
    output_path = tmp_path / "metrics.json"

    assert audio_evaluate_cli.main(
        ["--dataset", str(tmp_path / "cases.jsonl"), "--json-out", str(output_path)]
    ) == 0
    assert "AGGREGATE" in capsys.readouterr().out
    assert json.loads(output_path.read_text(encoding="utf-8"))["case_count"] == 1


def test_audio_evaluate_cli_passes_selected_model(monkeypatch, tmp_path) -> None:
    selected: list[str] = []
    summary = {
        "case_count": 0,
        "per_case": [],
        "aggregate": {
            "reference_words": 0,
            "hypothesis_words": 0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": 0,
            "word_error_rate": 0.0,
            "total_processing_seconds": 0.0,
        },
    }
    monkeypatch.setattr(audio_evaluate_cli, "load_audio_cases", lambda _path: [{}])

    def fake_evaluate(_cases, model_name):
        selected.append(model_name)
        return summary

    monkeypatch.setattr(audio_evaluate_cli, "evaluate_audio_cases", fake_evaluate)

    assert audio_evaluate_cli.main(
        ["--dataset", str(tmp_path / "cases.jsonl"), "--model", "base.en"]
    ) == 0
    assert selected == ["base.en"]


def test_audio_evaluate_cli_reports_invalid_dataset(tmp_path, capsys) -> None:
    assert audio_evaluate_cli.main(["--dataset", str(tmp_path / "missing.jsonl")]) == 2
    assert "could not be read" in capsys.readouterr().err
