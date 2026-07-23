#!/bin/bash
# ============================================================
# push-to-github.sh
# Initialize Git repo, commit all files, and push to GitHub.
# ============================================================

set -e

# ── Configuration ──────────────────────────────────────────
# Replace with your actual GitHub repository URL
REPO_URL="${1:-https://github.com/YOUR_USERNAME/autonomous-devops-assistant.git}"
BRANCH="main"

echo "=========================================="
echo "  Pushing to GitHub"
echo "  Repo: $REPO_URL"
echo "=========================================="

# ── Initialize Git ─────────────────────────────────────────
if [ ! -d ".git" ]; then
    echo "[1/5] Initializing Git repository..."
    git init
    git branch -M "$BRANCH"
else
    echo "[1/5] Git repository already initialized."
fi

# ── Add all files ──────────────────────────────────────────
echo "[2/5] Staging all files..."
git add -A

# ── Commit ─────────────────────────────────────────────────
echo "[3/5] Committing..."
git commit -m "feat: initial commit — Autonomous DevOps & Log Debugging Assistant

- Java Spring Boot victim service with intentional bugs
  (NullPointerException, ArrayIndexOutOfBoundsException,
   StringIndexOutOfBoundsException, memory leak)
- PostgreSQL + pgvector for vector similarity search
- Python LangChain RAG pipeline (agent.py)
- Streamlit dashboard (app.py)
- Docker Compose orchestration
- Shared log volume architecture"

# ── Set remote ─────────────────────────────────────────────
echo "[4/5] Setting remote origin..."
if git remote get-url origin &>/dev/null; then
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi

# ── Push ───────────────────────────────────────────────────
echo "[5/5] Pushing to $BRANCH..."
git push -u origin "$BRANCH"

echo ""
echo "=========================================="
echo "  ✅ Successfully pushed to GitHub!"
echo "  $REPO_URL"
echo "=========================================="
