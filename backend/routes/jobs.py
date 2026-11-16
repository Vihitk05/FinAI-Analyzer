import io

from flask import Blueprint, g, jsonify, request, send_file

from services import db, ocr
from services.logging_config import get_logger, log_extra
from utils.auth_utils import login_required
from workers.analysis_worker import notify_work_available

logger = get_logger(__name__)
jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs")

_MAX_OCR_PAGES = 2000


def _serialize(job: dict) -> dict:
    return {
        "job_id": job["job_id"],
        "custom_id": job["report_public_id"],
        "status": job["status"],
        "stage": job["stage"],
        "progress": job["progress"],
        "retry_count": job["retry_count"],
        "error": job["error"],
        "metrics": job.get("metrics") or {},
        "awaiting_ocr": job["status"] == "awaiting_ocr",
    }


@jobs_bp.route("/<job_id>/status", methods=["GET"])
@login_required
def job_status(job_id):
    job = db.get_job(job_id, g.user_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(_serialize(job))


@jobs_bp.route("/by-report/<report_public_id>/status", methods=["GET"])
@login_required
def job_status_by_report(report_public_id):
    report_id = db.resolve_report_id(report_public_id, g.user_id)
    job = db.get_latest_job_for_report(report_id, g.user_id) if report_id is not None else None
    if job is None:
        return jsonify({"error": "No job found for this report"}), 404
    return jsonify(_serialize(job))


@jobs_bp.route("/<job_id>/ocr-document", methods=["GET"])
@login_required
def ocr_document(job_id):
    result = db.get_awaiting_ocr_job_bytes(job_id, g.user_id)
    if result is None:
        return jsonify({"error": "No document is awaiting OCR for this job"}), 404
    file_bytes, file_name = result
    return send_file(io.BytesIO(file_bytes), mimetype="application/pdf", as_attachment=False, download_name=file_name)


@jobs_bp.route("/<job_id>/ocr-result", methods=["POST"])
@login_required
def ocr_result(job_id):
    job = db.get_job(job_id, g.user_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] != "awaiting_ocr":
        return jsonify({"error": "This job is not awaiting OCR"}), 409

    payload = request.get_json(silent=True) or {}
    outcome = (payload.get("status") or "").lower()

    if outcome in {"failed", "cancelled", "canceled"}:
        reason = str(payload.get("error") or "").strip()[:200]
        message = "OCR could not be completed" + (f": {reason}" if reason else ". Please try re-uploading the document.")
        db.fail_awaiting_ocr_job(job_id, g.user_id, message)
        logger.info("client_ocr_failed", extra=log_extra(job_id=job_id, reason=reason or outcome))
        return jsonify({"status": "failed", "error": message})

    if outcome != "completed":
        return jsonify({"error": "status must be 'completed', 'failed', or 'cancelled'"}), 400

    raw_pages = payload.get("pages")
    if isinstance(raw_pages, list) and len(raw_pages) > _MAX_OCR_PAGES:
        return jsonify({"error": f"Too many OCR pages (max {_MAX_OCR_PAGES})"}), 400
    try:
        pages = ocr.normalize_ocr_pages(raw_pages)
    except ocr.OCRError as exc:
        return jsonify({"error": str(exc)}), 400

    if not db.attach_client_ocr_and_requeue(job_id, g.user_id, pages):
        return jsonify({"error": "This job is not awaiting OCR"}), 409

    notify_work_available()
    logger.info("client_ocr_attached", extra=log_extra(job_id=job_id, pages=len(pages)))
    return jsonify({"status": "queued", "pages_received": len(pages)})
