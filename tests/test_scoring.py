from gdpr_scanner.models import Finding, FindingType
from gdpr_scanner.scoring import assess_exposure


def make_finding(finding_type: FindingType, value: str) -> Finding:
    return Finding(finding_type, value, value.casefold(), 0, len(value), "test", True)


def test_empty_result_scores_zero() -> None:
    assessment = assess_exposure([])
    assert assessment.score == 0
    assert assessment.band == "none detected"


def test_unique_values_are_counted_but_duplicates_are_not() -> None:
    findings = [
        make_finding(FindingType.EMAIL_ADDRESS, "a@example.test"),
        make_finding(FindingType.EMAIL_ADDRESS, "a@example.test"),
        make_finding(FindingType.EMAIL_ADDRESS, "b@example.test"),
    ]
    assessment = assess_exposure(findings)
    assert assessment.score == 20
    assert assessment.contributions[0].unique_count == 2


def test_each_type_is_capped_at_three_unique_values() -> None:
    findings = [make_finding(FindingType.PAYMENT_CARD_NUMBER, str(index)) for index in range(5)]
    assessment = assess_exposure(findings)
    assert assessment.score == 75
    assert assessment.band == "very high"
    assert assessment.contributions[0].capped_count == 3


def test_total_score_is_capped_at_one_hundred() -> None:
    findings = []
    for finding_type in FindingType:
        findings.extend(make_finding(finding_type, f"{finding_type.value}-{index}") for index in range(3))
    assert assess_exposure(findings).score == 100


def _findings_for_band(score: int) -> list[Finding]:
    locations = [make_finding(FindingType.LOCATION_REFERENCE, f"place-{index}") for index in range(3)]
    people = [make_finding(FindingType.PERSON_NAME, f"person-{index}") for index in range(3)]
    ibans = [make_finding(FindingType.IBAN, f"iban-{index}") for index in range(3)]
    cards = [make_finding(FindingType.PAYMENT_CARD_NUMBER, "card-1")]
    if score == 0:
        return []
    if score == 24:
        return locations + people
    if score == 25:
        return ibans[:1]
    if score == 49:
        return locations + people + ibans[:1]
    if score == 50:
        return ibans[:2]
    if score == 74:
        return locations + people + ibans[:1] + cards
    if score == 75:
        return ibans
    raise AssertionError(f"Unsupported test score: {score}")


def test_score_band_boundaries() -> None:
    expected = {
        0: "none detected",
        24: "low",
        25: "moderate",
        49: "moderate",
        50: "high",
        74: "high",
        75: "very high",
    }
    for score, band in expected.items():
        assessment = assess_exposure(_findings_for_band(score))
        assert assessment.score == score
        assert assessment.band == band
