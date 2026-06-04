from typing import List
import httpx
import config


def embed_texts(texts: List[str]) -> List[List[float]]:
    response = httpx.post(
        config.LLM_EMBEDDINGS_ENDPOINT,
        headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
        json={"model": config.EMBEDDING_MODEL, "input": texts},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()["data"]
    data.sort(key=lambda x: x["index"])
    return [item["embedding"] for item in data]


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]
