from dagster import solid, ExecutionTargetHandle, ModeDefinition, PipelineDefinition

from dagster_dask import execute_on_dask, DaskConfig


@solid()
def simple(_):
    return 1


def define_dask_test_pipeline():
    return PipelineDefinition(
        name='test_dask_engine', mode_defs=[ModeDefinition()], solid_defs=[simple]
    )


def test_execute_on_dask():
    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_fn(define_dask_test_pipeline),
        env_config={'storage': {'filesystem': {}}},
        dask_config=DaskConfig(timeout=30),
    )
    assert result.result_for_solid('simple').result_value() == 1
