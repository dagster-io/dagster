import os
import subprocess
from pathlib import Path
from typing import Any, Dict

import pytest
from dagster._utils import file_relative_path, pushd
from dagster_dbt import DbtCliClientResource, DbtCliResource, dbt_cli_resource

from .dbt_projects import (
    test_asset_checks_path,
    test_asset_key_exceptions_path,
    test_dbt_alias_path,
    test_dbt_model_versions_path,
    test_dbt_python_interleaving_path,
    test_jaffle_shop_path,
    test_meta_config_path,
    test_metadata_path,
)

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
        pytest.param("DbtCliResource"),
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


def _create_dbt_manifest(project_dir: Path) -> Dict[str, Any]:
    dbt = DbtCliResource(project_dir=os.fspath(project_dir), global_config_flags=["--quiet"])

    dbt.cli(["deps"]).wait()
    dbt_invocation = dbt.cli(["compile"]).wait()

    return dbt_invocation.get_artifact("manifest.json")


@pytest.fixture(name="test_jaffle_shop_manifest", scope="session")
def test_jaffle_shop_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_jaffle_shop_path)


@pytest.fixture(name="test_asset_checks_manifest", scope="session")
def test_asset_checks_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_asset_checks_path)


@pytest.fixture(name="test_asset_key_exceptions_manifest", scope="session")
def test_asset_key_exceptions_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_asset_key_exceptions_path)


@pytest.fixture(name="test_dbt_alias_manifest", scope="session")
def test_dbt_alias_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_dbt_alias_path)


@pytest.fixture(name="test_dbt_model_versions_manifest", scope="session")
def test_dbt_model_versions_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_dbt_model_versions_path)


@pytest.fixture(name="test_dbt_python_interleaving_manifest", scope="session")
def test_dbt_python_interleaving_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_dbt_python_interleaving_path)


@pytest.fixture(name="test_meta_config_manifest", scope="session")
def test_meta_config_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_meta_config_path)


@pytest.fixture(name="test_metadata_manifest", scope="session")
def test_metadata_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_manifest(test_metadata_path)
