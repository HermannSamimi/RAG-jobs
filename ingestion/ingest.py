"""
Ingestion pipeline: fetch jobs from Apify, embed descriptions, upsert into Qdrant.

Usage:
    python -m ingestion.ingest --title "data engineer" --country germany --location berlin --limit 50
"""
import argparse
import logging
from typing import List

from embedder import embed_texts
from ingestion.apify_fetcher import fetch_jobs
from ingestion.qdrant_store import ensure_jobs_collection, get_client, upsert_jobs
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def build_embed_text(job: dict) -> str:
    """Embed description when available; fall back to title + company + location."""
    title = (job.get("title") or "").strip()
    description = (job.get("description") or "").strip()
    company = (job.get("company") or "").strip()
    location = (job.get("location") or "").strip()

    if description:
        return f"{title}\n\n{description}"
    return "\n".join(p for p in [title, company, location] if p)


def run(title: str, country: str, location: str, limit: int, language: str) -> int:
    client = get_client()
    ensure_jobs_collection(client)

    buffer: List[dict] = []
    total = 0

    log.info(f"Fetching: title={title!r}  country={country}  location={location}  limit={limit}")

    for job in fetch_jobs(title=title, country=country, location=location, limit=limit, language=language):
        if not job.get("title"):  # skip only if there's truly nothing to embed
            continue
        buffer.append(job)

        if len(buffer) >= config.INGEST_BATCH_SIZE:
            texts = [build_embed_text(j) for j in buffer]
            vectors = embed_texts(texts)
            n = upsert_jobs(buffer, vectors, client)
            total += n
            log.info(f"Upserted {n} jobs  (running total: {total})")
            buffer = []

    if buffer:
        texts = [build_embed_text(j) for j in buffer]
        vectors = embed_texts(texts)
        n = upsert_jobs(buffer, vectors, client)
        total += n
        log.info(f"Upserted {n} jobs  (running total: {total})")

    log.info(f"Ingestion complete — total upserted: {total}")
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest job listings into Qdrant")
    parser.add_argument("--title", default="software engineer")
    parser.add_argument("--country", default="germany")
    parser.add_argument("--location", default="berlin")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--language", default="en")
    args = parser.parse_args()
    run(args.title, args.country, args.location, args.limit, args.language)
