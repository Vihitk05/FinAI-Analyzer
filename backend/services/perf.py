from __future__ import annotations

import copy
import datetime
import threading
from contextlib import contextmanager
from time import perf_counter


class PerformanceRecorder:
    def __init__(self, *, job_id: str, report_id: int, retry_count: int):
        self._lock = threading.RLock()
        self._started = perf_counter()
        self._data = {
            "job_id": job_id,
            "report_id": report_id,
            "retry_count": retry_count,
            "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "processing",
            "timings_ms": {},
            "counts": {
                "pages": 0,
                "chunks": 0,
                "embedding_calls": 0,
                "embedding_texts": 0,
                "llm_calls": 0,
                "llm_retries": 0,
                "db_queries": 0,
                "db_commits": 0,
                "citations_checked": 0,
            },
            "events": {
                "openrouter_calls": [],
                "hybrid_retrieval": [],
                "embedding_batches": [],
                "fastembed": [],
                "db_operations": [],
                "verification": [],
            },
            "audit": {},
        }

    def now(self) -> float:
        return perf_counter()

    def duration_ms(self, started: float) -> float:
        return round((perf_counter() - started) * 1000, 1)

    @contextmanager
    def timed(self, stage: str, **extra):
        started = perf_counter()
        try:
            yield
        finally:
            self.record_stage(stage, started, **extra)

    def record_stage(self, stage: str, started: float, **extra) -> None:
        self._safe(self._record_stage, stage, self.duration_ms(started), extra)

    def increment(self, key: str, amount: int = 1) -> None:
        self._safe(self._increment, key, amount)

    def set_count(self, key: str, value: int) -> None:
        self._safe(self._set_count, key, value)

    def set_audit(self, **fields) -> None:
        self._safe(self._set_audit, fields)

    def record_db_operation(
        self,
        name: str,
        kind: str,
        started: float,
        *,
        queries: int = 1,
        commits: int = 0,
        rows: int | None = None,
        bulk: bool = False,
    ) -> None:
        self._safe(
            self._record_db_operation,
            name,
            kind,
            self.duration_ms(started),
            queries,
            commits,
            rows,
            bulk,
        )

    def record_embedding_batch(
        self,
        *,
        purpose: str,
        batch_size: int,
        vector_count: int,
        started: float,
    ) -> None:
        self._safe(
            self._record_embedding_batch,
            purpose,
            batch_size,
            vector_count,
            self.duration_ms(started),
        )

    def record_fastembed(self, *, created: bool, reused: bool, started: float, cache_info=None) -> None:
        self._safe(
            self._record_fastembed,
            created,
            reused,
            self.duration_ms(started),
            cache_info,
        )

    def record_hybrid_retrieval(
        self,
        *,
        name: str,
        top_k: int,
        rows_scored: int,
        rows_returned: int,
        started: float,
    ) -> None:
        self._safe(
            self._record_hybrid_retrieval,
            name,
            top_k,
            rows_scored,
            rows_returned,
            self.duration_ms(started),
        )

    def record_openrouter_call(
        self,
        *,
        call_name: str,
        task: str,
        model: str,
        tool_name: str,
        started: float,
        status: str,
        error_class: str | None = None,
    ) -> None:
        self._safe(
            self._record_openrouter_call,
            call_name,
            task,
            model,
            tool_name,
            self.duration_ms(started),
            status,
            error_class,
        )

    def record_verification(
        self,
        *,
        name: str,
        started: float,
        citations_checked: int = 0,
        citations_verified: int = 0,
        fields_checked: int | None = None,
    ) -> None:
        self._safe(
            self._record_verification,
            name,
            self.duration_ms(started),
            citations_checked,
            citations_verified,
            fields_checked,
        )

    def finish(self, status: str) -> dict:
        self._safe(self._finish, status)
        return self.summary()

    def summary(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._data)

    def _record_stage(self, stage: str, duration_ms: float, extra: dict) -> None:
        with self._lock:
            self._data["timings_ms"][stage] = {"duration_ms": duration_ms, **extra}

    def _increment(self, key: str, amount: int) -> None:
        with self._lock:
            self._data["counts"][key] = self._data["counts"].get(key, 0) + amount

    def _set_count(self, key: str, value: int) -> None:
        with self._lock:
            self._data["counts"][key] = value

    def _set_audit(self, fields: dict) -> None:
        with self._lock:
            self._data["audit"].update(fields)

    def _record_db_operation(
        self,
        name: str,
        kind: str,
        duration_ms: float,
        queries: int,
        commits: int,
        rows: int | None,
        bulk: bool,
    ) -> None:
        with self._lock:
            self._data["counts"]["db_queries"] += queries
            self._data["counts"]["db_commits"] += commits
            self._add_timing_locked("database_reads_writes", duration_ms)
            self._add_timing_locked(f"database_{kind}s", duration_ms)
            event = {
                "name": name,
                "kind": kind,
                "duration_ms": duration_ms,
                "queries": queries,
                "commits": commits,
                "bulk": bulk,
            }
            if rows is not None:
                event["rows"] = rows
            self._data["events"]["db_operations"].append(event)

    def _record_embedding_batch(self, purpose: str, batch_size: int, vector_count: int, duration_ms: float) -> None:
        with self._lock:
            self._data["counts"]["embedding_calls"] += 1
            self._data["counts"]["embedding_texts"] += batch_size
            self._add_timing_locked("embedding_generation", duration_ms)
            self._data["events"]["embedding_batches"].append({
                "purpose": purpose,
                "batch_size": batch_size,
                "vector_count": vector_count,
                "duration_ms": duration_ms,
            })

    def _record_fastembed(self, created: bool, reused: bool, duration_ms: float, cache_info) -> None:
        event = {"created": created, "reused": reused, "duration_ms": duration_ms}
        if cache_info is not None:
            event["cache"] = {
                "hits": cache_info.hits,
                "misses": cache_info.misses,
                "maxsize": cache_info.maxsize,
                "currsize": cache_info.currsize,
            }
        with self._lock:
            self._data["events"]["fastembed"].append(event)
            if created:
                self._data["timings_ms"]["fastembed_initialization"] = {"duration_ms": duration_ms}

    def _record_hybrid_retrieval(
        self,
        name: str,
        top_k: int,
        rows_scored: int,
        rows_returned: int,
        duration_ms: float,
    ) -> None:
        with self._lock:
            self._add_timing_locked("hybrid_retrieval_total", duration_ms)
            self._data["events"]["hybrid_retrieval"].append({
                "name": name,
                "top_k": top_k,
                "rows_scored": rows_scored,
                "rows_returned": rows_returned,
                "duration_ms": duration_ms,
            })

    def _record_openrouter_call(
        self,
        call_name: str,
        task: str,
        model: str,
        tool_name: str,
        duration_ms: float,
        status: str,
        error_class: str | None,
    ) -> None:
        with self._lock:
            self._data["counts"]["llm_calls"] += 1
            if status != "success":
                self._data["counts"]["llm_retries"] += 1
            self._add_timing_locked("openrouter_calls_total", duration_ms)
            event = {
                "call_name": call_name,
                "task": task,
                "model": model,
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "status": status,
            }
            if error_class:
                event["error_class"] = error_class
            self._data["events"]["openrouter_calls"].append(event)

    def _record_verification(
        self,
        name: str,
        duration_ms: float,
        citations_checked: int,
        citations_verified: int,
        fields_checked: int | None,
    ) -> None:
        with self._lock:
            self._data["counts"]["citations_checked"] += citations_checked
            self._add_timing_locked("verification_total", duration_ms)
            event = {
                "name": name,
                "duration_ms": duration_ms,
                "citations_checked": citations_checked,
                "citations_verified": citations_verified,
            }
            if fields_checked is not None:
                event["fields_checked"] = fields_checked
            self._data["events"]["verification"].append(event)

    def _finish(self, status: str) -> None:
        with self._lock:
            self._data["status"] = status
            self._data["total_ms"] = self.duration_ms(self._started)
            self._data["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _add_timing_locked(self, stage: str, duration_ms: float) -> None:
        existing = self._data["timings_ms"].get(stage)
        if existing is None:
            self._data["timings_ms"][stage] = {"duration_ms": duration_ms, "count": 1}
            return
        existing["duration_ms"] = round(existing.get("duration_ms", 0) + duration_ms, 1)
        existing["count"] = existing.get("count", 0) + 1

    def _safe(self, fn, *args, **kwargs) -> None:
        try:
            fn(*args, **kwargs)
        except Exception:
            return
