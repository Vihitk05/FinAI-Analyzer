from __future__ import annotations

PASS = "pass"
FAIL = "fail"
SKIPPED = "skipped"

_DEFAULT_TOLERANCE_PCT = 2.0


def _present(*values) -> bool:
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and v != 0 for v in values)


def _check(name: str, formula: str, expected: float, actual: float, tolerance_pct: float = _DEFAULT_TOLERANCE_PCT) -> dict:
    denominator = max(abs(expected), 1)
    diff_pct = round(100 * abs(expected - actual) / denominator, 2)
    return {
        "check": name,
        "formula": formula,
        "expected": round(expected, 2),
        "actual": round(actual, 2),
        "differencePercent": diff_pct,
        "status": PASS if diff_pct <= tolerance_pct else FAIL,
    }


def _skip(name: str, formula: str, reason: str) -> dict:
    return {"check": name, "formula": formula, "status": SKIPPED, "reason": reason}


def run_consistency_checks(report: dict) -> list[dict]:
    results = []


    assets, liabilities, equity = report.get("totalAssets", 0), report.get("totalLiabilities", 0), report.get("totalEquity", 0)
    if _present(assets, liabilities, equity):
        results.append(_check("balance_sheet_identity", "Total Assets = Total Liabilities + Total Equity", assets, liabilities + equity))
    else:
        results.append(_skip("balance_sheet_identity", "Total Assets = Total Liabilities + Total Equity", "one or more of totalAssets/totalLiabilities/totalEquity was not extracted"))


    opening, closing = report.get("openingCash", 0), report.get("closingCash", 0)
    ocf, icf, fcf_financing = report.get("cashFlowOperations", 0), report.get("cashFlowInvesting", 0), report.get("cashFlowFinancing", 0)
    fx = report.get("fxEffectOnCash", 0)
    if _present(opening, closing) and (ocf or icf or fcf_financing):
        results.append(_check("cash_flow_rollforward", "Opening Cash + Operating CF + Investing CF + Financing CF + FX = Closing Cash", closing, opening + ocf + icf + fcf_financing + fx))
    else:
        results.append(_skip("cash_flow_rollforward", "Opening Cash + Operating CF + Investing CF + Financing CF + FX = Closing Cash", "opening/closing cash was not extracted"))


    revenue, cost_of_revenue, gross_profit = report.get("revenue", 0), report.get("costOfRevenue", 0), report.get("grossProfit", 0)
    if _present(revenue, cost_of_revenue, gross_profit):
        results.append(_check("gross_profit", "Revenue - Cost of Revenue = Gross Profit", gross_profit, revenue - cost_of_revenue))
    else:
        results.append(_skip("gross_profit", "Revenue - Cost of Revenue = Gross Profit", "one or more of revenue/costOfRevenue/grossProfit was not extracted"))

    return results


def has_material_failure(checks: list[dict]) -> bool:
    return any(c["status"] == FAIL for c in checks)
