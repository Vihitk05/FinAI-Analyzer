from flask import Blueprint, g, jsonify, request

from services import db
from utils.auth_utils import login_required

reports_bp = Blueprint("reports", __name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _parse_int(value, default, minimum=None, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


@reports_bp.route("/fetch_data/<report_public_id>", methods=["GET"])
@login_required
def fetch_data(report_public_id):
    report_id = db.resolve_report_id(report_public_id, g.user_id)
    document = db.get_report(report_id, g.user_id) if report_id is not None else None
    if not document:
        return jsonify({"error": f"No document found with custom_id: {report_public_id}"}), 404
    return jsonify({"message": "Data fetched successfully", "data": document})


@reports_bp.route("/fetch_data/<report_public_id>", methods=["DELETE"])
@login_required
def delete_report(report_public_id):
    report_id = db.resolve_report_id(report_public_id, g.user_id)
    deleted = db.delete_report(report_id, g.user_id) if report_id is not None else False
    if not deleted:
        return jsonify({"error": f"No document found with custom_id: {report_public_id}"}), 404
    return jsonify({"success": True})


@reports_bp.route("/api/reports/<report_public_id>/diagnostics", methods=["GET"])
@login_required
def report_diagnostics(report_public_id):
    report_id = db.resolve_report_id(report_public_id, g.user_id)
    document = db.get_report(report_id, g.user_id) if report_id is not None else None
    if not document:
        return jsonify({"error": f"No document found with custom_id: {report_public_id}"}), 404
    return jsonify({
        "documentType": document.get("documentType", ""),
        "completeness": document.get("completeness", {}),
        "consistencyChecks": document.get("consistencyChecks", []),
        "needsReview": document.get("needsReview", False),
    })


@reports_bp.route("/fetch_all_data/", methods=["GET"])
@login_required
def fetch_all_data():
    limit = _parse_int(request.args.get("limit"), DEFAULT_PAGE_SIZE, minimum=1, maximum=MAX_PAGE_SIZE)
    offset = _parse_int(request.args.get("offset"), 0, minimum=0)

    documents, total = db.list_reports(g.user_id, limit=limit, offset=offset)
    return jsonify(
        {
            "message": "All data fetched successfully",
            "data": documents,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )
