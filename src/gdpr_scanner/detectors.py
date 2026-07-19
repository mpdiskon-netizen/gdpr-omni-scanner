"""spaCy NER and deterministic structured-identifier detectors."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable
from typing import Any

from gdpr_scanner.models import Finding, FindingType

EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
IBAN_RE = re.compile(
    r"(?<![A-Z0-9])(?:"
    r"[A-Z]{2}\d{2}(?: [A-Z0-9]{4}){2,7}(?: [A-Z0-9]{1,3})?"
    r"|[A-Z]{2}\d{2}[A-Z0-9]{11,30}"
    r")(?![A-Z0-9])",
    re.I,
)
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
IP_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?!\w)(?!\.\d)")
PHONE_RE = re.compile(r"(?<![\w])\+?\d[\d ()-]{5,}\d(?!\w)")


class ModelUnavailableError(RuntimeError):
    """Raised when the local spaCy model has not been installed."""


def _normalise_spaces(value: str) -> str:
    return " ".join(value.split())


def _digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def is_valid_iban(value: str) -> bool:
    compact = re.sub(r"[^A-Z0-9]", "", value.upper())
    if not 15 <= len(compact) <= 34 or not compact[:2].isalpha() or not compact[2:4].isdigit():
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = "".join(str(ord(character) - 55) if character.isalpha() else character for character in rearranged)
    remainder = 0
    for character in numeric:
        remainder = (remainder * 10 + int(character)) % 97
    return remainder == 1


def is_valid_luhn(value: str) -> bool:
    digits = _digits(value)
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    total = 0
    parity = len(digits) % 2
    for index, character in enumerate(digits):
        digit = int(character)
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _overlaps(start: int, end: int, findings: Iterable[Finding]) -> bool:
    return any(start < finding.end and end > finding.start for finding in findings)


def deterministic_findings(text: str) -> list[Finding]:
    findings: list[Finding] = []
    iban_candidates = list(IBAN_RE.finditer(text))
    card_candidates = list(CARD_RE.finditer(text))
    reserved_numeric_spans = [match.span() for match in (*iban_candidates, *card_candidates)]

    for match in EMAIL_RE.finditer(text):
        findings.append(
            Finding(
                FindingType.EMAIL_ADDRESS,
                match.group(),
                match.group().casefold(),
                match.start(),
                match.end(),
                "deterministic",
                True,
            )
        )

    for match in iban_candidates:
        value = match.group()
        if is_valid_iban(value):
            findings.append(
                Finding(
                    FindingType.IBAN,
                    value,
                    re.sub(r"[^A-Z0-9]", "", value.upper()),
                    match.start(),
                    match.end(),
                    "deterministic",
                    True,
                )
            )

    for match in card_candidates:
        value = match.group()
        if is_valid_luhn(value):
            findings.append(
                Finding(
                    FindingType.PAYMENT_CARD_NUMBER,
                    value,
                    _digits(value),
                    match.start(),
                    match.end(),
                    "deterministic",
                    True,
                )
            )

    for match in IP_RE.finditer(text):
        value = match.group()
        try:
            normalized = str(ipaddress.ip_address(value))
        except ValueError:
            continue
        findings.append(
            Finding(
                FindingType.IP_ADDRESS,
                value,
                normalized,
                match.start(),
                match.end(),
                "deterministic",
                True,
            )
        )

    for match in PHONE_RE.finditer(text):
        value = match.group()
        digits = _digits(value)
        overlaps_reserved = any(
            match.start() < reserved_end and match.end() > reserved_start
            for reserved_start, reserved_end in reserved_numeric_spans
        )
        if (
            7 <= len(digits) <= 15
            and not overlaps_reserved
            and not _overlaps(match.start(), match.end(), findings)
        ):
            prefix = "+" if value.lstrip().startswith("+") else ""
            findings.append(
                Finding(
                    FindingType.PHONE_NUMBER,
                    value,
                    prefix + digits,
                    match.start(),
                    match.end(),
                    "deterministic",
                    True,
                )
            )

    return sorted(findings, key=lambda finding: (finding.start, finding.end, finding.finding_type.value))


def load_spacy_model() -> Any:
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except (ImportError, OSError) as error:
        raise ModelUnavailableError(
            "The spaCy English model is unavailable. Run: python -m spacy download en_core_web_sm"
        ) from error


def spacy_findings(text: str, nlp: Any | None = None) -> list[Finding]:
    nlp = nlp or load_spacy_model()
    mapping = {
        "PERSON": FindingType.PERSON_NAME,
        "GPE": FindingType.LOCATION_REFERENCE,
        "LOC": FindingType.LOCATION_REFERENCE,
        "FAC": FindingType.LOCATION_REFERENCE,
    }
    findings: list[Finding] = []
    for entity in nlp(text).ents:
        finding_type = mapping.get(entity.label_)
        if finding_type is None:
            continue
        value = entity.text
        findings.append(
            Finding(
                finding_type,
                value,
                _normalise_spaces(value).casefold(),
                entity.start_char,
                entity.end_char,
                "spacy:en_core_web_sm",
                None,
            )
        )
    return findings


def detect_all(text: str, nlp: Any | None = None) -> tuple[Finding, ...]:
    combined = deterministic_findings(text) + spacy_findings(text, nlp)
    unique: dict[tuple[FindingType, str, int, int], Finding] = {}
    for finding in combined:
        key = (finding.finding_type, finding.normalized_value, finding.start, finding.end)
        unique[key] = finding
    return tuple(sorted(unique.values(), key=lambda finding: (finding.start, finding.end, finding.finding_type.value)))
