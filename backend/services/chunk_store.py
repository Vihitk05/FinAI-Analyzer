from services import db
from services.embeddings import compact_document_text, embed_texts
from services.logging_config import get_logger, log_extra
from services.memory import log_memory

logger = get_logger(__name__)


def store_chunks(report_id: int, pages: list[dict], *, perf=None) -> int:

    chunk_started = perf.now() if perf is not None else None
    texts = [p["text"] for p in pages]
    compacted = [compact_document_text(text) for text in texts]
    if perf is not None and chunk_started is not None:
        perf.record_stage(
            "chunking",
            chunk_started,
            chunks=len(pages),
            text_chars=sum(len(text) for text in texts),
            embedded_chars=sum(len(text) for text in compacted),
        )

    log_memory("before_document_embedding", chunks=len(compacted))
    embeddings = embed_texts(compacted, perf=perf, purpose="document_chunks")
    log_memory("after_document_embedding", chunks=len(compacted))

    chunks = [
        {"page_number": page["page_number"], "text": page["text"], "embedding": embedding}
        for page, embedding in zip(pages, embeddings)
    ]

    db.insert_chunks(report_id, chunks, perf=perf)
    if perf is not None:
        perf.set_count("chunks", len(chunks))
    logger.info("chunks_stored", extra=log_extra(report_id=report_id, chunk_count=len(chunks)))
    return len(chunks)


def backfill_missing_embeddings(report_id: int, *, perf=None) -> int:
    missing = db.get_chunks_missing_embeddings(report_id)
    if not missing:
        return 0
    embeddings = embed_texts(
        [compact_document_text(chunk["text"]) for chunk in missing],
        perf=perf,
        purpose="embedding_backfill",
    )
    db.set_chunk_embeddings([(chunk["id"], embedding) for chunk, embedding in zip(missing, embeddings)])
    logger.info("chunk_embeddings_backfilled", extra=log_extra(report_id=report_id, chunk_count=len(missing)))
    return len(missing)


def get_chunks(report_id: int) -> list[dict]:
    return db.get_chunks(report_id)


def update_chunk_texts(report_id: int, pages: list[dict], *, perf=None) -> int:
    updated = db.update_chunk_texts(report_id, pages, perf=perf)
    logger.info("chunk_texts_enriched", extra=log_extra(report_id=report_id, updated_chunks=updated))
    return updated
