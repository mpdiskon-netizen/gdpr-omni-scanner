"""Small dependency-free domain models used by the scanner."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class FindingType(str, Enum):
    PERSON_NAME = "PERSON_NAME"
    LOCATION_REFERENCE = "LOCATION_REFERENCE"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    IP_ADDRESS = "IP_ADDRESS"
    IBAN = "IBAN"
    PAYMENT_CARD_NUMBER = "PAYMENT_CARD_NUMBER"


@dataclass(frozen=True, slots=True)
class Finding:
    finding_type: FindingType
    value: str
    normalized_value: str
    start: int
    end: int
    detector: str
    validated: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["finding_type"] = self.finding_type.value
        return result


@dataclass(frozen=True, slots=True)
class ScoreContribution:
    finding_type: FindingType
    unique_count: int
    capped_count: int
    weight: int
    points: int

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["finding_type"] = self.finding_type.value
        return result


@dataclass(frozen=True, slots=True)
class ExposureAssessment:
    score: int
    band: str
    contributions: tuple[ScoreContribution, ...]
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "band": self.band,
            "contributions": [item.to_dict() for item in self.contributions],
            "disclaimer": self.disclaimer,
        }


@dataclass(frozen=True, slots=True)
class ScanResult:
    schema_version: str
    scan_id: str
    created_at: str
    source_name: str
    text: str
    findings: tuple[Finding, ...]
    assessment: ExposureAssessment
    models: tuple[str, ...]

    def to_dict(self, include_text: bool = True) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scan_id": self.scan_id,
            "created_at": self.created_at,
            "source_name": self.source_name,
            "text": self.text if include_text else None,
            "findings": [finding.to_dict() for finding in self.findings],
            "assessment": self.assessment.to_dict(),
            "models": list(self.models),
        }

