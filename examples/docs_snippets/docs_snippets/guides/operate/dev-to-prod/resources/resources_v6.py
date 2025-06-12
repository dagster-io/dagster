from typing import Any, Optional

import os

import dagster as dg

import requests

from dagster_snowflake_pandas import SnowflakePandasIOManager


class HNAPIClient(dg.ConfigurableResource):
    """Hacker News client that fetches live data."""

    def fetch_item_by_id(self, item_id: int) -> Optional[dict[str, Any]]:
        """Fetches a single item from the Hacker News API by item id."""
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        item = requests.get(item_url, timeout=5).json()
        return item

    def fetch_max_item_id(self) -> int:
        return requests.get(
            "https://hacker-news.firebaseio.com/v0/maxitem.json", timeout=5
        ).json()

    @property
    def item_field_names(self) -> list:
        # omitted for brevity
        return []

# highlight-start
class StubHNClient:
    """Hacker News Client that returns fake data."""

    def __init__(self):
        self.data = {
            1: {
                "id": 1,
                "type": "comment",
                "title": "the first comment",
                "by": "user1",
            },
            2: {"id": 2, "type": "story", "title": "an awesome story", "by": "user2"},
        }

    def fetch_item_by_id(self, item_id: int) -> Optional[dict[str, Any]]:
        return self.data.get(item_id)

    def fetch_max_item_id(self) -> int:
        return 2

    @property
    def item_field_names(self) -> list:
        return ["id", "type", "title", "by"]
# highlight-end


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources = {
            "local": {
                # highlight-start
                "hn_client": HNAPIClient(),
                # highlight-end
                "snowflake_io_manager": SnowflakePandasIOManager(
                    account="abc1234.us-east-1",
                    user=dg.EnvVar("DEV_SNOWFLAKE_USER"),
                    password=dg.EnvVar("DEV_SNOWFLAKE_PASSWORD"),
                    database="LOCAL",
                    schema=dg.EnvVar("DEV_SNOWFLAKE_SCHEMA"),
                ),
            },
            "staging": {
                # highlight-start
                "hn_client": HNAPIClient(),
                # highlight-end
                "snowflake_io_manager": SnowflakePandasIOManager(
                    account="abc1234.us-east-1",
                    user="system@company.com",
                    password=dg.EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
                    database="STAGING",
                    schema="HACKER_NEWS",
                ),
            },
            "production": {
                # highlight-start
                "hn_client": HNAPIClient(),
                # highlight-end
                "snowflake_io_manager": SnowflakePandasIOManager(
                    account="abc1234.us-east-1",
                    user="system@company.com",
                    password=dg.EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
                    database="PRODUCTION",
                    schema="HACKER_NEWS",
                ),
            },
        }
    )

deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

defs = dg.Definitions(
    resources=resources[deployment_name]
)
