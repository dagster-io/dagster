import pandas as pd

from dagster import asset


@asset(
    config_schema={"N": int},
    required_resource_keys={"hn_client"},
    io_manager_key="snowflake_io_manager",
)
def items(context) -> pd.DataFrame:
    """Items from the Hacker News API: each is a story or a comment on a story."""

    hn_client = context.resources.hn_client

    max_id = hn_client.fetch_max_item_id()
    rows = []
    log_count = 0
    # Hacker News API is 1-indexed, so adjust range by 1
    for item_id in range(max_id - context.op_config["N"] + 1, max_id + 1):
        rows.append(hn_client.fetch_item_by_id(item_id))
        log_count += 1
        if log_count >= 50:
            context.log.info("Fetched 50 items.")
            log_count = 0

    result = pd.DataFrame(rows, columns=hn_client.item_field_names).drop_duplicates(subset=["id"])
    result.rename(columns={"by": "user_id"}, inplace=True)

    return result


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
