# ============================================
# AI Engine Dockerfile
# Runs both the Antigravity agent and Streamlit
# ============================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (includes google-antigravity SDK)
COPY requirements.txt .
RUN pip install --default-timeout=1000 --upgrade pip && pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Pre-download the embedding model during build (avoids runtime latency)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Entrypoint: run Antigravity agent in background, Streamlit in foreground
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
