import os
from dagster import (
    DependencyDefinition,
    PipelineDefinition,
    InputDefinition,
    OutputDefinition,
    lambda_solid,
)
from dagster.cli.dynamic_loader import RepositoryTargetInfo
from dagster.core.events import EventType
from dagster.core.execution import create_execution_plan
from dagster.utils import script_relative_path
import dagster_pandas as dagster_pd

from dagit.app import RepositoryContainer
from dagit.pipeline_execution_manager import MultiprocessingExecutionManager
from dagit.pipeline_run_storage import InMemoryPipelineRun, PipelineRunStatus


def get_events_of_type(events, event_type):
    return [event for event in events if event.event_type == event_type]


def test_running():
    run_id = 'run-1'
    repository_container = RepositoryContainer(
        RepositoryTargetInfo(
            repository_yaml=None,
            python_file=__file__,
            fn_name='define_passing_pipeline',
            module_name=None,
        )
    )
    pipeline = define_passing_pipeline()
    env_config = {
        'solids': {
            'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('num.csv')}}}}
        }
    }
    pipeline_run = InMemoryPipelineRun(
        run_id, 'pandas_hello_world', env_config, create_execution_plan(pipeline, env_config)
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(repository_container, pipeline, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS
    events = pipeline_run.all_logs()
    assert events

    process_start_events = get_events_of_type(events, EventType.PIPELINE_PROCESS_START)
    assert len(process_start_events) == 1

    process_started_events = get_events_of_type(events, EventType.PIPELINE_PROCESS_STARTED)
    assert len(process_started_events) == 1


def test_failing():
    run_id = 'run-1'
    repository_container = RepositoryContainer(
        RepositoryTargetInfo(
            repository_yaml=None,
            python_file=__file__,
            fn_name='define_failing_pipeline',
            module_name=None,
        )
    )
    pipeline = define_failing_pipeline()
    env_config = {
        'solids': {
            'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('num.csv')}}}}
        }
    }
    pipeline_run = InMemoryPipelineRun(
        run_id, 'pandas_hello_world', env_config, create_execution_plan(pipeline, env_config)
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(repository_container, pipeline, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    assert pipeline_run.all_logs()


def test_execution_crash():
    run_id = 'run-1'
    repository_container = RepositoryContainer(
        RepositoryTargetInfo(
            repository_yaml=None,
            python_file=__file__,
            fn_name='define_crashy_pipeline',
            module_name=None,
        )
    )
    pipeline = define_crashy_pipeline()
    env_config = {
        'solids': {
            'sum_solid': {'inputs': {'num': {'csv': {'path': script_relative_path('num.csv')}}}}
        }
    }
    pipeline_run = InMemoryPipelineRun(
        run_id, 'pandas_hello_world', env_config, create_execution_plan(pipeline, env_config)
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(repository_container, pipeline, pipeline_run)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    last_log = pipeline_run.all_logs()[-1]
    assert last_log.message == (
        'Exception: Pipeline execution process for {run_id} unexpectedly exited\n'
    ).format(run_id=run_id)


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
def error_solid(sum_df):  # pylint: disable=W0613
    raise Exception('foo')


@lambda_solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def crashy_solid(sum_df):  # pylint: disable=W0613
    os._exit(1)  # pylint: disable=W0212


def define_passing_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world', solids=[sum_solid], dependencies={'sum_solid': {}}
    )


def define_failing_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[sum_solid, error_solid],
        dependencies={
            'sum_solid': {},
            'error_solid': {'sum_df': DependencyDefinition('sum_solid')},
        },
    )


def define_crashy_pipeline():
    return PipelineDefinition(
        name='pandas_hello_world',
        solids=[sum_solid, crashy_solid],
        dependencies={
            'sum_solid': {},
            'crashy_solid': {'sum_df': DependencyDefinition('sum_solid')},
        },
    )
