import json

from gdpr_scanner import image_pipeline_evaluate_cli


def test_image_pipeline_cli_writes_summary(monkeypatch, tmp_path, capsys) -> None:
    summary = {
        "case_count": 2,
        "ocr": {"character_error_rate": 0.1},
        "findings": {
            "micro": {
                "true_positives": 4,
                "false_positives": 1,
                "false_negatives": 1,
                "precision": 0.8,
                "recall": 0.8,
                "f1": 0.8,
            }
        },
        "timing": {"total_processing_seconds": 1.5},
    }
    monkeypatch.setattr(image_pipeline_evaluate_cli, "load_image_cases", lambda _path: [{}])
    monkeypatch.setattr(
        image_pipeline_evaluate_cli,
        "evaluate_image_pipeline_cases",
        lambda _cases, ocr=None: summary,
    )
    output = tmp_path / "metrics.json"
    assert image_pipeline_evaluate_cli.main(
        ["--dataset", "cases.jsonl", "--json-out", str(output)]
    ) == 0
    assert "Finding TP" in capsys.readouterr().out
    assert json.loads(output.read_text())["case_count"] == 2


def test_image_pipeline_cli_reports_bad_dataset(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        image_pipeline_evaluate_cli,
        "load_image_cases",
        lambda _path: (_ for _ in ()).throw(ValueError("bad manifest")),
    )
    assert image_pipeline_evaluate_cli.main(["--dataset", "bad.jsonl"]) == 2
    assert "bad manifest" in capsys.readouterr().err
