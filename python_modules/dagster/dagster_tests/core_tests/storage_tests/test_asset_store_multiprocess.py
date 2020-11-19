from dagster import (
    ModeDefinition,
    execute_pipeline,
    fs_asset_store,
    pipeline,
    reconstructable,
    seven,
    solid,
)
from dagster.core.test_utils import instance_for_test


@solid
def solid_a(_context):
    return [1, 2, 3]


@solid
def solid_b(_context, _df):
    return 1


@pipeline(mode_defs=[ModeDefinition("local", resource_defs={"asset_store": fs_asset_store})])
def asset_pipeline():
    solid_b(solid_a())


def test_asset_store_with_multi_process_executor():
    with instance_for_test() as instance:
        with seven.TemporaryDirectory() as tmpdir_path:
            result = execute_pipeline(
                reconstructable(asset_pipeline),
                run_config={
                    "execution": {"multiprocess": {}},
                    "resources": {"asset_store": {"config": {"base_dir": tmpdir_path}}},
                },
                instance=instance,
            )
            assert result.success
