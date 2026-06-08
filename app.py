import base64
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
    @import url('https://fonts.bunny.net/css?family=inter:400,500,600,700&display=swap');

    :root {
        --font: "Inter", system-ui, -apple-system, sans-serif;
        --mono: ui-monospace, "SF Mono", monospace;

        --bg:     #ffffff;
        --bg-mid: #f7f7f8;
        --bg-hi:  #f0f0f1;

        --b1: #e4e4e7;
        --b2: #d4d4d8;
        --b3: #a1a1aa;

        --ac:    #0891b2;
        --ac-hi: #06b6d4;
        --ac-lo: rgba(8,145,178,0.07);
        --ac-br: rgba(8,145,178,0.2);

        --t1: #18181b;
        --t2: #52525b;
        --t3: #a1a1aa;

        --gr:    #16a34a;
        --gr-lo: rgba(22,163,74,0.07);
        --gr-br: rgba(22,163,74,0.2);

        --r:  10px;
        --rl: 14px;
    }

    /* ── base ── */
    .stApp,
    .stApp p, .stApp label,
    .stApp textarea, .stApp input,
    [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] {
        font-family: var(--font) !important;
        color: var(--t1) !important;
    }
    .stApp span:not([class*="material"]) { font-family: var(--font) !important; }

    /* buttons: font only — colour set per-type below */
    .stApp button { font-family: var(--font) !important; }

    .stApp { background: var(--bg) !important; }

    .main .block-container,
    [data-testid="stSidebar"] .block-container { background: transparent; }

    header[data-testid="stHeader"] { background: transparent !important; }

    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 780px;
    }

    hr { border-color: var(--b1) !important; }

    /* ── sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-mid) !important;
        border-right: 1px solid var(--b1) !important;
    }

    [data-testid="stSidebar"] .block-container { padding-top: 2rem; }

    /* kill the sticky bottom bar entirely */
    [data-testid="stBottomBlockContainer"] { display: none !important; }

    /* ── brand ── */
    .jr-brand {
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--t1);
        margin: 0 0 0.2rem;
        line-height: 1;
    }
    .jr-brand em { font-style: normal; color: var(--ac); }

    .jr-tagline {
        font-size: 0.78rem;
        color: var(--t3);
        margin: 0 0 2rem;
        line-height: 1.5;
    }

    /* ── sidebar labels ── */
    .jr-section-label {
        font-size: 0.64rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--t3);
        margin: 0 0 0.5rem;
    }

    .jr-panel {
        border: 1px solid var(--b1);
        border-radius: var(--r);
        padding: 0.85rem 1rem;
        margin-bottom: 1.5rem;
        background: var(--bg);
    }
    .jr-panel-title { font-size: 0.84rem; font-weight: 600; margin: 0 0 0.2rem; }
    .jr-panel-text  { font-size: 0.77rem; color: var(--t2); margin: 0; line-height: 1.5; }

    .jr-session-id {
        font-family: var(--mono);
        font-size: 0.71rem;
        color: var(--t3);
        border: 1px solid var(--b1);
        padding: 0.38rem 0.65rem;
        border-radius: var(--r);
        word-break: break-all;
        margin-bottom: 0.6rem;
        background: var(--bg);
    }

    .jr-stack { display: flex; flex-direction: column; gap: 0.28rem; font-size: 0.77rem; color: var(--t2); }
    .jr-stack strong { color: var(--t1); font-weight: 500; }

    /* ── hero ── */
    .jr-hero {
        padding: 2rem 0 2rem;
        border-bottom: 1px solid var(--b1);
        margin-bottom: 2rem;
    }
    .jr-hero h1 {
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        margin: 0 0 0.65rem;
        color: var(--t1);
        line-height: 1.1;
    }
    .jr-hero p {
        font-size: 0.97rem;
        color: var(--t2);
        margin: 0;
        line-height: 1.7;
        max-width: 46ch;
    }
    .jr-pill-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 1.1rem; }
    .jr-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        background: var(--ac-lo);
        border: 1px solid var(--ac-br);
        color: var(--ac);
        font-size: 0.72rem;
        font-weight: 500;
    }

    /* ── suggestions ── */
    .jr-suggestions-title {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--t3);
        margin: 0 0 0.6rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .stButton > button {
        border-radius: var(--r);
        border: 1px solid var(--b1);
        background: var(--bg);
        color: var(--t2) !important;
        font-weight: 400;
        font-size: 0.83rem;
        padding: 0.55rem 0.9rem;
        transition: border-color 0.14s, color 0.14s, background 0.14s;
        box-shadow: none;
        text-align: left;
        line-height: 1.4;
    }
    .stButton > button:hover {
        border-color: var(--b2);
        background: var(--bg-mid);
        color: var(--t1) !important;
        box-shadow: none;
    }

    /* sidebar primary button — target button AND all inner p/span Streamlit injects */
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[kind="primary"] *,
    .jr-primary-btn .stButton > button,
    .jr-primary-btn .stButton > button * {
        background: var(--t1) !important;
        border-color: transparent !important;
        color: #fff !important;
        font-weight: 600;
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover *,
    .jr-primary-btn .stButton > button:hover,
    .jr-primary-btn .stButton > button:hover * {
        background: var(--t2) !important;
        color: #fff !important;
        border-color: transparent !important;
    }

    /* ── chat messages ── */
    div[data-testid="stChatMessage"] { background: transparent; border: none; padding: 0.3rem 0; }

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        border-radius: var(--rl);
        padding: 0.85rem 1.05rem;
        font-size: 0.92rem;
        line-height: 1.72;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
        background: var(--bg-hi);
        border: 1px solid var(--b1);
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
        background: var(--bg);
        border: 1px solid var(--b1);
    }
    [data-testid="stChatMessageAvatar"] {
        background: var(--bg-hi) !important;
        border: 1px solid var(--b1) !important;
    }

    /* ── sources ── */
    .jr-sources-header {
        font-size: 0.67rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--t3);
        margin: 1.5rem 0 0.65rem;
    }
    .jr-source-card {
        border: 1px solid var(--b1);
        border-radius: var(--rl);
        padding: 0.95rem 1.1rem;
        margin-bottom: 0.45rem;
        background: var(--bg);
        transition: border-color 0.14s;
    }
    .jr-source-card:hover { border-color: var(--b2); }

    .jr-source-title  { font-size: 0.9rem; font-weight: 600; margin: 0 0 0.12rem; }
    .jr-source-company { font-size: 0.8rem; color: var(--ac); font-weight: 500; margin: 0 0 0.55rem; }

    .jr-meta-row { display: flex; flex-wrap: wrap; gap: 0.28rem; margin-bottom: 0.6rem; }
    .jr-meta-tag {
        font-size: 0.7rem;
        color: var(--t2);
        border: 1px solid var(--b1);
        border-radius: 999px;
        padding: 0.13rem 0.48rem;
    }
    .jr-score {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--gr);
        background: var(--gr-lo);
        border: 1px solid var(--gr-br);
        border-radius: 999px;
        padding: 0.13rem 0.48rem;
    }
    .jr-source-desc { font-size: 0.81rem; color: var(--t2); line-height: 1.6; margin: 0; }

    /* link buttons */
    .stLinkButton > a {
        border-radius: var(--r) !important;
        font-weight: 500 !important;
        font-size: 0.77rem !important;
        background: var(--bg) !important;
        border: 1px solid var(--b1) !important;
        color: var(--t2) !important;
        transition: border-color 0.14s, color 0.14s !important;
    }
    .stLinkButton > a:hover { border-color: var(--b2) !important; color: var(--t1) !important; }

    /* ── chat form ── */
    [data-testid="stForm"] {
        border: 1px solid var(--b1) !important;
        border-radius: 18px !important;
        padding: 8px 12px 8px 18px !important;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
        background: var(--bg) !important;
        margin-top: 1.5rem !important;
    }

    [data-testid="stForm"] > div,
    [data-testid="stForm"] > div > div { border: none !important; box-shadow: none !important; }

    /* align the columns row so button stays vertically centred */
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 0 !important;
    }
    [data-testid="stForm"] [data-testid="column"] { padding: 0 4px 0 0 !important; }
    [data-testid="stForm"] [data-testid="column"]:last-child { padding: 0 !important; }

    [data-testid="stForm"] textarea {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        font-size: 0.93rem !important;
        color: var(--t1) !important;
        resize: none !important;
        padding: 4px 0 !important;
        line-height: 1.55 !important;
        font-family: var(--font) !important;
    }
    [data-testid="stForm"] textarea::placeholder { color: var(--t3) !important; }
    [data-testid="stForm"] textarea:focus { outline: none !important; box-shadow: none !important; }

    /* send button — right-aligned, square */
    [data-testid="stFormSubmitButton"] {
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
    }

    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFormSubmitButton"] button * {
        background: var(--t1) !important;
        color: #fff !important;
        border-radius: 10px !important;
        border: none !important;
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
        padding: 0 !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: background 0.14s !important;
        line-height: 1 !important;
    }
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover * { background: var(--t2) !important; }

    /* alerts */
    [data-testid="stAlert"] {
        background: var(--bg-mid) !important;
        border: 1px solid var(--b1) !important;
        border-radius: var(--r) !important;
        color: var(--t1) !important;
    }

    #MainMenu, footer, header[data-testid="stHeader"] { visibility: visible; }
</style>
"""


def _svg_b64(path: str, replacements: dict | None = None) -> str:
    with open(path, "rb") as f:
        data = f.read()
    for old, new in (replacements or {}).items():
        data = data.replace(old.encode(), new.encode())
    return base64.b64encode(data).decode()


_SEND_B64 = _svg_b64("send-svgrepo-com.svg", {'stroke="#000000"': 'stroke="#ffffff"'})
_SIDEBAR_B64 = _svg_b64("side-list-svgrepo-com.svg")

_ICON_CSS_RAW = """<style>
    /* ── send button: SVG icon ── */
    [data-testid="stFormSubmitButton"] button {
        background-image: url("data:image/svg+xml;base64,__SEND__") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 18px 18px !important;
        color: transparent !important;
        font-size: 0 !important;
    }

    /* ── sidebar toggle: SVG icon (covers both open and collapsed states) ── */
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="collapsedControl"] span,
    button[data-testid="baseButton-headerNoPadding"] span {
        font-size: 0 !important;
        color: transparent !important;
        background-image: url("data:image/svg+xml;base64,__SIDEBAR__") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 18px 18px !important;
        width: 22px !important;
        height: 22px !important;
        display: inline-block !important;
    }
</style>"""

ICON_CSS = _ICON_CSS_RAW.replace("__SEND__", _SEND_B64).replace("__SIDEBAR__", _SIDEBAR_B64)

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
        f'<p class="jr-sources-header">Sources · {len(sources)}</p>',
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
        desc_preview = html.escape(description[:400] + ("…" if len(description) > 400 else ""))

        tags_html = ""
        if location:
            tags_html += f'<span class="jr-meta-tag">{location}</span>'
        if seniority:
            tags_html += f'<span class="jr-meta-tag">{seniority}</span>'
        if employment:
            tags_html += f'<span class="jr-meta-tag">{employment}</span>'
        tags_html += f'<span class="jr-score">{score}</span>'

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
            st.link_button("View listing →", job["job_url"], use_container_width=False)


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<p class="jr-brand">Job<em>RAG</em></p>'
            '<p class="jr-tagline">Semantic search over live job listings.</p>',
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
            f'<div class="jr-session-id">{st.session_state.session_id[:20]}…</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="jr-primary-btn">', unsafe_allow_html=True)
        if st.button("New session", use_container_width=True, type="primary"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<p class="jr-section-label" style="margin-top:1.5rem">Stack</p>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="jr-stack">
                <span><strong>Vector store</strong>&ensp;Qdrant Cloud</span>
                <span><strong>Embeddings</strong>&ensp;qwen3-embedding:8b</span>
                <span><strong>Chat model</strong>&ensp;gemma3:27b</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_hero() -> None:
    st.markdown(
        """
        <div class="jr-hero">
            <h1>Find the right role, faster.</h1>
            <p>Ask natural-language questions about Software Engineer openings in Berlin.
            Every answer is grounded in retrieved listings.</p>
            <div class="jr-pill-row">
                <span class="jr-pill">Berlin, Germany</span>
                <span class="jr-pill">Software Engineer</span>
                <span class="jr-pill">RAG-powered</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_suggestions() -> None:
    st.markdown('<p class="jr-suggestions-title">Try asking</p>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(suggestion, use_container_width=True, key=f"suggest_{i}"):
                st.session_state._prefill = suggestion
                st.rerun()


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(ICON_CSS, unsafe_allow_html=True)

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

with st.form("chat_form", clear_on_submit=True):
    col_text, col_btn = st.columns([15, 1])
    with col_text:
        user_text = st.text_area(
            "",
            placeholder="Ask about roles, skills, companies, or requirements…",
            label_visibility="collapsed",
            height=68,
        )
    with col_btn:
        submitted = st.form_submit_button("↑", use_container_width=False)

user_input = prefill or (user_text.strip() if submitted and user_text.strip() else None)

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
            response_text = f"Something went wrong: {e}"
            sources = []
            st.error(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": sources,
    })
    st.rerun()
