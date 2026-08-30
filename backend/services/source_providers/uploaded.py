from __future__ import annotations

from services.field_registry import DEFAULT_SOURCE_PRIORITY, SOURCE_PRIORITY_BY_DOC_TYPE
from services.retrieval import hybrid_search
from services.source_providers.base import (
    SourceCandidate,
    SourceContent,
    SourceProvider,
)


class UploadedDocumentProvider(SourceProvider):
    name = "uploaded_document"

    def __init__(self, report_id: int, *, document_type: str = "", document_name: str = "", cache=None):
        self.report_id = report_id
        self.document_type = document_type or ""
        self.document_name = document_name or "Uploaded report.pdf"
        self._cache = cache
        self.tier = SOURCE_PRIORITY_BY_DOC_TYPE.get(self.document_type, DEFAULT_SOURCE_PRIORITY)

    def is_configured(self) -> bool:
        return self.report_id is not None

    def search(self, query: str, context: dict) -> list[SourceCandidate]:
        top_k = int(context.get("top_k", 5))
        if self._cache is not None:
            chunks = self._cache.get_or_retrieve(query, top_k, hybrid_search)
        else:
            chunks = hybrid_search(self.report_id, query, top_k=top_k)
        return [
            SourceCandidate(
                provider=self.name,
                tier=self.tier,
                title=self.document_name,
                locator={"report_id": self.report_id, "page": c["page_number"]},
                reference=f"{self.document_name}, p.{c['page_number']}",
            )
            for c in chunks
        ]

    def fetch(self, candidate: SourceCandidate) -> SourceContent | None:
        page = candidate.locator.get("page")
        text = None
        if self._cache is not None:
            text = self._cache.page_text(page)
        if text is None:

            for c in hybrid_search(self.report_id, self.document_name, top_k=25):
                if c["page_number"] == page:
                    text = c["text"]
                    break
        if not text:
            return None
        return SourceContent(
            provider=self.name,
            tier=self.tier,
            text=text,
            page=page,
            reference=candidate.reference,
            metadata={"document_type": self.document_type, "document_name": self.document_name},
        )

    def metadata(self) -> dict:
        return {
            **super().metadata(),
            "report_id": self.report_id,
            "document_type": self.document_type,
            "document_name": self.document_name,
        }
