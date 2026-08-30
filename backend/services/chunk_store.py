from services import db
from services.embeddings import compact_document_text, embed_texts
from services.logging_config import get_logger, log_extra

logger = get_logger(__name__)


def store_chunks(report_id: int, pages: list[dict]) -> int:

    texts = [p["text"] for p in pages]



    embeddings = embed_texts([compact_document_text(text) for text in texts])

    chunks = [
        {"page_number": page["page_number"], "text": page["text"], "embedding": embedding}
        for page, embedding in zip(pages, embeddings)
    ]

    db.insert_chunks(report_id, chunks)
    logger.info("chunks_stored", extra=log_extra(report_id=report_id, chunk_count=len(chunks)))
    return len(chunks)


def get_chunks(report_id: int) -> list[dict]:
    return db.get_chunks(report_id)


def update_chunk_texts(report_id: int, pages: list[dict]) -> int:
    updated = db.update_chunk_texts(report_id, pages)
    logger.info("chunk_texts_enriched", extra=log_extra(report_id=report_id, updated_chunks=updated))
    return updated
