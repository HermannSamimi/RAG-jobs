# Deployment Guide — Hugging Face Space + GitHub Actions

Production layout for JobRAG:

| Component | Platform | Role |
|---|---|---|
| **Streamlit chat UI** | [Hugging Face Space](https://huggingface.co/spaces) | Live demo (`app.py`) |
| **Hourly ingestion** | GitHub Actions | Replaces Airflow scheduler in cloud |
| **Vector DB** | Qdrant Cloud | Shared by UI + ingestion |
| **LLM API** | Tempico Labs (or any OpenAI-compatible) | Embeddings + chat |
| **Airflow DAG** | `dags/` in repo | Local Docker dev + documentation |

```
GitHub Actions (hourly) ──► ingestion ──► Qdrant Cloud ◄── HF Space (Streamlit)
                                              ▲
                                    Tempico LLM API
```

---

## 1. GitHub repository secrets

In **GitHub → Settings → Secrets and variables → Actions → Secrets**, add:

| Secret | Used by |
|---|---|
| `APIFY_API_KEY` | Hourly ingestion workflow |
| `QDRANT_HOST` | Ingestion + Space |
| `QDRANT_API_KEY` | Ingestion + Space |
| `LLM_EMBEDDINGS_ENDPOINT` | Ingestion + Space |
| `LLM_COMPLETIONS_ENDPOINT` | Space only |
| `LLM_API_KEY` | Ingestion + Space |

Copy values from your local `.env` (never commit `.env`).

---

## 2. Hugging Face Space

### Create the Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. **Owner:** `HermannS11`
3. **Space name:** `jobrag` (or your choice)
4. **SDK:** Streamlit
5. **License:** MIT
6. **Create Space**

### Deploy code to the Space

**GitHub linking is optional.** If the Space was created from the Streamlit template, it will show `src/` and a template `Dockerfile` until you upload your project files.

**Recommended — upload with the HF CLI** (avoids git binary-file restrictions):

```bash
pip install huggingface_hub
hf auth login   # token from https://huggingface.co/settings/tokens

cd /path/to/RAG-jobs-1
hf upload HermannS11/jobrag . . --repo-type space \
  --exclude ".env" --exclude ".git/*" --exclude "__pycache__/*" \
  --commit-message "Deploy JobRAG application"
```

Re-run the same command after code changes.

**Alternative — link GitHub** (if available in Space → Settings → Repository):

1. Connect **GitHub** → select `HermannSamimi/RAG-jobs`
2. Branch: `main`

Note: direct `git push` to HF may be rejected if the repo history contains binary files (e.g. `.gif`). Use `hf upload` instead.

### Space secrets

In **Space → Settings → Variables and secrets → Secrets**:

| Secret | Value |
|---|---|
| `QDRANT_HOST` | Your Qdrant cluster URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `QDRANT_JOBS_COLLECTION_NAME` | `knowledge_base` |
| `QDRANT_JOBS_VECTOR_SIZE` | `4096` |
| `QDRANT_JOBS_DISTANCE` | `Cosine` |
| `QDRANT_CHAT_HISTORY_COLLECTION_NAME` | `chat_history` |
| `LLM_EMBEDDINGS_ENDPOINT` | e.g. `https://api.tempico.com/v1/embeddings` |
| `LLM_COMPLETIONS_ENDPOINT` | e.g. `https://api.tempico.com/v1/chat/completions` |
| `LLM_API_KEY` | Your LLM API key |
| `EMBEDDING_MODEL` | `qwen3-embedding:8b` |
| `COMPLETIONS_MODEL` | `gemma3:27b` |

`APIFY_API_KEY` is **not** required on the Space (ingestion runs in GitHub Actions).

The root `README.md` includes Hugging Face Space frontmatter (`sdk: streamlit`, `app_file: app.py`).

---

## 3. Run ingestion once (before first demo)

Either wait for the hourly GitHub Action, or trigger manually:

**GitHub → Actions → Hourly job ingestion → Run workflow**

Or locally:

```bash
cp .env.example .env   # fill in values
pip install -r requirements-ingestion.txt
python -m ingestion.ingest --title "software engineer" --country germany --location berlin --limit 50
```

---

## 4. Verify

| Check | URL / command |
|---|---|
| Space live | `https://huggingface.co/spaces/HermannS11/jobrag` |
| Ingestion logs | GitHub → Actions → Hourly job ingestion |
| Qdrant data | Qdrant Cloud console → `knowledge_base` collection |

---

## 5. Local development (optional)

Docker Compose + Airflow still works for full-stack local dev:

```bash
docker compose up --build -d
```

See the main [README.md](README.md) for details.

---

## Troubleshooting

**Space: “Could not connect to Qdrant”** — check Space secrets and that `QDRANT_JOBS_VECTOR_SIZE=4096`.

**Empty answers** — run ingestion at least once so `knowledge_base` has job vectors.

**GitHub Action fails on embed** — verify `LLM_EMBEDDINGS_ENDPOINT` and `LLM_API_KEY` secrets.

**Scheduled runs delayed** — GitHub free-tier cron can slip by a few minutes; use `workflow_dispatch` for exact timing.
