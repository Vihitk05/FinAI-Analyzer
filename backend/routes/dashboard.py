from flask import Blueprint, g, jsonify, request, send_file
import io

from services import curation, db, presentation
from services.logging_config import get_logger, log_extra
from services.presentation_model import build_presentation_model
from utils.auth_utils import login_required

logger = get_logger(__name__)
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


@dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
def list_company_dashboards():
    try:
        companies = db.list_companies(g.user_id)
    except db.DatabaseError:
        return jsonify({"error": "Unable to load company dashboards"}), 503
    return jsonify({"empty": not companies, "companies": companies})


@dashboard_bp.route("/companies/<company_public_id>/dashboard", methods=["GET"])
@login_required
def company_dashboard(company_public_id: str):
    company_id = db.resolve_company_id(company_public_id, g.user_id)
    company = db.get_company(company_id, g.user_id) if company_id is not None else None
    if not company:
        return jsonify({"error": "Company dashboard not found"}), 404
    try:
        reports = db.list_company_reports(company_id, g.user_id)
        if not reports:
            return jsonify({"error": "No validated reports are available for this company"}), 404
        stored = db.get_current_company_dashboard(company_id, g.user_id)
        return jsonify(curation.current_or_fresh_company_dashboard(stored, company, reports))
    except db.DatabaseError:
        return jsonify({"error": "Unable to load company dashboard"}), 503


def _export_presentation(dashboard: dict, *, user_id: int, company_id: int | None, name: str):
    fmt = request.args.get("format", "pptx").lower()
    if fmt not in {"pptx", "pdf"}:
        return jsonify({"error": "Unsupported presentation format"}), 400

    export_job = db.create_export_job(user_id, company_id, fmt)

    def _fail(stage: str, client_message: str, detail: str, status: int = 503):
        db.fail_export_job(export_job["id"], stage, detail)
        logger.error("export_failed", extra=log_extra(export_job_id=export_job["id"], stage=stage, error=detail))
        return jsonify({"error": client_message}), status

    try:
        db.update_export_job_stage(export_job["id"], "building")
        model = build_presentation_model(dashboard)
        coverage = presentation.enforce_coverage(dashboard, model)
        pptx = presentation.build_pptx(dashboard, model=model)
        db.update_export_job_stage(export_job["id"], "validating")
        slide_count = presentation.validate_pptx(pptx)
    except presentation.ExportValidationError as exc:
        return _fail("validating", "The presentation could not be generated correctly. Please try again.", str(exc))
    except Exception as exc:
        return _fail("building", "The presentation could not be generated. Please try again.", str(exc))

    logger.info(
        "export_coverage_ok",
        extra=log_extra(export_job_id=export_job["id"], slides=slide_count, **coverage["counts"]),
    )

    if fmt == "pptx":
        content, mimetype, extension = pptx, "application/vnd.openxmlformats-officedocument.presentationml.presentation", "pptx"
    else:
        try:
            db.update_export_job_stage(export_job["id"], "converting")
            pdf, method = presentation.pdf_export(pptx, data=dashboard, model=model)
            db.update_export_job_stage(export_job["id"], "checking")
            presentation.validate_pdf(pdf, slide_count, exact=(method == "soffice"))
        except RuntimeError as exc:
            return _fail("converting", "The PDF export is currently unavailable. Please try the PPTX export.", str(exc))
        except presentation.ExportValidationError as exc:
            return _fail("checking", "The PDF export could not be generated correctly. Please try again.", str(exc))
        content, mimetype, extension = pdf, "application/pdf", "pdf"

    db.complete_export_job(export_job["id"], len(content), presentation.file_checksum(content))
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in (name or "")).strip("-") or "report"
    return send_file(io.BytesIO(content), mimetype=mimetype, as_attachment=True,
                     download_name=f"{safe_name}-financial-intelligence.{extension}")


@dashboard_bp.route("/companies/<company_public_id>/presentation", methods=["GET"])
@login_required
def company_presentation(company_public_id: str):
    company_id = db.resolve_company_id(company_public_id, g.user_id)
    company = db.get_company(company_id, g.user_id) if company_id is not None else None
    if not company:
        return jsonify({"error": "Company dashboard not found"}), 404
    reports = db.list_company_reports(company_id, g.user_id)
    if not reports:
        return jsonify({"error": "No validated reports are available for this company"}), 404
    stored = db.get_current_company_dashboard(company_id, g.user_id)
    dashboard = curation.current_or_fresh_company_dashboard(stored, company, reports)
    return _export_presentation(dashboard, user_id=g.user_id, company_id=company_id, name=company["name"])


@dashboard_bp.route("/reports/<report_public_id>/presentation", methods=["GET"])
@login_required
def report_presentation(report_public_id: str):
    report_id = db.resolve_report_id(report_public_id, g.user_id)
    report = db.get_report(report_id, g.user_id) if report_id is not None else None
    if not report:
        return jsonify({"error": "Report dashboard not found"}), 404
    if report.get("status") != "completed":
        return jsonify({"error": "This report is still being processed"}), 409
    dashboard = curation.build_dashboard({"id": None, "name": report.get("companyName", "")}, [report], scope="report")
    return _export_presentation(dashboard, user_id=g.user_id, company_id=None, name=report.get("companyName", "report"))


@dashboard_bp.route("/reports/<report_public_id>/dashboard", methods=["GET"])
@login_required
def report_dashboard(report_public_id: str):
    report_id = db.resolve_report_id(report_public_id, g.user_id)
    report = db.get_report(report_id, g.user_id) if report_id is not None else None
    if not report:
        return jsonify({"error": "Report dashboard not found"}), 404
    if report.get("status") != "completed":
        return jsonify({"error": "This report is still being processed"}), 409
    company = {"id": None, "name": report.get("companyName", "")}
    return jsonify(curation.build_dashboard(company, [report], scope="report"))


@dashboard_bp.route("/demo/dashboard", methods=["GET"])
def demo_dashboard():
    sample = {
        "custom_id": "demo-report-2025", "companyName": "Northstar Retail (Demo)", "currency": "USD",
        "reportingPeriod": "FY2025", "sourceFileName": "Northstar_Retail_Demo_FY2025.pdf",
        "revenue": 1250000000, "ebitda": 145000000, "netIncome": 72000000,
        "executiveSummary": "Northstar Retail (Demo) grew revenue and EBITDA in FY2025, with net income remaining positive for the period.",
        "citations": [
            {"field": "revenue", "page": 42, "filename": "Northstar_Retail_Demo_FY2025.pdf", "reportId": "demo-report-2025", "description": "Contains demo revenue figures.", "verificationStatus": "verified"},
            {"field": "ebitda", "page": 43, "filename": "Northstar_Retail_Demo_FY2025.pdf", "reportId": "demo-report-2025", "description": "Contains demo EBITDA figures.", "verificationStatus": "verified"},
            {"field": "netIncome", "page": 43, "filename": "Northstar_Retail_Demo_FY2025.pdf", "reportId": "demo-report-2025", "description": "Contains demo net income figures.", "verificationStatus": "verified"},
            {"field": "executiveSummary", "page": 2, "filename": "Northstar_Retail_Demo_FY2025.pdf", "reportId": "demo-report-2025", "description": "Contains the demo executive summary.", "verificationStatus": "verified"},
        ],
    }
    data = curation.build_dashboard({"id": "demo", "name": sample["companyName"]}, [sample])
    data["isDemo"] = True
    data["demoNotice"] = "Demo data only, not an uploaded company report or investment advice."
    return jsonify(data)
