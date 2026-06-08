from typing import Iterator
from apify_client import ApifyClient
import config

ACTOR_ID = "3HJWd9KfGyItAD5N9"


def fetch_jobs(
    title: str = "software engineer",
    country: str = "germany",
    location: str = "berlin",
    limit: int = 10,
    language: str = "en",
    skip: int = 0,
) -> Iterator[dict]:
    client = ApifyClient(config.APIFY_API_KEY)
    run_input = {
        "country": country,
        "limit": limit,
        "title": title,
        "company": None,
        "site": None,
        "language": language,
        "Remote": None,
        "Academic": None,
        "Research": None,
        "Freelancer": None,
        "B2B": None,
        "PartTime": None,
        "location": location,
        "datetime_from": None,
        "datetime_to": None,
        "skip": skip,
        "sort_field": "datetime_from",
        "sort_direction": -1,
    }
    # Pay-per-result actor: max_items maps to Apify's maxItems query param (required > 0).
    run = client.actor(ACTOR_ID).call(run_input=run_input, max_items=limit)
    # apify_client <2 returns a dict, >=2 returns a Run object
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id
    yield from client.dataset(dataset_id).iterate_items()
