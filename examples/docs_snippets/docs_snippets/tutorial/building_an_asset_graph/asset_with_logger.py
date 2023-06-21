import pandas as pd
import requests

# start_topstories_asset_with_logger
from dagster import asset, get_dagster_logger


@asset
def topstories(topstory_ids):
    logger = get_dagster_logger()

    with open("topstory_ids.txt", "r") as input_file:
        ids = input_file.read().split(",")

    results = []
    for item_id in ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            logger.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    conn = duckdb.connect('analytics.db')
    conn.execute("create or replace table topstories as select * from df")

# end_topstories_asset_with_logger
