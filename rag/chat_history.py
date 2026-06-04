import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from embedder import embed_text
from ingestion.qdrant_store import ensure_history_collection, get_client
import config


def save_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    client: Optional[QdrantClient] = None,
) -> None:
    client = client or get_client()
    ensure_history_collection(client)
    vector = embed_text(content)
    client.upsert(
        collection_name=config.QDRANT_HISTORY_COLLECTION,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    config.TENANT_FIELD: user_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        ],
    )


def get_session_history(
    user_id: str,
    session_id: str,
    limit: int = config.MAX_HISTORY_TURNS * 2,
    client: Optional[QdrantClient] = None,
) -> List[Dict[str, str]]:
    client = client or get_client()
    ensure_history_collection(client)
    records, _ = client.scroll(
        collection_name=config.QDRANT_HISTORY_COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(key=config.TENANT_FIELD, match=MatchValue(value=user_id)),
                FieldCondition(key="session_id", match=MatchValue(value=session_id)),
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    records.sort(key=lambda r: r.payload.get("timestamp", ""))
    return [{"role": r.payload["role"], "content": r.payload["content"]} for r in records]
