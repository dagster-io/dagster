import pandas as pd
from dagster import Config, asset
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

from ..resources import HNAPIClient


class ItemsConfig(Config):
    base_item_id: int


CREATE_TABLE_QUERY = """
create table if not exists {table_name} (
    id number,
    parent number,
    time number,
    type varchar,
    user_id varchar,
    text varchar,
    kids variant,
    score number,
    title varchar,
    descendants number,
    url varchar
);
"""

CLEAR_TABLE_QUERY = """
delete from {table_name} where id = id;
"""


UPDATE_TABLE_QUERY = """
insert into {table_name}
select
    id,
    parent,
    time,
    type,
    user_id,
    text,
    kids,
    score,
    title,
    descendants,
    url
from items
where type = '{item_type}'
"""


@asset
def items(config: ItemsConfig, snowflake_resource: SnowflakeResource, hn_client: HNAPIClient):
    """Items from the Hacker News API: each is a story or a comment on a story."""
    rows = []
    max_id = hn_client.fetch_max_item_id()

    # Hacker News API is 1-indexed, so adjust range by 1
    for item_id in range(max_id - config.base_item_id + 1, max_id + 1):
        rows.append(hn_client.fetch_item_by_id(item_id))

    result = pd.DataFrame(rows, columns=hn_client.item_field_names).drop_duplicates(subset=["id"])
    result.rename(columns={"by": "user_id"}, inplace=True)

    # Upload data to Snowflake as a dataframe
    with snowflake_resource.get_connection() as conn:
        write_pandas(
            conn=conn,
            df=result,
            table_name="ITEMS",
            schema=snowflake_resource.schema_,
            database=snowflake_resource.database,
            auto_create_table=True,
            use_logical_type=True,
            quote_identifiers=False,
        )


@asset(deps=[items])
def comments(snowflake_resource: SnowflakeResource):
    """Comments from the Hacker News API."""
    table_name = "comments"
    item_type = "comment"

    create_table = CREATE_TABLE_QUERY.format(
        table_name=table_name,
    )
    clear_table = CLEAR_TABLE_QUERY.format(table_name=table_name)
    update_table = UPDATE_TABLE_QUERY.format(table_name=table_name, item_type=item_type)

    with snowflake_resource.get_connection() as conn:
        conn.cursor().execute(create_table)
        conn.cursor().execute(clear_table)
        conn.cursor().execute(update_table)


@asset(deps=[items])
def stories(snowflake_resource: SnowflakeResource):
    """Stories from the Hacker News API."""
    table_name = "stories"
    item_type = "story"

    create_table = CREATE_TABLE_QUERY.format(
        table_name=table_name,
    )
    clear_table = CLEAR_TABLE_QUERY.format(table_name=table_name)
    update_table = UPDATE_TABLE_QUERY.format(table_name=table_name, item_type=item_type)

    with snowflake_resource.get_connection() as conn:
        conn.cursor().execute(create_table)
        conn.cursor().execute(clear_table)
        conn.cursor().execute(update_table)
