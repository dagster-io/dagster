from unittest import mock

import pytest
from dagster import DagsterResourceFunctionError, job, op
from dagster._core.test_utils import environ
from dagster_snowflake import snowflake_resource

from .utils import create_mock_connector


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    @job(resource_defs={"snowflake": snowflake_resource})
    def snowflake_job():
        snowflake_op()

    result = snowflake_job.execute_in_process(
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
        }
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


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource_from_envvars(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    @job(resource_defs={"snowflake": snowflake_resource})
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
        result = snowflake_job.execute_in_process(
            run_config={
                "resources": {
                    "snowflake": {
                        "config": {
                            "account": {"env": "SNOWFLAKE_ACCOUNT"},
                            "user": {"env": "SNOWFLAKE_USER"},
                            "password": {"env": "SNOWFLAKE_PASSWORD"},
                            "database": {"env": "SNOWFLAKE_DATABASE"},
                            "schema": {"env": "SNOWFLAKE_SCHEMA"},
                            "warehouse": {"env": "SNOWFLAKE_WAREHOUSE"},
                        }
                    }
                }
            },
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


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource_no_auth(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    @job(resource_defs={"snowflake": snowflake_resource})
    def snowflake_job():
        snowflake_op()

    with pytest.raises(DagsterResourceFunctionError):
        snowflake_job.execute_in_process(
            run_config={
                "resources": {
                    "snowflake": {
                        "config": {
                            "account": "foo",
                            "user": "bar",
                            "database": "TESTDB",
                            "schema": "TESTSCHEMA",
                            "warehouse": "TINY_WAREHOUSE",
                        }
                    }
                }
            }
        )


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_resource_duplicate_auth(snowflake_connect):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    @job(resource_defs={"snowflake": snowflake_resource})
    def snowflake_job():
        snowflake_op()

    with pytest.raises(DagsterResourceFunctionError):
        snowflake_job.execute_in_process(
            run_config={
                "resources": {
                    "snowflake": {
                        "config": {
                            "account": "foo",
                            "user": "bar",
                            "database": "TESTDB",
                            "password": "baz",
                            "schema": "TESTSCHEMA",
                            "warehouse": "TINY_WAREHOUSE",
                            "private_key": "TESTKEY",
                        }
                    }
                }
            }
        )
