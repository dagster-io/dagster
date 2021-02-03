import os
import subprocess

import pytest
from dagster.utils import file_relative_path, pushd
from dagster_postgres.utils import get_conn_string, wait_for_connection

BUILDKITE = bool(os.getenv("BUILDKITE"))


def is_postgres_running():
    try:
        output = subprocess.check_output(
            [
                "docker",
                "container",
                "ps",
                "-f",
                "name=dbt_example_postgresql",
                "-f",
                "status=running",
            ]
        )
        decoded = output.decode("utf-8")

        lines = decoded.split("\n")

        # header, one line for container, trailing \n
        return len(lines) == 3
    except:  # pylint: disable=bare-except
        return False


@pytest.fixture(scope="session")
def pg_hostname():
    # In buildkite we get the ip address from this variable (see buildkite code for commentary)
    # Otherwise assume local development and assume localhost
    env_name = "DAGSTER_DBT_EXAMPLE_PGHOST"
    original_value = os.getenv(env_name)
    try:
        if original_value is None:
            os.environ[env_name] = "localhost"
        yield os.environ[env_name]
    finally:
        if original_value is None:
            del os.environ[env_name]


@pytest.fixture(scope="function")
def postgres(pg_hostname):  # pylint: disable=redefined-outer-name
    conn_string = get_conn_string(
        username="dbt_example",
        password="dbt_example",
        hostname=pg_hostname,
        db_name="dbt_example",
    )

    if not BUILDKITE:
        script_path = file_relative_path(__file__, ".")

        if not is_postgres_running():
            with pushd(script_path):
                try:
                    subprocess.check_output(["docker-compose", "stop", "dbt_example_postgresql"])
                    subprocess.check_output(
                        ["docker-compose", "rm", "-f", "dbt_example_postgresql"]
                    )
                except Exception:  # pylint: disable=broad-except
                    pass
                subprocess.check_output(["docker-compose", "up", "-d", "dbt_example_postgresql"])

        wait_for_connection(conn_string)

    old_env = None
    if os.getenv("DBT_EXAMPLE_CONN_STRING") is not None:
        old_env = os.getenv("DBT_EXAMPLE_CONN_STRING")

    try:
        os.environ["DBT_EXAMPLE_CONN_STRING"] = conn_string
        yield
    finally:
        if old_env is not None:
            os.environ["DBT_EXAMPLE_CONN_STRING"] = old_env
        else:
            del os.environ["DBT_EXAMPLE_CONN_STRING"]
