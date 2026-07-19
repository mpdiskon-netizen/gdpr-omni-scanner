import json
from types import SimpleNamespace

from gdpr_scanner.annotation_cli import annotate_file, main
from gdpr_scanner.models import FindingType


def _write_case(path) -> None:
    path.write_text(
        json.dumps(
            {
                "id": "enron-example",
                "source_ref": "user/inbox/1.",
                "annotation_status": "unlabelled",
                "text": "From: person@example.test\nBody: Please reply.",
                "expected": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_annotation_adds_exact_label_and_preserves_backup(tmp_path) -> None:
    path = tmp_path / "pilot.jsonl"
    _write_case(path)
    responses = iter(["a", "EMAIL_ADDRESS", "person@example.test", "d"])

    assert annotate_file(path, case_number=1, input_fn=lambda _prompt: next(responses), output=lambda _line: None) == 0

    case = json.loads(path.read_text(encoding="utf-8"))
    assert case["annotation_status"] == "labelled"
    assert case["expected"] == [
        {"finding_type": "EMAIL_ADDRESS", "value": "person@example.test"}
    ]
    assert path.with_name(path.name + ".original.bak").exists()


def test_annotation_rejects_value_not_in_email(tmp_path) -> None:
    path = tmp_path / "pilot.jsonl"
    _write_case(path)
    output: list[str] = []
    responses = iter(["a", "PERSON_NAME", "Missing Person", "s"])

    annotate_file(path, case_number=1, input_fn=lambda _prompt: next(responses), output=output.append)

    case = json.loads(path.read_text(encoding="utf-8"))
    assert case["expected"] == []
    assert case["annotation_status"] == "unlabelled"
    assert any("does not occur" in line for line in output)


def test_annotation_cli_reports_missing_file(capsys, tmp_path) -> None:
    assert main(["--dataset", str(tmp_path / "missing.jsonl"), "--case", "1"]) == 2
    assert "could not be read" in capsys.readouterr().err


def test_assisted_annotation_accepts_grouped_suggestions_and_records_method(tmp_path) -> None:
    path = tmp_path / "pilot.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "enron-example",
                "source_ref": "user/inbox/1.",
                "annotation_status": "unlabelled",
                "text": "From: person@example.test\nCC: person@example.test\nBody: Hello.",
                "expected": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    finding = lambda: SimpleNamespace(
        finding_type=FindingType.EMAIL_ADDRESS,
        value="person@example.test",
    )
    scan = lambda _text: SimpleNamespace(
        findings=(finding(), finding()),
        models=("spacy:test", "deterministic-identifiers:v1"),
    )
    # PERSON missed, LOCATION missed, EMAIL accept + missed, four remaining missed, final confirmation.
    responses = iter(["", "", "a", "", "", "", "", "", "y"])

    assert annotate_file(
        path,
        case_number=1,
        assisted=True,
        input_fn=lambda _prompt: next(responses),
        output=lambda _line: None,
        scan=scan,
    ) == 0

    case = json.loads(path.read_text(encoding="utf-8"))
    assert case["expected"] == [
        {"finding_type": "EMAIL_ADDRESS", "value": "person@example.test"},
        {"finding_type": "EMAIL_ADDRESS", "value": "person@example.test"},
    ]
    assert case["annotation_status"] == "labelled"
    assert case["annotation_method"] == "model_assisted_human_review"
    assert case["annotation_models"] == ["spacy:test", "deterministic-identifiers:v1"]


def test_assisted_annotation_can_reject_prediction_and_add_missed_value(tmp_path) -> None:
    path = tmp_path / "pilot.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "enron-example",
                "source_ref": "user/inbox/1.",
                "annotation_status": "unlabelled",
                "text": "Email wrote to Correct Person.",
                "expected": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    scan = lambda _text: SimpleNamespace(
        findings=(
            SimpleNamespace(finding_type=FindingType.PERSON_NAME, value="Email"),
        ),
        models=("spacy:test",),
    )
    # Reject PERSON suggestion, add missed name, finish PERSON, then six empty types, confirm.
    responses = iter(["n", "Correct Person", "", "", "", "", "", "", "", "y"])

    annotate_file(
        path,
        case_number=1,
        assisted=True,
        input_fn=lambda _prompt: next(responses),
        output=lambda _line: None,
        scan=scan,
    )

    case = json.loads(path.read_text(encoding="utf-8"))
    assert case["expected"] == [
        {"finding_type": "PERSON_NAME", "value": "Correct Person"}
    ]
    assert case["annotation_status"] == "labelled"
