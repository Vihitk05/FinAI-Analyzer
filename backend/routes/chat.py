from flask import Blueprint, g, jsonify, request

import config
from services import chat_grounding, curation, db
from services.logging_config import get_logger, log_extra
from services.llm import LLMError, QuotaExhaustedError
from utils.auth_utils import login_required

logger = get_logger(__name__)
chat_bp = Blueprint("chat", __name__)


def _validate_query(payload: dict) -> tuple[str, str | None]:
    query = (payload.get("query") or "").strip()
    if not query:
        return "", "query is required"
    if len(query) > config.MAX_QUERY_LENGTH:
        return "", f"query must be at most {config.MAX_QUERY_LENGTH} characters"
    return query, None


def _format_response(result: dict, *, sources_prefix: str) -> dict:
    answer = result["answer"]
    pages = result["cited_pages"]
    if pages and not result["insufficient_context"]:
        answer = f"{answer}\n\n{sources_prefix} {', '.join(str(p) for p in pages)}"
    return {
        "message": "Query processed successfully",
        "response": answer,
        "cited_pages": pages,
        "insufficient_context": result["insufficient_context"],
        "missing_information": result["missing_information"],
        "claims": result["claims"],
        "grounded_in": result["groundedIn"],
        "corrected_for_unsupported_claims": result["correctedForUnsupportedClaims"],
    }


@chat_bp.route("/query/", methods=["POST"])
@login_required
def query_data():
    payload = request.get_json(silent=True) or {}
    query, error = _validate_query(payload)
    if error:
        return jsonify({"error": error}), 400

    company_public_id = payload.get("company_id")
    if company_public_id:
        return _company_query(query, company_public_id)

    raw_custom_id = payload.get("custom_id")
    if not raw_custom_id:
        return jsonify({"error": "custom_id or company_id is required"}), 400
    return _report_query(query, raw_custom_id)


def _report_query(query: str, raw_custom_id: str):
    try:
        report_id = db.resolve_report_id(raw_custom_id, g.user_id)
        report = db.get_report(report_id, g.user_id) if report_id is not None else None
        if report is None:
            return jsonify({"error": f"No document found with custom_id: {raw_custom_id}"}), 404
        if report.get("status") != "completed":
            return jsonify({"error": "This report is still being processed"}), 409

        dashboard = curation.build_dashboard(
            {"id": None, "name": report.get("companyName", "")}, [report], scope="report"
        )
    except db.DatabaseError as exc:
        return jsonify({"error": f"Database error: {exc}"}), 503

    try:
        result = chat_grounding.answer(query, report, dashboard, report_id)
    except QuotaExhaustedError as exc:
        logger.warning("chat_query_quota_exhausted", extra=log_extra(user_id=g.user_id, report_id=report_id))
        return jsonify({"error": str(exc)}), 503
    except LLMError as exc:
        logger.error("chat_query_failed", extra=log_extra(user_id=g.user_id, report_id=report_id, error=str(exc)))
        return jsonify({"error": "Failed to process query"}), 502

    return jsonify(_format_response(result, sources_prefix="Source pages:"))


def _company_query(query: str, company_public_id: str):
    try:
        company_id = db.resolve_company_id(company_public_id, g.user_id)
        company = db.get_company(company_id, g.user_id) if company_id is not None else None
        if company is None:
            return jsonify({"error": "Company dashboard not found"}), 404

        reports = db.list_company_reports(company_id, g.user_id)
        if not reports:
            return jsonify({"error": "No validated reports are available for this company"}), 404
        stored = db.get_current_company_dashboard(company_id, g.user_id)
        dashboard = curation.current_or_fresh_company_dashboard(stored, company, reports)
        report_ids = {row["custom_id"]: row["id"] for row in db.list_company_report_ids(company_id, g.user_id)}
    except db.DatabaseError as exc:
        return jsonify({"error": f"Database error: {exc}"}), 503

    try:
        result = chat_grounding.answer_company(query, dashboard, reports, report_ids)
    except QuotaExhaustedError as exc:
        logger.warning("company_chat_quota_exhausted", extra=log_extra(user_id=g.user_id, company_id=company_id))
        return jsonify({"error": str(exc)}), 503
    except LLMError as exc:
        logger.error("company_chat_failed", extra=log_extra(user_id=g.user_id, company_id=company_id, error=str(exc)))
        return jsonify({"error": "Failed to process query"}), 502

    return jsonify(_format_response(result, sources_prefix="Source pages:"))
