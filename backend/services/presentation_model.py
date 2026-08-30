from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Section:
    id: str
    kind: str
    title: str
    body: dict = field(default_factory=dict)
    source_refs: list[dict] = field(default_factory=list)
    dashboard_keys: tuple[str, ...] = ()


@dataclass
class PresentationModel:
    company: str
    period: str
    currency: str
    sections: list[Section]

    @property
    def slide_count(self) -> int:
        return len(self.sections)


def _label(field_id: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(field_id or "")).strip().title()


def _fact(data: dict, field_id: str) -> dict | None:
    return next((f for f in data.get("facts", []) if f.get("field") == field_id), None)


def _refs(*items: dict) -> list[dict]:
    seen, out = set(), []
    for item in items:
        for c in (item or {}).get("citations", []) or []:
            key = (c.get("filename"), c.get("page"))
            if key not in seen:
                seen.add(key)
                out.append({"document": c.get("filename", "Uploaded report"), "page": c.get("page"), "section": c.get("description", "")})
    return out


def _text_fact_paragraphs(data: dict, fields: tuple[str, ...]) -> tuple[list, list]:
    parts, facts = [], []
    for field_id in fields:
        fact = _fact(data, field_id)
        if fact and fact.get("value"):
            value = fact["value"]
            parts.append(value if isinstance(value, list) else [value] if not isinstance(value, str) else value)
            facts.append(fact)
    flat = []
    for p in parts:
        flat.extend(p) if isinstance(p, list) else flat.append(p)
    return [x for x in flat if x], facts


def build_presentation_model(data: dict) -> PresentationModel:
    company = (data.get("company") or {}).get("name") or "Company"
    currency = data.get("currency", "")
    period = data.get("reportingPeriod") or (data.get("sourceReports") or [{}])[0].get("period", "")
    sections: list[Section] = []

    def add(section: Section):
        sections.append(section)

    add(Section("title", "title", company, body={"period": period}, dashboard_keys=("company",)))

    summary_parts, summary_facts = _text_fact_paragraphs(data, ("executiveSummary", "businessOverviewSummary", "companyProfile"))
    if summary_parts:
        add(Section("summary", "summary", "Financial Summary", body={"paragraphs": summary_parts},
                    source_refs=_refs(*summary_facts), dashboard_keys=("executiveSummary", "businessOverviewSummary", "companyProfile")))

    if data.get("sourceReports"):
        add(Section("documents", "documents", "Documents Analyzed", body={
            "reports": data["sourceReports"], "period": period,
            "documentTypes": data.get("documentTypes", []),
        }, dashboard_keys=("sourceReports", "reportingPeriod")))

    if data.get("metrics"):
        add(Section("kpi", "kpi", "Key Financial Performance", body={"metrics": data["metrics"], "currency": currency},
                    source_refs=_refs(*data["metrics"]), dashboard_keys=("metrics",)))

    rating_fields = ("overallFinancialHealth", "liquidity", "solvency", "profitability", "riskAssessment")
    rating_facts = [_fact(data, f) for f in rating_fields]
    rating_rows = [[_label(f), fact["value"]] for f, fact in zip(rating_fields, rating_facts) if fact and fact.get("value")]
    if rating_rows:
        add(Section("health", "table", "Financial Health Assessment", body={"columns": ["Assessment", "Rating"], "rows": rating_rows},
                    source_refs=_refs(*[x for x in rating_facts if x]),
                    dashboard_keys=tuple(f for f, fact in zip(rating_fields, rating_facts) if fact and fact.get("value"))))

    for chart in data.get("charts", []) or []:
        add(Section(f"chart:{chart.get('field')}", "line_chart", f"{chart.get('title', 'Trend')} - Trend", body={
            "series": chart.get("data", []), "currency": currency, "unit": chart.get("unit", currency),
        }, source_refs=_refs(*(chart.get("data") or [])), dashboard_keys=("charts",)))

    if data.get("derivedMetrics"):
        add(Section("derived", "table", "Period-over-Period Changes", body={
            "columns": ["Metric", "Change", "Basis"],
            "rows": [[m.get("label", _label(m.get("field"))), f"{m.get('value')}{m.get('unit', '')}", m.get("formula", "")]
                     for m in data["derivedMetrics"]],
        }, source_refs=_refs(*data["derivedMetrics"]), dashboard_keys=("derivedMetrics",)))

    rev_break = _fact(data, "incomeStatementRevenueBreakdown")
    exp_break = _fact(data, "incomeStatementExpenseAllocation")
    pies = [(f["field"], "Revenue" if "Revenue" in f["field"] else "Expenses", f["value"], f)
            for f in (rev_break, exp_break) if f and f.get("value")]
    if pies:
        add(Section("income_composition", "pie", "Income Statement Detail", body={
            "breakdowns": [{"subtitle": name, "rows": rows} for _, name, rows, _ in pies], "currency": currency,
        }, source_refs=_refs(*[f for *_, f in pies]), dashboard_keys=tuple(k for k, *_ in pies)))

    assets = _fact(data, "balanceSheetAssetsComposition")
    liabs = _fact(data, "balanceSheetLiabilitiesEquity")
    bs = [(f["field"], name, f["value"], f) for f, name in ((assets, "Assets"), (liabs, "Liabilities & Equity")) if f and f.get("value")]
    if bs:
        add(Section("balance_sheet", "pie", "Balance Sheet / Financial Position", body={
            "breakdowns": [{"subtitle": name, "rows": rows} for _, name, rows, _ in bs], "currency": currency,
        }, source_refs=_refs(*[f for *_, f in bs]), dashboard_keys=tuple(k for k, *_ in bs)))

    cash_metrics = [m for m in data.get("metrics", []) if m.get("field") in {"freeCashFlow", "cashFlowOperations"}]
    if cash_metrics:
        add(Section("cash_flow", "kpi", "Cash & Liquidity", body={"metrics": cash_metrics, "currency": currency},
                    source_refs=_refs(*cash_metrics), dashboard_keys=("metrics",)))

    ratio_rows, ratio_facts = [], []
    for field_id in ("calculatedRatios", "financialRatios"):
        fact = _fact(data, field_id)
        if fact and fact.get("value"):
            ratio_rows.extend(fact["value"])
            ratio_facts.append(fact)
    if ratio_rows:
        add(Section("ratios", "ratios", "Financial Ratios & KPIs", body={"rows": ratio_rows},
                    source_refs=_refs(*ratio_facts), dashboard_keys=("calculatedRatios", "financialRatios")))

    seg = _fact(data, "segmentPerformance")
    if seg and seg.get("value"):
        add(Section("segment", "table", "Segment Performance", body=_perf_table(seg["value"], "segment", currency),
                    source_refs=_refs(seg), dashboard_keys=("segmentPerformance", "segmentRevenueBreakdown")))
    elif _fact(data, "segmentRevenueBreakdown"):
        f = _fact(data, "segmentRevenueBreakdown")
        add(Section("segment", "pie", "Segment Revenue", body={"breakdowns": [{"subtitle": "Segment Revenue", "rows": f["value"]}], "currency": currency},
                    source_refs=_refs(f), dashboard_keys=("segmentRevenueBreakdown",)))

    geo = _fact(data, "geographicPerformance")
    if geo and geo.get("value"):
        add(Section("geographic", "table", "Geographic Performance", body=_perf_table(geo["value"], "region", currency),
                    source_refs=_refs(geo), dashboard_keys=("geographicPerformance", "geographicRevenueBreakdown")))
    elif _fact(data, "geographicRevenueBreakdown"):
        f = _fact(data, "geographicRevenueBreakdown")
        add(Section("geographic", "pie", "Geographic Revenue", body={"breakdowns": [{"subtitle": "Geographic Revenue", "rows": f["value"]}], "currency": currency},
                    source_refs=_refs(f), dashboard_keys=("geographicRevenueBreakdown",)))

    commentary_parts, commentary_facts = _text_fact_paragraphs(data, ("keyFindings", "strengths", "areasOfConcern", "keyObservations"))
    if commentary_parts:
        add(Section("commentary", "narrative", "Management Commentary", body={"bullets": commentary_parts},
                    source_refs=_refs(*commentary_facts), dashboard_keys=("keyFindings", "strengths", "areasOfConcern", "keyObservations")))

    outlook_parts, outlook_facts = _text_fact_paragraphs(data, ("managementOutlook", "outlookHighlights"))
    if outlook_parts:
        add(Section("outlook", "narrative", "Outlook & Guidance", body={"bullets": outlook_parts},
                    source_refs=_refs(*outlook_facts), dashboard_keys=("managementOutlook", "outlookHighlights")))

    risk_parts, risk_facts = _text_fact_paragraphs(data, ("keyRisks", "materialEvents", "riskAssessment"))
    if risk_parts:
        add(Section("risks", "narrative", "Risks & Material Events", body={"bullets": risk_parts, "accent": "risk"},
                    source_refs=_refs(*risk_facts), dashboard_keys=("keyRisks", "materialEvents", "riskAssessment")))

    auditor_fields = ("auditorName", "auditorOpinion", "goingConcernNote", "accountingPolicyNotes")
    auditor_parts, auditor_facts = _text_fact_paragraphs(data, auditor_fields)
    if auditor_parts:
        add(Section("auditor", "narrative", "Auditor & Accounting Matters", body={"bullets": auditor_parts},
                    source_refs=_refs(*auditor_facts), dashboard_keys=auditor_fields))

    notes = data.get("notesDisclosures") or []
    for chunk_index, chunk in enumerate(_chunk(notes, 3)):
        suffix = f" ({chunk_index + 1})" if len(notes) > 3 else ""
        add(Section(f"notes:{chunk_index}", "notes", f"Notes & Disclosures{suffix}", body={"notes": chunk},
                    source_refs=_refs(*chunk), dashboard_keys=("notesDisclosures",)))

    unresolved = [c for c in (data.get("conflicts") or []) if c.get("status") == "conflicting"]
    missing = data.get("missingExpected") or []
    if unresolved or missing:
        add(Section("data_status", "data_status", "Data Status & Source Conflicts", body={
            "conflicts": unresolved, "missing": missing,
        }, dashboard_keys=("conflicts", "missingExpected")))

    if data.get("insights"):
        add(Section("takeaways", "narrative", "Key Takeaways", body={
            "bullets": [f"{i.get('title')}: {i.get('statement')}" for i in data["insights"]],
        }, source_refs=_refs(*data["insights"]), dashboard_keys=("insights",)))

    if data.get("sourceReports"):
        add(Section("sources", "sources", "Sources", body={
            "reports": data["sourceReports"], "hierarchy": data.get("sourceHierarchy", []),
            "external": data.get("externalSources", {}),
        }, dashboard_keys=("sourceReports", "sourceHierarchy")))

    return PresentationModel(company=company, period=period, currency=currency, sections=sections)


def _perf_table(rows: list[dict], unit_key: str, currency: str) -> dict:
    has_profit = any("operatingProfit" in r for r in rows)
    columns = [unit_key.title(), "Revenue", "Growth", "% of Rev."]
    if has_profit:
        columns += ["Op. Profit", "Margin", "% of Profit"]

    def fmt_money(v):
        return "-" if v is None else f"{v:,.0f}"

    def fmt_pct(v):
        return "-" if v is None else f"{v:.1f}%"

    out_rows = []
    for r in rows:
        row = [str(r.get(unit_key, "")), fmt_money(r.get("revenue")),
               fmt_pct(r.get("revenueGrowth")), fmt_pct(r.get("contributionToRevenuePercent"))]
        if has_profit:
            row += [fmt_money(r.get("operatingProfit")), fmt_pct(r.get("marginPercent")), fmt_pct(r.get("contributionToProfitPercent"))]
        out_rows.append(row)
    return {"columns": columns, "rows": out_rows, "currency": currency}


def _chunk(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)] or []
