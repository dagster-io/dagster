from dagster import file_relative_path, pipeline, solid, ExecutionTargetHandle, InputDefinition
from dagster.core.test_utils import nesting_composite_pipeline
from dagster_dask import execute_on_dask, DaskConfig

import dagster_pandas as dagster_pd


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


@solid(input_defs=[InputDefinition('df', dagster_pd.DataFrame)])
def pandas_solid(_, df):  # pylint: disable=unused-argument
    pass


@pipeline
def pandas_pipeline():
    return pandas_solid()  # pylint: disable=no-value-for-parameter


def test_pandas_dask():
    environment_dict = {
        'solids': {
            'pandas_solid': {
                'inputs': {'df': {'csv': {'path': file_relative_path(__file__, 'ex.csv')}}}
            }
        }
    }

    result = execute_on_dask(
        ExecutionTargetHandle.for_pipeline_python_file(__file__, pandas_pipeline.name),
        env_config={'storage': {'filesystem': {}}, **environment_dict},
        dask_config=DaskConfig(timeout=30),
    )

    assert result.success
