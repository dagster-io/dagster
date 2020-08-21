import os
import subprocess

import pytest
from dagster_postgres.utils import get_conn_string, wait_for_connection

from dagster.utils import pushd, script_relative_path

BUILDKITE = bool(os.getenv("BUILDKITE"))


def is_postgres_running():
    try:
        output = subprocess.check_output(
            [
                "docker",
                "container",
                "ps",
                "-f",
                "name=test-postgres-db-airline",
                "-f",
                "status=running",
            ]
        )
        decoded = output.decode()

        lines = decoded.split("\n")

        # header, one line for container, trailing \n
        return len(lines) == 3
    except:  # pylint: disable=bare-except
        return False


@pytest.fixture(scope="session")
def spark_config():
    spark_packages = [
        "com.databricks:spark-avro_2.11:3.0.0",
        "com.databricks:spark-redshift_2.11:2.0.1",
        "com.databricks:spark-csv_2.11:1.5.0",
        "org.postgresql:postgresql:42.2.5",
        "org.apache.hadoop:hadoop-aws:2.6.5",
        "com.amazonaws:aws-java-sdk:1.7.4",
    ]
    return {"spark": {"jars": {"packages": ",".join(spark_packages)}}}


@pytest.fixture(scope="session")
def pg_hostname():
    # In buildkite we get the ip address from this variable (see buildkite code for commentary)
    # Otherwise assume local development and assume localhost
    env_name = "POSTGRES_TEST_DB_HOST"
    if env_name not in os.environ:
        os.environ[env_name] = "localhost"
    return os.environ[env_name]


@pytest.fixture(scope="function")
def postgres(pg_hostname):  # pylint: disable=redefined-outer-name
    if BUILDKITE:
        yield
        return

    script_path = script_relative_path(".")

    if not is_postgres_running():
        with pushd(script_path):
            try:
                subprocess.check_output(["docker-compose", "stop", "test-postgres-db-airline"])
                subprocess.check_output(["docker-compose", "rm", "-f", "test-postgres-db-airline"])
            except Exception:  # pylint: disable=broad-except
                pass
            subprocess.check_output(["docker-compose", "up", "-d", "test-postgres-db-airline"])

    wait_for_connection(
        get_conn_string(username="test", password="test", hostname=pg_hostname, db_name="test")
    )

    yield


@pytest.fixture(scope="session")
def s3_bucket():
    yield "dagster-scratch-80542c2"
