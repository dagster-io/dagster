ITEM_FIELD_NAMES = [
    "id",
    "parent",
    "time",
    "type",
    "by",
    "text",
    "kids",
    "score",
    "title",
    "descendants",
    "url",
]

# start_assets
# assets.py
import pandas as pd
import requests

import dagster as dg


class ItemsConfig(dg.Config):
    base_item_id: int


@dg.asset(
    io_manager_key="snowflake_io_manager",
)
def items(config: ItemsConfig) -> pd.DataFrame:
    """Items from the Hacker News API: each is a story or a comment on a story."""
    rows = []
    max_id = requests.get(
        "https://hacker-news.firebaseio.com/v0/maxitem.json", timeout=5
    ).json()
    # Hacker News API is 1-indexed, so adjust range by 1
    for item_id in range(max_id - config.base_item_id + 1, max_id + 1):
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        rows.append(requests.get(item_url, timeout=5).json())

    # ITEM_FIELD_NAMES is a list of the column names in the Hacker News dataset
    result = pd.DataFrame(rows, columns=ITEM_FIELD_NAMES).drop_duplicates(subset=["id"])
    result.rename(columns={"by": "user_id"}, inplace=True)
    return result


@dg.asset(
    io_manager_key="snowflake_io_manager",
)
def comments(items: pd.DataFrame) -> pd.DataFrame:
    """Comments from the Hacker News API."""
    return items[items["type"] == "comment"]


@dg.asset(
    io_manager_key="snowflake_io_manager",
)
def stories(items: pd.DataFrame) -> pd.DataFrame:
    """Stories from the Hacker News API."""
    return items[items["type"] == "story"]


# end_assets
