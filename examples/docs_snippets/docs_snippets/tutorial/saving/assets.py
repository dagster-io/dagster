from typing import List

import pandas as pd
import requests

from dagster import AssetExecutionContext, MetadataValue, asset, get_dagster_logger


# start_update_asset
@asset(
    group_name="hackernews",
    io_manager_key="database_io_manager",  # Addition: `io_manager_key` specified
)
def topstories(context: AssetExecutionContext, topstory_ids: List) -> pd.DataFrame:
    logger = get_dagster_logger()

    results = []
    for item_id in topstory_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            logger.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    context.add_output_metadata(
        metadata={
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )

    return df


# end_update_asset
