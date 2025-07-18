from contextlib import contextmanager
from typing import Any

from dagster_snowflake import SnowflakeResource
from dagster_snowflake.components.sql_component.component import (
    SnowflakeConnectionComponent,
)


class MockSqlConnectionComponent(SnowflakeConnectionComponent):
    """Mock Snowflake resource that uses mock connection."""

    def connect_and_execute(self, sql: str) -> None:
        pass
