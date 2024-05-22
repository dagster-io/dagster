import os
from typing import Any, Dict, cast

import mock
import pytest
from dagster import (
    AssetExecutionContext,
    _check as check,
    materialize,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliInvocation, DbtCliResource

from ..conftest import _create_dbt_invocation
from ..dbt_projects import test_jaffle_shop_path


@pytest.fixture(name="standalone_duckdb_dbfile_path")
def standalone_duckdb_dbfile_path_fixture(request) -> None:
    """Generate a unique duckdb dbfile path for certain tests which need
    it, rather than using the default one-file-per-worker approach.
    """
    node_name = cast(str, request.node.name).replace("[", "_").replace("]", "_")
    jaffle_shop_duckdb_db_file_name = f"{node_name}_jaffle_shop"
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


def test_no_row_count(test_jaffle_shop_manifest_standalone_duckdb_dbfile: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest_standalone_duckdb_dbfile)
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


@pytest.fixture(name="test_jaffle_shop_manifest_snowflake")
def test_jaffle_shop_manifest_snowflake_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_jaffle_shop_path, target="snowflake").get_artifact(
        "manifest.json"
    )


@pytest.fixture(name="test_jaffle_shop_manifest_bigquery")
def test_jaffle_shop_manifest_bigquery_fixture() -> Dict[str, Any]:
    return _create_dbt_invocation(test_jaffle_shop_path, target="bigquery").get_artifact(
        "manifest.json"
    )


@pytest.mark.parametrize(
    "target, manifest_fixture_name",
    [
        pytest.param(None, "test_jaffle_shop_manifest_standalone_duckdb_dbfile", id="duckdb"),
        pytest.param(
            "snowflake",
            "test_jaffle_shop_manifest_snowflake",
            marks=pytest.mark.snowflake,
            id="snowflake",
        ),
        pytest.param(
            "bigquery",
            "test_jaffle_shop_manifest_bigquery",
            marks=pytest.mark.bigquery,
            id="bigquery",
        ),
    ],
)
def test_row_count(request: pytest.FixtureRequest, target: str, manifest_fixture_name: str) -> None:
    manifest = cast(Dict[str, Any], request.getfixturevalue(manifest_fixture_name))

    @dbt_assets(manifest=manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream().fetch_row_counts()

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path), target=target)
        },
    )

    assert result.success

    metadata_by_asset_key = {
        check.not_none(event.asset_key): event.materialization.metadata
        for event in result.get_asset_materialization_events()
    }

    # Validate that we have row counts for all models which are not views
    assert all(
        "dagster/row_count" not in metadata
        for asset_key, metadata in metadata_by_asset_key.items()
        # staging tables are views, so we don't attempt to get row counts for them
        if "stg" in asset_key.path[-1]
    ), metadata_by_asset_key
    assert all(
        "dagster/row_count" in metadata
        for asset_key, metadata in metadata_by_asset_key.items()
        # staging tables are views, so we don't attempt to get row counts for them
        if "stg" not in asset_key.path[-1]
    ), metadata_by_asset_key


def test_row_count_err(
    test_jaffle_shop_manifest_standalone_duckdb_dbfile: Dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    # test that we can handle exceptions in row count fetching
    # and still complete the dbt assets materialization
    with mock.patch("dbt.adapters.duckdb.DuckDBAdapter.execute") as mock_execute:
        mock_execute.side_effect = Exception("mock_execute exception")

        @dbt_assets(manifest=test_jaffle_shop_manifest_standalone_duckdb_dbfile)
        def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
            yield from dbt.cli(["build"], context=context).stream().fetch_row_counts()

        result = materialize(
            [my_dbt_assets],
            resources={"dbt": DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))},
        )

        assert result.success

        # Validate that no row counts were fetched due to the exception
        assert not any(
            "dagster/row_count" in event.materialization.metadata
            for event in result.get_asset_materialization_events()
        )

        # assert we have warning message in logs
        assert "An error occurred while fetching row count for " in caplog.text
