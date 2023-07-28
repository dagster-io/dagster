import os
import subprocess

import dbt.version
import pytest
from dagster._utils import file_relative_path, pushd
from dagster_dbt import DbtCliClientResource, DbtCliResource, dbt_cli_resource
from packaging import version

# ======= CONFIG ========
DBT_EXECUTABLE = "dbt"
TEST_PROJECT_DIR = file_relative_path(__file__, "dagster_dbt_test_project")
DBT_CONFIG_DIR = TEST_PROJECT_DIR
TEST_DBT_TARGET_DIR = os.path.join(TEST_PROJECT_DIR, "target_test")

TEST_PYTHON_PROJECT_DIR = file_relative_path(__file__, "dagster_dbt_python_test_project")
DBT_PYTHON_CONFIG_DIR = TEST_PYTHON_PROJECT_DIR

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
        pytest.param("legacy", marks=pytest.mark.legacy),
        pytest.param("DbtCliClientResource", marks=pytest.mark.legacy),
        pytest.param(
            "DbtCliResource",
            marks=pytest.mark.skipif(
                version.parse(dbt.version.__version__) < version.parse("1.4.0"),
                reason="DbtCliResource only supports dbt 1.4+",
            ),
        ),
    ],
)
def dbt_cli_resource_factory(request):
    if request.param == "DbtCliClientResource":
        return lambda **kwargs: DbtCliClientResource(
            project_dir=kwargs["project_dir"],
            profiles_dir=kwargs.get("profiles_dir"),
            json_log_format=kwargs.get("json_log_format", True),
        )
    elif request.param == "DbtCliResource":
        return lambda **kwargs: DbtCliResource(
            project_dir=kwargs["project_dir"], profile=kwargs.get("profile")
        )
    else:
        return lambda **kwargs: dbt_cli_resource.configured(kwargs)


@pytest.fixture(scope="session")
def dbt_seed(dbt_executable, dbt_config_dir):
    with pushd(TEST_PROJECT_DIR):
        subprocess.run([dbt_executable, "seed", "--profiles-dir", dbt_config_dir], check=True)


@pytest.fixture(scope="session")
def dbt_build(dbt_executable, dbt_config_dir):
    with pushd(TEST_PROJECT_DIR):
        subprocess.run([dbt_executable, "seed", "--profiles-dir", dbt_config_dir], check=True)
        subprocess.run([dbt_executable, "run", "--profiles-dir", dbt_config_dir], check=True)
