import pymupdf as fitz
from time import perf_counter

from services.logging_config import get_logger, log_extra
from services.memory import log_memory

logger = get_logger(__name__)

_MIN_AVG_CHARS_PER_PAGE = 40


TABLE_SECTION_MARKER = "\n\n[Table rows, label then values in order]\n"


class OCRError(Exception):
    pass


class ClientOCRRequired(OCRError):
    pass


def _extract_tables_as_rows(page) -> str:
    try:
        tables = page.find_tables()
    except Exception:
        return ""

    rendered = []
    for table in tables:
        try:
            rows = table.extract()
        except Exception:
            continue
        for row in rows:
            cells = [str(cell).strip().replace("\n", " ") for cell in row if cell is not None and str(cell).strip()]
            if len(cells) >= 2:
                rendered.append(" | ".join(cells))

    return "\n".join(rendered)


def extract_text_locally(pdf_bytes: bytes, *, include_tables: bool = False, perf=None, timing_prefix: str = "initial") -> list[dict]:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning("local_text_extraction_failed", extra=log_extra(error=str(exc)))
        return []

    try:
        pages = []
        text_duration_ms = 0.0
        table_duration_ms = 0.0
        table_pages_scanned = 0
        for i, page in enumerate(doc, start=1):
            page_text_started = perf_counter()
            text = page.get_text("text").strip()
            text_duration_ms += (perf_counter() - page_text_started) * 1000
            text_had_prose = bool(text)
            table_rows = ""
            if include_tables:
                page_table_started = perf_counter()
                log_memory(f"before_{timing_prefix}_find_tables_page", page_number=i)
                table_rows = _extract_tables_as_rows(page)
                log_memory(f"after_{timing_prefix}_find_tables_page", page_number=i, has_table_rows=bool(table_rows))
                table_duration_ms += (perf_counter() - page_table_started) * 1000
                table_pages_scanned += 1
                if table_rows:
                    text = f"{text}{TABLE_SECTION_MARKER}{table_rows}" if text else table_rows
            if text:
                pages.append({
                    "page_number": i,
                    "text": text,
                    "_tables_extracted": include_tables,
                    "_table_rows": table_rows if table_rows and not text_had_prose else "",
                })
        if perf is not None:
            timing_finished = perf_counter()
            perf.record_stage(
                f"pymupdf_{timing_prefix}_plain_text_extraction",
                timing_finished - (text_duration_ms / 1000),
                pages_scanned=len(doc),
                pages_with_text=len(pages),
                measured_text_duration_ms=round(text_duration_ms, 1),
            )
            if include_tables:
                perf.record_stage(
                    f"pymupdf_{timing_prefix}_find_tables",
                    timing_finished - (table_duration_ms / 1000),
                    pages_scanned=table_pages_scanned,
                    measured_find_tables_duration_ms=round(table_duration_ms, 1),
                )
        return pages
    finally:
        doc.close()


def _has_meaningful_text(pages: list[dict]) -> bool:
    if not pages:
        return False
    total_chars = sum(len(p["text"]) for p in pages)
    return (total_chars / len(pages)) >= _MIN_AVG_CHARS_PER_PAGE


def normalize_ocr_pages(raw_pages) -> list[dict]:
    if not isinstance(raw_pages, list) or not raw_pages:
        raise OCRError("OCR result contained no pages")

    by_page: dict[int, str] = {}
    for entry in raw_pages:
        if not isinstance(entry, dict):
            raise OCRError("Each OCR page must be an object with page_number and text")
        raw_number = entry.get("page_number", entry.get("page"))
        try:
            page_number = int(raw_number)
        except (TypeError, ValueError):
            raise OCRError(f"OCR page has an invalid page number: {raw_number!r}")
        if page_number < 1:
            raise OCRError(f"OCR page number must be positive, got {page_number}")
        text = str(entry.get("text") or "").strip()
        if text:
            by_page[page_number] = text

    if not by_page:
        raise OCRError(
            "OCR produced no readable text on any page. The document may be blank, "
            "corrupted, or password-protected."
        )
    return [{"page_number": n, "text": by_page[n]} for n in sorted(by_page)]


def enrich_pages_with_tables(pdf_bytes: bytes, pages: list[dict], page_numbers: set[int], *, perf=None) -> list[dict]:
    if not page_numbers:
        return pages

    by_page = {page["page_number"]: dict(page) for page in pages}
    wanted = sorted(page_number for page_number in page_numbers if page_number in by_page)
    if not wanted:
        return pages

    doc = None
    needs_pdf = any(not by_page[page_number].get("_tables_extracted") for page_number in wanted)
    if needs_pdf:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            logger.warning("table_enrichment_open_failed", extra=log_extra(error=str(exc)))
            return pages

    try:
        table_duration_ms = 0.0
        table_pages_scanned = 0
        for page_number in wanted:
            existing = by_page[page_number]["text"]
            if by_page[page_number].get("_tables_extracted"):
                if TABLE_SECTION_MARKER in existing:
                    continue
                table_rows = by_page[page_number].get("_table_rows", "")
            else:
                page = doc[page_number - 1]
                page_table_started = perf_counter()
                log_memory("before_enrichment_find_tables_page", page_number=page_number)
                table_rows = _extract_tables_as_rows(page)
                log_memory("after_enrichment_find_tables_page", page_number=page_number, has_table_rows=bool(table_rows))
                table_duration_ms += (perf_counter() - page_table_started) * 1000
                table_pages_scanned += 1
            if not table_rows:
                continue
            if TABLE_SECTION_MARKER not in existing:
                by_page[page_number]["text"] = (
                    f"{existing}{TABLE_SECTION_MARKER}{table_rows}" if existing else table_rows
                )
        if perf is not None:
            timing_finished = perf_counter()
            perf.record_stage(
                "pymupdf_enrichment_find_tables",
                timing_finished - (table_duration_ms / 1000),
                selected_pages=len(wanted),
                pages_scanned=table_pages_scanned,
                measured_find_tables_duration_ms=round(table_duration_ms, 1),
            )
    finally:
        if doc is not None:
            doc.close()

    return [by_page[page["page_number"]] for page in pages]


def extract_pages_from_bytes(
    pdf_bytes: bytes,
    filename: str,
    *,
    client_ocr_pages=None,
    include_tables: bool = False,
    perf=None,
) -> list[dict]:
    local_pages = extract_text_locally(pdf_bytes, include_tables=include_tables, perf=perf)
    if _has_meaningful_text(local_pages):
        logger.info(
            "local_text_extraction_used",
            extra=log_extra(filename=filename, pages_with_text=len(local_pages)),
        )
        return local_pages

    if not include_tables:
        table_pages = extract_text_locally(pdf_bytes, include_tables=True, perf=perf, timing_prefix="fallback")
        if _has_meaningful_text(table_pages):
            logger.info(
                "local_table_extraction_used",
                extra=log_extra(filename=filename, pages_with_text=len(table_pages)),
            )
            return table_pages

    if client_ocr_pages:
        pages = normalize_ocr_pages(client_ocr_pages)
        logger.info(
            "client_ocr_pages_used",
            extra=log_extra(filename=filename, provider="puter_mistral", pages_with_text=len(pages)),
        )
        return pages

    logger.info("client_ocr_required", extra=log_extra(filename=filename))
    raise ClientOCRRequired(
        "This document has no extractable text layer. It needs to be processed with OCR."
    )
