from __future__ import annotations

import abc
from dataclasses import dataclass, field




TIER_AUDITED_STATEMENTS = 1
TIER_REGULATORY_FILING = 2
TIER_OFFICIAL_COMPANY_DOCUMENT = 3
TIER_INVESTOR_RELATIONS = 4
TIER_INVESTOR_PRESENTATION = 5
TIER_TRUSTED_SECONDARY = 6
TIER_UNAVAILABLE = 99


@dataclass
class SourceCandidate:
    provider: str
    tier: int
    title: str
    locator: dict
    reference: str = ""


@dataclass
class SourceContent:
    provider: str
    tier: int
    text: str
    page: int | None = None
    reference: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class VerificationResult:
    verified: bool
    method: str = ""
    detail: str = ""


@dataclass
class FieldEvidence:
    field: str
    found: bool
    provider: str
    tier: int
    value: object = None
    content: SourceContent | None = None
    verification: VerificationResult | None = None
    note: str = ""


class SourceProvider(abc.ABC):


    name: str = "abstract"
    tier: int = TIER_UNAVAILABLE

    @abc.abstractmethod
    def is_configured(self) -> bool: ...

    @abc.abstractmethod
    def search(self, query: str, context: dict) -> list[SourceCandidate]: ...

    @abc.abstractmethod
    def fetch(self, candidate: SourceCandidate) -> SourceContent | None: ...

    def verify(self, content: SourceContent, claim) -> VerificationResult:

        from services.number_match import number_present

        if content is None or not content.text:
            return VerificationResult(False, "none", "no source content")
        if isinstance(claim, str):
            ok = len(claim.strip()) >= 4 and claim.strip().lower() in content.text.lower()
            return VerificationResult(ok, "text_match")
        if isinstance(claim, (int, float)) and not isinstance(claim, bool):
            return VerificationResult(bool(number_present(claim, content.text)), "numeric_presence")
        return VerificationResult(False, "unsupported_claim_type")

    def metadata(self) -> dict:
        return {"name": self.name, "tier": self.tier, "configured": self.is_configured()}
