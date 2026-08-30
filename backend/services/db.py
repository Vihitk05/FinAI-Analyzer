import json
import os
import re
import uuid
from functools import lru_cache

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

from config import DATABASE_URL, JOB_MAX_RETRIES
from services.curation import (
    normalize_company_name,
    scrub_dashboard_public_ids,
    scrub_report_citation_ids,
)

_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "schema.sql")


class DatabaseError(Exception):
    pass


def _configure_connection(conn):
    register_vector(conn)


@lru_cache(maxsize=1)
def get_pool() -> ConnectionPool:
    pool = ConnectionPool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
        kwargs={"row_factory": dict_row},
        configure=_configure_connection,
        open=False,
    )
    pool.open()
    return pool


def check_connection():

    try:
        with get_pool().connection() as conn:
            conn.execute("SELECT 1")
    except psycopg.Error as exc:
        raise DatabaseError(f"Could not connect to Postgres at the configured DATABASE_URL: {exc}") from exc


def init_schema():

    with open(_SCHEMA_PATH) as f:
        sql = f.read()
    try:
        with get_pool().connection() as conn:
            conn.execute(sql)
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to apply schema: {exc}") from exc










def _valid_uuid(value) -> str | None:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        return None


def resolve_report_id(public_id, user_id: int) -> int | None:
    parsed = _valid_uuid(public_id)
    if parsed is None:
        return None
    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT id FROM reports WHERE public_id = %s AND user_id = %s", (parsed, user_id)
        ).fetchone()
    return row["id"] if row else None


def resolve_company_id(public_id, user_id: int) -> int | None:
    parsed = _valid_uuid(public_id)
    if parsed is None:
        return None
    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT id FROM companies WHERE public_id = %s AND user_id = %s", (parsed, user_id)
        ).fetchone()
    return row["id"] if row else None


def get_report_public_id(report_id: int) -> str:
    with get_pool().connection() as conn:
        row = conn.execute("SELECT public_id FROM reports WHERE id = %s", (report_id,)).fetchone()
    return str(row["public_id"])







def create_user(name: str, email: str, password_hash: str) -> dict:
    try:
        with get_pool().connection() as conn:
            row = conn.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, name, email, password_hash, created_at
                """,
                (name, email, password_hash),
            ).fetchone()
    except psycopg.errors.UniqueViolation as exc:
        raise DatabaseError("An account with this email already exists") from exc
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to create user: {exc}") from exc
    return dict(row)


def get_user_by_email(email: str) -> dict | None:
    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT id, name, email, password_hash, created_at FROM users WHERE email = %s", (email,)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT id, name, email, password_hash, created_at FROM users WHERE id = %s", (user_id,)
        ).fetchone()
    return dict(row) if row else None







def insert_report(data: dict, user_id: int | None = None, status: str = "completed") -> int:
    with get_pool().connection() as conn:
        row = conn.execute(
            """
            INSERT INTO reports (company_name, currency, analysis_date, data, user_id, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                data.get("companyName", ""),
                data.get("currency", ""),
                data.get("analysis_date", ""),
                json.dumps(data),
                user_id,
                status,
            ),
        ).fetchone()
        return row["id"]


def update_report(report_id: int, data: dict, status: str | None = None):
    with get_pool().connection() as conn:
        if status is None:
            conn.execute(
                """
                UPDATE reports
                SET company_name = %s, currency = %s, analysis_date = %s, data = %s, updated_at = now()
                WHERE id = %s
                """,
                (data.get("companyName", ""), data.get("currency", ""), data.get("analysis_date", ""), json.dumps(data), report_id),
            )
        else:
            conn.execute(
                """
                UPDATE reports
                SET company_name = %s, currency = %s, analysis_date = %s, data = %s, status = %s, updated_at = now()
                WHERE id = %s
                """,
                (
                    data.get("companyName", ""),
                    data.get("currency", ""),
                    data.get("analysis_date", ""),
                    json.dumps(data),
                    status,
                    report_id,
                ),
            )


def get_report(report_id: int, user_id: int) -> dict | None:
    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT id, public_id, status, updated_at, data FROM reports WHERE id = %s AND user_id = %s",
            (report_id, user_id),
        ).fetchone()
    if not row:
        return None
    result = dict(row["data"])
    result["custom_id"] = str(row["public_id"])
    result["status"] = row["status"]
    return scrub_report_citation_ids(result, result["custom_id"])


def list_reports(user_id: int, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:

    with get_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT id, public_id, status, created_at, updated_at, data FROM reports
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        ).fetchall()
        total = conn.execute("SELECT count(*) AS n FROM reports WHERE user_id = %s", (user_id,)).fetchone()["n"]

    results = []
    for row in rows:
        d = dict(row["data"])
        d["custom_id"] = str(row["public_id"])
        d["status"] = row["status"]
        results.append(scrub_report_citation_ids(d, d["custom_id"]))
    return results, total


def report_exists(report_id: int, user_id: int) -> bool:
    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM reports WHERE id = %s AND user_id = %s", (report_id, user_id)
        ).fetchone()
    return row is not None


def delete_report(report_id: int, user_id: int) -> bool:
    with get_pool().connection() as conn:
        row = conn.execute(
            "DELETE FROM reports WHERE id = %s AND user_id = %s RETURNING id", (report_id, user_id)
        ).fetchone()
    return row is not None







def insert_chunks(report_id: int, chunks: list[dict]):

    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM document_chunks WHERE report_id = %s", (report_id,))
            if chunks:
                cur.executemany(
                    "INSERT INTO document_chunks (report_id, page_number, text, embedding) VALUES (%s, %s, %s, %s)",
                    [(report_id, c["page_number"], c["text"], c["embedding"]) for c in chunks],
                )


def get_report_filename(report_id: int) -> str:

    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT file_name FROM analysis_jobs WHERE report_id = %s ORDER BY created_at DESC LIMIT 1", (report_id,)
        ).fetchone()
    return row["file_name"] if row else "Uploaded report.pdf"


def upsert_company(user_id: int, name: str) -> dict | None:
    normalized = normalize_company_name(name)
    if not normalized:
        return None
    with get_pool().connection() as conn:
        row = conn.execute(
            """
            INSERT INTO companies (user_id, name, normalized_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, normalized_name)
            DO UPDATE SET name = EXCLUDED.name, updated_at = now()
            RETURNING id, public_id, user_id, name, normalized_name, created_at, updated_at
            """,
            (user_id, name.strip(), normalized),
        ).fetchone()



    return dict(row)


def assign_report_company(report_id: int, company_id: int):
    with get_pool().connection() as conn:
        conn.execute("UPDATE reports SET company_id = %s, updated_at = now() WHERE id = %s", (company_id, report_id))


def get_company(company_id: int, user_id: int) -> dict | None:

    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT public_id, user_id, name, normalized_name, created_at, updated_at FROM companies WHERE id = %s AND user_id = %s",
            (company_id, user_id),
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["id"] = str(result.pop("public_id"))
    return result


def list_companies(user_id: int) -> list[dict]:



    with get_pool().connection() as conn:
        legacy = conn.execute(
            "SELECT id, company_name FROM reports WHERE user_id = %s AND status = 'completed' AND company_id IS NULL AND company_name <> ''",
            (user_id,),
        ).fetchall()
    for report in legacy:
        company = upsert_company(user_id, report["company_name"])
        if company:
            assign_report_company(report["id"], company["id"])
    with get_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.public_id, c.name, c.updated_at, count(r.id) AS report_count,
                   d.version AS dashboard_version, d.generated_at
            FROM companies c
            LEFT JOIN reports r ON r.company_id = c.id AND r.status = 'completed'
            LEFT JOIN company_dashboards d ON d.company_id = c.id AND d.is_current
            WHERE c.user_id = %s
            GROUP BY c.id, d.version, d.generated_at
            HAVING count(r.id) > 0
            ORDER BY c.updated_at DESC
            """, (user_id,)
        ).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        d["id"] = str(d.pop("public_id"))
        d["updated_at"] = row["updated_at"].isoformat() if row["updated_at"] else None
        d["generated_at"] = row["generated_at"].isoformat() if row["generated_at"] else None
        results.append(d)
    return results


def list_company_reports(company_id: int, user_id: int) -> list[dict]:
    with get_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.public_id, r.status, r.created_at, r.updated_at, r.data
            FROM reports r JOIN companies c ON c.id = r.company_id
            WHERE r.company_id = %s AND c.user_id = %s AND r.status = 'completed'
            ORDER BY r.created_at, r.id
            """, (company_id, user_id),
        ).fetchall()
    result = []
    for row in rows:
        data = dict(row["data"])
        data.update({"custom_id": str(row["public_id"]), "status": row["status"], "created_at": row["created_at"].isoformat() if row["created_at"] else None})
        result.append(scrub_report_citation_ids(data, data["custom_id"]))
    return result


def list_company_report_ids(company_id: int, user_id: int) -> list[dict]:

    with get_pool().connection() as conn:
        rows = conn.execute(
            """
            SELECT r.id, r.public_id
            FROM reports r JOIN companies c ON c.id = r.company_id
            WHERE r.company_id = %s AND c.user_id = %s AND r.status = 'completed'
            ORDER BY r.created_at, r.id
            """, (company_id, user_id),
        ).fetchall()
    return [{"id": row["id"], "custom_id": str(row["public_id"])} for row in rows]


def publish_company_dashboard(company_id: int, data: dict, source_report_ids: list[str]) -> dict:

    if data.get("validationStatus") != "valid":
        raise DatabaseError("Refusing to publish a dashboard that did not pass validation")
    with get_pool().connection() as conn:
        with conn.transaction():


            conn.execute("SELECT pg_advisory_xact_lock(%s)", (company_id,))
            latest = conn.execute(
                "SELECT version FROM company_dashboards WHERE company_id = %s ORDER BY version DESC LIMIT 1 FOR UPDATE",
                (company_id,),
            ).fetchone()
            version = (latest["version"] if latest else 0) + 1
            conn.execute("UPDATE company_dashboards SET is_current = FALSE WHERE company_id = %s AND is_current", (company_id,))
            row = conn.execute(
                """
                INSERT INTO company_dashboards (company_id, version, validation_status, data, source_report_ids, published_at, is_current)
                VALUES (%s, %s, 'valid', %s, %s, now(), TRUE)
                RETURNING id, version, generated_at, published_at
                """, (company_id, version, json.dumps(data), json.dumps(source_report_ids))
            ).fetchone()
    return dict(row)


def get_current_company_dashboard(company_id: int, user_id: int) -> dict | None:
    with get_pool().connection() as conn:
        row = conn.execute(
            """
            SELECT d.version, d.data, d.generated_at, d.published_at
            FROM company_dashboards d JOIN companies c ON c.id = d.company_id
            WHERE d.company_id = %s AND c.user_id = %s AND d.is_current AND d.validation_status = 'valid'
            """, (company_id, user_id)
        ).fetchone()
    if not row:
        return None
    data = dict(row["data"])
    data.update({"dashboardVersion": row["version"], "generatedAt": row["generated_at"].isoformat() if row["generated_at"] else None, "publishedAt": row["published_at"].isoformat() if row["published_at"] else None})
    return scrub_dashboard_public_ids(data)


def update_chunk_texts(report_id: int, pages: list[dict]) -> int:

    if not pages:
        return 0
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                UPDATE document_chunks SET text = %s
                WHERE report_id = %s AND page_number = %s AND text IS DISTINCT FROM %s
                """,
                [(page["text"], report_id, page["page_number"], page["text"]) for page in pages],
            )
            return cur.rowcount


def get_chunks(report_id: int) -> list[dict]:
    with get_pool().connection() as conn:
        rows = conn.execute(
            "SELECT page_number, text FROM document_chunks WHERE report_id = %s ORDER BY page_number",
            (report_id,),
        ).fetchall()
    return [dict(r) for r in rows]


_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_MAX_TSQUERY_TERMS = 30


def build_or_tsquery(query_text: str) -> tuple[str, list[str]]:

    words = _WORD_RE.findall(query_text)
    seen: set[str] = set()
    unique_words = []
    for word in words:
        lowered = word.lower()
        if lowered not in seen:
            seen.add(lowered)
            unique_words.append(word)
    unique_words = unique_words[:_MAX_TSQUERY_TERMS] or [query_text or ""]

    expr = " || ".join(["plainto_tsquery('english', %s)"] * len(unique_words))
    return f"({expr})", unique_words


def scored_chunks_for_query(report_id: int, query_text: str, query_embedding: list[float]) -> list[dict]:

    tsquery_expr, tsquery_params = build_or_tsquery(query_text)
    sql = f"""
        SELECT page_number, text,
               ts_rank_cd(tsv, {tsquery_expr}) AS text_score,
               1 - (embedding <=> %s::vector) AS vector_score
        FROM document_chunks
        WHERE report_id = %s
    """
    params = [*tsquery_params, query_embedding, report_id]
    with get_pool().connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]







def create_job(job_id: str, user_id: int, report_id: int, file_name: str, file_bytes: bytes) -> dict:
    with get_pool().connection() as conn:
        row = conn.execute(
            """
            INSERT INTO analysis_jobs (job_id, user_id, report_id, file_name, file_bytes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, job_id, user_id, report_id, status, stage, progress, retry_count, error,
                      metrics, created_at, updated_at, started_at, completed_at
            """,
            (job_id, user_id, report_id, file_name, psycopg.Binary(file_bytes)),
        ).fetchone()
    return dict(row)


def get_job(job_id: str, user_id: int) -> dict | None:
    with get_pool().connection() as conn:
        row = conn.execute(
            """
            SELECT j.id, j.job_id, j.user_id, j.report_id, r.public_id AS report_public_id,
                   j.status, j.stage, j.progress, j.retry_count, j.error,
                   j.metrics, j.created_at, j.updated_at, j.started_at, j.completed_at
            FROM analysis_jobs j JOIN reports r ON r.id = j.report_id
            WHERE j.job_id = %s AND j.user_id = %s
            """,
            (job_id, user_id),
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["report_public_id"] = str(result["report_public_id"])
    return result


def get_latest_job_for_report(report_id: int, user_id: int) -> dict | None:

    with get_pool().connection() as conn:
        row = conn.execute(
            """
            SELECT j.id, j.job_id, j.user_id, j.report_id, r.public_id AS report_public_id,
                   j.status, j.stage, j.progress, j.retry_count, j.error,
                   j.metrics, j.created_at, j.updated_at, j.started_at, j.completed_at
            FROM analysis_jobs j JOIN reports r ON r.id = j.report_id
            WHERE j.report_id = %s AND j.user_id = %s
            ORDER BY j.created_at DESC LIMIT 1
            """,
            (report_id, user_id),
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["report_public_id"] = str(result["report_public_id"])
    return result


def claim_next_queued_job() -> dict | None:

    with get_pool().connection() as conn:
        row = conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'processing', stage = 'extracting', started_at = now(), updated_at = now()
            WHERE id = (
                SELECT id FROM analysis_jobs
                WHERE status = 'queued'
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, job_id, user_id, report_id, status, stage, progress, retry_count, error,
                      metrics, file_name, file_bytes, ocr_pages, created_at, updated_at, started_at, completed_at
            """
        ).fetchone()
    return dict(row) if row else None


def update_job_progress(job_id: str, stage: str, progress: int):
    with get_pool().connection() as conn:
        conn.execute(
            "UPDATE analysis_jobs SET stage = %s, progress = %s, updated_at = now() WHERE job_id = %s",
            (stage, progress, job_id),
        )


def update_job_metrics(job_id: str, metrics: dict):

    with get_pool().connection() as conn:
        conn.execute(
            "UPDATE analysis_jobs SET metrics = %s, updated_at = now() WHERE job_id = %s",
            (json.dumps(metrics), job_id),
        )


def complete_job(job_id: str):
    with get_pool().connection() as conn:
        conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'completed', stage = 'completed', progress = 100,
                completed_at = now(), updated_at = now(), file_bytes = NULL
            WHERE job_id = %s
            """,
            (job_id,),
        )


def requeue_job(job_id: str, error: str):

    with get_pool().connection() as conn:
        conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'queued', stage = 'uploaded', progress = 0,
                retry_count = retry_count + 1, error = %s, updated_at = now()
            WHERE job_id = %s
            """,
            (error, job_id),
        )


def fail_job(job_id: str, error: str):
    with get_pool().connection() as conn:
        conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'failed', error = %s, completed_at = now(), updated_at = now(), file_bytes = NULL
            WHERE job_id = %s
            """,
            (error, job_id),
        )


def mark_job_awaiting_ocr(job_id: str, metrics: dict):

    with get_pool().connection() as conn:
        conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'awaiting_ocr', stage = 'ocr', progress = 10,
                metrics = %s, updated_at = now()
            WHERE job_id = %s
            """,
            (json.dumps(metrics), job_id),
        )


def get_awaiting_ocr_job_bytes(job_id: str, user_id: int) -> tuple[bytes, str] | None:

    with get_pool().connection() as conn:
        row = conn.execute(
            "SELECT file_bytes, file_name FROM analysis_jobs "
            "WHERE job_id = %s AND user_id = %s AND status = 'awaiting_ocr'",
            (job_id, user_id),
        ).fetchone()
    if not row or row["file_bytes"] is None:
        return None
    return bytes(row["file_bytes"]), row["file_name"]


def attach_client_ocr_and_requeue(job_id: str, user_id: int, pages: list[dict]) -> bool:

    with get_pool().connection() as conn:
        row = conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'queued', stage = 'uploaded', progress = 0,
                ocr_pages = %s, error = NULL, updated_at = now()
            WHERE job_id = %s AND user_id = %s AND status = 'awaiting_ocr'
            RETURNING id
            """,
            (json.dumps(pages), job_id, user_id),
        ).fetchone()
    return row is not None


def fail_awaiting_ocr_job(job_id: str, user_id: int, error: str) -> bool:

    with get_pool().connection() as conn:
        row = conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'failed', error = %s, completed_at = now(),
                updated_at = now(), file_bytes = NULL
            WHERE job_id = %s AND user_id = %s AND status = 'awaiting_ocr'
            RETURNING id
            """,
            (error, job_id, user_id),
        ).fetchone()
    return row is not None


def fail_stale_awaiting_ocr_jobs(timeout_seconds: int) -> int:

    with get_pool().connection() as conn:
        rows = conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'failed', completed_at = now(), updated_at = now(), file_bytes = NULL,
                error = 'OCR was not completed in time. Please re-upload this document.'
            WHERE status = 'awaiting_ocr'
              AND updated_at < now() - (%s || ' seconds')::interval
            RETURNING id
            """,
            (timeout_seconds,),
        ).fetchall()
    return len(rows)


def requeue_stale_jobs(stale_after_seconds: int) -> int:

    with get_pool().connection() as conn:
        rows = conn.execute(
            """
            UPDATE analysis_jobs
            SET status = 'queued', stage = 'uploaded', progress = 0,
                retry_count = retry_count + 1,
                error = 'Recovered after an interrupted processing attempt', updated_at = now()
            WHERE status = 'processing'
              AND updated_at < now() - (%s || ' seconds')::interval
              AND retry_count < %s
            RETURNING id
            """,
            (stale_after_seconds, JOB_MAX_RETRIES),
        ).fetchall()
        stale_ids = [r["id"] for r in rows]
        conn.execute(
            """
            UPDATE analysis_jobs SET status = 'failed', error = 'Gave up after repeated interrupted attempts',
                   completed_at = now(), updated_at = now(), file_bytes = NULL
            WHERE status = 'processing' AND updated_at < now() - (%s || ' seconds')::interval AND retry_count >= %s
            """,
            (stale_after_seconds, JOB_MAX_RETRIES),
        )
    return len(stale_ids)







def create_export_job(user_id: int, company_id: int, fmt: str) -> dict:
    with get_pool().connection() as conn:
        row = conn.execute(
            """
            INSERT INTO export_jobs (user_id, company_id, format, status, stage)
            VALUES (%s, %s, %s, 'preparing', 'preparing')
            RETURNING id, public_id, status, stage
            """,
            (user_id, company_id, fmt),
        ).fetchone()
    return dict(row)


def update_export_job_stage(export_job_id: int, stage: str):
    with get_pool().connection() as conn:
        conn.execute("UPDATE export_jobs SET stage = %s WHERE id = %s", (stage, export_job_id))


def complete_export_job(export_job_id: int, file_size_bytes: int, checksum: str):
    with get_pool().connection() as conn:
        conn.execute(
            """
            UPDATE export_jobs
            SET status = 'completed', stage = 'completed', file_size_bytes = %s, checksum = %s, completed_at = now()
            WHERE id = %s
            """,
            (file_size_bytes, checksum, export_job_id),
        )


def fail_export_job(export_job_id: int, stage: str, error: str):
    with get_pool().connection() as conn:
        conn.execute(
            "UPDATE export_jobs SET status = 'failed', stage = %s, error = %s, completed_at = now() WHERE id = %s",
            (stage, error, export_job_id),
        )
