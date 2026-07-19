from gdpr_scanner import evaluate_cli


def _summary() -> dict:
    metrics = {
        "true_positives": 1,
        "false_positives": 0,
        "false_negatives": 0,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
    }
    return {
        "case_count": 1,
        "per_type": {"EMAIL_ADDRESS": metrics},
        "micro": metrics,
    }


def test_evaluation_cli_prints_and_exports_metrics(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(evaluate_cli, "load_text_cases", lambda _path: [{}])
    monkeypatch.setattr(evaluate_cli, "evaluate_text_cases", lambda _cases: _summary())
    output_path = tmp_path / "metrics.json"

    exit_code = evaluate_cli.main(
        ["--dataset", "cases.jsonl", "--json-out", str(output_path)]
    )

    assert exit_code == 0
    assert "MICRO" in capsys.readouterr().out
    assert '"f1": 1.0' in output_path.read_text(encoding="utf-8")


def test_evaluation_cli_reports_invalid_dataset(monkeypatch, capsys) -> None:
    def invalid(_path):
        raise ValueError("invalid dataset")

    monkeypatch.setattr(evaluate_cli, "load_text_cases", invalid)
    assert evaluate_cli.main(["--dataset", "bad.jsonl"]) == 2
    assert "invalid dataset" in capsys.readouterr().err
