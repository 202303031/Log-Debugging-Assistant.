"""
app.py — Streamlit Dashboard for the Autonomous DevOps Assistant

Features:
  - 3D interactive Three.js topology header
  - Live Monitoring tab (reads errors from pgvector database)
  - Manual Debugger tab (calls Gemini directly, no background agent needed)
  - Side-by-side stack trace + AI analysis layout
  - Dual download: Markdown post-mortem + JSON incident payload
  - Cache management controls
"""

import json
import re
import streamlit as st
import streamlit.components.v1 as components
import psycopg2
from datetime import datetime

import config

# ======================== Page Config ========================
st.set_page_config(
    page_title="DevOps Debug Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================== Custom CSS ========================
st.markdown("""
<style>
    /* Dark glassmorphism cards */
    .stMetric {
        background: rgba(20, 20, 40, 0.6);
        border: 1px solid rgba(100, 100, 255, 0.15);
        border-radius: 12px;
        padding: 12px;
        backdrop-filter: blur(10px);
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a1a 0%, #111128 100%);
    }
    /* Download buttons */
    .stDownloadButton > button {
        border: 1px solid rgba(100, 200, 255, 0.3);
        background: rgba(20, 30, 60, 0.5);
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        border-color: rgba(100, 200, 255, 0.7);
        background: rgba(30, 50, 90, 0.7);
        box-shadow: 0 0 20px rgba(100, 200, 255, 0.15);
    }
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ======================== 3D Topology Header ========================
THREE_JS_HEADER = """
<div id="three-container" style="width:100%;height:220px;border-radius:16px;overflow:hidden;margin-bottom:8px;position:relative;">
<canvas id="topology-canvas"></canvas>
<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none;z-index:10;">
  <h1 style="color:#e0e8ff;font-family:'Segoe UI',system-ui,sans-serif;font-size:28px;margin:0;text-shadow:0 0 40px rgba(100,150,255,0.5);">
    🔍 Autonomous DevOps Assistant
  </h1>
  <p style="color:rgba(180,200,255,0.7);font-size:14px;margin:4px 0 0 0;letter-spacing:2px;">
    AI-POWERED LOG ANALYSIS • REAL-TIME MONITORING
  </p>
</div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){
  const canvas = document.getElementById('topology-canvas');
  const container = document.getElementById('three-container');
  const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
  renderer.setSize(container.clientWidth, 220);
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setClearColor(0x06060f, 1);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, container.clientWidth/220, 0.1, 1000);
  camera.position.z = 30;

  // Create floating nodes
  const nodes = [];
  const nodeGeo = new THREE.SphereGeometry(0.35, 16, 16);
  const colors = [0x4488ff, 0x44ffaa, 0xff6644, 0xaa44ff, 0xffaa44];
  for(let i=0; i<45; i++){
    const mat = new THREE.MeshBasicMaterial({color: colors[i%colors.length], transparent:true, opacity:0.8});
    const mesh = new THREE.Mesh(nodeGeo, mat);
    mesh.position.set(
      (Math.random()-0.5)*40,
      (Math.random()-0.5)*16,
      (Math.random()-0.5)*20
    );
    mesh.userData = {
      vx: (Math.random()-0.5)*0.015,
      vy: (Math.random()-0.5)*0.015,
      vz: (Math.random()-0.5)*0.01
    };
    scene.add(mesh);
    nodes.push(mesh);
  }

  // Create glowing edges between nearby nodes
  const lineMat = new THREE.LineBasicMaterial({color:0x2244aa, transparent:true, opacity:0.2});
  const edgeLines = [];
  for(let i=0; i<nodes.length; i++){
    for(let j=i+1; j<nodes.length; j++){
      if(nodes[i].position.distanceTo(nodes[j].position) < 12){
        const geo = new THREE.BufferGeometry().setFromPoints([nodes[i].position, nodes[j].position]);
        const line = new THREE.Line(geo, lineMat.clone());
        line.userData = {i, j};
        scene.add(line);
        edgeLines.push(line);
      }
    }
  }

  // Ambient glow
  const ambientLight = new THREE.AmbientLight(0x334466, 0.5);
  scene.add(ambientLight);

  // Mouse interaction
  let mouseX = 0, mouseY = 0;
  container.addEventListener('mousemove', (e) => {
    const rect = container.getBoundingClientRect();
    mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
  });

  // Animation loop
  let time = 0;
  function animate(){
    requestAnimationFrame(animate);
    time += 0.008;

    // Animate nodes
    nodes.forEach((n, idx) => {
      n.position.x += n.userData.vx;
      n.position.y += n.userData.vy + Math.sin(time + idx) * 0.003;
      n.position.z += n.userData.vz;
      // Bounce at boundaries
      if(Math.abs(n.position.x)>22) n.userData.vx *= -1;
      if(Math.abs(n.position.y)>9) n.userData.vy *= -1;
      if(Math.abs(n.position.z)>12) n.userData.vz *= -1;
      // Pulse opacity
      n.material.opacity = 0.5 + 0.3 * Math.sin(time*2 + idx*0.7);
    });

    // Update edge positions
    edgeLines.forEach(line => {
      const {i, j} = line.userData;
      const positions = new Float32Array([
        nodes[i].position.x, nodes[i].position.y, nodes[i].position.z,
        nodes[j].position.x, nodes[j].position.y, nodes[j].position.z
      ]);
      line.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const dist = nodes[i].position.distanceTo(nodes[j].position);
      line.material.opacity = Math.max(0, 0.3 - dist * 0.02);
    });

    // Camera follows mouse
    camera.position.x += (mouseX * 5 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 3 - camera.position.y) * 0.02;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
  }
  animate();

  // Resize handler
  window.addEventListener('resize', () => {
    renderer.setSize(container.clientWidth, 220);
    camera.aspect = container.clientWidth / 220;
    camera.updateProjectionMatrix();
  });
})();
</script>
"""

components.html(THREE_JS_HEADER, height=230)


# ======================== Database Connection ========================

@st.cache_resource
def get_connection():
    """Connect to PostgreSQL (Supabase or local Docker)."""
    try:
        if getattr(config, "DATABASE_URL", None):
            conn = psycopg2.connect(config.DATABASE_URL, sslmode="require" if config.DEPLOYMENT_MODE == "CLOUD" else "prefer")
        else:
            conn = psycopg2.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                sslmode="prefer",
            )
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None


def fetch_errors(limit=25):
    """Fetch recent errors from the database."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, timestamp, exception_type, raw_message, ai_analysis "
                "FROM error_logs ORDER BY timestamp DESC LIMIT %s",
                (limit,),
            )
            return cur.fetchall()
    except Exception as e:
        st.error(f"Query failed: {e}")
        return []


# ======================== Gemini Direct Call ========================

def call_gemini(stack_trace: str) -> str:
    """Call Gemini 1.5 Flash directly from the dashboard for manual debugging."""
    if not config.GOOGLE_API_KEY:
        return "⚠️ **GOOGLE_API_KEY is not set.** Please add it to your environment variables or Streamlit secrets. Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)"

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage

        chat = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.3,
        )

        system_prompt = (
            "You are a senior Java engineer and DevOps specialist. "
            "Analyze the given stack trace, explain the root cause of the bug, "
            "describe the impact, provide the corrected Java code, and suggest "
            "prevention strategies. Format your response in clear Markdown."
        )

        user_prompt = f"""## Stack Trace to Analyze
```
{stack_trace}
```

## Instructions
1. **Root Cause Analysis**: Explain exactly why this exception occurred.
   Reference the specific class, method, and the logical error in the code.
2. **Impact Assessment**: Describe the impact of this bug on the system.
3. **Corrected Java Code**: Provide the fixed version of the buggy code.
   Show the complete corrected method.
4. **Prevention**: Suggest how to prevent this class of errors in the future.

Format your response in clear Markdown with code blocks for Java code."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = chat.invoke(messages)
        return response.content

    except Exception as e:
        return f"⚠️ **Analysis failed:** {str(e)}"


def store_manual_error(raw_message: str, exception_type: str, analysis: str):
    """Store a manually analyzed error into the database."""
    conn = get_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO error_logs
                    (timestamp, log_level, service_name,
                     raw_message, exception_type, ai_analysis)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    datetime.now(),
                    "ERROR",
                    "manual-debugger",
                    raw_message,
                    exception_type,
                    analysis,
                ),
            )
            error_id = cur.fetchone()[0]
            conn.commit()
            return error_id
    except Exception as e:
        conn.rollback()
        st.error(f"Failed to store: {e}")
        return None


# ======================== Report Generators ========================

def generate_md_report(eid, ts, etype, file_line, raw_msg, analysis):
    """Generate a structured Markdown post-mortem report."""
    return f"""# 📋 Post-Mortem Report: Incident #{eid}

---

## Summary

| Field | Value |
|-------|-------|
| **Incident ID** | #{eid} |
| **Exception Type** | `{etype}` |
| **File / Line** | `{file_line}` |
| **Detected At** | {ts} |
| **Service** | victim-service |

---

## Raw Stack Trace

```java
{raw_msg}
```

---

## AI Root-Cause Analysis & Suggested Fix

{analysis or '_Analysis pending..._'}

---

*Generated by Autonomous DevOps & Log Debugging Assistant*
*Powered by Google Gemini 1.5 Flash + pgvector RAG*
"""


def generate_json_report(eid, ts, etype, file_line, raw_msg, analysis):
    """Generate a JSON incident payload for downstream integrations."""
    return json.dumps(
        {
            "incident_id": eid,
            "exception_type": etype,
            "file_line": file_line,
            "timestamp": str(ts),
            "service": "victim-service",
            "raw_stack_trace": raw_msg,
            "ai_analysis": analysis,
            "generated_at": datetime.now().isoformat(),
            "engine": f"Google Gemini ({config.GEMINI_MODEL})",
        },
        indent=2,
        ensure_ascii=False,
    )


# ======================== Sidebar ========================

st.sidebar.title("🚨 Recent Errors")

errors = fetch_errors()

# ── Cache Management ──
st.sidebar.divider()
st.sidebar.subheader("⚡ System Controls")

col_cache, col_refresh = st.sidebar.columns(2)
with col_cache:
    if st.button("🗑️ Clear Cache", use_container_width=True, key="clear_cache"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.sidebar.success("✅ Cache cleared!")
        st.rerun()
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True, key="refresh"):
        st.cache_resource.clear()
        st.rerun()

# ── Deployment Info ──
st.sidebar.divider()
st.sidebar.caption(f"🌐 Mode: **{config.DEPLOYMENT_MODE}**")
st.sidebar.caption(f"🤖 LLM: **{config.GEMINI_MODEL}**")
api_status = "✅ Connected" if config.GOOGLE_API_KEY else "❌ Missing"
st.sidebar.caption(f"🔑 API Key: **{api_status}**")


# ======================== Tabs ========================

tab1, tab2 = st.tabs(["📡 Live Monitoring", "🛠️ Manual Debugger"])


# ── Tab 1: Live Monitoring ──────────────────────────────────────

with tab1:
    if not errors:
        st.info(
            "📡 The system is monitoring logs. Errors will appear here "
            "automatically when the background agent detects them."
        )
    else:
        # Sidebar error list
        selected_id = None
        for err in errors:
            eid, ts, etype, _, _ = err
            label = f"**#{eid}** `{etype}`  \n{ts:%H:%M:%S}"
            if st.sidebar.button(label, key=f"err_{eid}", use_container_width=True):
                selected_id = eid

        if selected_id is None:
            selected_id = errors[0][0]

        selected = next((e for e in errors if e[0] == selected_id), errors[0])
        eid, ts, etype, raw_msg, analysis = selected

        # Parse file/line info
        file_line_match = re.search(r"at .*?\((.*?\.java:\d+)\)", raw_msg or "")
        file_line_info = file_line_match.group(1) if file_line_match else "Unknown"

        # ── Header Metrics ──
        st.subheader(f"🔍 Incident #{eid}: `{etype}`")
        st.caption(f"Detected at **{ts:%Y-%m-%d %H:%M:%S}**")

        m1, m2, m3 = st.columns(3)
        m1.metric("Exception Type", etype.split(".")[-1])
        m2.metric("File & Line", file_line_info)
        m3.metric("Service", "victim-service")

        st.divider()

        # ── Side-by-Side: Stack Trace + Analysis ──
        left, right = st.columns([1, 1])

        with left:
            st.subheader("📋 Raw Stack Trace")
            st.code(raw_msg, language="java")

        with right:
            st.subheader("🤖 AI Root-Cause Analysis")
            if analysis:
                st.markdown(analysis)
            else:
                st.warning("⏳ Analysis pending — the agent is still processing.")
                import time
                time.sleep(2)
                st.rerun()

        # ── Dual Download Buttons ──
        st.divider()
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                label="📥 Download Report (.md)",
                data=generate_md_report(eid, ts, etype, file_line_info, raw_msg, analysis),
                file_name=f"incident-{eid}-report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                label="📦 Download JSON (.json)",
                data=generate_json_report(eid, ts, etype, file_line_info, raw_msg, analysis),
                file_name=f"incident-{eid}-payload.json",
                mime="application/json",
                use_container_width=True,
            )


# ── Tab 2: Manual Debugger ──────────────────────────────────────

with tab2:
    st.subheader("🛠️ Manual Debugger")
    st.write(
        "Paste a Java stack trace below. Gemini 1.5 Flash will analyze it "
        "in real-time and generate a root-cause report with corrected code."
    )

    manual_log = st.text_area(
        "Raw Stack Trace / Log Entry",
        height=250,
        placeholder="Paste your stack trace here...\n\njava.lang.NullPointerException: ...\n\tat com.example.MyClass.method(MyClass.java:42)",
    )

    if st.button("🚀 Analyze with Gemini AI", use_container_width=True, type="primary"):
        if manual_log.strip():
            with st.spinner("🤖 Gemini is analyzing your stack trace..."):
                analysis = call_gemini(manual_log.strip())

            # Extract exception type
            exc_type = "UnknownException"
            exc_match = re.search(r"(\w+(?:\.\w+)*(?:Exception|Error|Throwable))", manual_log)
            if exc_match:
                exc_type = exc_match.group(1).split(".")[-1]

            # Store in database
            error_id = store_manual_error(manual_log.strip(), exc_type, analysis)

            st.success(f"✅ Analysis complete! Stored as Incident #{error_id}" if error_id else "✅ Analysis complete!")

            # Display results side-by-side
            st.divider()
            left, right = st.columns([1, 1])

            with left:
                st.subheader("📋 Your Stack Trace")
                st.code(manual_log.strip(), language="java")

            with right:
                st.subheader("🤖 AI Analysis & Fix")
                st.markdown(analysis)

            # Parse file/line
            fl_match = re.search(r"at .*?\((.*?\.java:\d+)\)", manual_log)
            fl_info = fl_match.group(1) if fl_match else "Unknown"

            # Download buttons
            st.divider()
            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button(
                    label="📥 Download Report (.md)",
                    data=generate_md_report(
                        error_id or "manual", datetime.now(), exc_type,
                        fl_info, manual_log.strip(), analysis,
                    ),
                    file_name=f"manual-debug-report.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="manual_md",
                )
            with dl2:
                st.download_button(
                    label="📦 Download JSON (.json)",
                    data=generate_json_report(
                        error_id or "manual", datetime.now(), exc_type,
                        fl_info, manual_log.strip(), analysis,
                    ),
                    file_name=f"manual-debug-payload.json",
                    mime="application/json",
                    use_container_width=True,
                    key="manual_json",
                )
        else:
            st.error("⚠️ Please paste a stack trace first.")
