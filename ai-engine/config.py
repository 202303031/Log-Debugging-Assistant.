"""
Shared configuration for the AI Engine.

All settings are loaded from environment variables (or Streamlit secrets on
Streamlit Community Cloud) with sensible defaults so the system works
out-of-the-box inside Docker Compose and can be overridden for cloud deployment.

Supports two deployment modes:
  - DOCKER: Full stack with local pgvector, Java victim, and background agent
  - CLOUD:  Streamlit Community Cloud with Supabase pgvector and Gemini API
"""

import os

# ======================== Streamlit Secrets Adapter ========================
# On Streamlit Community Cloud, secrets are injected via st.secrets.
# We bridge them into os.environ so the rest of the config stays uniform.

def _get(key: str, default: str = "") -> str:
    """Read from env vars first, then Streamlit secrets, then default."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


# ======================== Deployment Mode ========================
# Auto-detect: if DATABASE_URL is set, we are likely on Supabase/Cloud
DATABASE_URL = _get("DATABASE_URL", "")
DEPLOYMENT_MODE = "CLOUD" if DATABASE_URL else "DOCKER"

# ======================== Database ========================
if DATABASE_URL:
    # Parse Supabase-style connection string
    # Format: postgresql://user:password@host:port/dbname
    from urllib.parse import urlparse
    _parsed = urlparse(DATABASE_URL)
    DB_HOST = _parsed.hostname or "localhost"
    DB_PORT = str(_parsed.port or 5432)
    DB_NAME = (_parsed.path or "/postgres").lstrip("/")
    DB_USER = _parsed.username or "postgres"
    DB_PASSWORD = _parsed.password or ""
else:
    DB_HOST = _get("DB_HOST", "postgres")
    DB_PORT = _get("DB_PORT", "5432")
    DB_NAME = _get("DB_NAME", "devops_logs")
    DB_USER = _get("DB_USER", "devops")
    DB_PASSWORD = _get("DB_PASSWORD", "devops_secret")

# ======================== Google AI (Gemini) ========================
GOOGLE_API_KEY = _get("GOOGLE_API_KEY", "")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-1.5-flash")

# ======================== Log Monitoring ========================
LOG_FILE_PATH = _get("LOG_FILE_PATH", "/app/logs/app.log")
POLL_INTERVAL_SECONDS = int(_get("POLL_INTERVAL_SECONDS", "5"))

# ======================== Embedding Model ========================
# all-MiniLM-L6-v2 produces 384-dimensional vectors — must match
# the vector(384) column in the PostgreSQL error_logs table.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ======================== RAG Settings ========================
SIMILARITY_TOP_K = 3  # Number of similar past errors to retrieve
