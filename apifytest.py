from apify_client import ApifyClient
from dotenv import load_dotenv
import os
# Load environment variables from the .env file
load_dotenv()

# Initialize the ApifyClient with your API token
APIFY_API_KEY= os.getenv("APIFY_API_KEY")
client = ApifyClient(APIFY_API_KEY)

# Prepare the Actor input
run_input = {
    "action": "search_jobs",
    "country": "germany",
    "limit": 10,
    "title": "software engineer",
    "company": None,
    "site": None,
    "language": "en",
    "location": "berlin",
    "sort_field": "datetime_from",
    "sort_direction": -1,
}

# Run the Actor and wait for it to finish
run = client.actor("3HJWd9KfGyItAD5N9").call(run_input=run_input, max_items=run_input["limit"])

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)