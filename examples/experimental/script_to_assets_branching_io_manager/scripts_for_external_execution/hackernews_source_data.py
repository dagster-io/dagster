import json
import sys

import pandas as pd
import requests
from dagster._utils import file_relative_path
from tqdm import tqdm
from utils import NamespaceAwareStorage


def extract() -> pd.DataFrame:
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    hackernews_topstory_ids = requests.get(newstories_url).json()

    results = []
    for item_id in tqdm(hackernews_topstory_ids[:1]):
        # for item_id in tqdm(hackernews_topstory_ids[:100]):
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        results.append(item)

    hackernews_topstories = pd.DataFrame(results)

    return hackernews_topstories


if __name__ == "__main__":
    asset_namespace_lookup_json = sys.argv[1]
    asset_namespace_lookup = json.loads(asset_namespace_lookup_json)
    assert isinstance(asset_namespace_lookup, dict)
    storage_root = file_relative_path(__file__, "storage")

    namespace_aware_storage = NamespaceAwareStorage(
        storage_root=storage_root, asset_namespace_lookup=asset_namespace_lookup
    )

    asset_key = "hackernews_source_data"
    dataframe = extract()
    namespace_aware_storage.write_object(asset_key, dataframe)
