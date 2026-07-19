"""Transparent personal-data exposure indicator."""

from __future__ import annotations

from collections import defaultdict

from gdpr_scanner.models import ExposureAssessment, Finding, FindingType, ScoreContribution

DISCLAIMER = (
    "This tool highlights possible personal-data exposure for human review. "
    "It does not determine GDPR compliance or provide legal advice."
)

WEIGHTS: dict[FindingType, int] = {
    FindingType.LOCATION_REFERENCE: 3,
    FindingType.PERSON_NAME: 5,
    FindingType.IP_ADDRESS: 8,
    FindingType.EMAIL_ADDRESS: 10,
    FindingType.PHONE_NUMBER: 10,
    FindingType.IBAN: 25,
    FindingType.PAYMENT_CARD_NUMBER: 25,
}


def _band(score: int) -> str:
    if score == 0:
        return "none detected"
    if score <= 24:
        return "low"
    if score <= 49:
        return "moderate"
    if score <= 74:
        return "high"
    return "very high"


def assess_exposure(findings: tuple[Finding, ...] | list[Finding]) -> ExposureAssessment:
    unique_by_type: dict[FindingType, set[str]] = defaultdict(set)
    for finding in findings:
        unique_by_type[finding.finding_type].add(finding.normalized_value)

    contributions: list[ScoreContribution] = []
    for finding_type in sorted(unique_by_type, key=lambda item: item.value):
        unique_count = len(unique_by_type[finding_type])
        capped_count = min(unique_count, 3)
        weight = WEIGHTS[finding_type]
        contributions.append(
            ScoreContribution(finding_type, unique_count, capped_count, weight, capped_count * weight)
        )

    score = min(100, sum(item.points for item in contributions))
    return ExposureAssessment(score, _band(score), tuple(contributions), DISCLAIMER)

