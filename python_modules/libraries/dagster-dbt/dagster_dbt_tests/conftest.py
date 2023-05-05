import os
import subprocess

import pytest
from dagster._utils import file_relative_path, pushd
from dagster_dbt import DbtCliClientResource, dbt_cli_resource

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


@pytest.fixture(
    scope="session",
    params=[
        "legacy",
        "pythonic",
    ],
)
def dbt_cli_resource_factory(request):
    if request.param == "pythonic":
        return DbtCliClientResource
    else:
        return lambda **kwargs: dbt_cli_resource.configured(kwargs)


@pytest.fixture(scope="session")
def dbt_seed(dbt_executable, dbt_config_dir):
    with pushd(TEST_PROJECT_DIR):
        subprocess.run([dbt_executable, "seed", "--profiles-dir", dbt_config_dir], check=True)


@pytest.fixture(scope="session")
def dbt_seed_python(dbt_executable, dbt_python_config_dir):
    with pushd(TEST_PYTHON_PROJECT_DIR):
        subprocess.run(
            [dbt_executable, "seed", "--threads", "1", "--profiles-dir", dbt_python_config_dir],
            check=True,
        )


@pytest.fixture(scope="session")
def dbt_build(dbt_executable, dbt_config_dir):
    with pushd(TEST_PROJECT_DIR):
        subprocess.run([dbt_executable, "seed", "--profiles-dir", dbt_config_dir], check=True)
        subprocess.run([dbt_executable, "run", "--profiles-dir", dbt_config_dir], check=True)
