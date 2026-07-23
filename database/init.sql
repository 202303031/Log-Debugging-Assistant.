-- ============================================================
-- Autonomous DevOps & Log Debugging Assistant
-- PostgreSQL + pgvector initialization script
-- ============================================================

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the error_logs table
CREATE TABLE IF NOT EXISTS error_logs (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    log_level       VARCHAR(10) NOT NULL,
    service_name    VARCHAR(100) NOT NULL DEFAULT 'victim-service',
    raw_message     TEXT NOT NULL,
    embedding       vector(384),          -- all-MiniLM-L6-v2 produces 384-dim vectors
    ai_analysis     TEXT,                  -- LLM-generated root-cause + fix
    exception_type  VARCHAR(255),          -- e.g. NullPointerException
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create an index for fast similarity search (IVFFlat)
-- Using cosine distance operator (<=>)
-- We start with 1 list since initial data is small; rebuild with more lists as data grows
CREATE INDEX IF NOT EXISTS idx_error_logs_embedding
    ON error_logs
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 1);

-- Create a standard index on timestamp for dashboard queries
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp
    ON error_logs (timestamp DESC);

-- Create an index on log_level for filtering
CREATE INDEX IF NOT EXISTS idx_error_logs_level
    ON error_logs (log_level);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO devops;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO devops;
