<div align="center">

# 🔍 Autonomous DevOps & Log Debugging Assistant

**An AI-powered system that autonomously monitors a buggy Java service, detects errors in real time, and generates root-cause analysis with corrected code — powered by Google Gemini 1.5 Flash and pgvector RAG.**

[![Java](https://img.shields.io/badge/Java-17-ED8B00?logo=openjdk&logoColor=white)](https://openjdk.org/)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2-6DB33F?logo=spring-boot&logoColor=white)](https://spring.io/projects/spring-boot)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-1.5_Flash-4285F4?logo=google&logoColor=white)](https://aistudio.google.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

</div>

---

## ✨ Features

- **3D Interactive Dashboard** — Three.js animated topology header with floating nodes
- **Real-Time Log Monitoring** — Autonomous agent tails Java service logs for exceptions
- **AI Root-Cause Analysis** — Gemini 1.5 Flash generates detailed bug explanations + corrected Java code
- **RAG Pipeline** — pgvector similarity search retrieves relevant past errors for context
- **Manual Debugger** — Paste any stack trace and get instant AI analysis
- **Dual Report Export** — Download structured Markdown reports and JSON payloads
- **Free Cloud Deployment** — Deploy on Streamlit Community Cloud + Supabase (zero cost)

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Docker / Cloud
        VS["☕ Java Victim Service<br/><i>Spring Boot 3.2</i>"]
        LF["📁 Shared Log Volume<br/><i>/app/logs/app.log</i>"]
        AG["🐍 AI Agent<br/><i>Gemini RAG Pipeline</i>"]
        DB["🐘 PostgreSQL + pgvector<br/><i>384-dim vectors</i>"]
        ST["📊 Streamlit Dashboard<br/><i>3D Interactive UI</i>"]
        GM["🤖 Google Gemini<br/><i>1.5 Flash API</i>"]
    end

    VS -->|"writes structured logs"| LF
    LF -->|"tails for ERROR/EXCEPTION"| AG
    AG -->|"embed via MiniLM-L6-v2"| DB
    AG -->|"cosine similarity search"| DB
    AG -->|"prompt with RAG context"| GM
    GM -->|"root-cause + code fix"| AG
    AG -->|"stores AI analysis"| DB
    DB -->|"queries errors + analyses"| ST
```

### Data Flow

```
Java Error → Logback → app.log → Agent Tail → Stack Trace Extraction
    → MiniLM-L6-v2 Embedding (384-dim) → pgvector INSERT
    → Cosine Similarity Retrieval (top-3) → Gemini 1.5 Flash
    → Root-Cause Analysis + Code Fix → pgvector UPDATE
    → Streamlit Dashboard renders results
```

---

## 🚀 Zero-Cost Cloud Deployment

Deploy the full dashboard for **free** using Streamlit Community Cloud + Supabase.

### Step 1: Get a Free Google API Key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key — you'll need it in Step 3

### Step 2: Set Up Free Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project (choose any region, set a database password)
3. Once the project is ready, go to **Settings → Database → Connection string (URI)**
4. Copy the connection string (it looks like `postgresql://postgres.xxxx:password@aws-0-region.pooler.supabase.com:5432/postgres`)
5. Go to **SQL Editor** and run this query to enable pgvector and create the table:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the error_logs table
CREATE TABLE IF NOT EXISTS error_logs (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    log_level       VARCHAR(10) NOT NULL,
    service_name    VARCHAR(100) NOT NULL DEFAULT 'victim-service',
    raw_message     TEXT NOT NULL,
    embedding       vector(384),
    ai_analysis     TEXT,
    exception_type  VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp
    ON error_logs (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_error_logs_level
    ON error_logs (log_level);
```

### Step 3: Deploy to Streamlit Community Cloud

1. Push this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"** and select your repository
4. Set the **Main file path** to: `ai-engine/app.py`
5. Click **"Advanced settings"** → **"Secrets"** and paste:

```toml
GOOGLE_API_KEY = "your-google-api-key-from-step-1"
DATABASE_URL = "your-supabase-connection-string-from-step-2"
```

6. Click **"Deploy"** — your app will be live in ~2 minutes! 🎉

### That's it! Share the URL with your friends.

---

## 🖥️ Local Development (Docker)

### Prerequisites

- **Docker** & **Docker Compose** v2.20+
- A `GOOGLE_API_KEY` (free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))

### 1. Clone & Configure

```bash
git clone https://github.com/202303031/Log-Debugging-Assistant..git
cd "Log-Debugging-Assistant."

# Set your API key
export GOOGLE_API_KEY="your-key-here"
```

### 2. Build & Start

```bash
docker compose up --build -d
```

This launches:
- **PostgreSQL** with pgvector schema initialized
- **Java Victim Service** generating logs with random bugs
- **AI Engine** monitoring logs + Streamlit dashboard

### 3. Open the Dashboard

```
http://localhost:8501
```

---

## 🧩 Components

### 1. Victim Service (Java 17 + Spring Boot 3.2)

A simulated backend with intentionally buggy algorithms:

| Algorithm | Bug Type | Exception | Root Cause |
|-----------|----------|-----------|------------|
| **Facility Location** | Off-by-one | `NullPointerException` | Map lookup with out-of-range key |
| **Bin Packing** (FFD) | Undersized array | `ArrayIndexOutOfBoundsException` | Array allocated at `n/2` |
| **Array/String Ops** | Empty string | `StringIndexOutOfBoundsException` | `charAt(0)` without check |

### 2. AI Engine (Python + Gemini + sentence-transformers)

RAG pipeline: **Tail → Extract → Embed → Store → Retrieve → Generate → Persist**

### 3. Dashboard (Streamlit + Three.js)

- 3D interactive topology header
- Side-by-side stack trace + AI analysis
- Dual export (Markdown + JSON)
- Cache management controls

---

## 📁 Project Structure

```
Log-Debugging-Assistant/
│
├── docker-compose.yml                  # 3-service orchestration
├── README.md
├── .gitignore
│
├── victim-service/                     # ☕ Java Spring Boot 3.2
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/main/java/com/devops/victim/
│       ├── VictimApplication.java
│       ├── config/AppConfig.java
│       ├── scheduler/TaskScheduler.java
│       └── algorithms/
│           ├── FacilityLocation.java
│           ├── BinPacking.java
│           └── ArrayStringOps.java
│
├── database/
│   └── init.sql                        # pgvector schema + indexes
│
├── ai-engine/                          # 🐍 Python 3.11
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── config.py                       # Auto-detects Docker vs Cloud
│   ├── agent.py                        # Async RAG pipeline + Gemini
│   ├── app.py                          # Streamlit + Three.js dashboard
│   └── .streamlit/
│       ├── config.toml                 # Dark theme
│       └── secrets.toml.example        # Template for secrets
│
└── logs/
    └── .gitkeep
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | *(required)* | Google AI Studio API key for Gemini |
| `DATABASE_URL` | *(optional)* | Full Supabase connection string (cloud mode) |
| `DB_HOST` | `postgres` | PostgreSQL hostname (Docker mode) |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `devops_logs` | Database name |
| `DB_USER` | `devops` | Database user |
| `DB_PASSWORD` | `devops_secret` | Database password |
| `LOG_FILE_PATH` | `/app/logs/app.log` | Path to Java log file |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Which Gemini model to use |

---

## 🛠️ Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                       │
├──────────────┬──────────────────┬───────────────────────┤
│  Java 17     │  Python 3.11     │  PostgreSQL 16        │
│  Spring Boot │  Gemini 1.5 Flash│  pgvector extension   │
│  Logback     │  LangChain       │  IVFFlat indexing     │
│  Maven       │  Streamlit       │  384-dim vectors      │
│  @Scheduled  │  Three.js        │  cosine distance      │
│              │  sentence-xfmrs  │                       │
└──────────────┴──────────────────┴───────────────────────┘
```

---

## 📄 License

MIT
