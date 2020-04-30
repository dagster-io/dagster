from time import sleep

from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import DagsterEventType
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_store import build_fs_intermediate_store
from dagster.core.storage.tags import RESUME_RETRY_TAG
from dagster.core.utils import make_new_run_id

from .execution_queries import (
    PIPELINE_REEXECUTION_INFO_QUERY,
    START_PIPELINE_EXECUTION_QUERY,
    START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
    START_PIPELINE_REEXECUTION_QUERY,
    START_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
)
from .setup import (
    PoorMansDataFrame,
    csv_hello_world_solids_config,
    csv_hello_world_solids_config_fs_storage,
    define_test_context,
    define_test_subprocess_context,
    get_retry_multi_execution_params,
    retry_config,
)
from .utils import sync_get_all_logs_for_run

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


def first_event_of_type(logs, message_type):
    for log in logs:
        if log['__typename'] == message_type:
            return log
    return None


def has_event_of_type(logs, message_type):
    return first_event_of_type(logs, message_type) is not None


def get_step_output_event(logs, step_key, output_name='result'):
    for log in logs:
        if (
            log['__typename'] == 'ExecutionStepOutputEvent'
            and log['step']['key'] == step_key
            and log['outputName'] == output_name
        ):
            return log

    return None


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
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
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
                'executionMetadata': {
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
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
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
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
                'executionMetadata': {
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
            }
        },
    )

    run_id = retry_one.data['startPipelineReexecution']['run']['runId']
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
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
                'executionMetadata': {
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
            }
        },
    )

    run_id = retry_two.data['startPipelineReexecution']['run']['runId']
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']

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
                'executionMetadata': {
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
            }
        },
    )

    run_id = retry_three.data['startPipelineReexecution']['run']['runId']
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']

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
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
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
                'executionMetadata': {
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
            }
        },
    )
    run_id = retry_one.data['startPipelineReexecution']['run']['runId']
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
    assert step_did_not_run(logs, 'start.compute')
    assert step_did_fail(logs, 'will_fail.compute')


def test_retry_multi_output():
    context = define_test_context(instance=DagsterInstance.local_temp())
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={'executionParams': get_retry_multi_execution_params(should_fail=True)},
    )

    run_id = result.data['startPipelineExecution']['run']['runId']
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
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
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
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
    logs = sync_get_all_logs_for_run(context, run_id)['pipelineRunLogs']['messages']
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
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
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


def test_successful_pipeline_reexecution():
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    context = define_test_context(instance=instance)
    result_one = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    assert result_one.data['startPipelineExecution']['__typename'] == 'StartPipelineRunSuccess'

    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), '''
        '''('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), '''
        '''('sum_sq', 49)])]'''
    )

    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_sq_solid.compute', PoorMansDataFrame).obj)
        == expected_value_repr
    )

    # retry
    new_run_id = make_new_run_id()

    result_two = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
                'mode': 'default',
            }
        },
    )

    query_result = result_two.data['startPipelineReexecution']
    assert query_result['__typename'] == 'StartPipelineRunSuccess'

    result = sync_get_all_logs_for_run(context, new_run_id)
    logs = result['pipelineRunLogs']['messages']

    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert not get_step_output_event(logs, 'sum_solid.compute')
    assert get_step_output_event(logs, 'sum_sq_solid.compute')

    store = build_fs_intermediate_store(instance.intermediates_directory, new_run_id)
    assert not store.has_intermediate(None, 'sum_solid.inputs.num.read', 'input_thunk_output')
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_sq_solid.compute', PoorMansDataFrame).obj)
        == expected_value_repr
    )


def test_pipeline_reexecution_info_query(snapshot):
    context = define_test_context()

    run_id = make_new_run_id()
    execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    # retry
    new_run_id = make_new_run_id()
    execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
                'mode': 'default',
            }
        },
    )

    result_one = execute_dagster_graphql(
        context, PIPELINE_REEXECUTION_INFO_QUERY, variables={'runId': run_id}
    )
    query_result_one = result_one.data['pipelineRunOrError']
    assert query_result_one['__typename'] == 'PipelineRun'
    assert query_result_one['stepKeysToExecute'] is None

    result_two = execute_dagster_graphql(
        context, PIPELINE_REEXECUTION_INFO_QUERY, variables={'runId': new_run_id}
    )
    query_result_two = result_two.data['pipelineRunOrError']
    assert query_result_two['__typename'] == 'PipelineRun'
    stepKeysToExecute = query_result_two['stepKeysToExecute']
    assert stepKeysToExecute is not None
    snapshot.assert_match(stepKeysToExecute)


def test_pipeline_reexecution_invalid_step_in_subset():
    run_id = make_new_run_id()
    execute_dagster_graphql(
        define_test_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    # retry
    new_run_id = make_new_run_id()

    result_two = execute_dagster_graphql(
        define_test_context(),
        START_PIPELINE_REEXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'stepKeys': ['nope'],
                'executionMetadata': {
                    'runId': new_run_id,
                    'rootRunId': run_id,
                    'parentRunId': run_id,
                    'tags': [{'key': RESUME_RETRY_TAG, 'value': 'true'}],
                },
                'mode': 'default',
            }
        },
    )

    query_result = result_two.data['startPipelineReexecution']
    assert query_result['__typename'] == 'InvalidStepError'
    assert query_result['invalidStepKey'] == 'nope'
