import os
import uuid
from time import perf_counter

from flask import Flask, g, jsonify, request
from flask_cors import CORS

import config
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.dashboard import dashboard_bp
from routes.jobs import jobs_bp
from routes.reports import reports_bp
from routes.upload import upload_bp
from services import db
from services.logging_config import configure_logging, get_logger, log_extra
from workers.analysis_worker import start_worker_thread

configure_logging(config.LOG_LEVEL)
logger = get_logger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES
CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)

try:
    config.validate_required_config()
except config.ConfigError as exc:
    logger.warning("startup_config_incomplete", extra=log_extra(error=str(exc)))

try:
    db.init_schema()
except db.DatabaseError as exc:
    logger.warning("startup_schema_init_failed", extra=log_extra(error=str(exc)))


if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    start_worker_thread()

app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(chat_bp)


@app.before_request
def _assign_request_id():
    g.request_id = str(uuid.uuid4())
    g.request_started_at = perf_counter()


_QUIET_PATHS = ("/health", "/status")


@app.after_request
def _log_response(response):
    if response.status_code < 400 and request.path.endswith(_QUIET_PATHS):
        return response
    logger.info(
        "request_completed",
        extra=log_extra(
            request_id=getattr(g, "request_id", None),
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=round((perf_counter() - getattr(g, "request_started_at", perf_counter())) * 1000, 1),
        ),
    )
    return response


@app.errorhandler(413)
def _handle_too_large(_exc):
    return jsonify({"error": f"File exceeds the {config.MAX_UPLOAD_MB}MB upload limit"}), 413


@app.errorhandler(404)
def _handle_not_found(_exc):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def _handle_server_error(exc):
    logger.error("unhandled_exception", extra=log_extra(request_id=getattr(g, "request_id", None), error=str(exc)))
    return jsonify({"error": "An internal error occurred"}), 500


@app.route("/health", methods=["GET"])
def health():
    checks = {"database": "ok", "config": "ok"}
    healthy = True

    try:
        db.check_connection()
    except db.DatabaseError as exc:
        checks["database"] = str(exc)
        healthy = False

    try:
        config.validate_required_config()
    except config.ConfigError as exc:
        checks["config"] = str(exc)
        healthy = False

    return jsonify({"status": "ok" if healthy else "degraded", "checks": checks}), (200 if healthy else 503)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=(config.LOG_LEVEL == "DEBUG"))
