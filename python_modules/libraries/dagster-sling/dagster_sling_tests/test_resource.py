import json

from dagster import EnvVar
from dagster._core.test_utils import environ
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
            user={"env": "SNOWFLAKE_SLING_USER"},  # pyright: ignore[reportCallIssue]
            password=EnvVar("SNOWFLAKE_SLING_PASSWORD"),  # pyright: ignore[reportCallIssue]
            database="sling",  # pyright: ignore[reportCallIssue]
        ),
    ]

    with environ(
        {
            "SNOWFLAKE_SLING_USER": "the_user",
            "SNOWFLAKE_SLING_PASSWORD": "the_password",
        }
    ):
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
            "user": "the_user",
            "password": "the_password",
            "database": "sling",
        }


def test_sling_resource_prepares_environment_variables():
    sling_resource = SlingResource(connections=[])

    env = sling_resource.prepare_environment()
    assert "SLING_SOURCE" not in env
    assert "SLING_TARGET" not in env


def test_clean_line_preserves_inf_in_stream_names():
    """Test that _clean_line preserves 'INF' in stream names like CUSTOMERINFO.

    Regression test for issue #32208: stream names containing 'INF' should not
    have the 'INF' string stripped out when parsing Sling logs.
    """
    sling_resource = SlingResource(connections=[])

    # Test various log formats with INF in the stream name
    test_cases = [
        # Standard Sling log format with INF log level and INF in stream name
        (
            "1:04PM INF running stream public.CUSTOMERINFO",
            "running stream public.CUSTOMERINFO",
        ),
        # Log without timestamp prefix
        ("running stream public.CUSTOMERINFO", "running stream public.CUSTOMERINFO"),
        # Multiple INF occurrences in message
        (
            "2:15PM INF processing INFO table with CUSTOMERINFO data",
            "processing INFO table with CUSTOMERINFO data",
        ),
        # Different log levels
        ("3:30PM WRN warning about CUSTOMERINFO", "warning about CUSTOMERINFO"),
        ("4:45PM ERR error in CUSTOMERINFO processing", "error in CUSTOMERINFO processing"),
        # Edge case: INF at different positions
        ("11:59AM INF INFORMATION system active", "INFORMATION system active"),
    ]

    for input_line, expected_output in test_cases:
        result = sling_resource._clean_line(input_line)  # noqa: SLF001
        assert result == expected_output, f"Failed for input: {input_line}"
