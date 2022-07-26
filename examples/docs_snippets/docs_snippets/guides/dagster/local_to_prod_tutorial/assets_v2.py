import pandas as pd

from dagster import asset

# start_items
# assets.py


@asset(
    config_schema={"N": int},
    required_resource_keys={"hn_client"},
)
def items(context) -> pd.DataFrame:
    """Items from the Hacker News API: each is a story or a comment on a story."""
    hn_client = context.resources.hn_client

    max_id = hn_client.fetch_max_item_id()
    rows = []
    # Hacker News API is 1-indexed, so adjust range by 1
    for item_id in range(max_id - context.op_config["N"] + 1, max_id + 1):
        rows.append(hn_client.fetch_item_by_id(item_id))

    result = pd.DataFrame(rows, columns=hn_client.item_field_names).drop_duplicates(
        subset=["id"]
    )
    result.rename(columns={"by": "user_id"}, inplace=True)
    return result


# end_items
