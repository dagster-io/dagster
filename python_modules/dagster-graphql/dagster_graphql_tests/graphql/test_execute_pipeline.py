import uuid

from graphql import parse

from dagster.core.storage.intermediate_store import FileSystemIntermediateStore
from dagster.utils import script_relative_path, merge_dicts
from dagster.utils.test import get_temp_file_name
from dagster_graphql.test.utils import execute_dagster_graphql

from .execution_queries import (
    SUBSCRIPTION_QUERY,
    START_PIPELINE_EXECUTION_QUERY,
    START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
    PIPELINE_REEXECUTION_INFO_QUERY,
)

from .utils import sync_execute_get_run_log_data

from .setup import (
    define_context,
    csv_hello_world_solids_config,
    csv_hello_world_solids_config_fs_storage,
    PoorMansDataFrame,
)


def test_basic_start_pipeline_execution():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert result.data['startPipelineExecution']['run']['pipeline']['name'] == 'csv_hello_world'


def test_basic_start_pipeline_execution_config_failure():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': {'solids': {'sum_solid': {'inputs': {'num': 384938439}}}},
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineConfigValidationInvalid'


def test_basis_start_pipeline_not_found_error():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'sjkdfkdjkf'},
                'environmentConfigData': {'solids': {'sum_solid': {'inputs': {'num': 'test.csv'}}}},
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'PipelineNotFoundError'
    assert result.data['startPipelineExecution']['pipelineName'] == 'sjkdfkdjkf'


def test_basic_start_pipeline_execution_and_subscribe():
    run_logs = sync_execute_get_run_log_data(
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': {
                    'solids': {
                        'sum_solid': {'inputs': {'num': script_relative_path('../data/num.csv')}}
                    }
                },
                'mode': 'default',
            }
        }
    )

    assert run_logs['__typename'] == 'PipelineRunLogsSubscriptionSuccess'
    log_messages = []
    for message in run_logs['messages']:
        if message['__typename'] == 'LogMessageEvent':
            log_messages.append(message)
        else:
            # all the rest of the events are non-error system-level events
            # and should be at INFO level
            assert message['level'] == 'DEBUG'

    # skip the first one was we know it is not associatied with a step
    for log_message in log_messages[1:]:
        assert log_message['step']['key']


def test_subscription_query_error():
    run_logs = sync_execute_get_run_log_data(
        variables={
            'executionParams': {
                'selector': {'name': 'naughty_programmer_pipeline'},
                'mode': 'default',
            }
        },
        raise_on_error=False,
    )

    assert run_logs['__typename'] == 'PipelineRunLogsSubscriptionSuccess'

    step_run_log_entry = _get_step_run_log_entry(
        run_logs, 'throw_a_thing.compute', 'ExecutionStepFailureEvent'
    )

    assert step_run_log_entry
    # Confirm that it is the user stack

    assert (
        step_run_log_entry['message']
        == 'DagsterEventType.STEP_FAILURE for step throw_a_thing.compute'
    )
    assert step_run_log_entry['error']
    assert step_run_log_entry['level'] == 'ERROR'
    assert isinstance(step_run_log_entry['error']['stack'], list)

    assert 'bad programmer' in step_run_log_entry['error']['stack'][-1]


def test_subscribe_bad_run_id():
    context = define_context(raise_on_error=False)
    run_id = 'nope'
    subscription = execute_dagster_graphql(
        context, parse(SUBSCRIPTION_QUERY), variables={'runId': run_id}
    )

    subscribe_results = []
    subscription.subscribe(subscribe_results.append)

    assert len(subscribe_results) == 1
    subscribe_result = subscribe_results[0]

    assert (
        subscribe_result.data['pipelineRunLogs']['__typename']
        == 'PipelineRunLogsSubscriptionMissingRunIdFailure'
    )
    assert subscribe_result.data['pipelineRunLogs']['missingRunId'] == 'nope'


def _get_step_run_log_entry(pipeline_run_logs, step_key, typename):
    for message_data in pipeline_run_logs['messages']:
        if message_data['__typename'] == typename:
            if message_data['step']['key'] == step_key:
                return message_data


def test_basic_sync_execution_no_config():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'no_config_pipeline'},
                'environmentConfigData': None,
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data
    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')


def test_basic_inmemory_sync_execution():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'mode': 'default',
                'environmentConfigData': csv_hello_world_solids_config(),
            }
        },
    )

    assert not result.errors
    assert result.data

    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'DEBUG'

    sum_solid_output = get_step_output_event(logs, 'sum_solid.compute')
    assert sum_solid_output['step']['key'] == 'sum_solid.compute'


def test_basic_filesystem_sync_execution():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': merge_dicts(
                    csv_hello_world_solids_config(), {'storage': {'filesystem': {}}}
                ),
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data

    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'DEBUG'

    sum_solid_output = get_step_output_event(logs, 'sum_solid.compute')
    assert sum_solid_output['step']['key'] == 'sum_solid.compute'
    assert sum_solid_output['outputName'] == 'result'


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


def test_successful_pipeline_reexecution(snapshot):
    run_id = str(uuid.uuid4())
    result_one = execute_dagster_graphql(
        define_context(),
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

    assert (
        result_one.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    )

    snapshot.assert_match(result_one.data)

    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), '''
        '''('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), '''
        '''('sum_sq', 49)])]'''
    )

    store = FileSystemIntermediateStore(run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_sq_solid.compute', PoorMansDataFrame))
        == expected_value_repr
    )

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {'runId': new_run_id},
                'mode': 'default',
            },
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [{'stepKey': 'sum_solid.compute', 'outputName': 'result'}],
            },
        },
    )

    query_result = result_two.data['startPipelineExecution']
    assert query_result['__typename'] == 'StartPipelineExecutionSuccess'
    logs = query_result['run']['logs']['nodes']

    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert not get_step_output_event(logs, 'sum_solid.compute')
    assert get_step_output_event(logs, 'sum_sq_solid.compute')

    snapshot.assert_match(result_two.data)

    store = FileSystemIntermediateStore(new_run_id)
    assert not store.has_intermediate(None, 'sum_solid.inputs.num.read', 'input_thunk_output')
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_sq_solid.compute', PoorMansDataFrame))
        == expected_value_repr
    )


def test_pipeline_reexecution_info_query(snapshot):
    context = define_context()

    run_id = str(uuid.uuid4())
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

    new_run_id = str(uuid.uuid4())
    execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {'runId': new_run_id},
                'mode': 'default',
            },
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [{'stepKey': 'sum_solid.compute', 'outputName': 'result'}],
            },
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
    run_id = str(uuid.uuid4())
    execute_dagster_graphql(
        define_context(),
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

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'stepKeys': ['nope'],
                'executionMetadata': {'runId': new_run_id},
                'mode': 'default',
            },
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [{'stepKey': 'sum_solid.compute', 'outputName': 'result'}],
            },
        },
    )

    query_result = result_two.data['startPipelineExecution']
    assert query_result['__typename'] == 'InvalidStepError'
    assert query_result['invalidStepKey'] == 'nope'


def test_pipeline_reexecution_invalid_step_in_step_output_handle():
    run_id = str(uuid.uuid4())
    execute_dagster_graphql(
        define_context(),
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

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {'runId': new_run_id},
                'mode': 'default',
            },
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [
                    {'stepKey': 'invalid_in_step_output_handle', 'outputName': 'result'}
                ],
            },
        },
    )

    query_result = result_two.data['startPipelineExecution']
    assert query_result['__typename'] == 'InvalidStepError'
    assert query_result['invalidStepKey'] == 'invalid_in_step_output_handle'


def test_pipeline_reexecution_invalid_output_in_step_output_handle():
    run_id = str(uuid.uuid4())
    execute_dagster_graphql(
        define_context(),
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

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {'runId': new_run_id},
                'mode': 'default',
            },
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [
                    {'stepKey': 'sum_solid.compute', 'outputName': 'invalid_output'}
                ],
            },
        },
    )

    query_result = result_two.data['startPipelineExecution']
    assert query_result['__typename'] == 'InvalidOutputError'
    assert query_result['stepKey'] == 'sum_solid.compute'
    assert query_result['invalidOutputName'] == 'invalid_output'


def test_basic_start_pipeline_execution_with_materialization():

    with get_temp_file_name() as out_csv_path:

        environment_dict = {
            'solids': {
                'sum_solid': {
                    'inputs': {'num': script_relative_path('../data/num.csv')},
                    'outputs': [{'result': out_csv_path}],
                }
            }
        }

        run_logs = sync_execute_get_run_log_data(
            variables={
                'executionParams': {
                    'selector': {'name': 'csv_hello_world'},
                    'environmentConfigData': environment_dict,
                    'mode': 'default',
                }
            }
        )

        step_mat_event = None

        for message in run_logs['messages']:
            if message['__typename'] == 'StepMaterializationEvent':
                # ensure only one event
                assert step_mat_event is None
                step_mat_event = message

        # ensure only one event
        assert step_mat_event
        assert len(step_mat_event['materialization']['metadataEntries']) == 1
        assert step_mat_event['materialization']['metadataEntries'][0]['path'] == out_csv_path
