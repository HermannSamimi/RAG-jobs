import uuid
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    HnswConfigDiff,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)
import config


def get_client() -> QdrantClient:
    return QdrantClient(url=config.QDRANT_HOST, api_key=config.QDRANT_API_KEY)


def _collection_exists(client: QdrantClient, name: str) -> bool:
    return name in [c.name for c in client.get_collections().collections]


def _ensure_index(client: QdrantClient, collection: str, field: str) -> None:
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        pass  # index already exists — safe to ignore


def ensure_jobs_collection(client: Optional[QdrantClient] = None) -> None:
    client = client or get_client()
    if not _collection_exists(client, config.QDRANT_JOBS_COLLECTION):
        client.create_collection(
            collection_name=config.QDRANT_JOBS_COLLECTION,
            vectors_config=VectorParams(
                size=config.QDRANT_VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
            hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
        )
    for field in ["country", "is_remote", "seniority_level", "employment_type", "site", "language"]:
        _ensure_index(client, config.QDRANT_JOBS_COLLECTION, field)


def ensure_history_collection(client: Optional[QdrantClient] = None) -> None:
    client = client or get_client()
    if not _collection_exists(client, config.QDRANT_HISTORY_COLLECTION):
        client.create_collection(
            collection_name=config.QDRANT_HISTORY_COLLECTION,
            vectors_config=VectorParams(
                size=config.QDRANT_VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
    for field in [config.TENANT_FIELD, "session_id", "role"]:
        _ensure_index(client, config.QDRANT_HISTORY_COLLECTION, field)


def upsert_jobs(
    jobs: List[dict],
    vectors: List[List[float]],
    client: Optional[QdrantClient] = None,
) -> int:
    client = client or get_client()
    points = []
    for job, vector in zip(jobs, vectors):
        job_id = job.get("id") or job.get("job_id") or str(uuid.uuid4())
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, job_id))
        payload = {k: v for k, v in job.items() if k != "_id" and v is not None}
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))
    client.upsert(collection_name=config.QDRANT_JOBS_COLLECTION, points=points)
    return len(points)
