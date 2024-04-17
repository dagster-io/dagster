import pandas as pd
from dagster import build_asset_context
import os
import pytest

from development_to_production.assets import comments, items, stories, ItemsConfig
from development_to_production.resources import StubHNClient
from dagster_snowflake import SnowflakeResource

@pytest.fixture(scope="module")
def snowflake_resource():
    resource = SnowflakeResource(
        account="abc1234.us-east-1",
        user=os.getenv("DEV_SNOWFLAKE_USER"),
        password=os.getenv("DEV_SNOWFLAKE_PASSWORD"),
        database="TESTDB",
        schema=os.getenv("DEV_SNOWFLAKE_SCHEMA"),
    )

    yield resource

    # clean up tables from tests
    with resource.get_connection() as conn:
        conn.cursor().execute(f"drop table if exists {resource.database}.{resource.schema_}.ITEMS")
        conn.cursor().execute(f"drop table if exists {resource.database}.{resource.schema_}.COMMENTS")
        conn.cursor().execute(f"drop table if exists {resource.database}.{resource.schema_}.STORIES")


def test_assets(snowflake_resource):
    items(
        config=ItemsConfig(base_item_id=StubHNClient().fetch_max_item_id()),
        hn_client=StubHNClient(),
        snowflake_resource=snowflake_resource
    )
    with snowflake_resource.get_connection() as conn:
        hn_dataset = conn.cursor().execute(f"select * from {snowflake_resource.database}.{snowflake_resource.schema_}.ITEMS").fetch_pandas_all()
        assert isinstance(hn_dataset, pd.DataFrame)
        expected_data = pd.DataFrame(StubHNClient().data.values()).rename(
            columns={"by": "user_id"}
        ).rename(str.upper, copy=False, axis="columns")
        assert (hn_dataset["ID"] == expected_data["ID"]).all()
        assert (hn_dataset["TITLE"] == expected_data["TITLE"]).all()
        assert (hn_dataset["USER_ID"] == expected_data["USER_ID"]).all()

    comments(snowflake_resource=snowflake_resource)
    with snowflake_resource.get_connection() as conn:
        comments_df = conn.cursor().execute(f"select * from {snowflake_resource.database}.{snowflake_resource.schema_}.COMMENTS").fetch_pandas_all()
        assert isinstance(comments_df, pd.DataFrame)
        assert 1 in comments_df["ID"].tolist()
        assert 2 not in comments_df["ID"].tolist()

    stories(snowflake_resource=snowflake_resource)
    with snowflake_resource.get_connection() as conn:
        stories_df = conn.cursor().execute(f"select * from {snowflake_resource.database}.{snowflake_resource.schema_}.STORIES").fetch_pandas_all()
        assert isinstance(stories_df, pd.DataFrame)
        assert 1 not in stories_df["ID"].tolist()
        assert 2 in stories_df["ID"].tolist()
