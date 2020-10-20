from dagster import ModeDefinition, execute_solid
from dagster.seven import mock
from dagster_snowflake import snowflake_resource, snowflake_solid_for_query

from .utils import create_mock_connector


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_solid(snowflake_connect):
    snowflake_solid = snowflake_solid_for_query("SELECT 1")

    result = execute_solid(
        snowflake_solid,
        run_config={
            "resources": {
                "snowflake": {
                    "config": {
                        "account": "foo",
                        "user": "bar",
                        "password": "baz",
                        "database": "TESTDB",
                        "schema": "TESTSCHEMA",
                        "warehouse": "TINY_WAREHOUSE",
                    }
                }
            }
        },
        mode_def=ModeDefinition(resource_defs={"snowflake": snowflake_resource}),
    )
    assert result.success
    snowflake_connect.assert_called_once_with(
        account="foo",
        user="bar",
        password="baz",
        database="TESTDB",
        schema="TESTSCHEMA",
        warehouse="TINY_WAREHOUSE",
    )
