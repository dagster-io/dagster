from tornado import gen

from dagster import solid, ExecutionTargetHandle, ModeDefinition, PipelineDefinition
from dagster.core.test_utils import retry

from dagster_dask import execute_on_dask, DaskConfig


@solid()
def simple(_):
    return 1


def define_dask_test_pipeline():
    return PipelineDefinition(
        name='test_dask_engine', mode_definitions=[ModeDefinition()], solids=[simple]
    )


@retry(gen.TimeoutError, tries=3)
def test_execute_on_dask():
    '''This test is flaky on py27, I believe because of
    https://github.com/dask/distributed/issues/2446. For now, we just retry a couple times...
    '''
    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_fn(define_dask_test_pipeline),
        env_config={'storage': {'filesystem': {}}},
        dask_config=DaskConfig(timeout=30),
    )
    assert result.result_for_solid('simple').result_value() == 1
