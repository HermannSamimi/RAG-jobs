import json
from typing import Dict, Generator, List
import httpx
import config


def stream_chat(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    with httpx.stream(
        "POST",
        config.LLM_COMPLETIONS_ENDPOINT,
        headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
        json={
            "model": config.COMPLETIONS_MODEL,
            "messages": messages,
            "stream": True,
        },
        timeout=120,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            chunk = line[6:]
            if chunk == "[DONE]":
                break
            try:
                delta = json.loads(chunk)["choices"][0]["delta"].get("content", "")
                if delta:
                    yield delta
            except (KeyError, json.JSONDecodeError):
                continue
