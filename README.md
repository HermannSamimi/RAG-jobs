# JobRAG — AI Job Search Assistant for Software Engineers

An end-to-end **RAG (Retrieval-Augmented Generation)** pipeline focused on **Software Engineer** jobs.  
Job listings are automatically fetched every hour via Apache Airflow, stored as vector embeddings in Qdrant, and made available through a Streamlit chat UI powered by a self-hosted LLM.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Apache Airflow  (every hour)                                                │
│                                                                              │
│  DAG: ingest_software_engineer_jobs                                          │
│  ├── ingest__germany__berlin        ─┐                                       │
│  ├── ingest__germany__munich         │                                       │
│  ├── ingest__uk__london              │  Apify Actor → embed (qwen3-8b)       │
│  ├── ingest__usa__new_york           │  → upsert into Qdrant (deduplicated)  │
│  ├── ingest__netherlands__amsterdam  │                                       │
│  └── ingest__canada__toronto        ─┘                                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │     Qdrant       │
                              │  knowledge_base  │  ← job embeddings (512d)
                              │  chat_history    │  ← per-session turns
                              └─────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  Streamlit UI  :2312                                                         │
│                                                                              │
│  User query → embed → vector search → LLM (gemma3:27b) → streaming answer  │
│  Filters: job title · country · city · top-k                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Services

| Service | Port | Description |
|---|---|---|
| **Streamlit app** | `2312` | Chat UI for querying jobs |
| **Airflow webserver** | `8080` | DAG monitoring & manual triggers |
| **Qdrant** | `6333` | Vector database |
| **Postgres** | — (internal) | Airflow metadata store |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 2.10 |
| Data source | Apify Actor `3HJWd9KfGyItAD5N9` (LinkedIn/Indeed via JobSpy) |
| Vector DB | Qdrant |
| Embeddings | `qwen3-embedding:8b` (512d, Cosine) |
| LLM | `gemma3:27b` via OpenAI-compatible API |
| UI | Streamlit |
| Containerisation | Docker + Docker Compose |
| Language | Python 3.11 |

---

## Quick Start

### 1 — Prerequisites

- Docker Desktop installed and running
- `.env` file configured (see below)

### 2 — Configure `.env`

```env
APIFY_API_KEY=your_apify_key

LLM_COMPLETIONS_ENDPOINT=https://api.tempico.com/v1/chat/completions
LLM_EMBEDDINGS_ENDPOINT=https://api.tempico.com/v1/embeddings
LLM_API_KEY=your_llm_key
EMBEDDING_MODEL=qwen3-embedding:8b
COMPLETIONS_MODEL=gemma3:27b

QDRANT_API_KEY=QDRANT_API_KEY
QDRANT_HOST=http://localhost:6333
QDRANT_JOBS_COLLECTION_NAME=knowledge_base
QDRANT_JOBS_VECTOR_SIZE=512
QDRANT_JOBS_DISTANCE=Cosine
QDRANT_CHAT_HISTORY_COLLECTION_NAME=chat_history
TENANT_FIELD=user_id
```

### 3 — Build & Start

```bash
docker compose up --build -d
```

This starts: Postgres → Qdrant → Airflow init → Airflow webserver + scheduler → Streamlit.  
First build takes ~5 minutes (downloads Airflow image and installs packages).

### 4 — Check everything is up

```bash
docker compose ps
```

All 5 containers should show `running`:

```
rag-jobs-postgres             running
rag-jobs-qdrant               running
rag-jobs-airflow-init         exited (0)   ← expected, runs once
rag-jobs-airflow-webserver    running
rag-jobs-airflow-scheduler    running
rag-jobs-app                  running
```

### 5 — Trigger first ingestion manually

The DAG runs automatically every hour. To populate the database immediately:

```bash
docker exec rag-jobs-airflow-scheduler \
  airflow dags trigger ingest_software_engineer_jobs
```

Watch progress in the **Airflow UI → http://localhost:8080** (login: `admin` / `admin`).

### 6 — Open the chat app

[http://localhost:2312](http://localhost:2312)

The database fills up automatically every hour from this point on.

---

## All Commands

### Project lifecycle

```bash
# Start everything
docker compose up --build -d

# Stop everything (data is preserved in volumes)
docker compose down

# Stop and wipe all data (clean slate)
docker compose down -v

# View logs for a specific service
docker compose logs -f airflow-scheduler
docker compose logs -f app
docker compose logs -f qdrant
```

### Airflow

```bash
# Trigger ingestion manually right now
docker exec rag-jobs-airflow-scheduler \
  airflow dags trigger ingest_software_engineer_jobs

# Check DAG run status
docker exec rag-jobs-airflow-scheduler \
  airflow dags list-runs -d ingest_software_engineer_jobs

# Pause the DAG (stop scheduled runs)
docker exec rag-jobs-airflow-scheduler \
  airflow dags pause ingest_software_engineer_jobs

# Resume the DAG
docker exec rag-jobs-airflow-scheduler \
  airflow dags unpause ingest_software_engineer_jobs
```

### Qdrant inspection

```bash
# Count jobs in the database
curl http://localhost:6333/collections/knowledge_base | python3 -m json.tool

# List all collections
curl http://localhost:6333/collections | python3 -m json.tool
```

### Rebuilding after code changes

```bash
# Rebuild a specific service only
docker compose build app
docker compose build airflow-webserver airflow-scheduler

# Restart a service without full rebuild
docker compose restart app
```

---

## Project Structure

```
rag-jobs/
├── app.py                       # Streamlit chat UI  (:2312)
├── config.py                    # Centralised env-var config
├── embedder.py                  # Shared embedding utility
│
├── dags/
│   └── ingest_jobs_dag.py       # Airflow DAG — @hourly, 6 cities
│
├── ingestion/
│   ├── apify_fetcher.py         # Calls Apify actor
│   ├── qdrant_store.py          # Collection setup + upsert
│   └── ingest.py                # Core ingestion logic (called by DAG)
│
├── rag/
│   ├── retriever.py             # Vector search with filters
│   ├── llm_client.py            # Streaming chat completions
│   ├── chat_history.py          # Per-session history in Qdrant
│   └── pipeline.py              # Orchestrates retrieve → prompt → stream
│
├── Dockerfile                   # Streamlit app image
├── Dockerfile.airflow           # Airflow image + project deps
├── docker-compose.yml           # All 5 services
└── requirements.txt             # Python dependencies
```

---

## Airflow DAG Details

**DAG ID:** `ingest_software_engineer_jobs`  
**Schedule:** `@hourly`  
**Job title:** `software engineer` (fixed)  
**Locations:**

| Task ID | Country | City |
|---|---|---|
| `ingest__germany__berlin` | germany | berlin |
| `ingest__germany__munich` | germany | munich |
| `ingest__uk__london` | uk | london |
| `ingest__usa__new_york` | usa | new york |
| `ingest__netherlands__amsterdam` | netherlands | amsterdam |
| `ingest__canada__toronto` | canada | toronto |

Each task fetches 50 jobs, embeds descriptions (title fallback when description is null), and upserts into Qdrant with deduplication via `job_id`.

---

## Qdrant Collections

### `knowledge_base` (job embeddings)
- **Vector:** 512-dim, Cosine — embedded from `title + description`
- **Indexed payload fields:** `country`, `is_remote`, `seniority_level`, `employment_type`, `site`, `language`

### `chat_history` (conversation memory)
- **Vector:** 512-dim — embedded from message content
- **Indexed payload fields:** `user_id`, `session_id`, `role`
- Multi-tenant: each browser session gets its own `user_id`

---

## Deployment Notes

- LLM and embedding endpoints are **external** — no GPU needed on the Docker host.
- Qdrant, Postgres, and job data all persist across restarts via named Docker volumes.
- To use **Qdrant Cloud** instead of local: update `QDRANT_HOST` and `QDRANT_API_KEY` in `.env` and remove the `qdrant` service from `docker-compose.yml`.
- The `airflow-init` container exits with code 0 after first-time setup — this is expected.

---

## Author

Built as a senior data engineer portfolio project showcasing:
- End-to-end RAG pipeline design
- Automated data orchestration with Apache Airflow
- Vector search with Qdrant
- Streaming LLM integration
- Production-ready containerisation
