import os
import subprocess

import pytest
from dagster_postgres.utils import get_conn_string, wait_for_connection

from dagster.utils import pushd, script_relative_path

BUILDKITE = bool(os.getenv("BUILDKITE"))


def is_postgres_running():
    try:
        output = subprocess.check_output(
            ["docker", "container", "ps", "-f", "name=test-postgres-db", "-f", "status=running"]
        )
        decoded = output.decode()

        lines = decoded.split("\n")

        # header, one line for container, trailing \n
        return len(lines) == 3
    except:  # pylint: disable=bare-except
        return False


@pytest.fixture(scope="session")
def pg_hostname():
    # In buildkite we get the ip address from this variable (see buildkite code for commentary)
    # Otherwise assume local development and assume localhost
    env_name = "POSTGRES_TEST_DB_HOST"
    return os.environ.get(env_name, "localhost")


@pytest.fixture(scope="function")
def postgres(pg_hostname):  # pylint: disable=redefined-outer-name
    if BUILDKITE:
        yield get_conn_string(
            username="test", password="test", hostname=pg_hostname, db_name="test"
        )
        return

    # TODO move airline demo
    script_path = script_relative_path("../../../dagster_examples_tests/airline_demo_tests/")

    if not is_postgres_running():
        with pushd(script_path):
            try:
                subprocess.check_output(["docker-compose", "stop", "test-postgres-db"])
                subprocess.check_output(["docker-compose", "rm", "-f", "test-postgres-db"])
            except Exception:  # pylint: disable=broad-except
                pass
            subprocess.check_output(["docker-compose", "up", "-d", "test-postgres-db"])

    conn_str = get_conn_string(
        username="test", password="test", hostname=pg_hostname, db_name="test"
    )
    wait_for_connection(conn_str)

    yield conn_str
