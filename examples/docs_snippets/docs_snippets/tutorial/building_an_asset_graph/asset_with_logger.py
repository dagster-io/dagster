import pandas as pd


# start_topstories_asset_with_logger
from dagster import asset, get_dagster_logger
# Addition, added an import to `get_dagster_logger`

@asset
def topstories(topstory_ids):
    logger = get_dagster_logger()

    results = []
    for item_id in topstory_ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        results.append(item)

        if len(results) % 20 == 0:
            logger.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    return df
# end_topstories_asset_with_logger