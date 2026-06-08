import html
import uuid
import streamlit as st

from ingestion.qdrant_store import ensure_history_collection, ensure_jobs_collection, get_client
from rag.pipeline import query

st.set_page_config(
    page_title="JobRAG — Job Search Assistant",
    page_icon=":material/work:",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Serif+Display&display=swap');

    :root {
        --bg: #f6f7fb;
        --surface: #ffffff;
        --surface-muted: #f1f3f9;
        --border: #e4e8f1;
        --text: #0f172a;
        --text-muted: #64748b;
        --accent: #4f46e5;
        --accent-soft: #eef2ff;
        --accent-hover: #4338ca;
        --success: #059669;
        --radius: 14px;
        --shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06);
    }

    .stApp {
        background: linear-gradient(180deg, #f8f9fc 0%, var(--bg) 220px, var(--bg) 100%);
        font-family: "DM Sans", system-ui, sans-serif;
        color: var(--text);
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 920px;
    }

    [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    .jr-brand {
        font-family: "DM Serif Display", Georgia, serif;
        font-size: 1.65rem;
        font-weight: 400;
        letter-spacing: -0.02em;
        color: var(--text);
        margin: 0 0 0.25rem 0;
        line-height: 1.1;
    }

    .jr-tagline {
        color: var(--text-muted);
        font-size: 0.9rem;
        margin: 0 0 1.5rem 0;
        line-height: 1.5;
    }

    .jr-hero {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: calc(var(--radius) + 4px);
        padding: 2rem 2.25rem;
        margin-bottom: 1.75rem;
        box-shadow: var(--shadow);
    }

    .jr-hero h1 {
        font-family: "DM Serif Display", Georgia, serif;
        font-size: 2.35rem;
        font-weight: 400;
        letter-spacing: -0.03em;
        margin: 0 0 0.6rem 0;
        color: var(--text);
        line-height: 1.15;
    }

    .jr-hero p {
        color: var(--text-muted);
        font-size: 1.05rem;
        margin: 0;
        line-height: 1.6;
        max-width: 52ch;
    }

    .jr-pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1.25rem;
    }

    .jr-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: var(--surface-muted);
        border: 1px solid var(--border);
        color: var(--text-muted);
        font-size: 0.78rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }

    .jr-section-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin: 0 0 0.65rem 0;
    }

    .jr-panel {
        background: var(--surface-muted);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
    }

    .jr-panel-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--text);
        margin: 0 0 0.35rem 0;
    }

    .jr-panel-text {
        font-size: 0.84rem;
        color: var(--text-muted);
        margin: 0;
        line-height: 1.55;
    }

    .jr-session-id {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.78rem;
        color: var(--accent);
        background: var(--accent-soft);
        padding: 0.45rem 0.6rem;
        border-radius: 8px;
        word-break: break-all;
        margin-bottom: 0.75rem;
    }

    .jr-stack {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        font-size: 0.82rem;
        color: var(--text-muted);
    }

    .jr-stack strong {
        color: var(--text);
        font-weight: 600;
    }

    .jr-suggestions-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text);
        margin: 0 0 0.85rem 0;
    }

    div[data-testid="stChatMessage"] {
        background: transparent;
        border: none;
        padding: 0.35rem 0;
    }

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.15rem;
        box-shadow: var(--shadow);
    }

    div[data-testid="stChatMessage"][data-testid*="user"] [data-testid="stMarkdownContainer"],
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
        background: var(--accent-soft);
        border-color: #c7d2fe;
    }

    .jr-sources-header {
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin: 1.25rem 0 0.75rem 0;
    }

    .jr-source-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.15rem;
        margin-bottom: 0.65rem;
        box-shadow: var(--shadow);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .jr-source-card:hover {
        border-color: #c7d2fe;
        box-shadow: 0 4px 18px rgba(79, 70, 229, 0.08);
    }

    .jr-source-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text);
        margin: 0 0 0.2rem 0;
        line-height: 1.35;
    }

    .jr-source-company {
        font-size: 0.88rem;
        color: var(--accent);
        font-weight: 500;
        margin: 0 0 0.65rem 0;
    }

    .jr-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-bottom: 0.75rem;
    }

    .jr-meta-tag {
        font-size: 0.74rem;
        font-weight: 500;
        color: var(--text-muted);
        background: var(--surface-muted);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
    }

    .jr-score {
        font-size: 0.74rem;
        font-weight: 600;
        color: var(--success);
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
    }

    .jr-source-desc {
        font-size: 0.86rem;
        color: var(--text-muted);
        line-height: 1.6;
        margin: 0;
    }

    div[data-testid="stChatInput"] {
        padding-bottom: 1rem;
    }

    div[data-testid="stChatInput"] textarea {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--surface);
        box-shadow: var(--shadow);
    }

    div[data-testid="stChatInput"] textarea:focus {
        border-color: #a5b4fc;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
    }

    .stButton > button {
        border-radius: 10px;
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        font-weight: 500;
        font-size: 0.86rem;
        padding: 0.55rem 0.85rem;
        transition: all 0.15s ease;
        box-shadow: none;
    }

    .stButton > button:hover {
        border-color: #a5b4fc;
        background: var(--accent-soft);
        color: var(--accent-hover);
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    .jr-primary-btn .stButton > button {
        background: var(--accent);
        border-color: var(--accent);
        color: white;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    .jr-primary-btn .stButton > button:hover {
        background: var(--accent-hover);
        border-color: var(--accent-hover);
        color: white;
    }

    .stLinkButton > a {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
    }

    #MainMenu, footer, header[data-testid="stHeader"] {
        visibility: visible;
    }
</style>
"""

SUGGESTIONS = [
    "Which companies are actively hiring right now?",
    "What skills are most in demand?",
    "Are there any remote software engineer roles?",
    "What seniority levels are available?",
    "Which jobs require Python or Go?",
    "What are the most common job requirements?",
]


@st.cache_resource(show_spinner="Connecting to knowledge base…")
def _init_db():
    client = get_client()
    ensure_jobs_collection(client)
    ensure_history_collection(client)
    return client


def _render_sources(sources: list) -> None:
    if not sources:
        return
    st.markdown(
        f'<p class="jr-sources-header">Retrieved sources · {len(sources)}</p>',
        unsafe_allow_html=True,
    )
    for job in sources:
        title = html.escape(job.get("title") or "Untitled role")
        company = html.escape(job.get("company") or "Unknown company")
        score = html.escape(str(job.get("score", "—")))
        location = html.escape(job.get("location") or "")
        seniority = html.escape(job.get("seniority_level") or "")
        employment = html.escape(job.get("employment_type") or "")
        description = job.get("description") or "No description available."
        truncated = len(description) > 420
        desc_preview = html.escape(description[:420] + ("…" if truncated else ""))

        tags_html = ""
        if location:
            tags_html += f'<span class="jr-meta-tag">{location}</span>'
        if seniority:
            tags_html += f'<span class="jr-meta-tag">{seniority}</span>'
        if employment:
            tags_html += f'<span class="jr-meta-tag">{employment}</span>'
        tags_html += f'<span class="jr-score">Match {score}</span>'

        st.markdown(
            f"""
            <div class="jr-source-card">
                <p class="jr-source-title">{title}</p>
                <p class="jr-source-company">{company}</p>
                <div class="jr-meta-row">{tags_html}</div>
                <p class="jr-source-desc">{desc_preview}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if job.get("job_url"):
            st.link_button("Open listing", job["job_url"], use_container_width=False)


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<p class="jr-brand">JobRAG</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="jr-tagline">Semantic search over live job listings, grounded answers from retrieved context.</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<p class="jr-section-label">Dataset</p>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="jr-panel">
                <p class="jr-panel-title">Software Engineer · Berlin</p>
                <p class="jr-panel-text">Germany-focused listings refreshed on a scheduled ingestion pipeline.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<p class="jr-section-label">Session</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="jr-session-id">{st.session_state.session_id[:16]}…</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="jr-primary-btn">', unsafe_allow_html=True)
        if st.button("Start new session", use_container_width=True, type="primary"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<p class="jr-section-label">Stack</p>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="jr-stack">
                <span><strong>Vector store</strong> Qdrant Cloud</span>
                <span><strong>Embeddings</strong> qwen3-embedding:8b</span>
                <span><strong>Chat model</strong> gemma3:27b</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_hero() -> None:
    st.markdown(
        """
        <div class="jr-hero">
            <h1>Find the right role, faster.</h1>
            <p>
                Ask natural-language questions about Software Engineer openings in Berlin.
                Every answer is grounded in retrieved listings from the knowledge base.
            </p>
            <div class="jr-pill-row">
                <span class="jr-pill">Berlin, Germany</span>
                <span class="jr-pill">Software Engineer</span>
                <span class="jr-pill">RAG-powered answers</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_suggestions() -> None:
    st.markdown('<p class="jr-suggestions-title">Suggested questions</p>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(suggestion, use_container_width=True, key=f"suggest_{i}"):
                st.session_state._prefill = suggestion
                st.rerun()


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

try:
    _init_db()
except Exception as e:
    st.error(f"Could not connect to the knowledge base: {e}")
    st.stop()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

_render_sidebar()
_render_hero()

if not st.session_state.messages:
    _render_suggestions()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            _render_sources(msg["sources"])

prefill = st.session_state.pop("_prefill", None)
user_input = st.chat_input("Ask about roles, skills, companies, or requirements…") or prefill

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
            response_text = f"Something went wrong while generating a response: {e}"
            sources = []
            st.error(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": sources,
    })
    st.rerun()
