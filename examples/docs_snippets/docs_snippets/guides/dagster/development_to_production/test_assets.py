import pandas as pd

from dagster import ItemsConfig, SnowflakeResource

from .assets_v2 import ItemsConfig, items
from .resources.resources_v2 import StubHNClient

# start
# test_assets.py


def test_items():
    test_snowflake = (
        SnowflakeResource(
            account="abc1234.us-east-1",
            user="test@company.com",
            password=os.getenv("TEST_SNOWFLAKE_PASSWORD"),
            database="TEST",
            schema="HACKER_NEWS",
        ),
    )
    try:
        items(
            config=ItemsConfig(base_item_id=StubHNClient().fetch_max_item_id()),
            hn_client=StubHNClient(),
            snowflake_resource=test_snowflake,
        )
        with test_snowflake.get_connection() as conn:
            hn_dataset = conn.cursor.execute("select * from ITEMS").fetch_pandas_all()
            assert isinstance(hn_dataset, pd.DataFrame)
            expected_data = pd.DataFrame(StubHNClient().data.values()).rename(
                columns={"by": "user_id"}
            )
            assert (hn_dataset == expected_data).all().all()

    finally:
        with test_snowflake.get_connection() as conn:
            conn.cursor.execute("drop table if exists ITEMS")


# end
