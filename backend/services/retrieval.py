from time import perf_counter

from services.db import scored_chunks_for_query
from services.embeddings import embed_query


def fuse_scored_chunks(scored_rows: list[dict], top_k: int = 5, rrf_k: int = 60) -> list[dict]:

    if not scored_rows:
        return []

    text_ranked = sorted(range(len(scored_rows)), key=lambda i: scored_rows[i]["text_score"], reverse=True)
    vector_ranked = sorted(range(len(scored_rows)), key=lambda i: scored_rows[i]["vector_score"], reverse=True)

    text_rank_of = {idx: rank for rank, idx in enumerate(text_ranked)}
    vector_rank_of = {idx: rank for rank, idx in enumerate(vector_ranked)}

    fused = sorted(
        range(len(scored_rows)),
        key=lambda i: (1.0 / (rrf_k + text_rank_of[i])) + (1.0 / (rrf_k + vector_rank_of[i])),
        reverse=True,
    )

    results = []
    for idx in fused[:top_k]:
        score = (1.0 / (rrf_k + text_rank_of[idx])) + (1.0 / (rrf_k + vector_rank_of[idx]))
        results.append(
            {
                "page_number": scored_rows[idx]["page_number"],
                "text": scored_rows[idx]["text"],
                "score": score,
                "text_rank": text_rank_of[idx] + 1,
                "vector_rank": vector_rank_of[idx] + 1,
            }
        )
    return results


def hybrid_search(report_id: int, query: str, top_k: int = 5, *, perf=None, name: str = "query") -> list[dict]:
    started = perf_counter()
    query_embedding = embed_query(query, perf=perf, purpose="retrieval_query")
    scored_rows = scored_chunks_for_query(report_id, query, query_embedding, perf=perf)
    results = fuse_scored_chunks(scored_rows, top_k=top_k)
    if perf is not None:
        perf.record_hybrid_retrieval(
            name=name,
            top_k=top_k,
            rows_scored=len(scored_rows),
            rows_returned=len(results),
            started=started,
        )
    return results
