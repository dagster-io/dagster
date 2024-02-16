import os
from pathlib import Path
from typing import Any, Dict, List

import pytest
from dagster_dbt import DbtCliResource
from dagster_dbt.core.resources_v2 import DbtCliInvocation

from .dbt_projects import (
    test_asset_checks_path,
    test_asset_key_exceptions_path,
    test_dbt_alias_path,
    test_dbt_model_versions_path,
    test_dbt_python_interleaving_path,
    test_dbt_semantic_models_path,
    test_jaffle_shop_path,
    test_meta_config_path,
    test_metadata_path,
)


def pytest_collection_modifyitems(items: List[pytest.Item]):
    """Mark tests in the `cloud` and `legacy` directories. Mark other tests as `core`."""
    for item in items:
        if "cloud" in item.path.parts:
            item.add_marker(pytest.mark.cloud)
        elif "legacy" in item.path.parts:
            item.add_marker(pytest.mark.legacy)
        else:
            item.add_marker(pytest.mark.core)


def _create_dbt_invocation(project_dir: Path) -> DbtCliInvocation:
    dbt = DbtCliResource(project_dir=os.fspath(project_dir), global_config_flags=["--quiet"])

    dbt.cli(["deps"]).wait()
    dbt_invocation = dbt.cli(["compile"]).wait()

    return dbt_invocation


@pytest.fixture(name="test_jaffle_shop_invocation", scope="session")
def test_jaffle_shop_invocation_fixture() -> DbtCliInvocation:
    return _create_dbt_invocation(test_jaffle_shop_path)


@pytest.fixture(name="test_jaffle_shop_manifest_path", scope="session")
def test_jaffle_shop_manifest_path_fixture(test_jaffle_shop_invocation: DbtCliInvocation) -> Path:
    return test_jaffle_shop_invocation.target_path.joinpath("manifest.json")


@pytest.fixture(name="test_jaffle_shop_manifest", scope="session")
def test_jaffle_shop_manifest_fixture(
    test_jaffle_shop_invocation: DbtCliInvocation,
) -> Dict[str, Any]:
    return test_jaffle_shop_invocation.get_artifact("manifest.json")


@pytest.fixture(name="test_asset_checks_manifest", scope="session")
def test_asset_checks_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_asset_checks_path).get_artifact("manifest.json")


@pytest.fixture(name="test_asset_key_exceptions_manifest", scope="session")
def test_asset_key_exceptions_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_asset_key_exceptions_path).get_artifact("manifest.json")


@pytest.fixture(name="test_dbt_alias_manifest", scope="session")
def test_dbt_alias_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_dbt_alias_path).get_artifact("manifest.json")


@pytest.fixture(name="test_dbt_model_versions_manifest", scope="session")
def test_dbt_model_versions_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_dbt_model_versions_path).get_artifact("manifest.json")


@pytest.fixture(name="test_dbt_python_interleaving_manifest", scope="session")
def test_dbt_python_interleaving_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_dbt_python_interleaving_path).get_artifact("manifest.json")


@pytest.fixture(name="test_dbt_semantic_models_manifest", scope="session")
def test_dbt_semantic_models_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_dbt_semantic_models_path).get_artifact("manifest.json")


@pytest.fixture(name="test_meta_config_manifest", scope="session")
def test_meta_config_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_meta_config_path).get_artifact("manifest.json")


@pytest.fixture(name="test_metadata_manifest", scope="session")
def test_metadata_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_metadata_path).get_artifact("manifest.json")
