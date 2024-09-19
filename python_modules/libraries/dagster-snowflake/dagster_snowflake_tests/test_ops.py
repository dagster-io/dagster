from unittest import mock

from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_snowflake import snowflake_resource
from dagster_snowflake.constants import SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER
from dagster_snowflake.ops import snowflake_solid_for_query

from dagster_snowflake_tests.utils import create_mock_connector


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_op(snowflake_connect):
    snowflake_solid = snowflake_solid_for_query("SELECT 1")

    result = wrap_op_in_graph_and_execute(
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
        resources={"snowflake": snowflake_resource},
    )
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
