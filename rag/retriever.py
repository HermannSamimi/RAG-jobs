from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from embedder import embed_text
from ingestion.qdrant_store import get_client
import config


def search_jobs(
    query: str,
    top_k: int = config.TOP_K,
    client: QdrantClient | None = None,
) -> List[dict]:
    client = client or get_client()
    query_vector = embed_text(query)

    response = client.query_points(
        collection_name=config.QDRANT_JOBS_COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    return [{"score": round(p.score, 4), **p.payload} for p in response.points]
