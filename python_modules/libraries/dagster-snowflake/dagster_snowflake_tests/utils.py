import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

from dagster import build_resources
from dagster_snowflake import SnowflakeResource


def create_mock_connector(*_args, **_kwargs):
    return connect_with_fetchall_returning(None)


def connect_with_fetchall_returning(value):
    cursor_mock = mock.MagicMock()
    cursor_mock.fetchall.return_value = value
    snowflake_connect = mock.MagicMock()
    snowflake_connect.cursor.return_value = cursor_mock
    m = mock.Mock()
    m.return_value = snowflake_connect
    return m


@contextmanager
def temporary_snowflake_table() -> Iterator[str]:
    with build_resources(
        {
            "snowflake": SnowflakeResource(
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                user=os.environ["SNOWFLAKE_USER"],
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                database="TESTDB",
                schema="TESTSCHEMA",
            )
        }
    ) as resources:
        table_name = f"TEST_TABLE_{str(uuid.uuid4()).replace('-', '_').upper()}"  # Snowflake table names are expected to be capitalized.
        snowflake: SnowflakeResource = resources.snowflake
        with snowflake.get_connection() as conn:
            try:
                conn.cursor().execute(f"create table {table_name} (foo string)")
                # Insert one row
                conn.cursor().execute(f"insert into {table_name} values ('bar')")
                yield table_name
            finally:
                conn.cursor().execute(f"drop table {table_name}")


@contextmanager
def temporary_snowflake_view() -> Iterator[str]:
    """Creates a temporary view in Snowflake for testing."""
    with build_resources(
        {
            "snowflake": SnowflakeResource(
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                user=os.environ["SNOWFLAKE_USER"],
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                database="TESTDB",
                schema="TESTSCHEMA",
            )
        }
    ) as resources:
        view_name = f"TEST_VIEW_{str(uuid.uuid4()).replace('-', '_').upper()}"
        # Create a temporary table to base the view on
        base_table_name = f"BASE_TABLE_{str(uuid.uuid4()).replace('-', '_').upper()}"
        snowflake: SnowflakeResource = resources.snowflake
        with snowflake.get_connection() as conn:
            try:
                # Create base table
                conn.cursor().execute(f"create table {base_table_name} (id int, name string)")
                conn.cursor().execute(
                    f"insert into {base_table_name} values (1, 'test1'), (2, 'test2')"
                )
                # Create view
                conn.cursor().execute(f"create view {view_name} as select * from {base_table_name}")
                yield view_name
            finally:
                conn.cursor().execute(f"drop view if exists {view_name}")
                conn.cursor().execute(f"drop table if exists {base_table_name}")


@contextmanager
def temporary_snowflake_pipe() -> Iterator[str]:
    """Creates a temporary pipe in Snowflake for testing."""
    with build_resources(
        {
            "snowflake": SnowflakeResource(
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                user=os.environ["SNOWFLAKE_USER"],
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                database="TESTDB",
                schema="TESTSCHEMA",
            )
        }
    ) as resources:
        pipe_name = f"TEST_PIPE_{str(uuid.uuid4()).replace('-', '_').upper()}"
        # Create a temporary table and stage for the pipe
        stage_name = f"PIPE_STAGE_{str(uuid.uuid4()).replace('-', '_').upper()}"
        table_name = f"PIPE_TABLE_{str(uuid.uuid4()).replace('-', '_').upper()}"
        snowflake: SnowflakeResource = resources.snowflake
        with snowflake.get_connection() as conn:
            try:
                # Create table
                conn.cursor().execute(f"create table {table_name} (data variant)")
                # Create stage
                conn.cursor().execute(f"create stage {stage_name}")
                # Create pipe (doesn't need to be functional, just needs to exist)
                conn.cursor().execute(
                    f"create pipe {pipe_name} as copy into {table_name} from @{stage_name}"
                )
                yield pipe_name
            finally:
                conn.cursor().execute(f"drop pipe if exists {pipe_name}")
                conn.cursor().execute(f"drop stage if exists {stage_name}")
                conn.cursor().execute(f"drop table if exists {table_name}")


@contextmanager
def temporary_snowflake_stage() -> Iterator[str]:
    """Creates a temporary stage in Snowflake for testing."""
    with build_resources(
        {
            "snowflake": SnowflakeResource(
                account=os.getenv("SNOWFLAKE_ACCOUNT"),
                user=os.environ["SNOWFLAKE_USER"],
                password=os.getenv("SNOWFLAKE_PASSWORD"),
                database="TESTDB",
                schema="TESTSCHEMA",
            )
        }
    ) as resources:
        stage_name = f"TEST_STAGE_{str(uuid.uuid4()).replace('-', '_').upper()}"
        snowflake: SnowflakeResource = resources.snowflake
        with snowflake.get_connection() as conn:
            try:
                # Create an internal stage
                conn.cursor().execute(f"create stage {stage_name}")
                yield stage_name
            finally:
                conn.cursor().execute(f"drop stage if exists {stage_name}")
