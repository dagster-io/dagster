import os
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    AssetKey,
    _check as check,
    materialize,
)
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.resource import SdfCliResource

from .sdf_workspaces import lineage_path, moms_flower_shop_path


def test_decorator_arguments(lineage_target_dir: Path) -> None:
    @sdf_assets(workspace_dir=lineage_path, target_dir=lineage_target_dir)
    def my_sdf_assets(): ...

    assert my_sdf_assets.keys == {
        AssetKey(key)
        for key in {
            ("lineage", "pub", "source"),
            ("lineage", "pub", "sink"),
            ("lineage", "pub", "knis"),
            ("lineage", "pub", "middle"),
        }
    }


def test_sdf_with_materialize(lineage_target_dir: Path, moms_flower_shop_target_dir: Path) -> None:
    for workspace_dir, target_dir in [
        (lineage_path, lineage_target_dir),
        (moms_flower_shop_path, moms_flower_shop_target_dir),
    ]:

        @sdf_assets(workspace_dir=workspace_dir, target_dir=target_dir)
        def my_sdf_assets(context: AssetExecutionContext, sdf: SdfCliResource):
            yield from sdf.cli(["run"], target_dir=target_dir, context=context).stream()

        result = materialize(
            [my_sdf_assets],
            resources={
                "sdf": SdfCliResource(
                    workspace_dir=os.fspath(workspace_dir),
                    global_config_flags=["--log-form=nested"],
                )
            },
        )
        assert result.success

        # Assert that get_asset_materialization_events() is not empty
        assert result.get_asset_materialization_events()

        metadata_by_asset_key = {
            check.not_none(event.asset_key): event.materialization.metadata
            for event in result.get_asset_materialization_events()
        }

        # Validate that we have a materialized_at time for all models which are not views
        assert all(
            "materialized_at" in metadata for _, metadata in metadata_by_asset_key.items()
        ), str(metadata_by_asset_key)
