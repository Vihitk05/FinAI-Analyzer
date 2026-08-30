from __future__ import annotations





BROAD_DOC_TYPES = {"10-K", "20-F", "annual_report"}
MEDIUM_DOC_TYPES = {"10-Q", "quarterly_report", "earnings_release", "investor_presentation"}
NARROW_DOC_TYPES = {"financial_statements", "auditor_report", "other_financial_document"}
ALL_DOC_TYPES = BROAD_DOC_TYPES | MEDIUM_DOC_TYPES | NARROW_DOC_TYPES

CORE_STATEMENTS = ALL_DOC_TYPES
BROAD_ONLY = BROAD_DOC_TYPES
BROAD_AND_MEDIUM = BROAD_DOC_TYPES | MEDIUM_DOC_TYPES

REQUIRED = "required"
IMPORTANT = "important"
OPTIONAL = "optional"






SOURCE_PRIORITY_BY_DOC_TYPE = {
    "10-K": 1, "20-F": 1, "annual_report": 1, "financial_statements": 1, "auditor_report": 1,
    "10-Q": 2, "quarterly_report": 2,
    "earnings_release": 3,
    "investor_presentation": 5,
    "other_financial_document": 6,
}
DEFAULT_SOURCE_PRIORITY = 6




NOTE_DISCLOSURE_CATEGORIES: dict[str, str] = {
    "accountingPolicies": "Accounting Policies",
    "debtDisclosures": "Debt",
    "leaseDisclosures": "Leases",
    "pensionDisclosures": "Pensions & Post-employment Benefits",
    "taxDisclosures": "Tax",
    "stockCompensationDisclosures": "Share-based Compensation",
    "relatedPartyDisclosures": "Related-party Transactions",
    "contingentLiabilityDisclosures": "Contingent Liabilities",
    "commitmentDisclosures": "Commitments",
    "acquisitionDisclosures": "Acquisitions & Divestitures",
    "impairmentDisclosures": "Impairments",
    "restructuringDisclosures": "Restructuring",
    "shareCapitalDisclosures": "Share Capital",
    "treasuryShareDisclosures": "Treasury Shares",
    "dividendDisclosures": "Dividends",
    "subsidiaryDisclosures": "Subsidiaries & Group Structure",
    "otherMaterialDisclosures": "Other Material Disclosures",
}




FIELD_REGISTRY: dict[str, dict] = {

    "companyName": {"display_name": "Company", "category": "Overview", "data_type": "string", "required_level": REQUIRED, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "company name"},
    "reportingPeriod": {"display_name": "Reporting Period", "category": "Overview", "data_type": "string", "required_level": REQUIRED, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "reporting period fiscal year"},
    "currency": {"display_name": "Currency", "category": "Overview", "data_type": "string", "required_level": REQUIRED, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "reporting currency"},


    "revenue": {"display_name": "Revenue", "category": "Financial Performance", "data_type": "currency", "required_level": REQUIRED, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "total revenue net sales"},
    "costOfRevenue": {"display_name": "Cost of Revenue", "category": "Financial Performance", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "cost of revenue cost of sales cost of goods sold"},
    "grossProfit": {"display_name": "Gross Profit", "category": "Financial Performance", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "gross profit gross margin"},
    "operatingProfit": {"display_name": "Operating Profit", "category": "Financial Performance", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "operating profit operating income EBIT"},
    "ebitda": {"display_name": "EBITDA", "category": "Financial Performance", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "EBITDA"},
    "interestExpense": {"display_name": "Interest Expense", "category": "Financial Performance", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "interest expense finance costs"},
    "profitBeforeTax": {"display_name": "Profit Before Tax", "category": "Financial Performance", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "profit before tax"},
    "taxExpense": {"display_name": "Tax Expense", "category": "Financial Performance", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "income tax expense"},
    "netIncome": {"display_name": "Net Income", "category": "Financial Performance", "data_type": "currency", "required_level": REQUIRED, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "net income net profit"},
    "eps": {"display_name": "EPS", "category": "Financial Performance", "data_type": "ratio", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "earnings per share basic EPS"},
    "dilutedEps": {"display_name": "Diluted EPS", "category": "Financial Performance", "data_type": "ratio", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "diluted earnings per share"},


    "totalAssets": {"display_name": "Total Assets", "category": "Financial Position", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "total assets"},
    "totalLiabilities": {"display_name": "Total Liabilities", "category": "Financial Position", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "total liabilities"},
    "totalEquity": {"display_name": "Total Equity", "category": "Financial Position", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "total equity shareholders equity"},
    "currentAssets": {"display_name": "Current Assets", "category": "Financial Position", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "current assets"},
    "currentLiabilities": {"display_name": "Current Liabilities", "category": "Financial Position", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "current liabilities"},
    "cashAndEquivalents": {"display_name": "Cash & Equivalents", "category": "Financial Position", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "cash and cash equivalents"},
    "totalDebt": {"display_name": "Total Debt", "category": "Financial Position", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "total debt total borrowings"},


    "cashFlowOperations": {"display_name": "Operating Cash Flow", "category": "Cash Flow", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "cash flow from operating activities"},
    "cashFlowInvesting": {"display_name": "Investing Cash Flow", "category": "Cash Flow", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "cash flow from investing activities"},
    "cashFlowFinancing": {"display_name": "Financing Cash Flow", "category": "Cash Flow", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "cash flow from financing activities"},
    "freeCashFlow": {"display_name": "Free Cash Flow", "category": "Cash Flow", "data_type": "currency", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "free cash flow"},
    "capitalExpenditure": {"display_name": "Capital Expenditure", "category": "Cash Flow", "data_type": "currency", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "capital expenditure capex"},


    "segmentRevenueBreakdown": {"display_name": "Segment Revenue", "category": "Segment Performance", "data_type": "breakdown", "required_level": OPTIONAL, "expected_document_types": BROAD_ONLY, "retrieval_hint": "segment revenue by business segment"},
    "geographicRevenueBreakdown": {"display_name": "Geographic Revenue", "category": "Geographic Performance", "data_type": "breakdown", "required_level": OPTIONAL, "expected_document_types": BROAD_ONLY, "retrieval_hint": "geographic revenue by region"},


    "executiveSummary": {"display_name": "Executive Summary", "category": "Summary", "data_type": "narrative", "required_level": REQUIRED, "expected_document_types": CORE_STATEMENTS, "retrieval_hint": "executive summary business overview"},
    "overallFinancialHealth": {"display_name": "Overall Financial Health", "category": "Summary", "data_type": "rating", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "financial health assessment"},
    "riskAssessment": {"display_name": "Risk Assessment", "category": "Risks", "data_type": "rating", "required_level": IMPORTANT, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "risk assessment"},
    "keyRisks": {"display_name": "Key Risks", "category": "Risks", "data_type": "list", "required_level": IMPORTANT, "expected_document_types": BROAD_ONLY, "retrieval_hint": "principal risks risk factors"},
    "materialEvents": {"display_name": "Material Events", "category": "Risks", "data_type": "list", "required_level": OPTIONAL, "expected_document_types": BROAD_ONLY, "retrieval_hint": "material events litigation restructuring"},


    "managementOutlook": {"display_name": "Management Outlook", "category": "Outlook", "data_type": "narrative", "required_level": OPTIONAL, "expected_document_types": BROAD_AND_MEDIUM, "retrieval_hint": "management outlook guidance forward-looking"},


    "auditorOpinion": {"display_name": "Auditor Opinion", "category": "Auditor & Accounting", "data_type": "rating", "required_level": OPTIONAL, "expected_document_types": BROAD_ONLY, "retrieval_hint": "independent auditor's report opinion"},
}


_NOTE_RETRIEVAL_HINTS = {
    "accountingPolicies": "significant accounting policies basis of preparation",
    "debtDisclosures": "borrowings loans notes payable debt maturity interest rate covenants",
    "leaseDisclosures": "lease liabilities right-of-use assets operating finance leases",
    "pensionDisclosures": "defined benefit pension post-employment obligations actuarial",
    "taxDisclosures": "income tax deferred tax reconciliation effective tax rate",
    "stockCompensationDisclosures": "share-based payment stock options RSU expense",
    "relatedPartyDisclosures": "related party transactions key management personnel",
    "contingentLiabilityDisclosures": "contingent liabilities litigation claims guarantees",
    "commitmentDisclosures": "capital commitments purchase obligations contractual commitments",
    "acquisitionDisclosures": "business combination acquisition purchase price allocation goodwill",
    "impairmentDisclosures": "impairment loss goodwill write-down recoverable amount",
    "restructuringDisclosures": "restructuring provision severance exit costs",
    "shareCapitalDisclosures": "share capital authorised issued shares par value",
    "treasuryShareDisclosures": "treasury shares buyback repurchase of own shares",
    "dividendDisclosures": "dividends declared paid per share dividend policy",
    "subsidiaryDisclosures": "subsidiaries consolidated entities group structure ownership",
    "otherMaterialDisclosures": "subsequent events other notes to the financial statements",
}
for _fid, _label in NOTE_DISCLOSURE_CATEGORIES.items():
    FIELD_REGISTRY[_fid] = {
        "display_name": _label,
        "category": "Notes & Disclosures",
        "data_type": "list",
        "required_level": OPTIONAL,
        "expected_document_types": BROAD_ONLY,
        "retrieval_hint": _NOTE_RETRIEVAL_HINTS[_fid],
    }


def expected_fields_for(document_type: str, min_level: str = OPTIONAL) -> list[str]:

    levels = {REQUIRED: 3, IMPORTANT: 2, OPTIONAL: 1}
    threshold = levels[min_level]
    return [
        field_id
        for field_id, meta in FIELD_REGISTRY.items()
        if document_type in meta["expected_document_types"] and levels[meta["required_level"]] >= threshold
    ]


def registry_entry(field_id: str) -> dict | None:
    return FIELD_REGISTRY.get(field_id)
