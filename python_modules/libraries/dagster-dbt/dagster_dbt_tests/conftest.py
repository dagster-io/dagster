import os
import subprocess
from distutils import spawn

import pytest
from dagster.utils import file_relative_path, pushd
from dagster.utils.test.postgres_instance import TestPostgresInstance

# ======= CONFIG ========
DBT_EXECUTABLE = "dbt"
TEST_PROJECT_DIR = file_relative_path(__file__, "dagster_dbt_test_project")
DBT_CONFIG_DIR = os.path.join(TEST_PROJECT_DIR, "dbt_config")

IS_BUILDKITE = os.getenv("BUILDKITE") is not None


@pytest.fixture(scope="session")
def test_project_dir():
    return TEST_PROJECT_DIR


@pytest.fixture(scope="session")
def dbt_config_dir():
    return DBT_CONFIG_DIR


@pytest.fixture(scope="session")
def dbt_executable():
    return DBT_EXECUTABLE


@pytest.fixture(scope="session")
def conn_string():
    postgres_host = os.environ.get("POSTGRES_TEST_DB_DBT_HOST")
    if postgres_host is None and IS_BUILDKITE:
        pytest.fail("Env variable POSTGRES_TEST_DB_DBT_HOST is unset")

    try:
        if not IS_BUILDKITE:
            os.environ["POSTGRES_TEST_DB_DBT_HOST"] = "localhost"

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


@pytest.fixture(scope="class")
def dbt_seed(
    prepare_dbt_cli, dbt_executable, dbt_config_dir
):  # pylint: disable=unused-argument, redefined-outer-name
    subprocess.run([dbt_executable, "seed", "--profiles-dir", dbt_config_dir], check=True)
