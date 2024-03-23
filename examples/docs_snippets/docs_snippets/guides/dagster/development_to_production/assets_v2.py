import pandas as pd
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

from dagster import Config, asset

from .resources.resources_v1 import HNAPIClient

# start_items
# assets.py


class ItemsConfig(Config):
    base_item_id: int


@asset
def items(
    config: ItemsConfig, snowflake_resource: SnowflakeResource, hn_client: HNAPIClient
):
    """Items from the Hacker News API: each is a story or a comment on a story."""
    rows = []
    max_id = hn_client.fetch_max_item_id()

    # Hacker News API is 1-indexed, so adjust range by 1
    for item_id in range(max_id - config.base_item_id + 1, max_id + 1):
        rows.append(hn_client.fetch_item_by_id(item_id))

    result = pd.DataFrame(rows, columns=hn_client.item_field_names).drop_duplicates(
        subset=["id"]
    )
    result.rename(columns={"by": "user_id"}, inplace=True)

    # Upload data to Snowflake as a dataframe
    with snowflake_resource.get_connection() as conn:
        write_pandas(
            conn=conn,
            df=result,
            table_name="items",
            schema=snowflake_resource.schema,
            database=snowflake_resource.database,
            auto_create_table=True,
            use_logical_type=True,
        )


# end_items
