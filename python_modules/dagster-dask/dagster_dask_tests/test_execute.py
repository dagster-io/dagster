from dagster import pipeline, solid, ExecutionTargetHandle
from dagster.core.test_utils import nesting_composite_pipeline
from dagster_dask import execute_on_dask, DaskConfig


@solid
def simple(_):
    return 1


@pipeline
def dask_engine_pipeline():
    return simple()  # pylint: disable=no-value-for-parameter


def test_execute_on_dask():
    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_python_file(__file__, 'dask_engine_pipeline'),
        env_config={'storage': {'filesystem': {}}},
        dask_config=DaskConfig(timeout=30),
    )
    assert result.result_for_solid('simple').output_value() == 1


def dask_composite_pipeline():
    return nesting_composite_pipeline(6, 2)


def test_composite_execute():
    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_python_file(__file__, 'dask_composite_pipeline'),
        env_config={'storage': {'filesystem': {}}},
        dask_config=DaskConfig(timeout=30),
    )
    assert result.success
