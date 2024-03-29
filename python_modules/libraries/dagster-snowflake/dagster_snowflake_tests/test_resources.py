import os
import uuid
from contextlib import contextmanager
from typing import Iterator
from unittest import mock

import pendulum
import pytest
from dagster import (
    DagsterInstance,
    DagsterResourceFunctionError,
    DataVersion,
    EnvVar,
    ObserveResult,
    build_resources,
    job,
    observable_source_asset,
    op,
)
from dagster._check import CheckError
from dagster._core.definitions.metadata import FloatMetadataValue
from dagster._core.definitions.observe import observe
from dagster._core.test_utils import environ
from dagster_snowflake import SnowflakeResource, fetch_last_updated_timestamps, snowflake_resource

from .utils import create_mock_connector

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


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    resource = snowflake_resource.configured(
        {
            "account": "foo",
            "user": "bar",
            "password": "baz",
            "database": "TESTDB",
            "schema": "TESTSCHEMA",
            "warehouse": "TINY_WAREHOUSE",
        }
    )

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    result = snowflake_job.execute_in_process()
    assert result.success
    snowflake_connect.assert_called_once_with(
        account="foo",
        user="bar",
        password="baz",
        database="TESTDB",
        schema="TESTSCHEMA",
        warehouse="TINY_WAREHOUSE",
    )


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_pydantic_snowflake_resource(snowflake_connect):
    @op
    def snowflake_op(snowflake: SnowflakeResource):
        assert snowflake
        with snowflake.get_connection() as _:
            pass

    resource = SnowflakeResource(
        account="foo",
        user="bar",
        password="baz",
        database="TESTDB",
        schema="TESTSCHEMA",
        warehouse="TINY_WAREHOUSE",
    )

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    result = snowflake_job.execute_in_process()
    assert result.success
    snowflake_connect.assert_called_once_with(
        account="foo",
        user="bar",
        password="baz",
        database="TESTDB",
        schema="TESTSCHEMA",
        warehouse="TINY_WAREHOUSE",
    )


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource_from_envvars(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    resource = snowflake_resource.configured(
        {
            "account": {"env": "SNOWFLAKE_ACCOUNT"},
            "user": {"env": "SNOWFLAKE_USER"},
            "password": {"env": "SNOWFLAKE_PASSWORD"},
            "database": {"env": "SNOWFLAKE_DATABASE"},
            "schema": {"env": "SNOWFLAKE_SCHEMA"},
            "warehouse": {"env": "SNOWFLAKE_WAREHOUSE"},
        }
    )

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    env_vars = {
        "SNOWFLAKE_ACCOUNT": "foo",
        "SNOWFLAKE_USER": "bar",
        "SNOWFLAKE_PASSWORD": "baz",
        "SNOWFLAKE_DATABASE": "TESTDB",
        "SNOWFLAKE_SCHEMA": "TESTSCHEMA",
        "SNOWFLAKE_WAREHOUSE": "TINY_WAREHOUSE",
    }
    with environ(env_vars):
        result = snowflake_job.execute_in_process()
        assert result.success
        snowflake_connect.assert_called_once_with(
            account="foo",
            user="bar",
            password="baz",
            database="TESTDB",
            schema="TESTSCHEMA",
            warehouse="TINY_WAREHOUSE",
        )


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_pydantic_snowflake_resource_from_envvars(snowflake_connect):
    @op
    def snowflake_op(snowflake: SnowflakeResource):
        assert snowflake
        with snowflake.get_connection() as _:
            pass

    resource = SnowflakeResource(
        account=EnvVar("SNOWFLAKE_ACCOUNT"),
        user=EnvVar("SNOWFLAKE_USER"),
        password=EnvVar("SNOWFLAKE_PASSWORD"),
        database=EnvVar("SNOWFLAKE_DATABASE"),
        schema=EnvVar("SNOWFLAKE_SCHEMA"),
        warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
    )

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    env_vars = {
        "SNOWFLAKE_ACCOUNT": "foo",
        "SNOWFLAKE_USER": "bar",
        "SNOWFLAKE_PASSWORD": "baz",
        "SNOWFLAKE_DATABASE": "TESTDB",
        "SNOWFLAKE_SCHEMA": "TESTSCHEMA",
        "SNOWFLAKE_WAREHOUSE": "TINY_WAREHOUSE",
    }
    with environ(env_vars):
        result = snowflake_job.execute_in_process()
        assert result.success
        snowflake_connect.assert_called_once_with(
            account="foo",
            user="bar",
            password="baz",
            database="TESTDB",
            schema="TESTSCHEMA",
            warehouse="TINY_WAREHOUSE",
        )


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource_no_auth(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    resource = snowflake_resource.configured(
        {
            "account": "foo",
            "user": "bar",
            "database": "TESTDB",
            "schema": "TESTSCHEMA",
            "warehouse": "TINY_WAREHOUSE",
        }
    )

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    with pytest.raises(DagsterResourceFunctionError):
        snowflake_job.execute_in_process()


def test_pydantic_snowflake_resource_no_auth():
    with pytest.raises(CheckError):
        SnowflakeResource(
            account="foo",
            user="bar",
            database="TESTDB",
            schema="TESTSCHEMA",
            warehouse="TINY_WAREHOUSE",
        )


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource_duplicate_auth(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    resource = snowflake_resource.configured(
        {
            "account": "foo",
            "user": "bar",
            "password": "baz",
            "database": "TESTDB",
            "schema": "TESTSCHEMA",
            "warehouse": "TINY_WAREHOUSE",
            "private_key": "TESTKEY",
        }
    )

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    with pytest.raises(DagsterResourceFunctionError):
        snowflake_job.execute_in_process()


def test_pydantic_snowflake_resource_duplicate_auth():
    with pytest.raises(CheckError):
        SnowflakeResource(
            account="foo",
            user="bar",
            password="baz",
            database="TESTDB",
            schema="TESTSCHEMA",
            warehouse="TINY_WAREHOUSE",
            private_key="TESTKEY",
        )


def test_fetch_last_updated_timestamps_empty():
    with pytest.raises(CheckError):
        fetch_last_updated_timestamps(
            snowflake_connection={}, schema="TESTSCHEMA", database="TESTDB", tables=[]
        )


@pytest.mark.skipif(not IS_BUILDKITE, reason="Requires access to the BUILDKITE snowflake DB")
@pytest.mark.integration
@pytest.mark.parametrize("db_str", [None, "TESTDB"])
def test_fetch_last_updated_timestamps(db_str: str):
    start_time = pendulum.now("UTC").timestamp()
    table_name = "the_table"
    with temporary_snowflake_table() as table_name:

        @observable_source_asset
        def freshness_observe(snowflake: SnowflakeResource) -> ObserveResult:
            with snowflake.get_connection() as conn:
                freshness_for_table = fetch_last_updated_timestamps(
                    snowflake_connection=conn,
                    database="TESTDB",
                    tables=[table_name],
                    schema="TESTSCHEMA",
                )[table_name].timestamp()
                return ObserveResult(
                    data_version=DataVersion("foo"),
                    metadata={"freshness": FloatMetadataValue(freshness_for_table)},
                )

        instance = DagsterInstance.ephemeral()
        result = observe(
            [freshness_observe],
            instance=instance,
            resources={
                "snowflake": SnowflakeResource(
                    account=os.getenv("SNOWFLAKE_ACCOUNT"),
                    user=os.environ["SNOWFLAKE_USER"],
                    password=os.getenv("SNOWFLAKE_PASSWORD"),
                    database="TESTDB" if db_str is None else db_str,
                )
            },
        )
        observations = result.asset_observations_for_node(freshness_observe.op.name)
        assert len(observations) == 1
        observation = observations[0]
        assert observation.tags["dagster/data_version"] is not None
        assert observation.metadata["freshness"] is not None
        freshness_val = observation.metadata["freshness"]
        assert isinstance(freshness_val, FloatMetadataValue)
        assert freshness_val.value
        assert freshness_val.value > start_time
