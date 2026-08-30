from __future__ import annotations

_PAGES_TO_SCAN = 5


def classify_document(pages: list[dict]) -> str:

    text = " ".join(p.get("text", "") for p in pages[:_PAGES_TO_SCAN]).lower()

    if "form 10-k" in text or "annual report on form 10-k" in text:
        return "10-K"
    if "form 10-q" in text:
        return "10-Q"
    if "form 20-f" in text:
        return "20-F"
    if "investor presentation" in text or "earnings presentation" in text or "capital markets day" in text:
        return "investor_presentation"
    if "earnings release" in text or ("press release" in text and "results" in text):
        return "earnings_release"
    if "quarterly report" in text:
        return "quarterly_report"
    if "annual report" in text or "integrated report" in text:
        return "annual_report"
    if "independent auditor" in text and "opinion" in text and len(pages) <= 10:
        return "auditor_report"
    if len(pages) <= 15:
        return "financial_statements"
    return "other_financial_document"
