from types import SimpleNamespace

from gdpr_scanner.detectors import (
    deterministic_findings,
    is_valid_iban,
    is_valid_luhn,
    spacy_findings,
)
from gdpr_scanner.models import FindingType


class FakeNlp:
    def __call__(self, text: str):
        return SimpleNamespace(
            ents=(
                SimpleNamespace(text="Alex Morgan", label_="PERSON", start_char=0, end_char=11),
                SimpleNamespace(text="Malta", label_="GPE", start_char=21, end_char=26),
                SimpleNamespace(text="Example Ltd", label_="ORG", start_char=30, end_char=41),
            )
        )


def test_iban_validation() -> None:
    assert is_valid_iban("GB82 WEST 1234 5698 7654 32")
    assert not is_valid_iban("GB82 WEST 1234 5698 7654 31")


def test_luhn_validation() -> None:
    assert is_valid_luhn("4111 1111 1111 1111")
    assert not is_valid_luhn("4111 1111 1111 1112")
    assert not is_valid_luhn("0000 0000 0000 0000")


def test_deterministic_detector_finds_valid_identifiers() -> None:
    text = (
        "Email alex@example.test, phone +356 2123 4567, IP 192.0.2.1, "
        "IBAN GB82 WEST 1234 5698 7654 32 and card 4111 1111 1111 1111."
    )
    types = {finding.finding_type for finding in deterministic_findings(text)}
    assert types == {
        FindingType.EMAIL_ADDRESS,
        FindingType.PHONE_NUMBER,
        FindingType.IP_ADDRESS,
        FindingType.IBAN,
        FindingType.PAYMENT_CARD_NUMBER,
    }


def test_invalid_structured_values_are_not_reported() -> None:
    findings = deterministic_findings(
        "Bad IP 999.2.3.4, bad IBAN GB82 WEST 1234 5698 7654 31, "
        "bad card 4111 1111 1111 1112."
    )
    assert not findings


def test_spacy_mapping_uses_only_supported_labels() -> None:
    findings = spacy_findings("Alex Morgan lives in Malta for Example Ltd", FakeNlp())
    assert [finding.finding_type for finding in findings] == [
        FindingType.PERSON_NAME,
        FindingType.LOCATION_REFERENCE,
    ]


def test_finding_offsets_reference_original_text() -> None:
    text = "Contact alex@example.test today."
    finding = deterministic_findings(text)[0]
    assert text[finding.start : finding.end] == finding.value


def test_ip_before_sentence_full_stop_is_detected() -> None:
    findings = deterministic_findings("Documentation address 192.0.2.1.")
    assert [finding.finding_type for finding in findings] == [FindingType.IP_ADDRESS]
    assert findings[0].value == "192.0.2.1"
