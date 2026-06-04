from typing import Any, Dict, Generator, List, Optional, Tuple

from rag.retriever import search_jobs
from rag.llm_client import stream_chat
from rag.chat_history import get_session_history, save_message
import config

_SYSTEM_PROMPT = """\
You are a specialist job-search assistant with access to a live database of job listings.

Rules:
- Base every answer strictly on the job context provided below each question.
- When mentioning a specific position always cite the job title and company name.
- If the context does not contain enough information to answer, say so honestly.
- Be concise, structured, and use bullet points where helpful.
- Never fabricate salary figures, deadlines, or contact details.\
"""


def _format_context(jobs: List[dict]) -> str:
    blocks = []
    for i, job in enumerate(jobs, 1):
        lines = [
            f"[Job {i}]",
            f"Title        : {job.get('title', 'N/A')}",
            f"Company      : {job.get('company', 'N/A')}",
            f"Location     : {job.get('location', 'N/A')}",
        ]
        if job.get("seniority_level"):
            lines.append(f"Seniority    : {job['seniority_level']}")
        if job.get("employment_type"):
            lines.append(f"Employment   : {job['employment_type']}")
        if job.get("is_remote") is True:
            lines.append("Remote       : Yes")
        if job.get("job_url"):
            lines.append(f"URL          : {job['job_url']}")
        desc = (job.get("description") or "No description available.")[:1200]
        lines.append(f"Description  :\n{desc}")
        blocks.append("\n".join(lines))
    return "\n\n" + "\n\n---\n\n".join(blocks)


def query(
    user_message: str,
    user_id: str,
    session_id: str,
) -> Tuple[Generator[str, None, None], List[dict]]:
    relevant_jobs = search_jobs(user_message)
    history = get_session_history(user_id, session_id)

    context = _format_context(relevant_jobs)
    augmented_user_msg = f"Job context from database:{context}\n\nUser question: {user_message}"

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history[-(config.MAX_HISTORY_TURNS * 2):])
    messages.append({"role": "user", "content": augmented_user_msg})

    save_message(user_id, session_id, "user", user_message)

    def _stream_and_persist() -> Generator[str, None, None]:
        chunks: List[str] = []
        for chunk in stream_chat(messages):
            chunks.append(chunk)
            yield chunk
        save_message(user_id, session_id, "assistant", "".join(chunks))

    return _stream_and_persist(), relevant_jobs
