"""
app.py — Streamlit Dashboard for the Autonomous DevOps Assistant

Connects to PostgreSQL, displays recent errors in a sidebar, and
renders the raw stack trace alongside the Antigravity Agent's
AI-generated root-cause analysis and suggested Java code fix.
"""

import streamlit as st
import psycopg2
import config

st.set_page_config(page_title="DevOps Debug Assistant", page_icon="🔍", layout="wide")


@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
    )


def fetch_errors(limit=25):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, timestamp, exception_type, raw_message, ai_analysis "
            "FROM error_logs ORDER BY timestamp DESC LIMIT %s", (limit,)
        )
        return cur.fetchall()


# ── Sidebar: Recent Errors ──────────────────────────────────────
st.sidebar.title("🚨 Recent Errors")
errors = fetch_errors()

# ── Layout: Dual Tabs ───────────────────────────────────────────
tab1, tab2 = st.tabs(["📡 Live Monitoring", "🛠️ Manual Debugger"])

with tab1:
    if not errors:
        st.title("🔍 Autonomous DevOps & Log Debugging Assistant")
        st.info("The system is monitoring logs. Errors will appear here automatically.")
    else:
        selected_id = None
        for err in errors:
            eid, ts, etype, _, _ = err
            label = f"**#{eid}** `{etype}`  \n{ts:%H:%M:%S}"
            if st.sidebar.button(label, key=f"err_{eid}", use_container_width=True):
                selected_id = eid
        
        if selected_id is None:
            selected_id = errors[0][0]  # default to most recent
            
        selected = next((e for e in errors if e[0] == selected_id), errors[0])
        eid, ts, etype, raw_msg, analysis = selected
        
        import re
        
        # Parse File and Line Number from Stack Trace
        file_line_match = re.search(r"at .*?\((.*?\.java:\d+)\)", raw_msg)
        file_line_info = file_line_match.group(1) if file_line_match else "Unknown Location"
        
        st.title(f"🔍 Error #{eid}: `{etype}`")
        st.caption(f"Detected at **{ts:%Y-%m-%d %H:%M:%S}** from **victim-service**")
        
        # Display as sleek metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Exception Type", etype.split('.')[-1])
        col2.metric("File & Line", file_line_info)
        col3.metric("Service", "victim-service")
        
        st.divider()
        
        st.subheader("📋 Raw Stack Trace")
        st.code(raw_msg, language="java")
        
        st.divider()
        st.subheader("🤖 AI Root-Cause Analysis & Suggested Fix")
        if analysis:
            st.markdown(analysis)
            
            # Download Post-Mortem Report Button
            report_content = f"# Post-Mortem Report: Error #{eid}\n\n## Summary\n**Exception Type:** {etype}\n**File/Line:** {file_line_info}\n**Timestamp:** {ts}\n\n## Raw Stack Trace\n```java\n{raw_msg}\n```\n\n## AI Root-Cause Analysis & Fix\n{analysis}"
            st.download_button(
                label="📥 Download Post-Mortem Report",
                data=report_content,
                file_name=f"post-mortem-error-{eid}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.warning("Analysis pending — the Antigravity agent is still processing this error.")
            with st.spinner("Agent is generating root-cause analysis..."):
                import time
                time.sleep(2)
                st.rerun()

with tab2:
    st.title("🛠️ Manual Debugger")
    st.write("Paste a raw Java stack trace below. The AI Agent will process it as if it were intercepted in real-time from the application logs.")
    
    manual_log = st.text_area("Raw Stack Trace / Log Entry", height=300, placeholder="Paste your stack trace here...")
    
    if st.button("🚀 Trigger AI Analysis", use_container_width=True, type="primary"):
        if manual_log.strip():
            # Append to the shared log file to trigger the watchdog in agent.py
            with open(config.LOG_FILE_PATH, "a") as f:
                f.write(f"\n{manual_log.strip()}\n")
            
            st.success("✅ Stack trace injected into the log stream! The AI Agent is now processing it.")
            with st.spinner("Waiting for the AI Agent to process the logs..."):
                import time
                time.sleep(3)
                st.cache_resource.clear()
                st.rerun()
        else:
            st.error("Please paste a stack trace first.")

# ── Auto-refresh ────────────────────────────────────────────────
st.sidebar.divider()
if st.sidebar.button("🔄 Refresh", use_container_width=True):
    st.cache_resource.clear()
    st.rerun()
