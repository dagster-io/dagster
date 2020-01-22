import os
import time

from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import execute_pipeline
from dagster.core.instance import DagsterInstance
from dagster.utils import safe_tempfile_path

from .execution_queries import START_PIPELINE_EXECUTION_QUERY
from .setup import define_test_subprocess_context

RUN_CANCELLATION_QUERY = '''
mutation($runId: String!) {
  cancelPipelineExecution(runId: $runId){
    __typename
    ... on CancelPipelineExecutionSuccess{
      run {
        runId
      }
    }
    ... on CancelPipelineExecutionFailure {
      run {
        runId
      }
      message
    }
    ... on PipelineRunNotFoundError {
      runId
    }
  }
}
'''


def test_basic_cancellation():
    context = define_test_subprocess_context(DagsterInstance.local_temp())
    with safe_tempfile_path() as path:
        result = execute_dagster_graphql(
            context,
            START_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'infinite_loop_pipeline'},
                    'mode': 'default',
                    'environmentConfigData': {'solids': {'loop': {'config': {'file': path}}}},
                }
            },
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert (
            result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )
        run_id = result.data['startPipelineExecution']['run']['runId']

        assert run_id

        # ensure the execution has happened
        while not os.path.exists(path):
            time.sleep(0.1)

        result = execute_dagster_graphql(
            context, RUN_CANCELLATION_QUERY, variables={'runId': run_id}
        )

        assert (
            result.data['cancelPipelineExecution']['__typename'] == 'CancelPipelineExecutionSuccess'
        )


def test_run_not_found():
    context = define_test_subprocess_context(DagsterInstance.local_temp())
    result = execute_dagster_graphql(context, RUN_CANCELLATION_QUERY, variables={'runId': 'nope'})
    assert result.data['cancelPipelineExecution']['__typename'] == 'PipelineRunNotFoundError'


def test_terminate_failed():
    with safe_tempfile_path() as path:
        context = define_test_subprocess_context(DagsterInstance.local_temp())
        old_terminate = context.execution_manager.terminate
        context.execution_manager.terminate = lambda _run_id: False
        result = execute_dagster_graphql(
            context,
            START_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'infinite_loop_pipeline'},
                    'mode': 'default',
                    'environmentConfigData': {'solids': {'loop': {'config': {'file': path}}}},
                }
            },
        )

        assert not result.errors
        assert result.data

        # just test existence
        assert (
            result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
        )
        run_id = result.data['startPipelineExecution']['run']['runId']
        # ensure the execution has happened
        while not os.path.exists(path):
            time.sleep(0.1)

        result = execute_dagster_graphql(
            context, RUN_CANCELLATION_QUERY, variables={'runId': run_id}
        )
        assert (
            result.data['cancelPipelineExecution']['__typename'] == 'CancelPipelineExecutionFailure'
        )
        assert result.data['cancelPipelineExecution']['message'].startswith(
            'Unable to terminate run'
        )

        context.execution_manager.terminate = old_terminate

        result = execute_dagster_graphql(
            context, RUN_CANCELLATION_QUERY, variables={'runId': run_id}
        )

        assert (
            result.data['cancelPipelineExecution']['__typename'] == 'CancelPipelineExecutionSuccess'
        )


def test_run_finished():

    instance = DagsterInstance.local_temp()
    context = define_test_subprocess_context(instance)
    pipeline_result = execute_pipeline(
        context.repository_definition.get_pipeline('noop_pipeline'), instance=instance
    )
    assert pipeline_result.success
    assert pipeline_result.run_id

    time.sleep(0.05)  # guarantee execution finish

    result = execute_dagster_graphql(
        context, RUN_CANCELLATION_QUERY, variables={'runId': pipeline_result.run_id}
    )

    assert result.data['cancelPipelineExecution']['__typename'] == 'CancelPipelineExecutionFailure'
    assert (
        'is not in a started state. Current status is SUCCESS'
        in result.data['cancelPipelineExecution']['message']
    )
