#!/bin/bash
set -e

echo "=========================================="
echo "  AI Engine Starting..."
echo "  Agent: Google Gemini 1.5 Flash"
echo "  Dashboard: Streamlit"
echo "=========================================="

# Start the Gemini RAG agent in the background
echo "[entrypoint] Starting log monitoring agent..."
python agent.py &
AGENT_PID=$!
echo "[entrypoint] Agent started (PID: $AGENT_PID)"

# Start Streamlit in the foreground
echo "[entrypoint] Starting Streamlit dashboard..."
exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
