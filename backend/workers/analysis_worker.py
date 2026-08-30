import datetime
import threading
import traceback
from time import perf_counter

import config
from services import chunk_store, classification, completeness, consistency, curation, db, llm, ocr
from services.source_cache import SourceCache
from services.logging_config import get_logger, log_extra

logger = get_logger(__name__)

_stop_event = threading.Event()
_work_available = threading.Event()
_worker_thread: threading.Thread | None = None


def _process_job(job: dict):
    job_id = job["job_id"]
    report_id = job["report_id"]

    report_public_id = db.get_report_public_id(report_id)
    file_bytes = bytes(job["file_bytes"])
    file_name = job["file_name"]

    logger.info("job_started", extra=log_extra(job_id=job_id, report_id=report_id, user_id=job["user_id"]))

    started = perf_counter()
    metrics = {"started_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}

    def record(stage: str, began: float, **extra):
        metrics[stage] = {"duration_ms": round((perf_counter() - began) * 1000, 1), **extra}
        metrics["elapsed_ms"] = round((perf_counter() - started) * 1000, 1)
        db.update_job_metrics(job_id, metrics)

    db.update_job_progress(job_id, "extracting", 15)
    stage_started = perf_counter()

    client_ocr_pages = job.get("ocr_pages")
    try:
        pages = ocr.extract_pages_from_bytes(file_bytes, file_name, client_ocr_pages=client_ocr_pages)
    except ocr.ClientOCRRequired:
        metrics["ocr"] = {"required": True, "provider": "puter_mistral", "status": "awaiting_client"}
        db.mark_job_awaiting_ocr(job_id, metrics)
        logger.info("job_awaiting_client_ocr", extra=log_extra(job_id=job_id, report_id=report_id))
        return
    ocr_source = "client_ocr" if client_ocr_pages else "local_text_layer"
    if client_ocr_pages:
        metrics["ocr"] = {"required": True, "provider": "puter_mistral", "status": "completed", "pages": len(pages)}
    record(
        "text_extraction",
        stage_started,
        pages=len(pages),
        text_chars=sum(len(p["text"]) for p in pages),
        source=ocr_source,
    )

    document_type = classification.classify_document(pages)

    db.update_job_progress(job_id, "analysing", 40)
    stage_started = perf_counter()
    chunk_store.store_chunks(report_id, pages)
    record("chunk_indexing", stage_started)

    stage_started = perf_counter()
    retrieved_sections = llm.retrieve_extraction_sections(report_id, document_type)
    selected_page_numbers = {
        chunk["page_number"] for chunks in retrieved_sections.values() for chunk in chunks
    }
    enriched_pages = ocr.enrich_pages_with_tables(file_bytes, pages, selected_page_numbers)
    enriched_by_page = {page["page_number"]: page for page in enriched_pages}

    for chunks in retrieved_sections.values():
        for chunk in chunks:
            chunk["text"] = enriched_by_page.get(chunk["page_number"], chunk)["text"]
    updated_chunks = chunk_store.update_chunk_texts(report_id, enriched_pages)
    record("retrieval_and_table_enrichment", stage_started, selected_pages=len(selected_page_numbers), updated_chunks=updated_chunks)


    source_cache = SourceCache(report_id)
    source_cache.set_pages(enriched_pages)
    source_cache.set_metadata(file_name=file_name, document_type=document_type, page_count=len(pages))
    for section in llm.sections_for(document_type):
        source_cache.prime_retrieval(section["query"], section.get("top_k", 3), retrieved_sections.get(section["name"], []))

    db.update_job_progress(job_id, "analysing", 65)
    stage_started = perf_counter()
    extracted = llm.extract_financial_data(report_id, retrieved_sections=retrieved_sections, document_type=document_type)
    record("llm_analysis", stage_started)

    db.update_job_progress(job_id, "validating", 85)
    extracted["custom_id"] = report_public_id
    extracted["analysis_date"] = datetime.datetime.now().strftime("%B %d, %Y")
    extracted["sourceFileName"] = file_name
    extracted["documentType"] = document_type
    page_text_by_number = {page["page_number"]: page["text"] for page in enriched_pages}
    extracted["citations"] = curation.enrich_and_verify_citations(extracted, page_text_by_number, file_name)


    stage_started = perf_counter()
    report_completeness = completeness.evaluate_completeness(extracted, document_type)
    reevaluated_fields: list[str] = []
    missing = completeness.missing_fields_worth_reevaluating(report_completeness)
    if missing:
        recovered = llm.reevaluate_missing_fields(report_id, missing, source_scale=extracted.get("sourceReportingScale", "actual"), cache=source_cache)
        if recovered["values"]:
            extracted.update(recovered["values"])
            extracted["citations"] = extracted["citations"] + recovered["citations"]
            extracted["citations"] = curation.enrich_and_verify_citations(extracted, page_text_by_number, file_name)
            report_completeness = completeness.evaluate_completeness(extracted, document_type)
            reevaluated_fields = list(recovered["values"].keys())
    record(
        "completeness_and_reevaluation",
        stage_started,
        missing_before=len(missing),
        recovered=len(reevaluated_fields),
        cache_retrieval_hits=source_cache.stats["retrieval_hits"],
        cache_retrieval_misses=source_cache.stats["retrieval_misses"],
    )
    extracted["completeness"] = report_completeness


    checks = consistency.run_consistency_checks(extracted)
    extracted["consistencyChecks"] = checks
    extracted["needsReview"] = consistency.has_material_failure(checks)

    db.update_job_progress(job_id, "saving", 95)
    db.update_report(report_id, extracted, status="completed")


    company_name = extracted.get("companyName", "")
    company_name_verified = any(c.get("field") == "companyName" for c in extracted["citations"])
    if company_name and company_name_verified:
        company = db.upsert_company(job["user_id"], company_name)
        if company:
            db.assign_report_company(report_id, company["id"])
            reports = db.list_company_reports(company["id"], job["user_id"])
            display_company = {"id": str(company["public_id"]), "name": company["name"]}
            dashboard = curation.build_dashboard(display_company, reports)
            db.publish_company_dashboard(company["id"], dashboard, [report["custom_id"] for report in reports])
    elif company_name:
        logger.warning("company_identity_not_verified", extra=log_extra(report_id=report_id, company=company_name))

    db.complete_job(job_id)
    metrics["total_ms"] = round((perf_counter() - started) * 1000, 1)
    db.update_job_metrics(job_id, metrics)
    logger.info("job_completed", extra=log_extra(job_id=job_id, report_id=report_id))


def _sanitize_error(exc: Exception) -> str:
    if isinstance(exc, ocr.OCRError):
        if "No extractable text" in str(exc):
            return str(exc)
        return "We couldn't read this document. Please try again or use a different file."
    if isinstance(exc, llm.QuotaExhaustedError):
        return str(exc)
    if isinstance(exc, llm.LLMError):
        return "We couldn't analyze this document's financial data. Please try again."
    if isinstance(exc, db.DatabaseError):
        return "A temporary storage error occurred. Please try again."
    return "Something went wrong while processing this report."


def _handle_failure(job: dict, exc: Exception):
    job_id = job["job_id"]
    retry_count = job["retry_count"]
    safe_message = _sanitize_error(exc)

    logger.error(
        "job_failed",
        extra=log_extra(
            job_id=job_id,
            report_id=job["report_id"],
            retry_count=retry_count,
            error=str(exc),
            trace=traceback.format_exc(),
        ),
    )


    if isinstance(exc, llm.QuotaExhaustedError):
        db.fail_job(job_id, error=safe_message)
    elif retry_count + 1 < config.JOB_MAX_RETRIES:
        db.requeue_job(job_id, error=safe_message)
    else:
        db.fail_job(job_id, error=safe_message)


def _safe_process_job(job: dict):
    try:
        _process_job(job)
    except Exception as exc:
        _handle_failure(job, exc)


def run_worker_loop(stop_event: threading.Event):
    logger.info("worker_loop_started")
    while not stop_event.is_set():
        try:
            reclaimed = db.requeue_stale_jobs(config.JOB_STALE_AFTER_SECONDS)
            if reclaimed:
                logger.warning("stale_jobs_reclaimed", extra=log_extra(count=reclaimed))

            abandoned_ocr = db.fail_stale_awaiting_ocr_jobs(config.JOB_OCR_TIMEOUT_SECONDS)
            if abandoned_ocr:
                logger.warning("awaiting_ocr_jobs_timed_out", extra=log_extra(count=abandoned_ocr))

            job = db.claim_next_queued_job()
            if job is None:
                _work_available.wait(config.JOB_POLL_INTERVAL_SECONDS)
                _work_available.clear()
                continue

            _safe_process_job(job)
        except db.DatabaseError as exc:
            logger.error("worker_loop_db_error", extra=log_extra(error=str(exc)))
            stop_event.wait(config.JOB_POLL_INTERVAL_SECONDS)
        except Exception:
            logger.error("worker_loop_unexpected_error", extra=log_extra(trace=traceback.format_exc()))
            stop_event.wait(config.JOB_POLL_INTERVAL_SECONDS)


def start_worker_thread() -> threading.Thread | None:

    global _worker_thread
    if config.DISABLE_BACKGROUND_WORKER:
        logger.info("worker_disabled_by_configuration")
        return None
    if _worker_thread is not None and _worker_thread.is_alive():
        return _worker_thread

    _stop_event.clear()
    _worker_thread = threading.Thread(target=run_worker_loop, args=(_stop_event,), daemon=True, name="analysis-worker")
    _worker_thread.start()
    return _worker_thread


def notify_work_available():

    _work_available.set()


def stop_worker_thread(timeout: float = 5.0):
    _stop_event.set()
    _work_available.set()
    if _worker_thread is not None:
        _worker_thread.join(timeout=timeout)
