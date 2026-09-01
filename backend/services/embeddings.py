from functools import lru_cache
from time import perf_counter

from config import EMBEDDING_DOCUMENT_MAX_CHARS, EMBEDDING_MODEL_NAME
from services.memory import log_memory

DOCUMENT_EMBEDDING_BATCH_SIZE = 8
_UNSET = object()


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    log_memory("before_fastembed_initialization", model=EMBEDDING_MODEL_NAME)
    model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME, threads=1)
    log_memory("after_fastembed_initialization", model=EMBEDDING_MODEL_NAME)
    return model


def compact_document_text(text: str) -> str:
    limit = EMBEDDING_DOCUMENT_MAX_CHARS
    if limit <= 0 or len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return f"{text[:head]}\n[... page text omitted from embedding only ...]\n{text[-tail:]}"


def embed_texts(
    texts: list[str],
    *,
    perf=None,
    purpose: str = "document",
    batch_size: int | None = None,
    parallel=_UNSET,
) -> list[list[float]]:
    if not texts:
        return []
    model_started = perf_counter()
    cache_before = _model.cache_info()
    model = _model()
    cache_after = _model.cache_info()
    if perf is not None:
        perf.record_fastembed(
            created=cache_after.misses > cache_before.misses,
            reused=cache_after.hits > cache_before.hits,
            started=model_started,
            cache_info=cache_after,
        )

    vectors = []
    effective_batch_size = batch_size if batch_size is not None else len(texts)
    for batch_index, offset in enumerate(range(0, len(texts), effective_batch_size), start=1):
        batch = texts[offset: offset + effective_batch_size]
        log_memory(
            "before_embedding_batch",
            purpose=purpose,
            batch_index=batch_index,
            batch_size=len(batch),
            total_texts=len(texts),
        )
        batch_started = perf_counter()
        embed_kwargs = {}
        if batch_size is not None:
            embed_kwargs["batch_size"] = effective_batch_size
        if parallel is not _UNSET:
            embed_kwargs["parallel"] = parallel
        batch_vectors = [vec.tolist() for vec in model.embed(batch, **embed_kwargs)]
        log_memory(
            "after_embedding_batch",
            purpose=purpose,
            batch_index=batch_index,
            batch_size=len(batch),
            vector_count=len(batch_vectors),
            total_texts=len(texts),
        )
        if perf is not None:
            perf.record_embedding_batch(
                purpose=f"{purpose}:batch",
                batch_size=len(batch),
                vector_count=len(batch_vectors),
                started=batch_started,
            )
        vectors.extend(batch_vectors)
    return vectors


def embed_query(text: str, *, perf=None, purpose: str = "query") -> list[float]:
    return embed_texts([text], perf=perf, purpose=purpose)[0]
