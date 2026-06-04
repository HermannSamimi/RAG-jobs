from typing import Iterator
from apify_client import ApifyClient
import config

ACTOR_ID = "3HJWd9KfGyItAD5N9"


def fetch_jobs(
    title: str = "software engineer",
    country: str = "germany",
    location: str = "berlin",
    limit: int = 50,
    language: str = "en",
    skip: int = 0,
) -> Iterator[dict]:
    client = ApifyClient(config.APIFY_API_KEY)
    run_input = {
        "action": "search_jobs",
        "country": country,
        "limit": limit,
        "title": title,
        "language": language,
        "location": location,
        "skip": skip,
        "sort_field": "datetime_from",
        "sort_direction": -1,
    }
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    # apify_client <2 returns a dict, >=2 returns a Run object
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id
    yield from client.dataset(dataset_id).iterate_items()
