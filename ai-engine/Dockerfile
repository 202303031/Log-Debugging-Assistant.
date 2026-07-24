# ============================================
# AI Engine Dockerfile
# Runs both the Gemini RAG agent and Streamlit
# ============================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
COPY agent-requirements.txt .
RUN pip install --default-timeout=1000 --retries 5 --upgrade pip && \
    pip install --default-timeout=1000 --retries 5 --no-cache-dir \
    -r requirements.txt -r agent-requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Pre-download the embedding model during build (avoids runtime latency)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Entrypoint: run Gemini agent in background, Streamlit in foreground
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
