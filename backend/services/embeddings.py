from functools import lru_cache
from time import perf_counter

from config import EMBEDDING_DOCUMENT_MAX_CHARS, EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=EMBEDDING_MODEL_NAME)


def compact_document_text(text: str) -> str:
    limit = EMBEDDING_DOCUMENT_MAX_CHARS
    if limit <= 0 or len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return f"{text[:head]}\n[... page text omitted from embedding only ...]\n{text[-tail:]}"


def embed_texts(texts: list[str], *, perf=None, purpose: str = "document") -> list[list[float]]:
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

    embedding_started = perf_counter()
    vectors = [vec.tolist() for vec in model.embed(texts)]
    if perf is not None:
        perf.record_embedding_batch(
            purpose=purpose,
            batch_size=len(texts),
            vector_count=len(vectors),
            started=embedding_started,
        )
    return vectors


def embed_query(text: str, *, perf=None, purpose: str = "query") -> list[float]:
    return embed_texts([text], perf=perf, purpose=purpose)[0]
