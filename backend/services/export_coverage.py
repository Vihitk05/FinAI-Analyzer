from __future__ import annotations

from services.presentation_model import PresentationModel

_SUBSTANTIVE_DASHBOARD_KEYS = {
    "metrics", "charts", "derivedMetrics", "insights", "notesDisclosures",
    "conflicts", "missingExpected", "sourceReports",
}
_SUBSTANTIVE_FACT_FIELDS = {
    "executiveSummary", "businessOverviewSummary", "companyProfile",
    "keyFindings", "strengths", "areasOfConcern", "keyObservations",
    "overallFinancialHealth", "liquidity", "solvency", "profitability", "riskAssessment",
    "financialRatios", "calculatedRatios",
    "incomeStatementRevenueBreakdown", "incomeStatementExpenseAllocation",
    "balanceSheetAssetsComposition", "balanceSheetLiabilitiesEquity",
    "segmentPerformance", "segmentRevenueBreakdown", "geographicPerformance", "geographicRevenueBreakdown",
    "managementOutlook", "outlookHighlights", "keyRisks", "materialEvents",
    "auditorName", "auditorOpinion", "goingConcernNote", "accountingPolicyNotes",
}


def dashboard_inventory(data: dict) -> dict:

    keys = {k for k in _SUBSTANTIVE_DASHBOARD_KEYS if data.get(k)}
    fact_fields = {
        f.get("field") for f in data.get("facts", [])
        if f.get("field") in _SUBSTANTIVE_FACT_FIELDS and f.get("value") not in (None, "", [], {})
    }
    charts = {f"chart:{c.get('field')}" for c in data.get("charts", []) or []}
    tables = set()
    if any(f.get("field") == "segmentPerformance" for f in data.get("facts", [])):
        tables.add("segmentPerformance")
    if any(f.get("field") == "geographicPerformance" for f in data.get("facts", [])):
        tables.add("geographicPerformance")
    if data.get("derivedMetrics"):
        tables.add("derivedMetrics")
    return {"keys": keys, "factFields": fact_fields, "charts": charts, "tables": tables}


def presentation_inventory(model: PresentationModel) -> dict:
    covered_keys: set[str] = set()
    for section in model.sections:
        covered_keys.update(section.dashboard_keys)
    charts = {s.id for s in model.sections if s.kind == "line_chart"}
    tables = {s.id for s in model.sections if s.kind == "table"}
    return {"keys": covered_keys, "charts": charts, "tables": tables}


def check_coverage(data: dict, model: PresentationModel) -> dict:
    dash = dashboard_inventory(data)
    pres = presentation_inventory(model)

    want_keys = dash["keys"] | dash["factFields"]
    missing_keys = sorted(want_keys - pres["keys"])
    missing_charts = sorted(dash["charts"] - pres["charts"])
    covered_table_intent = {
        "derivedMetrics" if "derived" in {s.id for s in model.sections} else None,
        "segmentPerformance" if any(s.id == "segment" for s in model.sections) else None,
        "geographicPerformance" if any(s.id == "geographic" for s in model.sections) else None,
    }
    missing_tables = sorted(dash["tables"] - {t for t in covered_table_intent if t})

    ok = not (missing_keys or missing_charts or missing_tables)
    return {
        "ok": ok,
        "missingKeys": missing_keys,
        "missingCharts": missing_charts,
        "missingTables": missing_tables,
        "counts": {
            "dashboardSections": len(want_keys),
            "coveredSections": len(want_keys) - len(missing_keys),
            "dashboardCharts": len(dash["charts"]),
            "coveredCharts": len(dash["charts"]) - len(missing_charts),
            "presentationSlides": model.slide_count,
        },
    }


def coverage_failure_message(coverage: dict) -> str:
    bits = []
    if coverage["missingKeys"]:
        bits.append("sections: " + ", ".join(coverage["missingKeys"]))
    if coverage["missingCharts"]:
        bits.append("charts: " + ", ".join(coverage["missingCharts"]))
    if coverage["missingTables"]:
        bits.append("tables: " + ", ".join(coverage["missingTables"]))
    return "Presentation is missing dashboard content -> " + "; ".join(bits)
