import concurrent.futures
from functools import lru_cache
from time import perf_counter

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import (
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_DOCUMENT_MAX_CHARS,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_TIMEOUT_SECONDS,
)
from services.ai_errors import (
    QUOTA_EXHAUSTED_MESSAGE,
    LLMError,
    QuotaExhaustedError,
    TransientLLMError,
    is_daily_quota_exhausted,
    is_transient,
)
from services.memory import log_memory

_MAX_PARALLEL_BATCHES = 4


@lru_cache(maxsize=1)
def _client():
    if not EMBEDDING_API_KEY:
        raise LLMError("EMBEDDING_API_KEY (or LLM_API_KEY) is not configured")
    return OpenAI(api_key=EMBEDDING_API_KEY, base_url=EMBEDDING_BASE_URL, max_retries=0, timeout=EMBEDDING_TIMEOUT_SECONDS)


def compact_document_text(text: str) -> str:
    limit = EMBEDDING_DOCUMENT_MAX_CHARS
    if limit <= 0 or len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return f"{text[:head]}\n[... page text omitted from embedding only ...]\n{text[-tail:]}"


@retry(
    retry=retry_if_exception_type(TransientLLMError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _embed_batch(batch: list[str]) -> list[list[float]]:
    try:
        response = _client().embeddings.create(
            model=EMBEDDING_MODEL_NAME,
            input=batch,
            dimensions=EMBEDDING_DIMENSIONS,
            encoding_format="float",
        )
    except Exception as exc:
        if is_daily_quota_exhausted(exc):
            raise QuotaExhaustedError(QUOTA_EXHAUSTED_MESSAGE) from exc
        if is_transient(exc) or "timed out" in str(exc).lower():
            raise TransientLLMError(f"Embedding request failed: {exc}") from exc
        raise LLMError(f"Embedding request failed: {exc}") from exc

    vectors = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
    if len(vectors) != len(batch) or any(len(v) != EMBEDDING_DIMENSIONS for v in vectors):
        raise TransientLLMError(
            f"Embedding response had {len(vectors)} vectors for {len(batch)} inputs "
            f"(expected {EMBEDDING_DIMENSIONS} dimensions each)"
        )
    return vectors


def embed_texts(texts: list[str], *, perf=None, purpose: str = "document") -> list[list[float]]:
    if not texts:
        return []
    texts = [text if text.strip() else "(empty page)" for text in texts]
    batches = [texts[offset: offset + EMBEDDING_BATCH_SIZE] for offset in range(0, len(texts), EMBEDDING_BATCH_SIZE)]

    def run(batch_index: int, batch: list[str]) -> list[list[float]]:
        log_memory("before_embedding_batch", purpose=purpose, batch_index=batch_index, batch_size=len(batch), total_texts=len(texts))
        batch_started = perf_counter()
        vectors = _embed_batch(batch)
        if perf is not None:
            perf.record_embedding_batch(
                purpose=f"{purpose}:batch",
                batch_size=len(batch),
                vector_count=len(vectors),
                started=batch_started,
            )
        return vectors

    if len(batches) == 1:
        return run(1, batches[0])
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(batches), _MAX_PARALLEL_BATCHES)) as executor:
        results = executor.map(run, range(1, len(batches) + 1), batches)
        return [vector for batch_vectors in results for vector in batch_vectors]


def embed_query(text: str, *, perf=None, purpose: str = "query") -> list[float]:
    return embed_texts([text], perf=perf, purpose=purpose)[0]
