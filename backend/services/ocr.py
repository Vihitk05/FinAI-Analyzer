import pymupdf as fitz

from services.logging_config import get_logger, log_extra

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


def extract_text_locally(pdf_bytes: bytes, *, include_tables: bool = True) -> list[dict]:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning("local_text_extraction_failed", extra=log_extra(error=str(exc)))
        return []

    try:
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if include_tables:
                table_rows = _extract_tables_as_rows(page)
                if table_rows:
                    text = f"{text}{TABLE_SECTION_MARKER}{table_rows}" if text else table_rows
            if text:
                pages.append({"page_number": i, "text": text})
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


def enrich_pages_with_tables(pdf_bytes: bytes, pages: list[dict], page_numbers: set[int]) -> list[dict]:
    if not page_numbers:
        return pages

    by_page = {page["page_number"]: dict(page) for page in pages}
    wanted = sorted(page_number for page_number in page_numbers if page_number in by_page)
    if not wanted:
        return pages

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning("table_enrichment_open_failed", extra=log_extra(error=str(exc)))
        return pages

    try:
        for page_number in wanted:
            page = doc[page_number - 1]
            table_rows = _extract_tables_as_rows(page)
            if not table_rows:
                continue
            existing = by_page[page_number]["text"]
            if TABLE_SECTION_MARKER not in existing:
                by_page[page_number]["text"] = (
                    f"{existing}{TABLE_SECTION_MARKER}{table_rows}" if existing else table_rows
                )
    finally:
        doc.close()

    return [by_page[page["page_number"]] for page in pages]


def extract_pages_from_bytes(
    pdf_bytes: bytes,
    filename: str,
    *,
    client_ocr_pages=None,
    include_tables: bool = True,
) -> list[dict]:
    local_pages = extract_text_locally(pdf_bytes, include_tables=include_tables)
    if _has_meaningful_text(local_pages):
        logger.info(
            "local_text_extraction_used",
            extra=log_extra(filename=filename, pages_with_text=len(local_pages)),
        )
        return local_pages

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
