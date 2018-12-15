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
)
from dagster.core.evaluator import evaluate_config_value
from dagster.utils import script_relative_path
import dagster_contrib.pandas as dagster_pd

from dagit.pipeline_execution_manager import MultiprocessingExecutionManager
from dagit.pipeline_run_storage import PipelineRun, PipelineRunStatus


def test_running():
    run_id = 'run-1'
    pipeline = define_passing_pipeline()
    config = evaluate_config_value(
        pipeline.environment_type, {
            'solids': {
                'load_num_csv': {
                    'config': {
                        'path': script_relative_path('num.csv'),
                    }
                },
            },
        }
    )
    pipeline_run = PipelineRun(
        run_id, 'pandas_hello_world', config, create_execution_plan(pipeline, config.value)
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(pipeline, config.value, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS
    assert len(pipeline_run.all_logs()) > 0


def test_failing():
    run_id = 'run-1'
    pipeline = define_failing_pipeline()
    config = evaluate_config_value(
        pipeline.environment_type, {
            'solids': {
                'load_num_csv': {
                    'config': {
                        'path': script_relative_path('num.csv'),
                    }
                },
            },
        }
    )
    pipeline_run = PipelineRun(
        run_id, 'pandas_hello_world', config, create_execution_plan(pipeline, config.value)
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(pipeline, config.value, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    assert len(pipeline_run.all_logs()) > 0


def test_execution_crash():
    run_id = 'run-1'
    pipeline = define_crashy_pipeline()
    config = evaluate_config_value(
        pipeline.environment_type, {
            'solids': {
                'load_num_csv': {
                    'config': {
                        'path': script_relative_path('num.csv'),
                    }
                },
            },
        }
    )
    pipeline_run = PipelineRun(
        run_id, 'pandas_hello_world', config, create_execution_plan(pipeline, config.value)
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(pipeline, config.value, pipeline_run)
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
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
        ],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
        },
    )


def define_failing_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
            error_solid,
        ],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
            'error_solid': {
                'sum_df': DependencyDefinition('sum_solid')
            }
        },
    )


def define_crashy_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[
            dagster_pd.load_csv_solid('load_num_csv'),
            sum_solid,
            crashy_solid,
        ],
        dependencies={
            'sum_solid': {
                'num': DependencyDefinition('load_num_csv')
            },
            'crashy_solid': {
                'sum_df': DependencyDefinition('sum_solid')
            }
        },
    )
