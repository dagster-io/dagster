import pandas as pd

from dagster import asset

# start_assets
# assets.py


@asset(
    required_resource_keys={"hn_client"},
)
def items(context) -> pd.DataFrame:
    """Items from the Hacker News API: each is a story or a comment on a story."""

    hn_client = context.resources.hn_client

    rows = []
    for item_id in range(1, hn_client.fetch_max_item_id()):
        rows.append(hn_client.fetch_item_by_id(item_id))

    result = pd.DataFrame(rows, columns=hn_client.item_field_names).drop_duplicates(
        subset=["id"]
    )
    result.rename(columns={"by": "user_id"}, inplace=True)

    return result


@asset
def comments(items: pd.DataFrame) -> pd.DataFrame:
    """Comments from the Hacker News API."""
    return items[items["type"] == "comment"]


@asset
def stories(items: pd.DataFrame) -> pd.DataFrame:
    """Stories from the Hacker News API."""
    return items[items["type"] == "story"]


# end_assets
