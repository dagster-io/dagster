import dagster_pandas as dagster_pd
from dagster_dask import dask_executor

from dagster import (
    ExecutionTargetHandle,
    InputDefinition,
    ModeDefinition,
    execute_pipeline,
    file_relative_path,
    pipeline,
    seven,
    solid,
)
from dagster.core.definitions.executor import default_executors
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import nesting_composite_pipeline


@solid
def simple(_):
    return 1


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
def dask_engine_pipeline():
    return simple()


def test_execute_on_dask():
    with seven.TemporaryDirectory() as tempdir:
        result = execute_pipeline(
            ExecutionTargetHandle.for_pipeline_python_file(
                __file__, 'dask_engine_pipeline'
            ).build_pipeline_definition(),
            environment_dict={
                'storage': {'filesystem': {'config': {'base_dir': tempdir}}},
                'execution': {'dask': {'config': {'timeout': 30}}},
            },
            instance=DagsterInstance.local_temp(),
        )
        assert result.result_for_solid('simple').output_value() == 1


def dask_composite_pipeline():
    return nesting_composite_pipeline(
        6, 2, mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])]
    )


def test_composite_execute():
    result = execute_pipeline(
        ExecutionTargetHandle.for_pipeline_python_file(
            __file__, 'dask_composite_pipeline'
        ).build_pipeline_definition(),
        environment_dict={
            'storage': {'filesystem': {}},
            'execution': {'dask': {'config': {'timeout': 30}}},
        },
        instance=DagsterInstance.local_temp(),
    )
    assert result.success


@solid(input_defs=[InputDefinition('df', dagster_pd.DataFrame)])
def pandas_solid(_, df):  # pylint: disable=unused-argument
    pass


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
def pandas_pipeline():
    return pandas_solid()


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
        environment_dict={
            'storage': {'filesystem': {}},
            'execution': {'dask': {'config': {'timeout': 30}}},
            **environment_dict,
        },
        instance=DagsterInstance.local_temp(),
    )

    assert result.success
