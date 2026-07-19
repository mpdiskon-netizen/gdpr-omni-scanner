from types import SimpleNamespace

import json

from gdpr_scanner import cli
from gdpr_scanner.detectors import ModelUnavailableError
from gdpr_scanner.scanner import scan_text


class EmptyNlp:
    def __call__(self, text: str):
        return SimpleNamespace(ents=())


def test_cli_prints_masked_result(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "scan_text", lambda text: scan_text(text, nlp=EmptyNlp()))
    exit_code = cli.main(["--text", "Email alex@example.test"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Exposure indicator: 10/100" in output
    assert "alex@example.test" not in output
    assert "does not determine GDPR compliance" in output


def test_cli_reports_missing_model(monkeypatch, capsys) -> None:
    def unavailable(_text: str):
        raise ModelUnavailableError("model missing")

    monkeypatch.setattr(cli, "scan_text", unavailable)
    assert cli.main(["--text", "hello"]) == 2
    assert "model missing" in capsys.readouterr().err


def test_cli_can_show_extracted_text(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "scan_text", lambda text: scan_text(text, nlp=EmptyNlp()))
    exit_code = cli.main(
        ["--text", "Email alex@example.test", "--show-extracted-text"]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Extracted text:" in output
    assert "Email alex@example.test" in output


def test_cli_writes_a_json_export(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(cli, "scan_text", lambda text: scan_text(text, nlp=EmptyNlp()))
    output_path = tmp_path / "scan.json"

    exit_code = cli.main(
        ["--text", "Email alex@example.test", "--json-out", str(output_path)]
    )

    assert exit_code == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["assessment"]["score"] == 10
    assert "JSON written:" in capsys.readouterr().out


def test_cli_reports_an_invalid_export_extension(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(cli, "scan_text", lambda text: scan_text(text, nlp=EmptyNlp()))

    exit_code = cli.main(
        ["--text", "Email alex@example.test", "--json-out", str(tmp_path / "scan.txt")]
    )

    assert exit_code == 2
    assert "Export error:" in capsys.readouterr().err
