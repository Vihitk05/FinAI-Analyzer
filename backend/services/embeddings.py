from functools import lru_cache

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


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [vec.tolist() for vec in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
