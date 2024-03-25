import os
from pathlib import Path
from typing import Any, Dict, Iterator, List

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
    test_dbt_source_freshness_path,
    test_duplicate_source_asset_key_path,
    test_jaffle_shop_path,
    test_meta_config_path,
    test_metadata_path,
)


@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(items: List[pytest.Item]) -> Iterator[None]:
    """Mark tests in the `cloud` and `legacy` directories. Mark other tests as `core`."""
    for item in items:
        if "cloud" in item.path.parts:
            item.add_marker(pytest.mark.cloud)
        elif "legacy" in item.path.parts:
            item.add_marker(pytest.mark.legacy)
        else:
            item.add_marker(pytest.mark.core)

    yield


@pytest.fixture(scope="session", autouse=True)
def setup_duckdb_dbfile_path_fixture(worker_id: str) -> None:
    """Set `DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH` to generate a unique duckdb dbfile path
    for each pytest-xdist worker.
    """
    jaffle_shop_duckdb_db_file_name = f"{worker_id}_jaffle_shop"
    jaffle_shop_duckdb_dbfile_path = f"target/{jaffle_shop_duckdb_db_file_name}.duckdb"

    os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_NAME"] = jaffle_shop_duckdb_db_file_name
    os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH"] = jaffle_shop_duckdb_dbfile_path


@pytest.fixture(scope="session", autouse=True)
def disable_openblas_threading_affinity_fixture() -> None:
    """Disable OpenBLAS and GotoBLAS threading affinity to prevent test failures."""
    os.environ["OPENBLAS_MAIN_FREE"] = "1"
    os.environ["GOTOBLAS_MAIN_FREE"] = "1"


def _create_dbt_invocation(project_dir: Path, build_project: bool = False) -> DbtCliInvocation:
    dbt = DbtCliResource(project_dir=os.fspath(project_dir), global_config_flags=["--quiet"])

    dbt.cli(["deps"]).wait()
    dbt_invocation = dbt.cli(["compile"]).wait()

    if build_project:
        dbt.cli(["build"], raise_on_error=False).wait()

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
    # Prepopulate duckdb with jaffle shop data to support testing individual asset checks.
    return _create_dbt_invocation(
        test_asset_checks_path,
        build_project=True,
    ).get_artifact("manifest.json")


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


@pytest.fixture(name="test_dbt_source_freshness_manifest", scope="session")
def test_dbt_source_freshness_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_dbt_source_freshness_path).get_artifact("manifest.json")


@pytest.fixture(name="test_duplicate_source_asset_key_manifest", scope="session")
def test_duplicate_source_asset_key_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_duplicate_source_asset_key_path).get_artifact(
        "manifest.json"
    )


@pytest.fixture(name="test_meta_config_manifest", scope="session")
def test_meta_config_manifest_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_meta_config_path).get_artifact("manifest.json")


@pytest.fixture(name="test_metadata_manifest", scope="session")
def test_metadata_manifest_fixture() -> Dict[str, Any]:
    # Prepopulate duckdb with jaffle shop data to support testing individual column metadata.
    return _create_dbt_invocation(
        test_metadata_path,
        build_project=True,
    ).get_artifact("manifest.json")
