from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.instance import DagsterInstance

from .execution_queries import START_PIPELINE_EXECUTION_QUERY
from .setup import define_test_context, retry_config

NON_PERSISTENT_INTERMEDIATES_ERROR = (
    'Cannot perform reexecution with non persistent intermediates manager'
)


def step_did_not_run(logs, step_key):
    return not any(
        log['step']['key'] == step_key
        for log in logs
        if log['__typename']
        in ('ExecutionStepSuccessEvent', 'ExecutionStepSkippedEvent', 'ExecutionStepFailureEvent')
    )


def step_did_succeed(logs, step_key):
    return any(
        log['__typename'] == 'ExecutionStepSuccessEvent' and step_key == log['step']['key']
        for log in logs
    )


def step_did_skip(logs, step_key):
    return any(
        log['__typename'] == 'ExecutionStepSkippedEvent' and step_key == log['step']['key']
        for log in logs
    )


def step_did_fail(logs, step_key):
    return any(
        log['__typename'] == 'ExecutionStepFailureEvent' and step_key == log['step']['key']
        for log in logs
    )


def test_retry_requires_intermediates():
    context = define_test_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {'mode': 'default', 'selector': {'name': 'eventually_successful'}}
        },
    )

    assert not result.errors
    assert result.data

    run_id = result.data['startPipelineExecution']['run']['runId']
    assert run_id
    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)

    assert step_did_succeed(logs, 'spawn.compute')
    assert step_did_fail(logs, 'fail.compute')
    assert step_did_skip(logs, 'fail_2.compute')
    assert step_did_skip(logs, 'fail_3.compute')
    assert step_did_skip(logs, 'reset.compute')

    retry_one = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'retryRunId': run_id,
            }
        },
    )

    assert not retry_one.errors
    assert retry_one.data
    assert retry_one.data['startPipelineExecution']['__typename'] == 'PythonError'
    assert NON_PERSISTENT_INTERMEDIATES_ERROR in retry_one.data['startPipelineExecution']['message']


def test_retry_pipeline_execution():
    context = define_test_context(instance=DagsterInstance.local_temp())
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'environmentConfigData': retry_config(0),
            }
        },
    )

    run_id = result.data['startPipelineExecution']['run']['runId']
    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert step_did_succeed(logs, 'spawn.compute')
    assert step_did_fail(logs, 'fail.compute')
    assert step_did_skip(logs, 'fail_2.compute')
    assert step_did_skip(logs, 'fail_3.compute')
    assert step_did_skip(logs, 'reset.compute')

    retry_one = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'environmentConfigData': retry_config(1),
                'retryRunId': run_id,
            }
        },
    )

    run_id = retry_one.data['startPipelineExecution']['run']['runId']
    logs = retry_one.data['startPipelineExecution']['run']['logs']['nodes']
    assert step_did_not_run(logs, 'spawn.compute')
    assert step_did_succeed(logs, 'fail.compute')
    assert step_did_fail(logs, 'fail_2.compute')
    assert step_did_skip(logs, 'fail_3.compute')
    assert step_did_skip(logs, 'reset.compute')

    retry_two = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'environmentConfigData': retry_config(2),
                'retryRunId': run_id,
            }
        },
    )

    run_id = retry_two.data['startPipelineExecution']['run']['runId']
    logs = retry_two.data['startPipelineExecution']['run']['logs']['nodes']

    assert step_did_not_run(logs, 'spawn.compute')
    assert step_did_not_run(logs, 'fail.compute')
    assert step_did_succeed(logs, 'fail_2.compute')
    assert step_did_fail(logs, 'fail_3.compute')
    assert step_did_skip(logs, 'reset.compute')

    retry_three = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'environmentConfigData': retry_config(3),
                'retryRunId': run_id,
            }
        },
    )

    run_id = retry_three.data['startPipelineExecution']['run']['runId']
    logs = retry_three.data['startPipelineExecution']['run']['logs']['nodes']

    assert step_did_not_run(logs, 'spawn.compute')
    assert step_did_not_run(logs, 'fail.compute')
    assert step_did_not_run(logs, 'fail_2.compute')
    assert step_did_succeed(logs, 'fail_3.compute')
    assert step_did_succeed(logs, 'reset.compute')


def test_retry_resource_pipeline():
    context = define_test_context(instance=DagsterInstance.local_temp())
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'retry_resource_pipeline'},
                'environmentConfigData': {'storage': {'filesystem': {}}},
            }
        },
    )

    run_id = result.data['startPipelineExecution']['run']['runId']
    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert step_did_succeed(logs, 'start.compute')
    assert step_did_fail(logs, 'will_fail.compute')

    retry_one = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'retry_resource_pipeline'},
                'environmentConfigData': {'storage': {'filesystem': {}}},
                'retryRunId': run_id,
            }
        },
    )
    run_id = retry_one.data['startPipelineExecution']['run']['runId']
    logs = retry_one.data['startPipelineExecution']['run']['logs']['nodes']
    assert step_did_not_run(logs, 'start.compute')
    assert step_did_fail(logs, 'will_fail.compute')
