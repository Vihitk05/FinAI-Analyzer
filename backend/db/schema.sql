CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL DEFAULT '',
    currency TEXT NOT NULL DEFAULT '',
    analysis_date TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    data JSONB NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'completed';
ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE reports ADD COLUMN IF NOT EXISTS company_id INTEGER;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS public_id UUID NOT NULL DEFAULT gen_random_uuid();

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, normalized_name)
);

ALTER TABLE companies ADD COLUMN IF NOT EXISTS public_id UUID NOT NULL DEFAULT gen_random_uuid();

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'reports_company_id_fkey') THEN
        ALTER TABLE reports ADD CONSTRAINT reports_company_id_fkey
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS company_dashboards (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    validation_status TEXT NOT NULL CHECK (validation_status IN ('valid', 'failed')),
    data JSONB NOT NULL,
    source_report_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (company_id, version)
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    embedding VECTOR(384) NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_jobs (
    id SERIAL PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'processing', 'awaiting_ocr', 'completed', 'failed')),
    stage TEXT NOT NULL DEFAULT 'uploaded'
        CHECK (stage IN ('uploaded', 'extracting', 'ocr', 'analysing', 'validating', 'saving', 'completed')),
    progress INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    file_name TEXT NOT NULL,
    file_bytes BYTEA,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS metrics JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS ocr_pages JSONB;
DO $$
BEGIN
    ALTER TABLE analysis_jobs DROP CONSTRAINT IF EXISTS analysis_jobs_status_check;
    ALTER TABLE analysis_jobs ADD CONSTRAINT analysis_jobs_status_check
        CHECK (status IN ('queued', 'processing', 'awaiting_ocr', 'completed', 'failed'));
END $$;

CREATE TABLE IF NOT EXISTS export_jobs (
    id SERIAL PRIMARY KEY,
    public_id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    format TEXT NOT NULL CHECK (format IN ('pptx', 'pdf')),
    status TEXT NOT NULL DEFAULT 'preparing'
        CHECK (status IN ('preparing', 'building', 'validating', 'converting', 'checking', 'completed', 'failed')),
    stage TEXT,
    error TEXT,
    file_size_bytes INTEGER,
    checksum TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS export_jobs_user_id_idx ON export_jobs (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS export_jobs_public_id_idx ON export_jobs (public_id);

CREATE INDEX IF NOT EXISTS document_chunks_report_id_idx ON document_chunks (report_id);
CREATE INDEX IF NOT EXISTS document_chunks_tsv_idx ON document_chunks USING GIN (tsv);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS reports_user_id_idx ON reports (user_id);
CREATE INDEX IF NOT EXISTS reports_user_id_created_at_idx ON reports (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS reports_company_id_idx ON reports (company_id);
CREATE UNIQUE INDEX IF NOT EXISTS reports_public_id_idx ON reports (public_id);
CREATE INDEX IF NOT EXISTS companies_user_id_idx ON companies (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS companies_public_id_idx ON companies (public_id);
CREATE UNIQUE INDEX IF NOT EXISTS company_dashboards_one_current_idx
    ON company_dashboards (company_id) WHERE is_current;

CREATE INDEX IF NOT EXISTS analysis_jobs_user_id_idx ON analysis_jobs (user_id);
CREATE INDEX IF NOT EXISTS analysis_jobs_status_idx ON analysis_jobs (status);
CREATE INDEX IF NOT EXISTS analysis_jobs_updated_at_idx ON analysis_jobs (updated_at);
