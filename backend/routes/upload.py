import os
import uuid

from flask import Blueprint, g, jsonify, request
from werkzeug.utils import secure_filename

import config
from services import db
from services.logging_config import get_logger, log_extra
from utils.auth_utils import login_required
from workers.analysis_worker import notify_work_available

logger = get_logger(__name__)
upload_bp = Blueprint("upload", __name__)


def _looks_like_pdf(file_bytes: bytes) -> bool:
    return file_bytes[:5] == b"%PDF-"


@upload_bp.route("/upload/", methods=["POST"])
@login_required
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in config.ALLOWED_UPLOAD_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type '{ext}'. Only PDF files are accepted."}), 400

    file_bytes = file.read()
    if not file_bytes:
        return jsonify({"error": "The uploaded file is empty"}), 400
    if not _looks_like_pdf(file_bytes):
        return jsonify({"error": "The uploaded file is not a valid PDF"}), 400

    try:
        report_id = db.insert_report({}, user_id=g.user_id, status="queued")
        report_public_id = db.get_report_public_id(report_id)
        job_id = str(uuid.uuid4())
        db.create_job(job_id, g.user_id, report_id, filename, file_bytes)
    except db.DatabaseError as exc:
        logger.error("upload_job_creation_failed", extra=log_extra(user_id=g.user_id, error=str(exc)))
        return jsonify({"error": "Failed to queue this document for analysis"}), 503

    logger.info("upload_queued", extra=log_extra(user_id=g.user_id, report_id=report_id, job_id=job_id))
    notify_work_available()
    return jsonify({"success": True, "custom_id": report_public_id, "job_id": job_id, "status": "queued"}), 202
