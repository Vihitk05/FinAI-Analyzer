from __future__ import annotations

from services.source_providers.base import (
    FieldEvidence,
    SourceProvider,
    VerificationResult,
)
from services.source_providers.external import (
    InvestorRelationsProvider,
    OfficialCompanySourceProvider,
    RegulatorySourceProvider,
    TrustedSecondaryProvider,
)
from services.source_providers.uploaded import UploadedDocumentProvider


class SourceProviderRegistry:
    def __init__(self, providers: list[SourceProvider] | None = None):
        self._providers: list[SourceProvider] = []
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: SourceProvider) -> None:
        self._providers.append(provider)
        self._providers.sort(key=lambda p: p.tier)

    def all(self) -> list[SourceProvider]:
        return list(self._providers)

    def configured(self) -> list[SourceProvider]:
        return [p for p in self._providers if p.is_configured()]

    def has_external_configured(self) -> bool:
        return any(p.is_configured() and p.name != "uploaded_document" for p in self._providers)

    def hierarchy(self) -> list[dict]:
        return [p.metadata() for p in self._providers]


class SourceResolver:
    def __init__(self, registry: SourceProviderRegistry):
        self.registry = registry

    def resolve(self, field: str, query: str, claim, *, context: dict | None = None) -> FieldEvidence:
        context = context or {}
        last_note = "no configured source produced a candidate for this field"
        for provider in self.registry.configured():
            candidates = provider.search(query, context)
            for candidate in candidates:
                content = provider.fetch(candidate)
                if content is None:
                    continue
                verification: VerificationResult = provider.verify(content, claim)
                if verification.verified:
                    return FieldEvidence(
                        field=field, found=True, provider=provider.name, tier=provider.tier,
                        value=claim, content=content, verification=verification,
                        note=candidate.reference,
                    )
                last_note = f"{provider.name}: candidate found but claim not verified in source text"
        return FieldEvidence(field=field, found=False, provider="", tier=0, note=last_note)

    def external_status(self) -> dict:

        if self.registry.has_external_configured():
            return {"externalVerifiedSourceAvailable": True}
        return {
            "externalVerifiedSourceAvailable": False,
            "message": "No approved external verified source was available; "
                       "facts are verified against the uploaded document(s) only.",
        }


def default_registry(report_id: int | None = None, *, document_type: str = "", document_name: str = "", cache=None) -> SourceProviderRegistry:

    providers: list[SourceProvider] = [
        RegulatorySourceProvider(),
        OfficialCompanySourceProvider(),
        InvestorRelationsProvider(),
        TrustedSecondaryProvider(),
    ]
    if report_id is not None:
        providers.append(
            UploadedDocumentProvider(report_id, document_type=document_type, document_name=document_name, cache=cache)
        )
    return SourceProviderRegistry(providers)
