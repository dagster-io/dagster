from unittest import mock

import pytest
from dagster import DagsterResourceFunctionError, EnvVar, job, op
from dagster._core.test_utils import environ
from dagster_snowflake import SnowflakeResource, snowflake_resource

from .utils import create_mock_connector

pythonic_snowflake_resource = SnowflakeResource(
    account="foo",
    user="bar",
    password="baz",
    database="TESTDB",
    schema="TESTSCHEMA",
    warehouse="TINY_WAREHOUSE",
)
old_snowflake_resource = snowflake_resource.configured(
    {
        "account": "foo",
        "user": "bar",
        "password": "baz",
        "database": "TESTDB",
        "schema": "TESTSCHEMA",
        "warehouse": "TINY_WAREHOUSE",
    }
)


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
@pytest.mark.parametrize("resource", [(pythonic_snowflake_resource), (old_snowflake_resource)])
def test_snowflake_resource(snowflake_connect, resource):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

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


pythonic_snowflake_resource_env = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    database=EnvVar("SNOWFLAKE_DATABASE"),
    schema=EnvVar("SNOWFLAKE_SCHEMA"),
    warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
)
old_snowflake_resource_env = snowflake_resource.configured(
    {
        "account": {"env": "SNOWFLAKE_ACCOUNT"},
        "user": {"env": "SNOWFLAKE_USER"},
        "password": {"env": "SNOWFLAKE_PASSWORD"},
        "database": {"env": "SNOWFLAKE_DATABASE"},
        "schema": {"env": "SNOWFLAKE_SCHEMA"},
        "warehouse": {"env": "SNOWFLAKE_WAREHOUSE"},
    }
)


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
@pytest.mark.parametrize(
    "resource", [(pythonic_snowflake_resource_env), (old_snowflake_resource_env)]
)
def test_snowflake_resource_from_envvars(snowflake_connect, resource):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

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


pythonic_snowflake_resource_no_auth = SnowflakeResource(
    account="foo", user="bar", database="TESTDB", schema="TESTSCHEMA", warehouse="TINY_WAREHOUSE"
)
old_snowflake_resource_no_auth = snowflake_resource.configured(
    {
        "account": "foo",
        "user": "bar",
        "database": "TESTDB",
        "schema": "TESTSCHEMA",
        "warehouse": "TINY_WAREHOUSE",
    }
)


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
@pytest.mark.parametrize(
    "resource", [(pythonic_snowflake_resource_no_auth), (old_snowflake_resource_no_auth)]
)
def test_snowflake_resource_no_auth(snowflake_connect, resource):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    with pytest.raises(DagsterResourceFunctionError):
        snowflake_job.execute_in_process()


pythonic_snowflake_resource_auth = SnowflakeResource(
    account="foo",
    user="bar",
    password="baz",
    database="TESTDB",
    schema="TESTSCHEMA",
    warehouse="TINY_WAREHOUSE",
    private_key="TESTKEY",
)
old_snowflake_resource_auth = snowflake_resource.configured(
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


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
@pytest.mark.parametrize(
    "resource", [(pythonic_snowflake_resource_auth), (old_snowflake_resource_auth)]
)
def test_snowflake_resource_duplicate_auth(snowflake_connect, resource):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    with pytest.raises(DagsterResourceFunctionError):
        snowflake_job.execute_in_process()


pythonic_snowflake_resource_pk_password = SnowflakeResource(
    account="foo",
    user="bar",
    database="TESTDB",
    schema="TESTSCHEMA",
    warehouse="TINY_WAREHOUSE",
    private_key="TESTKEY",
)
old_snowflake_resource_pk_password = snowflake_resource.configured(
    {
        "account": "foo",
        "user": "bar",
        "database": "TESTDB",
        "schema": "TESTSCHEMA",
        "warehouse": "TINY_WAREHOUSE",
        "private_key": "TESTKEY",
    }
)


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
@pytest.mark.parametrize(
    "resource", [(pythonic_snowflake_resource_pk_password), (old_snowflake_resource_pk_password)]
)
def test_snowflake_resource_missing_private_key_password(snowflake_connect, resource):
    @op(required_resource_keys={"snowflake"})
    def snowflake_op(context):
        assert context.resources.snowflake
        with context.resources.snowflake.get_connection() as _:
            pass

    @job(resource_defs={"snowflake": resource})
    def snowflake_job():
        snowflake_op()

    with pytest.raises(DagsterResourceFunctionError):
        snowflake_job.execute_in_process()
