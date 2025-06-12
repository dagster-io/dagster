import pandas as pd

from dagster import Config, asset


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

class ItemsConfig(Config):
    base_item_id: int


@asset(
    io_manager_key="snowflake_io_manager",
)
# highlight-start
def items(config: ItemsConfig, hn_client) -> pd.DataFrame:
    """Items from the Hacker News API: each is a story or a comment on a story."""
    max_id = hn_client.fetch_max_item_id()
    rows = []
    # Hacker News API is 1-indexed, so adjust range by 1
    for item_id in range(max_id - config.base_item_id + 1, max_id + 1):
        rows.append(hn_client.fetch_item_by_id(item_id))

    result = pd.DataFrame(rows, columns=hn_client.item_field_names).drop_duplicates(
        subset=["id"]
    )
    result.rename(columns={"by": "user_id"}, inplace=True)
    return result
# highlight-end

@asset(
    io_manager_key="snowflake_io_manager",
)
def comments(items: pd.DataFrame) -> pd.DataFrame:
    """Comments from the Hacker News API."""
    return items[items["type"] == "comment"]


@asset(
    io_manager_key="snowflake_io_manager",
)
def stories(items: pd.DataFrame) -> pd.DataFrame:
    """Stories from the Hacker News API."""
    return items[items["type"] == "story"]
