import json
from email.message import EmailMessage

import pytest

from gdpr_scanner.enron_prep import _io_path, main, prepare_enron_subset
from gdpr_scanner.evaluation import load_text_cases


def _write_message(path, subject: str, sender: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = "recipient@example.test"
    message.set_content(f"Please contact {sender} about {subject}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(message.as_bytes())


def test_enron_selection_is_reproducible_and_traceable(tmp_path) -> None:
    corpus = tmp_path / "maildir"
    for index in range(5):
        _write_message(corpus / "user" / "inbox" / str(index), f"Topic {index}", f"p{index}@example.test")

    first = prepare_enron_subset(corpus, tmp_path / "first.jsonl", limit=3)
    second = prepare_enron_subset(corpus, tmp_path / "second.jsonl", limit=3)

    assert [case["source_ref"] for case in first] == [case["source_ref"] for case in second]
    assert all(len(case["source_sha256"]) == 64 for case in first)
    assert all(case["annotation_status"] == "unlabelled" for case in first)


def test_windows_io_path_preserves_a_trailing_period(tmp_path) -> None:
    path = tmp_path / "1."
    result = _io_path(path, platform_name="nt")
    assert result.startswith("\\\\?\\")
    assert result.endswith("1.")


def test_unlabelled_enron_cases_cannot_be_evaluated(tmp_path) -> None:
    path = tmp_path / "unlabelled.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "enron-example",
                "text": "Email person@example.test",
                "expected": [],
                "annotation_status": "unlabelled",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not labelled"):
        load_text_cases(path)


def test_enron_cli_reports_missing_corpus(capsys, tmp_path) -> None:
    exit_code = main(
        ["--corpus", str(tmp_path / "missing"), "--out", str(tmp_path / "out.jsonl")]
    )
    assert exit_code == 2
    assert "does not exist" in capsys.readouterr().err
