import os
from typing import Any, Dict, cast

import pytest
from dagster import (
    AssetExecutionContext,
    _check as check,
    materialize,
)
from dagster._core.definitions.metadata import IntMetadataValue
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliInvocation, DbtCliResource

from ..conftest import _create_dbt_invocation
from ..dbt_projects import test_jaffle_shop_path


@pytest.fixture(name="standalone_duckdb_dbfile_path")
def standalone_duckdb_dbfile_path_fixture(request) -> None:
    """Generate a unique duckdb dbfile path for certain tests which need
    it, rather than using the default one-file-per-worker approach.
    """
    jaffle_shop_duckdb_db_file_name = "cool_jaffle_shop"
    jaffle_shop_duckdb_dbfile_path = f"target/{jaffle_shop_duckdb_db_file_name}.duckdb"

    os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_NAME"] = jaffle_shop_duckdb_db_file_name
    os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH"] = jaffle_shop_duckdb_dbfile_path


@pytest.fixture(name="test_jaffle_shop_invocation_standalone_duckdb_dbfile")
def test_jaffle_shop_invocation_standalone_duckdb_dbfile_fixture(
    standalone_duckdb_dbfile_path,
) -> DbtCliInvocation:
    return _create_dbt_invocation(test_jaffle_shop_path)


@pytest.fixture(name="test_jaffle_shop_manifest_standalone_duckdb_dbfile")
def test_jaffle_shop_manifest_standalone_duckdb_dbfile_fixture(
    test_jaffle_shop_invocation_standalone_duckdb_dbfile: DbtCliInvocation,
) -> Dict[str, Any]:
    return test_jaffle_shop_invocation_standalone_duckdb_dbfile.get_artifact("manifest.json")


def test_no_row_count(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))},
    )

    assert result.success

    assert not any(
        "dagster/row_count" in event.materialization.metadata
        for event in result.get_asset_materialization_events()
    )


def test_row_count(
    test_jaffle_shop_manifest_standalone_duckdb_dbfile: Dict[str, Any],
) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest_standalone_duckdb_dbfile)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).enable_fetch_row_count().stream()

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))},
    )

    assert result.success

    # Validate that we have row counts for all models which are not views
    assert all(
        "dagster/row_count" not in event.materialization.metadata
        for event in result.get_asset_materialization_events()
        # staging tables are views, so we don't attempt to get row counts for them
        if "stg" in check.not_none(event.asset_key).path[-1]
    )
    assert all(
        "dagster/row_count" in event.materialization.metadata
        for event in result.get_asset_materialization_events()
        if "stg" not in check.not_none(event.asset_key).path[-1]
    )

    row_counts = [
        cast(IntMetadataValue, event.materialization.metadata["dagster/row_count"]).value
        for event in result.get_asset_materialization_events()
        if "stg" not in check.not_none(event.asset_key).path[-1]
    ]
    assert all(row_count and row_count > 0 for row_count in row_counts), row_counts
