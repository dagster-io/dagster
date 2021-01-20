import tempfile

from dagster import (
    ModeDefinition,
    execute_pipeline,
    fs_io_manager,
    pipeline,
    reconstructable,
    solid,
)
from dagster.core.test_utils import instance_for_test


@solid
def solid_a(_context):
    return [1, 2, 3]


@solid
def solid_b(_context, _df):
    return 1


@pipeline(mode_defs=[ModeDefinition("local", resource_defs={"io_manager": fs_io_manager})])
def my_pipeline():
    solid_b(solid_a())


def test_io_manager_with_multi_process_executor():
    with instance_for_test() as instance:
        with tempfile.TemporaryDirectory() as tmpdir_path:
            result = execute_pipeline(
                reconstructable(my_pipeline),
                run_config={
                    "execution": {"multiprocess": {}},
                    "resources": {"io_manager": {"config": {"base_dir": tmpdir_path}}},
                },
                instance=instance,
            )
            assert result.success
