import os
import pytest
import time
import gevent
from dagster import (
    DependencyDefinition,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    InputDefinition,
    OutputDefinition,
    RepositoryDefinition,
    SolidDefinition,
    check,
    lambda_solid,
    types,
)
from dagster.core.execution import (
    create_execution_plan,
    create_typed_environment,
)
from dagster.core.evaluator import (
    evaluate_config_value,
)
from dagster.utils import script_relative_path
import dagster_contrib.pandas as dagster_pd
from dagster.cli.dynamic_loader import RepositoryTargetInfo

from dagit.app import RepositoryContainer
from dagit.pipeline_execution_manager import MultiprocessingExecutionManager
from dagit.pipeline_run_storage import InMemoryPipelineRun, PipelineRunStatus


def test_running():
    run_id = 'run-1'
    repository_container = RepositoryContainer(
        RepositoryTargetInfo(
            repository_yaml=None,
            python_file=None,
            fn_name='define_passing_pipeline',
            module_name='dagit.dagit_tests.test_multiprocessing',
        )
    )
    pipeline = define_passing_pipeline()
    config = {
        'solids': {
            'sum_solid': {
                'inputs': {
                    'num': {
                        'csv': {
                            'path': script_relative_path('num.csv'),
                        },
                    },
                }
            },
        },
    }
    typed_environment = create_typed_environment(pipeline, config)
    pipeline_run = InMemoryPipelineRun(
        run_id,
        'pandas_hello_world',
        typed_environment,
        config,
        create_execution_plan(pipeline, typed_environment),
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(repository_container, pipeline, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS
    assert len(pipeline_run.all_logs()) > 0


def test_failing():
    run_id = 'run-1'
    repository_container = RepositoryContainer(
        RepositoryTargetInfo(
            repository_yaml=None,
            python_file=None,
            fn_name='define_failing_pipeline',
            module_name='dagit.dagit_tests.test_multiprocessing',
        )
    )
    pipeline = define_failing_pipeline()
    config = {
        'solids': {
            'sum_solid': {
                'inputs': {
                    'num': {
                        'csv': {
                            'path': script_relative_path('num.csv'),
                        },
                    },
                }
            },
        },
    }
    typed_environment = create_typed_environment(pipeline, config)
    pipeline_run = InMemoryPipelineRun(
        run_id,
        'pandas_hello_world',
        typed_environment,
        config,
        create_execution_plan(pipeline, typed_environment),
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(repository_container, pipeline, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    assert len(pipeline_run.all_logs()) > 0


def test_execution_crash():
    run_id = 'run-1'
    repository_container = RepositoryContainer(
        RepositoryTargetInfo(
            repository_yaml=None,
            python_file=None,
            fn_name='define_crashy_pipeline',
            module_name='dagit.dagit_tests.test_multiprocessing',
        )
    )
    pipeline = define_crashy_pipeline()
    config = {
        'solids': {
            'sum_solid': {
                'inputs': {
                    'num': {
                        'csv': {
                            'path': script_relative_path('num.csv'),
                        },
                    },
                }
            },
        },
    }
    typed_environment = create_typed_environment(pipeline, config)
    pipeline_run = InMemoryPipelineRun(
        run_id,
        'pandas_hello_world',
        typed_environment,
        config,
        create_execution_plan(
            pipeline,
            typed_environment,
        ),
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(repository_container, pipeline, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    last_log = pipeline_run.all_logs()[-1]
    assert last_log.message == 'Exception: Pipeline execution process for {run_id} unexpectedly exited\n'.format(
        run_id=run_id
    )


@lambda_solid(
    inputs=[InputDefinition('num', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_solid(num):
    sum_df = num.copy()
    sum_df['sum'] = sum_df['num1'] + sum_df['num2']
    return sum_df


@lambda_solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def error_solid(sum_df):
    raise Exception('foo')


@lambda_solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def crashy_solid(sum_df):
    os._exit(1)


def define_passing_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[
            sum_solid,
        ],
        dependencies={
            'sum_solid': {},
        },
    )


def define_failing_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[
            sum_solid,
            error_solid,
        ],
        dependencies={
            'sum_solid': {},
            'error_solid': {
                'sum_df': DependencyDefinition('sum_solid')
            }
        },
    )


def define_crashy_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[
            sum_solid,
            crashy_solid,
        ],
        dependencies={
            'sum_solid': {},
            'crashy_solid': {
                'sum_df': DependencyDefinition('sum_solid')
            }
        },
    )
