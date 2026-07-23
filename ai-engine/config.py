"""
Shared configuration for the AI Engine.

All settings are loaded from environment variables with sensible defaults
so the system works out-of-the-box inside Docker Compose and can be
overridden for local development.
"""

import os

# ======================== Database ========================
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "devops_logs")
DB_USER = os.getenv("DB_USER", "devops")
DB_PASSWORD = os.getenv("DB_PASSWORD", "devops_secret")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ======================== Log Monitoring ========================
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/app/logs/app.log")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))

# ======================== Embedding Model ========================
# all-MiniLM-L6-v2 produces 384-dimensional vectors — must match
# the vector(384) column in the PostgreSQL error_logs table.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ======================== RAG Settings ========================
SIMILARITY_TOP_K = 3  # Number of similar past errors to retrieve
