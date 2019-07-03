import csv
import os
from collections import OrderedDict
from copy import deepcopy

from dagster import (
    DependencyDefinition,
    ExecutionTargetHandle,
    InputDefinition,
    Materialization,
    OutputDefinition,
    Path,
    PipelineDefinition,
    as_dagster_type,
    input_hydration_config,
    lambda_solid,
    output_materialization_config,
)
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import ExecutionSelector
from dagster.core.utils import make_new_run_id
from dagster.utils import script_relative_path
from dagster_graphql.implementation.pipeline_execution_manager import (
    MultiprocessingExecutionManager,
)
from dagster_graphql.implementation.pipeline_run_storage import (
    InMemoryPipelineRun,
    PipelineRunStatus,
)


class PoorMansDataFrame_(list):
    pass


@input_hydration_config(Path)
def df_input_schema(_context, path):
    with open(path, 'r') as fd:
        return PoorMansDataFrame_(
            [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]
        )


@output_materialization_config(Path)
def df_output_schema(_context, path, value):
    with open(path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return Materialization.file(path)


PoorMansDataFrame = as_dagster_type(
    PoorMansDataFrame_,
    input_hydration_config=df_input_schema,
    output_materialization_config=df_output_schema,
)


def get_events_of_type(events, event_type):
    return [
        event
        for event in events
        if event.is_dagster_event and event.dagster_event.event_type == event_type
    ]


def test_running():
    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_fn(define_passing_pipeline)
    pipeline = define_passing_pipeline()
    env_config = {
        'solids': {'sum_solid': {'inputs': {'num': script_relative_path('data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')
    pipeline_run = InMemoryPipelineRun(
        run_id,
        selector,
        env_config,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(handle, pipeline, pipeline_run, raise_on_error=False)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.SUCCESS
    events = pipeline_run.all_logs()
    assert events

    process_start_events = get_events_of_type(events, DagsterEventType.PIPELINE_PROCESS_START)
    assert len(process_start_events) == 1

    process_started_events = get_events_of_type(events, DagsterEventType.PIPELINE_PROCESS_STARTED)
    assert len(process_started_events) == 1


def test_failing():
    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_fn(define_failing_pipeline)
    pipeline = define_failing_pipeline()
    env_config = {
        'solids': {'sum_solid': {'inputs': {'num': script_relative_path('data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')
    pipeline_run = InMemoryPipelineRun(
        run_id,
        selector,
        env_config,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(handle, pipeline, pipeline_run, raise_on_error=False)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    assert pipeline_run.all_logs()


def test_execution_crash():
    run_id = make_new_run_id()
    handle = ExecutionTargetHandle.for_pipeline_fn(define_crashy_pipeline)
    pipeline = define_crashy_pipeline()
    env_config = {
        'solids': {'sum_solid': {'inputs': {'num': script_relative_path('data/num.csv')}}}
    }
    selector = ExecutionSelector('csv_hello_world')
    pipeline_run = InMemoryPipelineRun(
        run_id,
        selector,
        env_config,
        mode='default',
        reexecution_config=None,
        step_keys_to_execute=None,
    )
    execution_manager = MultiprocessingExecutionManager()
    execution_manager.execute_pipeline(handle, pipeline, pipeline_run, raise_on_error=False)
    execution_manager.join()
    assert pipeline_run.status == PipelineRunStatus.FAILURE
    last_log = pipeline_run.all_logs()[-1]
    print(last_log.message)
    assert last_log.message.startswith(
        'Exception: Pipeline execution process for {run_id} unexpectedly exited\n'.format(
            run_id=run_id
        )
    )


@lambda_solid(
    input_defs=[InputDefinition('num', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x['sum'] = x['num1'] + x['num2']
    return PoorMansDataFrame(sum_df)


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def error_solid(sum_df):  # pylint: disable=W0613
    raise Exception('foo')


@lambda_solid(
    input_defs=[InputDefinition('sum_df', PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def crashy_solid(sum_df):  # pylint: disable=W0613
    os._exit(1)  # pylint: disable=W0212


def define_passing_pipeline():
    return PipelineDefinition(
        name='csv_hello_world', solid_defs=[sum_solid], dependencies={'sum_solid': {}}
    )


def define_failing_pipeline():
    return PipelineDefinition(
        name='csv_hello_world',
        solid_defs=[sum_solid, error_solid],
        dependencies={
            'sum_solid': {},
            'error_solid': {'sum_df': DependencyDefinition('sum_solid')},
        },
    )


def define_crashy_pipeline():
    return PipelineDefinition(
        name='csv_hello_world',
        solid_defs=[sum_solid, crashy_solid],
        dependencies={
            'sum_solid': {},
            'crashy_solid': {'sum_df': DependencyDefinition('sum_solid')},
        },
    )
