import os
import time
import uuid
from unittest import mock

import pytest
import sqlalchemy  # noqa: F401
from dagster import (
    DagsterInstance,
    DagsterResourceFunctionError,
    DataVersion,
    EnvVar,
    ObserveResult,
    job,
    observable_source_asset,
    op,
)
from dagster._check import CheckError
from dagster._core.definitions.metadata import FloatMetadataValue
from dagster._core.definitions.observe import observe
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp
from dagster_snowflake import SnowflakeResource, fetch_last_updated_timestamps, snowflake_resource
from dagster_snowflake.constants import SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER

from dagster_snowflake_tests.utils import create_mock_connector, temporary_snowflake_table


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
        application=SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER,
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
        application=SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER,
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
            application=SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER,
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
            application=SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER,
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


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.importorskip(
    "snowflake.sqlalchemy", reason="sqlalchemy is not available in the test environment"
)
@pytest.mark.integration
def test_fetch_last_updated_timestamps_missing_table():
    with SnowflakeResource(
        connector="sqlalchemy",
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.environ["SNOWFLAKE_USER"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="TESTDB",
        schema="TESTSCHEMA",
    ).get_connection() as conn:
        table_name = f"test_table_{str(uuid.uuid4()).replace('-', '_')}".lower()
        try:
            conn.cursor().execute(f"create table {table_name} (foo string)")
            conn.cursor().execute(f"insert into {table_name} values ('bar')")

            reversed_table_name = table_name[::-1]
            with pytest.raises(ValueError):
                freshness = fetch_last_updated_timestamps(
                    snowflake_connection=conn,
                    database="TESTDB",
                    # Second table does not exist, expects ValueError
                    tables=[table_name, reversed_table_name],
                    schema="TESTSCHEMA",
                )

            freshness = fetch_last_updated_timestamps(
                snowflake_connection=conn,
                database="TESTDB",
                tables=[table_name, reversed_table_name],
                schema="TESTSCHEMA",
                ignore_missing_tables=True,
            )
            assert table_name in freshness
            assert len(freshness) == 1
        finally:
            conn.cursor().execute(f"drop table if exists {table_name}")


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
@pytest.mark.parametrize("db_str", [None, "TESTDB"], ids=["db_from_resource", "db_from_param"])
def test_fetch_last_updated_timestamps(db_str: str):
    start_time = get_current_timestamp()
    with temporary_snowflake_table() as table_name:

        @observable_source_asset
        def freshness_observe(snowflake: SnowflakeResource) -> ObserveResult:
            with snowflake.get_connection() as conn:
                freshness_for_table = fetch_last_updated_timestamps(
                    snowflake_connection=conn,
                    database="TESTDB",
                    tables=[
                        table_name.lower()
                    ],  # Snowflake table names are expected uppercase. Test that lowercase also works.
                    schema="TESTSCHEMA",
                )[
                    table_name.lower()
                ].timestamp()  # Expect that table name is returned in the same case it was passed in.
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


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.importorskip(
    "snowflake.sqlalchemy", reason="sqlalchemy is not available in the test environment"
)
@pytest.mark.integration
def test_resources_snowflake_sqlalchemy_connection():
    with SnowflakeResource(
        connector="sqlalchemy",
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.environ["SNOWFLAKE_USER"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="TESTDB",
        schema="TESTSCHEMA",
    ).get_connection() as conn:
        # Snowflake table names are expected to be capitalized.
        table_name = f"test_table_{str(uuid.uuid4()).replace('-', '_')}".lower()
        try:
            start_time = get_current_timestamp()
            conn.cursor().execute(f"create table {table_name} (foo string)")
            # Insert one row
            conn.cursor().execute(f"insert into {table_name} values ('bar')")

            freshness_for_table = fetch_last_updated_timestamps(
                snowflake_connection=conn,
                database="TESTDB",
                tables=[
                    table_name
                ],  # Snowflake table names are expected uppercase. Test that lowercase also works.
                schema="TESTSCHEMA",
            )[table_name].timestamp()

            # The test is flaky without this sleep.
            time.sleep(3)

            end_time = get_current_timestamp()

            assert freshness_for_table > start_time
            assert freshness_for_table < end_time
        finally:
            conn.cursor().execute(f"drop table if exists {table_name}")


def test_resources_snowflake_additional_snowflake_connection_args():
    """Tests that args passed to additional_snowflake_connection_args are correctly forwarded to
    snowflake.connector.connect.
    """
    with mock.patch("snowflake.connector.connect") as snowflake_conn_mock:
        with SnowflakeResource(
            account="account",
            user="user",
            password="password",
            database="TESTDB",
            schema="TESTSCHEMA",
            additional_snowflake_connection_args={"foo": "bar"},
        ).get_connection():
            assert snowflake_conn_mock.call_count == 1
            assert snowflake_conn_mock.call_args[1]["foo"] == "bar"


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_snowpark_session_integration():
    """Integration test for create_snowpark_session with real connection."""
    resource = SnowflakeResource(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.environ["SNOWFLAKE_USER"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="TESTDB",
        schema="TESTSCHEMA",
    )

    with resource.create_snowpark_session() as session:
        # Test that we can execute a simple query
        result = session.sql("SELECT 1 as test_col").collect()
        assert len(result) == 1
        assert result[0]["TEST_COL"] == 1


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_get_databases_integration():
    """Integration test for get_databases with real connection."""
    resource = SnowflakeResource(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.environ["SNOWFLAKE_USER"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="TESTDB",
        schema="TESTSCHEMA",
    )

    # Get databases matching TESTDB pattern
    databases = resource.get_databases("TESTDB")

    # Should find at least the TESTDB database
    assert len(databases) >= 1
    db_names = [db.name for db in databases]
    assert "TESTDB" in db_names


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_get_schemas_integration():
    """Integration test for get_schemas with real connection."""
    resource = SnowflakeResource(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.environ["SNOWFLAKE_USER"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="TESTDB",
        schema="TESTSCHEMA",
    )

    # Get schemas in TESTDB matching TESTSCHEMA pattern
    schemas = resource.get_schemas("TESTDB", "TESTSCHEMA")

    # Should find at least the TESTSCHEMA schema
    assert len(schemas) >= 1
    schema_names = [s.name for s in schemas]
    assert "TESTSCHEMA" in schema_names


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_get_tables_integration():
    """Integration test for get_tables with real connection."""
    with temporary_snowflake_table() as table_name:
        resource = SnowflakeResource(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.environ["SNOWFLAKE_USER"],
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database="TESTDB",
            schema="TESTSCHEMA",
        )

        # Get all tables in TESTSCHEMA
        tables = resource.get_tables("TESTDB", "TESTSCHEMA", "%")

        # Check that our test table is in the results
        table_names = [t.name for t in tables]
        assert table_name in table_names


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_multiple_patterns_integration():
    """Integration test for methods handling multiple databases/schemas."""
    resource = SnowflakeResource(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.environ["SNOWFLAKE_USER"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="TESTDB",
        schema="TESTSCHEMA",
    )

    # Test with wildcard patterns
    databases = resource.get_databases("%")
    assert len(databases) > 0

    # Test schemas with wildcard
    schemas = resource.get_schemas("TESTDB", "%")
    assert len(schemas) > 0

    # Ensure INFORMATION_SCHEMA and PUBLIC are typically present
    schema_names = [s.name for s in schemas]
    assert "INFORMATION_SCHEMA" in schema_names or "PUBLIC" in schema_names


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_get_views_integration():
    """Integration test for get_views with real connection."""
    from dagster_snowflake_tests.utils import temporary_snowflake_view

    with temporary_snowflake_view() as view_name:
        resource = SnowflakeResource(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.environ["SNOWFLAKE_USER"],
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database="TESTDB",
            schema="TESTSCHEMA",
        )

        # Get all views in TESTSCHEMA
        views = resource.get_views("TESTDB", "TESTSCHEMA", "%")

        # Check that our test view is in the results
        view_names = [v.name for v in views]
        assert view_name in view_names


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_get_pipes_integration():
    """Integration test for get_pipes with real connection."""
    from dagster_snowflake_tests.utils import temporary_snowflake_pipe

    with temporary_snowflake_pipe() as pipe_name:
        resource = SnowflakeResource(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.environ["SNOWFLAKE_USER"],
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database="TESTDB",
            schema="TESTSCHEMA",
        )

        # Get all pipes in TESTSCHEMA
        pipes = resource.get_pipes("TESTDB", "TESTSCHEMA", "%")

        # Check that our test pipe is in the results
        pipe_names = [p.name for p in pipes]
        assert pipe_name in pipe_names


@pytest.mark.skip_if_no_snowflake_credentials
@pytest.mark.integration
def test_get_stages_integration():
    """Integration test for get_stages with real connection."""
    from dagster_snowflake_tests.utils import temporary_snowflake_stage

    with temporary_snowflake_stage() as stage_name:
        resource = SnowflakeResource(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.environ["SNOWFLAKE_USER"],
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database="TESTDB",
            schema="TESTSCHEMA",
        )

        # Get all stages in TESTSCHEMA
        stages = resource.get_stages("TESTDB", "TESTSCHEMA", "%")

        # Check that our test stage is in the results
        stage_names = [s.name for s in stages]
        assert stage_name in stage_names
