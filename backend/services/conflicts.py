from __future__ import annotations

import re



from services.field_registry import DEFAULT_SOURCE_PRIORITY as _DEFAULT_SOURCE_PRIORITY
from services.field_registry import SOURCE_PRIORITY_BY_DOC_TYPE as _SOURCE_PRIORITY_BY_DOC_TYPE

STATUS_CONFLICTING = "conflicting"
STATUS_RESOLVED = "resolved"





DEFAULT_CONFLICT_FIELDS = (
    "revenue", "costOfRevenue", "grossProfit", "operatingProfit", "ebitda",
    "interestExpense", "profitBeforeTax", "taxExpense", "netIncome",
    "eps", "dilutedEps",
    "totalAssets", "totalLiabilities", "totalEquity", "currentAssets",
    "currentLiabilities", "cashAndEquivalents", "totalDebt",
    "cashFlowOperations", "cashFlowInvesting", "cashFlowFinancing",
    "freeCashFlow", "capitalExpenditure",
)

_WS_RE = re.compile(r"[\s,._/-]+")
_DEFAULT_ROUNDING_TOLERANCE_PCT = 1.0


def _normalise_period(value) -> str:
    return _WS_RE.sub(" ", str(value or "").strip().lower())


def _source_priority(report: dict) -> int:
    return _SOURCE_PRIORITY_BY_DOC_TYPE.get(report.get("documentType") or "", _DEFAULT_SOURCE_PRIORITY)


def _has_verified_value(report: dict, field: str):
    value = report.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value == 0:
        return None
    verified = any(
        isinstance(c, dict) and c.get("field") == field and c.get("verificationStatus") == "verified"
        for c in report.get("citations") or []
    )
    return value if verified else None


def _relative_spread(values: list[float]) -> float:
    lo, hi = min(values), max(values)
    denom = max(abs(hi), abs(lo), 1e-9)
    return abs(hi - lo) / denom * 100.0


def _candidate(report: dict, field: str, value: float) -> dict:
    return {
        "field": field,
        "value": value,
        "period": str(report.get("reportingPeriod") or report.get("analysis_date") or "Undated report"),
        "currency": (report.get("currency") or "").upper(),
        "scale": report.get("sourceReportingScale", "actual"),
        "reportId": report.get("custom_id"),
        "document": report.get("sourceFileName", "Uploaded report.pdf"),
        "documentType": report.get("documentType") or "",
        "sourcePriority": _source_priority(report),
    }


def _resolve(candidates: list[dict]) -> tuple[str, dict | None, str]:

    best_priority = min(c["sourcePriority"] for c in candidates)
    top = [c for c in candidates if c["sourcePriority"] == best_priority]
    if len(top) == 1:
        others = sorted({c["documentType"] or "an equal-or-lower-authority source" for c in candidates if c is not top[0]})
        reason = (
            f"Selected the value from the higher-authority source "
            f"({top[0]['documentType'] or 'uploaded document'}, priority {best_priority}); "
            f"retained the differing value(s) from {', '.join(others)} as conflicting evidence."
        )
        return STATUS_RESOLVED, top[0], reason
    return STATUS_CONFLICTING, None, (
        f"{len(top)} sources of equal authority (priority {best_priority}) report different values "
        f"for the same period; no single source is authoritative."
    )


def detect_field_conflicts(
    reports: list[dict],
    fields: tuple[str, ...] | None = None,
    *,
    rounding_tolerance_pct: float = _DEFAULT_ROUNDING_TOLERANCE_PCT,
) -> dict[str, dict]:

    fields = fields or DEFAULT_CONFLICT_FIELDS
    conflicts: dict[str, dict] = {}

    for field in fields:
        groups: dict[tuple, list[dict]] = {}
        for report in reports:
            value = _has_verified_value(report, field)
            if value is None:
                continue
            candidate = _candidate(report, field, value)
            key = (_normalise_period(candidate["period"]), candidate["currency"], candidate["scale"])
            groups.setdefault(key, []).append(candidate)

        for (period, currency, scale), candidates in groups.items():
            distinct = {round(c["value"], 4) for c in candidates}
            if len(candidates) < 2 or len(distinct) < 2:
                continue
            if _relative_spread([c["value"] for c in candidates]) <= rounding_tolerance_pct:
                continue

            status, chosen, reason = _resolve(candidates)
            conflicts[field] = {
                "field": field,
                "status": status,
                "comparabilityKey": {"period": period, "currency": currency, "scale": scale},
                "candidates": sorted(candidates, key=lambda c: c["sourcePriority"]),
                "chosen": chosen,
                "resolutionReason": reason,
                "spreadPercent": round(_relative_spread([c["value"] for c in candidates]), 2),
            }
            break

    return conflicts


def conflict_status_overrides(conflicts: dict[str, dict]) -> dict[str, str]:

    return {field: "conflicting" for field, record in conflicts.items() if record["status"] == STATUS_CONFLICTING}
