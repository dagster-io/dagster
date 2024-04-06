import pandas as pd
import requests
from dagster import Config, asset
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

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


CREATE_UPDATE_TABLE_QUERY = """
create table if not exists {table_name} (
    id varchar,
    parent varchar,
    time datetime,
    type varchar,
    user_id varchar,
    text varchar,
    kids varchar,
    score double,
    title varchar,
    descendants varchar,
    url varchar
);

delete from {table_name} where id = id;

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
def items(config: ItemsConfig, snowflake_resource: SnowflakeResource):
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

    # Upload data to Snowflake as a dataframe
    with snowflake_resource.get_connection() as conn:
        write_pandas(
            conn=conn,
            df=result,
            table_name="items",
            database=snowflake_resource.database,
            auto_create_table=True,
            use_logical_type=True,
        )


@asset(deps=[items])
def comments(snowflake_resource: SnowflakeResource):
    """Comments from the Hacker News API."""
    table_name = "comments"
    item_type = "comment"

    create_table = CREATE_UPDATE_TABLE_QUERY.format(
        table_name=table_name,
        item_type=item_type,
    )

    with snowflake_resource.get_connection() as conn:
        conn.cursor.execute(create_table)


@asset(deps=[items])
def stories(snowflake_resource: SnowflakeResource):
    """Stories from the Hacker News API."""
    table_name = "stories"
    item_type = "story"

    create_table = CREATE_UPDATE_TABLE_QUERY.format(
        table_name=table_name,
        item_type=item_type,
    )

    with snowflake_resource.get_connection() as conn:
        conn.cursor.execute(create_table)
