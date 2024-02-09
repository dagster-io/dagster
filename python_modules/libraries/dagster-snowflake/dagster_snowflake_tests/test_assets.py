import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

import pytest
from dagster import DagsterInstance, build_resources
from dagster._core.definitions.observe import observe
from dagster_snowflake.assets import observe_table_factory
from dagster_snowflake.resources import SnowflakeResource

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


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


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
@pytest.mark.integration
def test_observe_table_factory():
    table_name = "the_table"
    with temporary_snowflake_table() as table_name:
        table_src_asset = observe_table_factory("TESTSCHEMA", table_name)
        instance = DagsterInstance.ephemeral()
        result = observe(
            [table_src_asset],
            instance=instance,
            resources={
                "snowflake": SnowflakeResource(
                    account=os.getenv("SNOWFLAKE_ACCOUNT"),
                    user=os.environ["SNOWFLAKE_USER"],
                    password=os.getenv("SNOWFLAKE_PASSWORD"),
                    database="TESTDB",
                    schema="TESTSCHEMA",
                )
            },
        )
        observations = result.asset_observations_for_node(table_src_asset.op.name)
        assert len(observations) == 1
        observation = observations[0]
        assert observation.tags["dagster/data_version"] is not None
        # Interpret the data version as a timestamp
        # Convert from a string in the format 2024-02-09 00:41:29.829000 to a timestamp
        timestamp = datetime.strptime(
            observation.tags["dagster/data_version"], "%Y-%m-%d %H:%M:%S.%f"
        )
        assert timestamp is not None
