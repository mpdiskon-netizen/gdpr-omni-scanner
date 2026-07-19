import pytest

from gdpr_scanner.detectors import load_spacy_model
from gdpr_scanner.models import FindingType
from gdpr_scanner.scanner import scan_text


@pytest.mark.model
def test_real_spacy_model_smoke() -> None:
    nlp = load_spacy_model()
    result = scan_text("Alex Morgan lives in Malta.", nlp=nlp)
    finding_types = {finding.finding_type for finding in result.findings}
    assert FindingType.PERSON_NAME in finding_types
    assert FindingType.LOCATION_REFERENCE in finding_types
    assert any(model.startswith("spacy:") and not model.endswith(":unknown") for model in result.models)
