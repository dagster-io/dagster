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
from dagster_dbt.core.resources_v2 import DbtCliResource

from ..dbt_projects import test_jaffle_shop_path


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


import shutil


@pytest.fixture()
def force_free_lock_on_db() -> None:
    db_file = os.getenv("DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH")

    # copy db file to a new location and delete the original
    if db_file and os.path.exists(db_file):
        db_file_copy = os.path.abspath(f"{db_file}_copy")
        db_file_abspath = os.path.abspath(db_file)

        shutil.copyfile(db_file_abspath, db_file_copy)
        os.remove(db_file_abspath)

        shutil.copyfile(db_file_copy, db_file_abspath)


def test_row_count(test_jaffle_shop_manifest: Dict[str, Any], force_free_lock_on_db) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
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
