from contextlib import contextmanager
from typing import Any

from dagster_snowflake import SnowflakeResource
from dagster_snowflake.components.sql_component.component import (
    SnowflakeTemplatedSqlComponent,
)


class MockSnowflakeConnection:
    """Mock Snowflake connection that no-ops on queries."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def cursor(self):
        return MockSnowflakeCursor()


class MockSnowflakeCursor:
    """Mock Snowflake cursor that no-ops on execute."""

    def execute(self, query: str, *args, **kwargs):
        pass

    def fetchall(self):
        return []

    def fetchone(self):
        return None


class MockSnowflakeResource(SnowflakeResource):
    """Mock Snowflake resource that uses mock connection."""

    def get_connection(self, raw_conn: bool = False):
        return MockSnowflakeConnection()
