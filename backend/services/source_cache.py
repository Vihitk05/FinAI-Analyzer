from __future__ import annotations

import re
from typing import Callable

_WS_RE = re.compile(r"\s+")


def _normalise_query(query: str) -> str:
    return _WS_RE.sub(" ", (query or "").strip().lower())


class SourceCache:


    def __init__(self, report_id: int):
        self.report_id = report_id
        self._pages: dict[int, str] = {}
        self._retrieval: dict[tuple, list[dict]] = {}
        self._metadata: dict = {}
        self.stats = {"retrieval_hits": 0, "retrieval_misses": 0}


    def set_pages(self, pages: list[dict]) -> None:

        for page in pages or []:
            if isinstance(page, dict) and "page_number" in page:
                self._pages[int(page["page_number"])] = page.get("text", "")

    def page_text(self, page_number: int) -> str | None:
        return self._pages.get(int(page_number))

    def pages(self) -> dict[int, str]:
        return dict(self._pages)


    def _key(self, query: str, top_k: int) -> tuple:
        return (self.report_id, _normalise_query(query), int(top_k))

    def prime_retrieval(self, query: str, top_k: int, chunks: list[dict]) -> None:

        self._retrieval[self._key(query, top_k)] = chunks

    def get_or_retrieve(self, query: str, top_k: int, retriever: Callable[[int, str, int], list[dict]]) -> list[dict]:
        key = self._key(query, top_k)
        if key in self._retrieval:
            self.stats["retrieval_hits"] += 1
            return self._retrieval[key]
        self.stats["retrieval_misses"] += 1
        chunks = retriever(self.report_id, query, top_k)
        self._retrieval[key] = chunks
        return chunks


    def set_metadata(self, **kwargs) -> None:
        self._metadata.update(kwargs)

    def metadata(self) -> dict:
        return dict(self._metadata)
