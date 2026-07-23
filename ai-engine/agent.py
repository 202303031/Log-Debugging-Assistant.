"""
agent.py — Autonomous RAG Pipeline & Log Monitoring Agent

Architecture: Log Tail → Stack Trace Extraction → Embedding (MiniLM-L6-v2)
            → pgvector Storage → Similarity Retrieval → Gemini 1.5 Flash
            → Root-Cause Analysis → Dashboard

This agent watches the Java victim service's log file for ERROR/EXCEPTION
entries, embeds them as 384-dim vectors via sentence-transformers, stores
them in PostgreSQL with pgvector for similarity search, and uses Google
Gemini 1.5 Flash (via LangChain) to perform root-cause analysis and
generate corrected Java code.

Requires a GOOGLE_API_KEY environment variable for Gemini access.
"""

import re
import sys
import time
import asyncio
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path

from sentence_transformers import SentenceTransformer

import config

# ======================== Logging Setup ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("agent")

# ======================== Globals ========================
embedding_model: SentenceTransformer | None = None


# ======================== Database Helpers ========================

def get_db_connection():
    """Create a new database connection with pgvector support."""
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
    psycopg2.extras.register_uuid()
    return conn


def wait_for_db(max_retries: int = 30, delay: int = 3) -> bool:
    """Block until PostgreSQL accepts connections (max ~90 s)."""
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            conn.close()
            logger.info("Database connection established.")
            return True
        except psycopg2.OperationalError:
            logger.warning(
                f"DB not ready (attempt {attempt + 1}/{max_retries}), "
                f"retrying in {delay}s..."
            )
            time.sleep(delay)
    logger.error("Failed to connect to database after max retries.")
    return False


# ======================== Embedding ========================

def init_embedding_model() -> None:
    """Load the all-MiniLM-L6-v2 sentence-transformers model."""
    global embedding_model
    logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
    embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    logger.info("Embedding model loaded successfully.")


def embed_text(text: str) -> list[float]:
    """Encode a string into a 384-dimensional vector."""
    return embedding_model.encode(text).tolist()


# ======================== Stack Trace Parsing ========================

def extract_exception_type(stack_trace: str) -> str:
    """Pull the top-level exception class name from a Java stack trace."""
    patterns = [
        r"(\w+(?:\.\w+)*(?:Exception|Error|Throwable))",
        r"Caused by:\s+(\w+(?:\.\w+)*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, stack_trace)
        if match:
            return match.group(1).split(".")[-1]
    return "UnknownException"


# ======================== pgvector CRUD ========================

def store_error(
    raw_message: str, embedding: list[float], exception_type: str
) -> int | None:
    """Insert an error log entry + its embedding vector into PostgreSQL."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO error_logs
                    (timestamp, log_level, service_name,
                     raw_message, embedding, exception_type)
                VALUES (%s, %s, %s, %s, %s::vector, %s)
                RETURNING id
                """,
                (
                    datetime.now(),
                    "ERROR",
                    "victim-service",
                    raw_message,
                    str(embedding),
                    exception_type,
                ),
            )
            error_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Stored error #{error_id} ({exception_type})")
            return error_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to store error: {e}")
        return None
    finally:
        conn.close()


def find_similar_errors(
    embedding: list[float], exclude_id: int | None = None
) -> list[dict]:
    """Return the top-K most similar past errors via cosine distance."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT id, timestamp, exception_type, raw_message, ai_analysis,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM error_logs
                WHERE embedding IS NOT NULL
            """
            params: list = [str(embedding)]

            if exclude_id:
                query += " AND id != %s"
                params.append(exclude_id)

            query += " ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([str(embedding), config.SIMILARITY_TOP_K])

            cur.execute(query, params)
            return [
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "exception_type": row[2],
                    "raw_message": row[3],
                    "ai_analysis": row[4],
                    "similarity": float(row[5]) if row[5] else 0.0,
                }
                for row in cur.fetchall()
            ]
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        return []
    finally:
        conn.close()


def update_analysis(error_id: int, analysis: str) -> None:
    """Persist the AI-generated root-cause analysis back to the DB."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE error_logs SET ai_analysis = %s WHERE id = %s",
                (analysis, error_id),
            )
            conn.commit()
            logger.info(f"Updated analysis for error #{error_id}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update analysis: {e}")
    finally:
        conn.close()


# ======================== Gemini AI Agent ========================

async def generate_analysis(
    new_error: str, similar_errors: list[dict]
) -> str:
    """
    Use Google Gemini 1.5 Flash via LangChain to generate root-cause
    analysis and corrected Java code for the given stack trace.
    """

    # ── Build RAG context from similar past errors ──────────────
    context_parts: list[str] = []
    for i, err in enumerate(similar_errors, 1):
        ctx = f"### Past Error #{i} (similarity: {err['similarity']:.2%})\n"
        ctx += f"**Type:** {err['exception_type']}\n"
        ctx += f"**Time:** {err['timestamp']}\n"
        ctx += f"```\n{err['raw_message'][:500]}\n```\n"
        if err.get("ai_analysis"):
            ctx += f"**Previous Analysis:** {err['ai_analysis'][:300]}\n"
        context_parts.append(ctx)

    context = (
        "\n---\n".join(context_parts)
        if context_parts
        else "No similar past errors found in the vector store."
    )

    # ── Compose the user prompt ─────────────────────────────────
    user_prompt = f"""## New Error Stack Trace
```
{new_error}
```

## Similar Past Errors (retrieved via pgvector cosine similarity)
{context}

## Instructions
1. **Root Cause Analysis**: Explain exactly why this exception occurred.
   Reference the specific class, method, and the logical error in the code.
2. **Impact Assessment**: Describe the impact of this bug on the system.
3. **Corrected Java Code**: Provide the fixed version of the buggy code.
   Show the complete corrected method.
4. **Prevention**: Suggest how to prevent this class of errors in the future.

Format your response in clear Markdown with code blocks for Java code."""

    system_prompt = (
        "You are a senior Java engineer and DevOps specialist. "
        "Based on these past logs, explain why this new stack trace "
        "occurred and provide the corrected Java code. Be specific "
        "about the bug, reference exact class names and line patterns, "
        "and provide production-ready fixed code."
    )

    # ── Check for API key ──────────────────────────────────────
    if not config.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is not set. Cannot generate analysis.")
        return "⚠️ **Analysis unavailable:** `GOOGLE_API_KEY` is not configured. Please set it in your environment or Streamlit secrets."

    # ── Run the Gemini agent ───────────────────────────────────
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage

        chat = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.3,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = chat.invoke(messages)
        return response.content

    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        return f"⚠️ **Agent analysis failed:** {str(e)}"


# ======================== RAG Pipeline Orchestrator ========================

async def process_error(raw_message: str) -> None:
    """Full RAG pipeline: embed → store → retrieve → generate → update."""
    logger.info("Processing new error entry...")

    # 1. Extract exception type
    exception_type = extract_exception_type(raw_message)
    logger.info(f"Exception type: {exception_type}")

    # 2. Generate 384-dim embedding
    embedding = embed_text(raw_message)

    # 3. Store in PostgreSQL + pgvector
    error_id = store_error(raw_message, embedding, exception_type)
    if error_id is None:
        return

    # 4. Retrieve similar past errors (cosine similarity)
    similar = find_similar_errors(embedding, exclude_id=error_id)
    logger.info(f"Found {len(similar)} similar past errors")

    # 5. Generate root-cause analysis via Gemini
    analysis = await generate_analysis(raw_message, similar)

    # 6. Persist analysis
    update_analysis(error_id, analysis)

    logger.info(f"Completed processing error #{error_id} ({exception_type})")


# ======================== Log Tail Monitor ========================

async def tail_log_file() -> None:
    """
    Continuously monitor the Java service's log file for new
    ERROR / EXCEPTION entries using file-seek position tracking.

    When a multi-line stack trace is detected (ERROR line followed
    by \\tat / Caused by lines), the full trace is dispatched to
    the async RAG pipeline.
    """
    log_path = Path(config.LOG_FILE_PATH)
    logger.info(f"Watching log file: {log_path}")

    # Wait for the log file to appear (victim service may start slowly)
    while not log_path.exists():
        logger.info(f"Log file not found, waiting... ({log_path})")
        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)

    # Start from the current end of the file
    file_size = log_path.stat().st_size
    logger.info(f"Log file found ({file_size} bytes). Starting tail...")

    error_buffer: list[str] = []
    in_stack_trace = False
    loops_without_new_lines = 0

    while True:
        try:
            current_size = log_path.stat().st_size

            if current_size < file_size:
                # File was rotated / truncated by logback
                logger.info("Log file rotated. Resetting position.")
                file_size = 0

            if current_size > file_size:
                loops_without_new_lines = 0
                with open(log_path, "r", errors="replace") as f:
                    f.seek(file_size)
                    new_lines = f.readlines()
                    file_size = current_size

                for line in new_lines:
                    stripped = line.strip()
                    if not stripped:
                        continue

                    # Standard Java log line starts with YYYY-MM-DD
                    is_log_header = bool(re.match(r"^\d{4}-\d{2}-\d{2}", stripped))

                    if is_log_header:
                        # Flush previous trace
                        if error_buffer:
                            await process_error("\n".join(error_buffer))
                            error_buffer = []
                        
                        if "ERROR" in stripped or "Exception" in stripped or "Error" in stripped:
                            error_buffer.append(stripped)
                            in_stack_trace = True
                        else:
                            in_stack_trace = False

                    elif in_stack_trace:
                        # Append any continuation lines to the current trace
                        error_buffer.append(stripped)

                    elif not in_stack_trace:
                        # Detect manual stack trace pasting (no timestamp header)
                        is_exception_name = bool(re.match(r"^[a-zA-Z0-9_.]+(?:Exception|Error)", stripped))
                        if is_exception_name:
                            error_buffer.append(stripped)
                            in_stack_trace = True
            else:
                loops_without_new_lines += 1
                # If no new lines for ~2 seconds, flush the buffer (handles EOF / manual inserts)
                if loops_without_new_lines > 1 and error_buffer:
                    await process_error("\n".join(error_buffer))
                    error_buffer = []
                    in_stack_trace = False

            await asyncio.sleep(config.POLL_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"Error in log tail loop: {e}", exc_info=True)
            await asyncio.sleep(config.POLL_INTERVAL_SECONDS)


# ======================== Entrypoint ========================

async def main() -> None:
    """Bootstrap the agent: DB wait → load models → tail logs."""
    logger.info("=" * 60)
    logger.info("Autonomous DevOps & Log Debugging Agent starting...")
    logger.info(f"Deployment mode: {config.DEPLOYMENT_MODE}")
    logger.info(f"LLM: Google Gemini ({config.GEMINI_MODEL})")
    logger.info("=" * 60)

    # Check for API key
    if not config.GOOGLE_API_KEY:
        logger.warning(
            "⚠️  GOOGLE_API_KEY is not set! AI analysis will not work. "
            "Get a free key at https://aistudio.google.com/apikey"
        )

    # Wait for PostgreSQL
    if not wait_for_db():
        sys.exit(1)

    # Load the embedding model (sentence-transformers)
    init_embedding_model()

    # Start the async log monitoring loop
    logger.info("Starting log file monitoring...")
    await tail_log_file()


if __name__ == "__main__":
    asyncio.run(main())
