from __future__ import annotations

import os

from services.source_providers.base import (
    TIER_INVESTOR_RELATIONS,
    TIER_OFFICIAL_COMPANY_DOCUMENT,
    TIER_REGULATORY_FILING,
    TIER_TRUSTED_SECONDARY,
    SourceCandidate,
    SourceContent,
    SourceProvider,
)


class _UnconfiguredExternalProvider(SourceProvider):


    credential_env: str = ""

    def is_configured(self) -> bool:
        return bool(self.credential_env and os.environ.get(self.credential_env))

    def search(self, query: str, context: dict) -> list[SourceCandidate]:
        return []

    def fetch(self, candidate: SourceCandidate) -> SourceContent | None:
        return None

    def metadata(self) -> dict:
        return {**super().metadata(), "credential_env": self.credential_env, "status": "not_configured"}


class RegulatorySourceProvider(_UnconfiguredExternalProvider):
    name = "regulatory_filing"
    tier = TIER_REGULATORY_FILING
    credential_env = "REGULATORY_SOURCE_API_KEY"


class OfficialCompanySourceProvider(_UnconfiguredExternalProvider):
    name = "official_company_document"
    tier = TIER_OFFICIAL_COMPANY_DOCUMENT
    credential_env = "OFFICIAL_COMPANY_SOURCE_API_KEY"


class InvestorRelationsProvider(_UnconfiguredExternalProvider):
    name = "investor_relations"
    tier = TIER_INVESTOR_RELATIONS
    credential_env = "INVESTOR_RELATIONS_API_KEY"


class TrustedSecondaryProvider(_UnconfiguredExternalProvider):
    name = "trusted_secondary"
    tier = TIER_TRUSTED_SECONDARY
    credential_env = "TRUSTED_SECONDARY_API_KEY"
