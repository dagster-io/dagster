import os
import subprocess
from distutils import spawn  # pylint: disable=deprecated-module

import psycopg2
import pytest

from dagster._utils import file_relative_path, pushd
from dagster._utils.test.postgres_instance import TestPostgresInstance

# ======= CONFIG ========
DBT_EXECUTABLE = "dbt"
TEST_PROJECT_DIR = file_relative_path(__file__, "dagster_dbt_test_project")
DBT_CONFIG_DIR = os.path.join(TEST_PROJECT_DIR, "dbt_config")
TEST_DBT_TARGET_DIR = os.path.join(TEST_PROJECT_DIR, "target_test")

TEST_PYTHON_PROJECT_DIR = file_relative_path(__file__, "dagster_dbt_python_test_project")
DBT_PYTHON_CONFIG_DIR = os.path.join(TEST_PYTHON_PROJECT_DIR, "dbt_config")

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture(scope="session")
def test_project_dir():
    return TEST_PROJECT_DIR


@pytest.fixture(scope="session")
def dbt_config_dir():
    return DBT_CONFIG_DIR


@pytest.fixture(scope="session")
def dbt_target_dir():
    return TEST_DBT_TARGET_DIR


@pytest.fixture(scope="session")
def dbt_executable():
    return DBT_EXECUTABLE


@pytest.fixture(scope="session")
def test_python_project_dir():
    return TEST_PYTHON_PROJECT_DIR


@pytest.fixture(scope="session")
def dbt_python_config_dir():
    return DBT_PYTHON_CONFIG_DIR


@pytest.fixture(scope="session")
def conn_string():
    postgres_host = os.environ.get("POSTGRES_TEST_DB_DBT_HOST")
    if postgres_host is None and IS_BUILDKITE:
        pytest.fail("Env variable POSTGRES_TEST_DB_DBT_HOST is unset")

    try:
        if not IS_BUILDKITE:
            os.environ["POSTGRES_TEST_DB_DBT_HOST"] = "localhost"

        os.environ["DBT_TARGET_PATH"] = "target"

        with TestPostgresInstance.docker_service_up_or_skip(
            file_relative_path(__file__, "docker-compose.yml"),
            "test-postgres-db-dbt",
            {"hostname": postgres_host} if IS_BUILDKITE else {},
        ) as conn_str:
            yield conn_str
    finally:
        if postgres_host is not None:
            os.environ["POSTGRES_TEST_DB_DBT_HOST"] = postgres_host


@pytest.fixture(scope="session")
def prepare_dbt_cli(conn_string):  # pylint: disable=unused-argument, redefined-outer-name
    if not spawn.find_executable(DBT_EXECUTABLE):
        raise Exception("executable not found in path for `dbt`")

    with pushd(TEST_PROJECT_DIR):
        yield


@pytest.fixture(scope="session")
def dbt_seed(
    prepare_dbt_cli, dbt_executable, dbt_config_dir
):  # pylint: disable=unused-argument, redefined-outer-name
    subprocess.run([dbt_executable, "seed", "--profiles-dir", dbt_config_dir], check=True)


@pytest.fixture(scope="session")
def dbt_build(
    prepare_dbt_cli, dbt_executable, dbt_config_dir
):  # pylint: disable=unused-argument, redefined-outer-name
    subprocess.run([dbt_executable, "seed", "--profiles-dir", dbt_config_dir], check=True)
    subprocess.run([dbt_executable, "run", "--profiles-dir", dbt_config_dir], check=True)


@pytest.fixture(scope="session")
def dbt_python_sources(conn_string):
    """Create sample users/events table sources"""

    conn = None
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        cur.execute("CREATE SCHEMA raw_data")
        cur.execute("CREATE TABLE raw_data.events (day integer, user_id integer, event_id integer)")
        cur.execute("CREATE TABLE raw_data.users (day integer, user_id integer)")
        cur.executemany(
            "INSERT INTO raw_data.users VALUES(%s, %s)", [(n / 10, n) for n in range(100)]
        )
        cur.executemany(
            "INSERT INTO raw_data.events VALUES(%s, %s, %s)",
            [(n / 10, n, n * 10) for n in range(100)],
        )
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()
