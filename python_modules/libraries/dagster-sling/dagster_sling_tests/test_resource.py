import json

from dagster import EnvVar
from dagster_sling import SlingResource
from dagster_sling.resources import SlingConnectionResource


def test_sling_resource_env_with_source_target():
    source = SlingConnectionResource(
        name="duckdb_source", type="duckdb", connection_string="duckdb://localhost:5000"
    )
    target = SlingConnectionResource(
        name="postgres_target",
        type="postgres",
        host="abchost.com",  # pyright: ignore[reportCallIssue]
        port="420",  # pyright: ignore[reportCallIssue]
    )

    sling_resource = SlingResource(connections=[source, target])

    env = sling_resource.prepare_environment()
    assert json.loads(env["duckdb_source"]) == {
        "name": "duckdb_source",
        "type": "duckdb",
        "url": "duckdb://localhost:5000",
    }
    assert json.loads(env["postgres_target"]) == {
        "name": "postgres_target",
        "type": "postgres",
        "host": "abchost.com",
        "port": "420",
    }


def test_sling_resource_env_with_connection_resources():
    connections = [
        SlingConnectionResource(
            name="CLOUD_PRODUCTION",
            type="postgres",
            host="CLOUD_PROD_READ_REPLICA_POSTGRES_HOST",  # pyright: ignore[reportCallIssue]
            user="CLOUD_PROD_POSTGRES_USER",  # pyright: ignore[reportCallIssue]
            database="dagster",  # pyright: ignore[reportCallIssue]
        ),
        SlingConnectionResource(
            name="SLING_DB",
            type="snowflake",
            host="SNOWFLAKE_ACCOUNT",  # pyright: ignore[reportCallIssue]
            user="SNOWFLAKE_SLING_USER",  # pyright: ignore[reportCallIssue]
            password=EnvVar("SNOWFLAKE_SLING_PASSWORD"),  # pyright: ignore[reportCallIssue]
            database="sling",  # pyright: ignore[reportCallIssue]
        ),
    ]

    sling_resource = SlingResource(connections=connections)
    env = sling_resource.prepare_environment()

    assert json.loads(env["CLOUD_PRODUCTION"]) == {
        "name": "CLOUD_PRODUCTION",
        "type": "postgres",
        "host": "CLOUD_PROD_READ_REPLICA_POSTGRES_HOST",
        "user": "CLOUD_PROD_POSTGRES_USER",
        "database": "dagster",
    }

    assert json.loads(env["SLING_DB"]) == {
        "name": "SLING_DB",
        "type": "snowflake",
        "host": "SNOWFLAKE_ACCOUNT",
        "user": "SNOWFLAKE_SLING_USER",
        "password": EnvVar("SNOWFLAKE_SLING_PASSWORD"),
        "database": "sling",
    }


def test_sling_resource_prepares_environment_variables():
    sling_resource = SlingResource(connections=[])

    env = sling_resource.prepare_environment()
    assert "SLING_SOURCE" not in env
    assert "SLING_TARGET" not in env
