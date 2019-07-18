from dagster import (
    execute_pipeline,
    file_relative_path,
    pipeline,
    solid,
    ExecutionTargetHandle,
    InputDefinition,
    RunConfig,
)
from dagster.core.test_utils import nesting_composite_pipeline
from dagster_dask import DaskConfig

import dagster_pandas as dagster_pd


@solid
def simple(_):
    return 1


@pipeline
def dask_engine_pipeline():
    return simple()  # pylint: disable=no-value-for-parameter


def test_execute_on_dask():
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_python_file(
            __file__, 'dask_engine_pipeline'
        ).build_pipeline_definition(),
        environment_dict={'storage': {'filesystem': {}}},
        run_config=RunConfig(executor_config=DaskConfig(timeout=30)),
    )
    assert result.result_for_solid('simple').output_value() == 1


def dask_composite_pipeline():
    return nesting_composite_pipeline(6, 2)


def test_composite_execute():
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_python_file(
            __file__, 'dask_composite_pipeline'
        ).build_pipeline_definition(),
        environment_dict={'storage': {'filesystem': {}}},
        run_config=RunConfig(executor_config=DaskConfig(timeout=30)),
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

    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_python_file(
            __file__, pandas_pipeline.name
        ).build_pipeline_definition(),
        environment_dict={'storage': {'filesystem': {}}, **environment_dict},
        run_config=RunConfig(executor_config=DaskConfig(timeout=30)),
    )

    assert result.success
