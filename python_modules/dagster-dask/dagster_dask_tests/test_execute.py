from dagster import solid, ExecutionTargetHandle, ModeDefinition, PipelineDefinition
from dagster.core.execution.config import RunConfig
from dagster.core.runs import RunStorageMode

from dagster_dask import execute_on_dask


@solid()
def simple(_):
    return 1


def define_dask_test_pipeline():
    return PipelineDefinition(
        name='test_dask_engine', mode_definitions=[ModeDefinition()], solids=[simple]
    )


def test_execute_on_dask():
    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_fn(define_dask_test_pipeline),
        env_config={'storage': {'filesystem': {}}},
        run_config=RunConfig(storage_mode=RunStorageMode.FILESYSTEM),
    )
    assert result.result_for_solid('simple').transformed_value() == 1
