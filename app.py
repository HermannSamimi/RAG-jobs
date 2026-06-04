import uuid
import streamlit as st

from ingestion.qdrant_store import ensure_history_collection, ensure_jobs_collection, get_client
from rag.pipeline import query

st.set_page_config(
    page_title="JobRAG — AI Job Search Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── bootstrap ──────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to Qdrant…")
def _init_db():
    client = get_client()
    ensure_jobs_collection(client)
    ensure_history_collection(client)
    return client

try:
    _init_db()
except Exception as e:
    st.error(f"Could not connect to Qdrant: {e}")
    st.stop()

# ── session state ──────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💼 JobRAG")
    st.caption("AI-powered job search assistant")
    st.divider()

    st.markdown("**Dataset**")
    st.caption("Software Engineer · Berlin, Germany")
    st.caption("Updated hourly via Airflow + Apify")

    st.divider()
    st.markdown("**Session**")
    st.caption(f"ID: `{st.session_state.session_id[:12]}…`")
    if st.button("New session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Qdrant Cloud · Gemma3:27b · qwen3-embedding:8b")


def _render_sources(sources: list) -> None:
    if not sources:
        return
    with st.expander(f"Sources — {len(sources)} job(s) retrieved"):
        for i, job in enumerate(sources, 1):
            score = job.get("score", "—")
            url = job.get("job_url")

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{i}. {job.get('title', 'N/A')}** — {job.get('company', 'N/A')}")
                st.caption(
                    f"{job.get('location', '')} | "
                    f"{job.get('seniority_level', '')} | "
                    f"{job.get('employment_type', '')} | "
                    f"score: {score}"
                )
            with col2:
                if url:
                    st.link_button("View job", url, use_container_width=True)

            with st.expander("Job description snippet"):
                st.text((job.get("description") or "No description available.")[:600] + "…")

            if i < len(sources):
                st.divider()


# ── main chat ──────────────────────────────────────────────────────────────────
st.markdown("# 💼 Job Search Assistant")
st.caption("Software Engineer jobs in Berlin, Germany — ask about skills, companies, salaries, requirements…")

# Suggested starter questions (shown only when chat is empty)
if not st.session_state.messages:
    st.markdown("#### Try asking:")
    cols = st.columns(3)
    suggestions = [
        "Which companies are actively hiring right now?",
        "What skills are most in demand?",
        "Are there any remote software engineer roles?",
        "What seniority levels are available?",
        "Which jobs require Python or Go?",
        "What are the most common job requirements?",
    ]
    for col, suggestion in zip(cols * 2, suggestions):
        with col:
            if st.button(suggestion, use_container_width=True):
                st.session_state._prefill = suggestion
                st.rerun()

# Replay full chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            _render_sources(msg["sources"])

# Handle suggestion pre-fill
prefill = st.session_state.pop("_prefill", None)

# Chat input
user_input = st.chat_input("Ask about Software Engineer jobs in Berlin…") or prefill

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "sources": None})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            stream, sources = query(
                user_message=user_input,
                user_id=st.session_state.user_id,
                session_id=st.session_state.session_id,
            )
            response_text = st.write_stream(stream)
            _render_sources(sources)
        except Exception as e:
            response_text = f"An error occurred: {e}"
            sources = []
            st.error(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": sources,
    })
    st.rerun()
