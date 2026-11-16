from __future__ import annotations

import re
import uuid
from collections import Counter
from datetime import date, datetime, timezone
from time import perf_counter

from services.number_match import number_present
from services.conflicts import (
    STATUS_CONFLICTING,
    conflict_status_overrides,
    detect_field_conflicts,
)
from services.field_registry import (
    DEFAULT_SOURCE_PRIORITY as _DEFAULT_SOURCE_PRIORITY,
    FIELD_REGISTRY,
    NOTE_DISCLOSURE_CATEGORIES,
    SOURCE_PRIORITY_BY_DOC_TYPE as _SOURCE_PRIORITY_BY_DOC_TYPE,
    expected_fields_for,
    registry_entry,
)




STATUS_VERIFIED = "verified"
STATUS_CALCULATED = "calculated"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_CONFLICTING = "conflicting"
STATUS_UNAVAILABLE = "unavailable"
STATUS_NOT_APPLICABLE = "not_applicable"

BUILDER_VERSION = 2




_CONSISTENCY_CHECK_FIELDS = {
    "balance_sheet_identity": {"totalAssets", "totalLiabilities", "totalEquity"},
    "cash_flow_rollforward": {
        "openingCash", "closingCash", "cashFlowOperations", "cashFlowInvesting", "cashFlowFinancing",
    },
    "gross_profit": {"revenue", "costOfRevenue", "grossProfit"},
}

_CORPORATE_SUFFIXES = {
    "inc", "incorporated", "corp", "corporation", "ltd", "limited", "llc",
    "plc", "pvt", "private", "co", "company", "sa", "ag", "nv",
}
_MONETARY = {"revenue", "ebitda", "netIncome", "freeCashFlow", "cashFlowOperations", "cashFlowInvesting", "cashFlowFinancing"}
_MATERIAL_LISTS = {"recommendations", "dueDiligenceRecommendations"}


_NOTABLE_WHEN_MISSING = {
    "segmentRevenueBreakdown": "Segment-level financial information",
    "geographicRevenueBreakdown": "Geographic revenue breakdown",
    "managementOutlook": "Management outlook / guidance",
    "keyRisks": "Principal risks / risk factors",
    "auditorOpinion": "Independent auditor's opinion",
    "cashFlowOperations": "Cash flow statement detail",
}









def _is_public_id(value) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def scrub_report_citation_ids(report: dict, public_id: str) -> dict:

    for citation in report.get("citations") or []:
        if isinstance(citation, dict):
            citation["reportId"] = public_id
    return report


def scrub_dashboard_public_ids(payload: dict) -> dict:

    def _fix_refs(items) -> None:
        for item in items or []:
            if isinstance(item, dict) and not _is_public_id(item.get("reportId")):
                item["reportId"] = None

    for key in ("facts", "metrics", "insights", "derivedMetrics", "notesDisclosures"):
        for item in payload.get(key) or []:
            if isinstance(item, dict):
                _fix_refs(item.get("citations"))
                _fix_refs(item.get("provenance"))
    for chart in payload.get("charts") or []:
        for point in (chart.get("data") if isinstance(chart, dict) else None) or []:
            if isinstance(point, dict):
                if not _is_public_id(point.get("reportId")):
                    point["reportId"] = None
                _fix_refs(point.get("citations"))
                _fix_refs(point.get("provenance"))
    for source_report in payload.get("sourceReports") or []:
        if isinstance(source_report, dict) and not _is_public_id(source_report.get("id")):
            source_report["id"] = None
    for record in payload.get("conflicts") or []:
        if isinstance(record, dict):
            _fix_refs(record.get("candidates"))
            if isinstance(record.get("chosen"), dict):
                _fix_refs([record["chosen"]])
    for item in [*(payload.get("metrics") or []), *(payload.get("facts") or [])]:
        conflict = item.get("conflict") if isinstance(item, dict) else None
        if isinstance(conflict, dict):
            _fix_refs(conflict.get("candidates"))
            if isinstance(conflict.get("chosen"), dict):
                _fix_refs([conflict["chosen"]])
    return payload


def normalize_company_name(name: str) -> str:

    tokens = re.findall(r"[a-z0-9]+", (name or "").lower())
    while tokens and tokens[-1] in _CORPORATE_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def _description(field: str, quote: str = "") -> str:
    label = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", field).lower()
    if quote:


        return f"Contains the reported {label} used in this analysis."
    return f"Contains source evidence supporting the reported {label}."


def enrich_and_verify_citations(report: dict, pages: dict[int, str], filename: str, *, perf=None) -> list[dict]:

    started = perf_counter()
    verified = []
    checked = 0
    for citation in report.get("citations") or []:
        checked += 1
        if not isinstance(citation, dict):
            continue
        field, page = citation.get("field"), citation.get("page")
        if not isinstance(field, str) or not isinstance(page, int) or page not in pages:
            continue
        value = report.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value != 0:
            if not number_present(value, pages[page]):
                continue


        if isinstance(value, str) and value.strip() and not citation.get("quote"):
            continue
        verified.append({
            "field": field,
            "page": page,
            "filename": filename or "Uploaded report.pdf",
            "reportId": report.get("custom_id"),
            "sourceType": "uploaded_report",
            "description": _description(field, str(citation.get("quote") or "")),
            "verificationStatus": "verified",
            "quote": citation.get("quote", ""),
        })
    if perf is not None:
        perf.record_verification(
            name="citation_numeric_source_verification",
            started=started,
            citations_checked=checked,
            citations_verified=len(verified),
        )
    return verified


def _citations_for(report: dict, field: str) -> list[dict]:
    return [c for c in report.get("citations") or [] if c.get("field") == field and c.get("verificationStatus") == "verified"]


def _consistency_review_fields(report: dict) -> set[str]:

    flagged: set[str] = set()
    for check in report.get("consistencyChecks") or []:
        if isinstance(check, dict) and check.get("status") == "fail":
            flagged |= _CONSISTENCY_CHECK_FIELDS.get(check.get("check"), set())
    return flagged


def _source_object(citation: dict, report: dict) -> dict:

    field = citation.get("field", "")
    entry = registry_entry(field)
    doc_type = report.get("documentType") or ""
    return {
        "name": citation.get("filename") or "Uploaded report.pdf",
        "type": doc_type or "uploaded_document",
        "document": citation.get("filename") or "Uploaded report.pdf",
        "page": citation.get("page"),
        "section": entry["category"] if entry else None,
        "url": None,
        "priority": _SOURCE_PRIORITY_BY_DOC_TYPE.get(doc_type, _DEFAULT_SOURCE_PRIORITY),
        "verified": citation.get("verificationStatus") == "verified",
        "verificationMethod": "source_text_match",
        "reportId": citation.get("reportId"),
        "reportingPeriod": _period(report),
    }


def _fact(report: dict, field: str, review_fields: set[str] | None = None) -> dict | None:
    value = report.get(field)
    if value in (None, "", [], {}):
        return None
    citations = _citations_for(report, field)
    if not citations:
        return None
    review_fields = review_fields if review_fields is not None else _consistency_review_fields(report)
    return {
        "field": field,
        "value": value,
        "citations": citations,
        "kind": "reported_fact",
        "valueType": "reported",
        "status": STATUS_NEEDS_REVIEW if field in review_fields else STATUS_VERIFIED,
        "period": _period(report),
        "currency": report.get("currency") or "",
        "provenance": [_source_object(c, report) for c in citations],
    }


def _fact_with_fallback(reports_newest_first: list[dict], field: str) -> dict | None:

    for index, report in enumerate(reports_newest_first):
        fact = _fact(report, field)
        if fact:
            if index > 0:
                fact = {**fact, "sourcedFromPeriod": _period(report), "isFallbackSource": True}
            return fact
    return None



_RATIO_DEFINITIONS = [

    {"name": "Current Ratio", "formula": "Current Assets / Current Liabilities", "inputs": ("currentAssets", "currentLiabilities"), "compute": lambda a, b: a / b, "isPercentage": False},
    {"name": "Quick Ratio", "formula": "(Current Assets − Inventory) / Current Liabilities", "inputs": ("currentAssets", "inventory", "currentLiabilities"), "compute": lambda a, b, c: (a - b) / c, "isPercentage": False},
    {"name": "Cash Ratio", "formula": "Cash & Equivalents / Current Liabilities", "inputs": ("cashAndEquivalents", "currentLiabilities"), "compute": lambda a, b: a / b, "isPercentage": False},

    {"name": "Gross Margin", "formula": "Gross Profit / Revenue × 100", "inputs": ("grossProfit", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Operating Margin", "formula": "Operating Profit / Revenue × 100", "inputs": ("operatingProfit", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "EBITDA Margin", "formula": "EBITDA / Revenue × 100", "inputs": ("ebitda", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Pre-tax Margin", "formula": "Profit Before Tax / Revenue × 100", "inputs": ("profitBeforeTax", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Net Margin", "formula": "Net Income / Revenue × 100", "inputs": ("netIncome", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Effective Tax Rate", "formula": "Tax Expense / Profit Before Tax × 100", "inputs": ("taxExpense", "profitBeforeTax"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Return on Assets", "formula": "Net Income / Total Assets × 100", "inputs": ("netIncome", "totalAssets"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Return on Equity", "formula": "Net Income / Total Equity × 100", "inputs": ("netIncome", "totalEquity"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Asset Turnover", "formula": "Revenue / Total Assets", "inputs": ("revenue", "totalAssets"), "compute": lambda a, b: a / b, "isPercentage": False},

    {"name": "Debt to Equity", "formula": "Total Debt / Total Equity", "inputs": ("totalDebt", "totalEquity"), "compute": lambda a, b: a / b, "isPercentage": False},
    {"name": "Debt to Assets", "formula": "Total Debt / Total Assets × 100", "inputs": ("totalDebt", "totalAssets"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Equity Ratio", "formula": "Total Equity / Total Assets × 100", "inputs": ("totalEquity", "totalAssets"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Net Debt to EBITDA", "formula": "(Total Debt − Cash & Equivalents) / EBITDA", "inputs": ("totalDebt", "cashAndEquivalents", "ebitda"), "compute": lambda a, b, c: (a - b) / c, "isPercentage": False},
    {"name": "Interest Coverage", "formula": "Operating Profit / Interest Expense", "inputs": ("operatingProfit", "interestExpense"), "compute": lambda a, b: a / b, "isPercentage": False},
    {"name": "Average Cost of Debt", "formula": "Interest Expense / Total Debt × 100", "inputs": ("interestExpense", "totalDebt"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},

    {"name": "Operating Cash Flow Margin", "formula": "Operating Cash Flow / Revenue × 100", "inputs": ("cashFlowOperations", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Free Cash Flow Margin", "formula": "Free Cash Flow / Revenue × 100", "inputs": ("freeCashFlow", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Cash Flow to Debt", "formula": "Operating Cash Flow / Total Debt × 100", "inputs": ("cashFlowOperations", "totalDebt"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Capex to Revenue", "formula": "Capital Expenditure / Revenue × 100", "inputs": ("capitalExpenditure", "revenue"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Capex to Operating Cash Flow", "formula": "Capital Expenditure / Operating Cash Flow × 100", "inputs": ("capitalExpenditure", "cashFlowOperations"), "compute": lambda a, b: (a / b) * 100, "isPercentage": True},
    {"name": "Cash Flow Reinvestment", "formula": "Investing Cash Flow / Operating Cash Flow × 100", "inputs": ("cashFlowInvesting", "cashFlowOperations"), "compute": lambda a, b: (abs(a) / b) * 100, "isPercentage": True},
]


def _calculated_ratios(report: dict) -> dict | None:

    rows, all_citations = [], []
    for definition in _RATIO_DEFINITIONS:
        input_facts = [_fact(report, name) for name in definition["inputs"]]
        if any(f is None for f in input_facts):
            continue
        values = [f["value"] for f in input_facts]
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            continue
        if values[-1] == 0:
            continue
        try:
            value = definition["compute"](*values)
        except ZeroDivisionError:
            continue
        rows.append({"ratio": definition["name"], "value": round(value, 2), "isPercentage": definition["isPercentage"], "formula": definition["formula"]})
        for f in input_facts:
            all_citations.extend(f["citations"])
    if not rows:
        return None



    seen, deduped = set(), []
    for citation in all_citations:
        key = (citation.get("field"), citation.get("page"))
        if key not in seen:
            seen.add(key)
            deduped.append(citation)
    return {
        "field": "calculatedRatios",
        "value": rows,
        "citations": deduped,
        "kind": "calculated_metric",
        "valueType": "calculated",
        "status": STATUS_CALCULATED,
        "period": _period(report),
        "currency": report.get("currency") or "",
        "calculation": {
            "formula": "per-row: see each ratio's formula",
            "inputs": sorted({name for definition in _RATIO_DEFINITIONS for name in definition["inputs"]
                              if _fact(report, name)}),
        },
        "provenance": [_source_object(c, report) for c in deduped],
    }


def _period(report: dict) -> str:


    return str(report.get("reportingPeriod") or report.get("analysis_date") or "Undated report")


_MONTHS = {
    name: number
    for number, names in enumerate(
        [("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"), ("may",), ("june", "jun"),
         ("july", "jul"), ("august", "aug"), ("september", "sep", "sept"), ("october", "oct"),
         ("november", "nov"), ("december", "dec")],
        start=1,
    )
    for name in names
}

_PERIOD_LENGTHS = [
    (re.compile(r"\b(three|3)[\s-]+months?\b|\bq[1-4]\b|\bquarter"), 3),
    (re.compile(r"\b(six|6)[\s-]+months?\b|\bh[12]\b|\bhalf[\s-]+year|\b(first|second) half\b"), 6),
    (re.compile(r"\b(nine|9)[\s-]+months?\b|\b9m\b"), 9),
    (re.compile(r"\b(twelve|12)[\s-]+months?\b|\byear\b|\bfy\s?'?\d|\bannual\b|\bfiscal\b"), 12),
]

_MONTH_DAY_YEAR = re.compile(r"\b([a-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})\b")
_DAY_MONTH_YEAR = re.compile(r"\b(\d{1,2})\s+([a-z]{3,9})\.?,?\s+(\d{4})\b")
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_QUARTER_YEAR = re.compile(r"\bq([1-4])\s*(?:fy\s*)?'?(\d{4})\b")
_HALF_YEAR = re.compile(r"\bh([12])\s*(?:fy\s*)?'?(\d{4})\b")
_FISCAL_YEAR = re.compile(r"\b(?:fy|fiscal(?: year)?)\s*'?(\d{4}|\d{2})\b")
_ORDINAL_QUARTER = re.compile(r"\b(first|second|third|fourth) quarter(?: of)?(?: fiscal(?: year)?| fy)?\s*'?(\d{4})\b")
_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
_QUARTER_END_DAY = {3: 31, 6: 30, 9: 30, 12: 31}


def _period_months(report: dict) -> int | None:
    text = str(report.get("reportingPeriod") or "").lower()
    for pattern, months in _PERIOD_LENGTHS:
        if pattern.search(text):
            return months
    return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _period_end(report: dict) -> date | None:
    text = str(report.get("reportingPeriod") or "").lower()
    match = _MONTH_DAY_YEAR.search(text)
    if match and match.group(1) in _MONTHS:
        return _safe_date(int(match.group(3)), _MONTHS[match.group(1)], int(match.group(2)))
    match = _DAY_MONTH_YEAR.search(text)
    if match and match.group(2) in _MONTHS:
        return _safe_date(int(match.group(3)), _MONTHS[match.group(2)], int(match.group(1)))
    match = _ISO_DATE.search(text)
    if match:
        return _safe_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    match = _QUARTER_YEAR.search(text)
    if match:
        month = int(match.group(1)) * 3
        return _safe_date(int(match.group(2)), month, _QUARTER_END_DAY[month])
    match = _ORDINAL_QUARTER.search(text)
    if match:
        month = _ORDINALS[match.group(1)] * 3
        return _safe_date(int(match.group(2)), month, _QUARTER_END_DAY[month])
    match = _HALF_YEAR.search(text)
    if match:
        month = int(match.group(1)) * 6
        return _safe_date(int(match.group(2)), month, _QUARTER_END_DAY[month])
    match = _FISCAL_YEAR.search(text)
    if match:
        year = int(match.group(1))
        return _safe_date(year + 2000 if year < 100 else year, 12, 31)
    return None


def _sort_by_period(reports: list[dict]) -> list[dict]:
    if reports and all(_period_end(r) for r in reports):
        return sorted(reports, key=lambda r: (_period_end(r), r.get("created_at") or ""))
    return reports


def _comparable_reports(reports: list[dict]) -> list[dict]:
    if not reports:
        return []
    months = _period_months(reports[-1])
    if months is None:
        return []
    by_end_date = {}
    for report in reports:
        end = _period_end(report)
        if end and _period_months(report) == months:
            by_end_date[end] = report
    return [by_end_date[end] for end in sorted(by_end_date)]


_BREAKDOWN_FIELDS = (
    "incomeStatementRevenueBreakdown", "incomeStatementExpenseAllocation",
    "balanceSheetAssetsComposition", "balanceSheetLiabilitiesEquity",
    "segmentRevenueBreakdown", "segmentProfitBreakdown",
    "geographicRevenueBreakdown", "geographicProfitBreakdown",
)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_subtotal(amount: float, previous_rows: list[dict]) -> bool:
    running = 0
    for count, row in enumerate(reversed(previous_rows), start=1):
        running += row["amount"]
        if count >= 2 and abs(running - amount) <= abs(amount) * 0.001:
            return True
    return False


def _line_items_only(rows) -> list:
    if not isinstance(rows, list):
        return rows
    items = []
    for row in rows:
        if not isinstance(row, dict) or not _is_number(row.get("amount")) or row["amount"] == 0:
            continue
        if _is_subtotal(row["amount"], items):
            continue
        items.append(row)
    return items


def _with_line_items_only(report: dict) -> dict:
    cleaned = dict(report)
    for field in _BREAKDOWN_FIELDS:
        if isinstance(report.get(field), list):
            cleaned[field] = _line_items_only(report[field])
    return cleaned


def _metric_series(reports: list[dict], field: str) -> list[dict]:
    result = []
    for report in reports:
        fact = _fact(report, field)
        if fact and isinstance(fact["value"], (int, float)) and not isinstance(fact["value"], bool):
            result.append({
                "period": _period(report),
                "value": fact["value"],
                "reportId": report.get("custom_id"),
                "citations": fact["citations"],
                "provenance": fact["provenance"],
            })
    return result


def _derived_change(field: str, series: list[dict]) -> dict | None:
    if len(series) < 2:
        return None
    prior, current = series[-2], series[-1]
    if prior["value"] == 0:
        return None
    change = ((current["value"] - prior["value"]) / abs(prior["value"])) * 100
    label = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", field).lower()
    formula = "(current period − prior period) / |prior period| × 100"
    inputs = [{"period": prior["period"], "value": prior["value"]}, {"period": current["period"], "value": current["value"]}]
    return {
        "kind": "calculated_metric", "field": f"{field}Change", "label": f"{label.title()} change",
        "value": round(change, 2), "unit": "%", "formula": formula,
        "basis": f"{current['period']} vs {prior['period']}",
        "inputs": inputs,
        "citations": prior["citations"] + current["citations"], "verificationStatus": "verified",
        "valueType": "calculated", "status": STATUS_CALCULATED,
        "calculation": {"formula": formula, "inputs": inputs},
        "provenance": prior.get("provenance", []) + current.get("provenance", []),
    }


def _norm_category(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name or "").lower()).strip()


def _breakdown_performance(report: dict, revenue_field: str, profit_field: str, out_field: str, row_key: str) -> dict | None:

    revenue_rows = report.get(revenue_field)
    if not isinstance(revenue_rows, list) or len(revenue_rows) < 2:
        return None
    citations = _citations_for(report, revenue_field)
    if not citations:
        return None

    profit_by_cat = {
        _norm_category(r.get("category")): r.get("amount")
        for r in (report.get(profit_field) or [])
        if isinstance(r, dict) and isinstance(r.get("amount"), (int, float)) and not isinstance(r.get("amount"), bool)
    }
    total_revenue = sum(
        r["amount"] for r in revenue_rows
        if isinstance(r, dict) and isinstance(r.get("amount"), (int, float)) and not isinstance(r.get("amount"), bool)
    )
    total_profit = sum(v for v in profit_by_cat.values()) if profit_by_cat else 0

    rows = []
    for r in revenue_rows:
        if not isinstance(r, dict) or not isinstance(r.get("amount"), (int, float)) or isinstance(r.get("amount"), bool):
            continue
        revenue = r["amount"]
        profit = profit_by_cat.get(_norm_category(r.get("category")))
        row = {
            row_key: str(r.get("category", "")),
            "revenue": revenue,
            "revenueGrowth": r["growth"] if isinstance(r.get("growth"), (int, float)) and not isinstance(r.get("growth"), bool) else None,
            "contributionToRevenuePercent": round(revenue / total_revenue * 100, 1) if total_revenue else None,
        }
        if profit is not None:
            row["operatingProfit"] = profit
            row["marginPercent"] = round(profit / revenue * 100, 1) if revenue else None
            row["contributionToProfitPercent"] = round(profit / total_profit * 100, 1) if total_profit else None
        rows.append(row)

    if not rows:
        return None
    return {
        "field": out_field,
        "value": rows,
        "kind": "calculated_metric",
        "valueType": "calculated",
        "status": STATUS_CALCULATED,
        "period": _period(report),
        "currency": report.get("currency") or "",
        "citations": citations,
        "provenance": [_source_object(c, report) for c in citations],
        "calculation": {
            "formula": "marginPercent = operatingProfit / revenue × 100; "
                       "contributionToRevenuePercent = unit revenue / Σ unit revenue × 100; "
                       "contributionToProfitPercent = unit profit / Σ unit profit × 100",
            "inputs": [revenue_field, profit_field],
        },
    }


def _notes_disclosures(report: dict) -> list[dict]:

    out = []


    legacy_policies = report.get("accountingPolicyNotes") or []
    for field_id, label in NOTE_DISCLOSURE_CATEGORIES.items():
        items = report.get(field_id) or []
        source_field = field_id
        if field_id == "accountingPolicies" and not items and legacy_policies:
            items, source_field = legacy_policies, "accountingPolicyNotes"
        items = [str(i).strip() for i in items if str(i).strip()]
        if not items:
            continue
        citations = _citations_for(report, source_field)
        if not citations:
            continue
        out.append({
            "field": field_id,
            "category": label,
            "items": items,
            "status": STATUS_VERIFIED,
            "period": _period(report),
            "citations": citations,
            "provenance": [_source_object(c, report) for c in citations],
        })
    return out


def build_dashboard(company: dict, reports: list[dict], scope: str = "company") -> dict:

    if scope not in {"company", "report"}:
        raise ValueError(f"Unsupported dashboard scope: {scope}")
    reports = sorted(reports, key=lambda r: (r.get("created_at") or "", str(r.get("custom_id") or "")))
    reports = _sort_by_period([_with_line_items_only(r) for r in reports])
    currency_counts = Counter((r.get("currency") or "").upper() for r in reports if r.get("currency"))
    currency = currency_counts.most_common(1)[0][0] if currency_counts else ""
    compatible = [r for r in reports if not currency or (r.get("currency") or "").upper() == currency]
    latest = compatible[-1] if compatible else (reports[-1] if reports else {})
    newest_first = list(reversed(compatible)) or ([reports[-1]] if reports else [])

    metrics = []
    for field in ("revenue", "ebitda", "netIncome", "freeCashFlow", "cashFlowOperations"):
        fact = _fact_with_fallback(newest_first, field)




        if fact and fact["value"] != 0:
            metrics.append({**fact, "label": re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", field)})

    charts, derived = [], []
    _CHART_FIELDS = ("revenue", "ebitda", "netIncome", "freeCashFlow")



    _CHANGE_FIELDS = (
        "revenue", "ebitda", "netIncome", "operatingProfit", "grossProfit",
        "freeCashFlow", "cashFlowOperations", "totalAssets", "totalEquity", "totalDebt",
    )
    comparable = _comparable_reports(compatible)
    for field in _CHANGE_FIELDS:
        series = _metric_series(comparable, field)
        if len(series) < 2:
            continue
        if field in _CHART_FIELDS:
            charts.append({"title": re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", field).title(), "field": field, "unit": currency, "data": series})
        change = _derived_change(field, series)
        if change:
            derived.append(change)










    facts = []
    for field in (
        "companyProfile", "businessOverviewSummary", "executiveSummary",
        "keyFindings", "strengths", "areasOfConcern", "keyObservations",
        "overallFinancialHealth", "liquidity", "solvency", "profitability", "riskAssessment",
        "financialRatios",
        "incomeStatementRevenueBreakdown", "incomeStatementExpenseAllocation",
        "balanceSheetAssetsComposition", "balanceSheetLiabilitiesEquity",
        "segmentRevenueBreakdown", "segmentProfitBreakdown", "geographicRevenueBreakdown",
        "managementOutlook", "outlookHighlights", "keyRisks", "materialEvents",
        "auditorName", "auditorOpinion", "goingConcernNote", "accountingPolicyNotes",
    ):
        fact = _fact_with_fallback(newest_first, field)
        if fact:
            facts.append(fact)

    calculated_ratios = _calculated_ratios(latest)
    if calculated_ratios:
        facts.append(calculated_ratios)



    segment_performance = _breakdown_performance(
        latest, "segmentRevenueBreakdown", "segmentProfitBreakdown", "segmentPerformance", "segment"
    )
    if segment_performance:
        facts.append(segment_performance)
    geographic_performance = _breakdown_performance(
        latest, "geographicRevenueBreakdown", "geographicProfitBreakdown", "geographicPerformance", "region"
    )
    if geographic_performance:
        facts.append(geographic_performance)

    notes_disclosures = _notes_disclosures(latest)

    insights = []
    for item in derived:
        if item["field"] == "revenueChange":
            direction = "increased" if item["value"] > 0 else "declined"
            insights.append({"kind": "inferred_conclusion", "title": f"Revenue {direction}", "statement": f"Revenue {direction} {abs(item['value']):.1f}% ({item['basis']}).", "why": "This conclusion is calculated from reported revenue values.", "citations": item["citations"], "verificationStatus": "verified"})
            if item["value"] < 0:
                insights.append({"kind": "recommendation", "title": "Investigate revenue pressure", "statement": "Monitor the drivers of the reported revenue decline and assess whether it is temporary or structural.", "why": "The recommendation follows the verified decline in reported revenue; it is not a reported management statement.", "citations": item["citations"], "verificationStatus": "verified"})




    for field in _MATERIAL_LISTS:
        fact = _fact(latest, field)
        if fact:
            facts.append(fact)

    field_statuses = _field_statuses(latest, facts, metrics, derived)





    conflicts = detect_field_conflicts(reports) if scope == "company" and len(reports) > 1 else {}
    for field, override in conflict_status_overrides(conflicts).items():
        field_statuses[field] = override
    if conflicts:
        _annotate_conflicts(metrics, facts, conflicts)



    from services.source_providers import SourceResolver, default_registry

    registry = default_registry()
    source_hierarchy = registry.hierarchy()
    external_sources = SourceResolver(registry).external_status()

    missing_expected = [
        {
            "field": field_id,
            "label": label,
            "message": f"{label} was not identified in the verified sources.",
        }
        for field_id, label in _NOTABLE_WHEN_MISSING.items()
        if field_statuses.get(field_id) == STATUS_UNAVAILABLE
    ]

    return {
        "scope": scope, "validationStatus": "valid", "generatedAt": datetime.now(timezone.utc).isoformat(),
        "builderVersion": BUILDER_VERSION,
        "company": {"id": company.get("id"), "name": company.get("name") or latest.get("companyName", "")},
        "currency": currency, "currencyMismatch": len(currency_counts) > 1,
        "reportingPeriod": _period(latest) if latest else "",
        "documentTypes": sorted({r.get("documentType", "") for r in reports if r.get("documentType")}),
        "sourceReports": [
            {
                "id": r.get("custom_id"),
                "filename": r.get("sourceFileName", "Uploaded report.pdf"),
                "period": _period(r),
                "currency": r.get("currency", ""),
                "documentType": r.get("documentType", ""),
            }
            for r in reports
        ],
        "metrics": metrics, "charts": charts, "derivedMetrics": derived,
        "facts": facts,
        "insights": insights,
        "notesDisclosures": notes_disclosures,
        "missingExpected": missing_expected,
        "fieldStatuses": field_statuses,
        "conflicts": list(conflicts.values()),
        "sourceHierarchy": source_hierarchy,
        "externalSources": external_sources,
    }


def current_or_fresh_company_dashboard(stored: dict | None, company: dict, reports: list[dict]) -> dict:

    if stored and stored.get("builderVersion") == BUILDER_VERSION:
        return stored
    return build_dashboard(company, reports)


def _annotate_conflicts(metrics: list[dict], facts: list[dict], conflicts: dict[str, dict]) -> None:

    for item in [*metrics, *facts]:
        record = conflicts.get(item.get("field"))
        if not record:
            continue
        if record["status"] == STATUS_CONFLICTING:
            item["status"] = STATUS_CONFLICTING
        item["conflict"] = {
            "status": record["status"],
            "candidates": record["candidates"],
            "chosen": record["chosen"],
            "resolutionReason": record["resolutionReason"],
            "spreadPercent": record["spreadPercent"],
        }


def _field_statuses(latest: dict, facts: list[dict], metrics: list[dict], derived: list[dict]) -> dict[str, str]:

    doc_type = latest.get("documentType") or ""



    produced = {
        c.get("field") for c in latest.get("citations") or []
        if isinstance(c, dict) and c.get("verificationStatus") == "verified"
        and latest.get(c.get("field")) not in (None, "", [], {}, 0)
    }
    produced |= {f["field"] for f in facts} | {m["field"] for m in metrics}
    calculated = {f["field"] for f in facts if f.get("valueType") == "calculated"}
    calculated |= {d["field"] for d in derived}
    review_fields = _consistency_review_fields(latest)
    expected = set(expected_fields_for(doc_type)) if doc_type else set()

    statuses: dict[str, str] = {}
    for field_id, meta in FIELD_REGISTRY.items():
        if doc_type and doc_type not in meta["expected_document_types"]:
            statuses[field_id] = STATUS_NOT_APPLICABLE
        elif field_id in review_fields and field_id in produced:
            statuses[field_id] = STATUS_NEEDS_REVIEW
        elif field_id in produced:
            statuses[field_id] = STATUS_VERIFIED
        elif field_id in expected:
            statuses[field_id] = STATUS_UNAVAILABLE
    for field_id in calculated:
        statuses[field_id] = STATUS_CALCULATED
    return statuses
