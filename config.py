import os
from dotenv import load_dotenv

load_dotenv()

APIFY_API_KEY = os.getenv("APIFY_API_KEY", "")

LLM_COMPLETIONS_ENDPOINT = os.getenv("LLM_COMPLETIONS_ENDPOINT", "")
LLM_EMBEDDINGS_ENDPOINT = os.getenv("LLM_EMBEDDINGS_ENDPOINT", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:8b")
COMPLETIONS_MODEL = os.getenv("COMPLETIONS_MODEL", "gemma3:27b")

_raw_qdrant_key = os.getenv("QDRANT_API_KEY", "")
QDRANT_API_KEY = _raw_qdrant_key if _raw_qdrant_key and _raw_qdrant_key != "QDRANT_API_KEY" else None

QDRANT_HOST = os.getenv("QDRANT_HOST", "http://localhost:6333")
QDRANT_JOBS_COLLECTION = os.getenv("QDRANT_JOBS_COLLECTION_NAME", "knowledge_base")
QDRANT_VECTOR_SIZE = int(os.getenv("QDRANT_JOBS_VECTOR_SIZE", "512"))
QDRANT_DISTANCE = os.getenv("QDRANT_JOBS_DISTANCE", "Cosine")
QDRANT_HISTORY_COLLECTION = os.getenv("QDRANT_CHAT_HISTORY_COLLECTION_NAME", "chat_history")
TENANT_FIELD = os.getenv("TENANT_FIELD", "user_id")

TOP_K = 5
MAX_HISTORY_TURNS = 10
INGEST_BATCH_SIZE = 10
