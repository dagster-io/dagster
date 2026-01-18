import json  # noqa: I001

import pandas as pd
import requests
from .assets_initial_state import topstory_ids

# start_topstories_asset_with_logger
from dagster import asset, AssetExecutionContext


@asset(deps=[topstory_ids])
def topstories(context: AssetExecutionContext) -> None:
    with open("data/topstory_ids.json") as f:
        topstory_ids = json.load(f)

    results = []
    for item_id in topstory_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            context.log.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)
    df.to_csv("data/topstories.csv")


# end_topstories_asset_with_logger
