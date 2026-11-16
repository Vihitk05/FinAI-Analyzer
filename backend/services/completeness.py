from __future__ import annotations

from services.field_registry import FIELD_REGISTRY, expected_fields_for

NOT_FOUND = "not_found_in_document"
VERIFIED = "verified"
NOT_APPLICABLE = "not_applicable"


def _has_verified_citation(report: dict, field: str) -> bool:
    return any(
        isinstance(c, dict) and c.get("field") == field and c.get("verificationStatus") == "verified"
        for c in (report.get("citations") or [])
    )


def _is_present(value) -> bool:
    return value not in (None, "", [], {}, 0)


def evaluate_completeness(report: dict, document_type: str) -> dict:

    field_statuses: dict[str, str] = {}
    for field_id, meta in FIELD_REGISTRY.items():
        if document_type not in meta["expected_document_types"]:
            field_statuses[field_id] = NOT_APPLICABLE
            continue
        present = _is_present(report.get(field_id))
        verified = present and _has_verified_citation(report, field_id)
        field_statuses[field_id] = VERIFIED if verified else NOT_FOUND

    expected = expected_fields_for(document_type)
    required = expected_fields_for(document_type, min_level="required")
    verified_fields = [f for f in expected if field_statuses[f] == VERIFIED]
    missing_required = [f for f in required if field_statuses[f] != VERIFIED]

    citation_coverage = round(100 * len(verified_fields) / len(expected), 1) if expected else 100.0

    return {
        "documentType": document_type,
        "expectedFieldCount": len(expected),
        "verifiedFieldCount": len(verified_fields),
        "citationCoveragePercent": citation_coverage,
        "missingRequiredFields": missing_required,
        "fieldStatuses": field_statuses,
    }


def missing_fields_worth_reevaluating(completeness: dict, limit: int = 8) -> list[str]:

    candidates = [
        field for field in completeness["fieldStatuses"]
        if completeness["fieldStatuses"][field] == NOT_FOUND
        and FIELD_REGISTRY[field]["required_level"] in {"required", "important"}
    ]
    return candidates[:limit]
