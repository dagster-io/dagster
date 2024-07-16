import os
from pathlib import Path

from dagster import (
    AssetKey,
    AssetExecutionContext,
    materialize,
    _check as check,
)
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.sdf_cli_resource import SdfCliResource
from .sdf_workspaces import test_csv_123_path

def test_decorator_arguments(
    test_csv_123_target_dir: Path
) -> None:
    for (workspace_dir, target_dir) in [ (test_csv_123_path, test_csv_123_target_dir) ]:
        @sdf_assets(workspace_dir=workspace_dir, target_dir=target_dir)
        def my_sdf_assets(): ...
        assert my_sdf_assets.keys == {
            AssetKey(key)
            for key in {
                ("csv_123","pub","one"),
                ("csv_123","pub","two"),
                ("csv_123","pub","three"),
            }
        }

def test_sdf_with_materialize(test_csv_123_target_dir: Path) -> None:
    for (workspace_dir, target_dir) in [ (test_csv_123_path, test_csv_123_target_dir) ]:
        @sdf_assets(workspace_dir=workspace_dir, target_dir=target_dir)
        def my_sdf_assets(context: AssetExecutionContext, sdf: SdfCliResource):
            yield from sdf.cli(["run"], target_dir=target_dir, context=context).stream()

        result = materialize(
            [my_sdf_assets],
            resources={"sdf": SdfCliResource(workspace_dir=os.fspath(workspace_dir), global_config_flags=["--show=none", "--log-level=info", "--log-form=nested"])},
        )
        assert result.success

def test_no_row_count(test_csv_123_target_dir: Path) -> None:
    for (workspace_dir, target_dir) in [ (test_csv_123_path, test_csv_123_target_dir) ]:
        @sdf_assets(workspace_dir=workspace_dir, target_dir=target_dir)
        def my_sdf_assets(context: AssetExecutionContext, sdf: SdfCliResource):
            yield from sdf.cli(["run"], target_dir=target_dir, context=context).stream()

        result = materialize(
            [my_sdf_assets],
            resources={"sdf": SdfCliResource(workspace_dir=os.fspath(workspace_dir), global_config_flags=["--show=none", "--log-level=info", "--log-form=nested"])},
        )

        assert result.success

        # Assert that get_asset_materialization_events() is not empty
        assert result.get_asset_materialization_events()

        metadata_by_asset_key = {
        check.not_none(event.asset_key): event.materialization.metadata
            for event in result.get_asset_materialization_events()
        }

        # Validate that we have row counts for all models which are not views
        assert all(
            "materialized_at" in metadata
            for _, metadata in metadata_by_asset_key.items()
        ), str(metadata_by_asset_key)
