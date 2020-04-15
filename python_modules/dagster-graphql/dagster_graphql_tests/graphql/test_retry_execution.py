from time import sleep

from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import DagsterEventType
from dagster.core.instance import DagsterInstance
from dagster.core.utils import make_new_run_id

from .execution_queries import START_PIPELINE_EXECUTION_QUERY, START_PIPELINE_REEXECUTION_QUERY
from .setup import (
    define_test_context,
    define_test_subprocess_context,
    get_retry_multi_execution_params,
    retry_config,
)

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


def step_did_fail_in_records(records, step_key):
    return any(
        record.step_key == step_key
        and record.dagster_event.event_type_value == DagsterEventType.STEP_FAILURE.value
        for record in records
    )


def step_did_succeed_in_records(records, step_key):
    return any(
        record.step_key == step_key
        and record.dagster_event.event_type_value == DagsterEventType.STEP_SUCCESS.value
        for record in records
    )


def step_did_not_run_in_records(records, step_key):
    return not any(
        record.step_key == step_key
        and record.dagster_event.event_type_value
        in (
            DagsterEventType.STEP_SUCCESS.value,
            DagsterEventType.STEP_FAILURE.value,
            DagsterEventType.STEP_SKIPPED.value,
        )
        for record in records
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
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'retryRunId': run_id,
                'executionMetadata': {'rootRunId': run_id, 'parentRunId': run_id,},
            }
        },
    )

    assert not retry_one.errors
    assert retry_one.data
    assert retry_one.data['startPipelineReexecution']['__typename'] == 'PythonError'
    assert (
        NON_PERSISTENT_INTERMEDIATES_ERROR in retry_one.data['startPipelineReexecution']['message']
    )


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
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'environmentConfigData': retry_config(1),
                'retryRunId': run_id,
                'executionMetadata': {'rootRunId': run_id, 'parentRunId': run_id,},
            }
        },
    )

    run_id = retry_one.data['startPipelineReexecution']['run']['runId']
    logs = retry_one.data['startPipelineReexecution']['run']['logs']['nodes']
    assert step_did_not_run(logs, 'spawn.compute')
    assert step_did_succeed(logs, 'fail.compute')
    assert step_did_fail(logs, 'fail_2.compute')
    assert step_did_skip(logs, 'fail_3.compute')
    assert step_did_skip(logs, 'reset.compute')

    retry_two = execute_dagster_graphql(
        context,
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'environmentConfigData': retry_config(2),
                'retryRunId': run_id,
                'executionMetadata': {'rootRunId': run_id, 'parentRunId': run_id,},
            }
        },
    )

    run_id = retry_two.data['startPipelineReexecution']['run']['runId']
    logs = retry_two.data['startPipelineReexecution']['run']['logs']['nodes']

    assert step_did_not_run(logs, 'spawn.compute')
    assert step_did_not_run(logs, 'fail.compute')
    assert step_did_succeed(logs, 'fail_2.compute')
    assert step_did_fail(logs, 'fail_3.compute')
    assert step_did_skip(logs, 'reset.compute')

    retry_three = execute_dagster_graphql(
        context,
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'eventually_successful'},
                'environmentConfigData': retry_config(3),
                'retryRunId': run_id,
                'executionMetadata': {'rootRunId': run_id, 'parentRunId': run_id,},
            }
        },
    )

    run_id = retry_three.data['startPipelineReexecution']['run']['runId']
    logs = retry_three.data['startPipelineReexecution']['run']['logs']['nodes']

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
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'retry_resource_pipeline'},
                'environmentConfigData': {'storage': {'filesystem': {}}},
                'retryRunId': run_id,
                'executionMetadata': {'rootRunId': run_id, 'parentRunId': run_id,},
            }
        },
    )
    run_id = retry_one.data['startPipelineReexecution']['run']['runId']
    logs = retry_one.data['startPipelineReexecution']['run']['logs']['nodes']
    assert step_did_not_run(logs, 'start.compute')
    assert step_did_fail(logs, 'will_fail.compute')


def test_retry_multi_output():
    context = define_test_context(instance=DagsterInstance.local_temp())
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={'executionParams': get_retry_multi_execution_params(should_fail=True)},
    )

    print(result.data)
    run_id = result.data['startPipelineExecution']['run']['runId']
    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert step_did_succeed(logs, 'multi.compute')
    assert step_did_skip(logs, 'child_multi_skip.compute')
    assert step_did_fail(logs, 'can_fail.compute')
    assert step_did_skip(logs, 'child_fail.compute')
    assert step_did_skip(logs, 'child_skip.compute')
    assert step_did_skip(logs, 'grandchild_fail.compute')

    retry_one = execute_dagster_graphql(
        context,
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': get_retry_multi_execution_params(should_fail=True, retry_id=run_id)
        },
    )

    run_id = retry_one.data['startPipelineReexecution']['run']['runId']
    logs = retry_one.data['startPipelineReexecution']['run']['logs']['nodes']
    assert step_did_not_run(logs, 'multi.compute')
    assert step_did_not_run(logs, 'child_multi_skip.compute')
    assert step_did_fail(logs, 'can_fail.compute')
    assert step_did_skip(logs, 'child_fail.compute')
    assert step_did_skip(logs, 'child_skip.compute')
    assert step_did_skip(logs, 'grandchild_fail.compute')

    retry_two = execute_dagster_graphql(
        context,
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': get_retry_multi_execution_params(should_fail=False, retry_id=run_id)
        },
    )

    run_id = retry_two.data['startPipelineReexecution']['run']['runId']
    logs = retry_two.data['startPipelineReexecution']['run']['logs']['nodes']
    assert step_did_not_run(logs, 'multi.compute')
    assert step_did_not_run(logs, 'child_multi_skip.compute')
    assert step_did_succeed(logs, 'can_fail.compute')
    assert step_did_succeed(logs, 'child_fail.compute')
    assert step_did_skip(logs, 'child_skip.compute')
    assert step_did_succeed(logs, 'grandchild_fail.compute')


def test_retry_early_terminate():
    instance = DagsterInstance.local_temp()
    context = define_test_subprocess_context(instance=instance)
    run_id = make_new_run_id()
    execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'retry_multi_input_early_terminate_pipeline'},
                'environmentConfigData': {
                    'solids': {
                        'get_input_one': {'config': {'wait_to_terminate': True}},
                        'get_input_two': {'config': {'wait_to_terminate': True}},
                    },
                    'storage': {'filesystem': {}},
                },
                'executionMetadata': {'runId': run_id},
            }
        },
    )
    # Wait until the first step succeeded
    while instance.get_run_stats(run_id).steps_succeeded < 1:
        sleep(0.1)
    # Terminate the current pipeline run at the second step
    context.execution_manager.terminate(run_id)

    records = instance.all_logs(run_id)

    # The first step should succeed, the second should fail or not start,
    # and the following steps should not appear in records
    assert step_did_succeed_in_records(records, 'return_one.compute')
    assert any(
        [
            step_did_fail_in_records(records, 'get_input_one.compute'),
            step_did_not_run_in_records(records, 'get_input_one.compute'),
        ]
    )
    assert step_did_not_run_in_records(records, 'get_input_two.compute')
    assert step_did_not_run_in_records(records, 'sum_inputs.compute')

    # Start retry
    new_run_id = make_new_run_id()

    execute_dagster_graphql(
        context,
        START_PIPELINE_REEXECUTION_QUERY,
        variables={
            'executionParams': {
                'mode': 'default',
                'selector': {'name': 'retry_multi_input_early_terminate_pipeline'},
                'environmentConfigData': {
                    'solids': {
                        'get_input_one': {'config': {'wait_to_terminate': False}},
                        'get_input_two': {'config': {'wait_to_terminate': False}},
                    },
                    'storage': {'filesystem': {}},
                },
                'retryRunId': run_id,
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                },
            }
        },
    )
    # Wait until the run is finished
    while context.execution_manager.is_process_running(new_run_id):
        pass

    retry_records = instance.all_logs(new_run_id)
    # The first step should not run and the other three steps should succeed in retry
    assert step_did_not_run_in_records(retry_records, 'return_one.compute')
    assert step_did_succeed_in_records(retry_records, 'get_input_one.compute')
    assert step_did_succeed_in_records(retry_records, 'get_input_two.compute')
    assert step_did_succeed_in_records(retry_records, 'sum_inputs.compute')
