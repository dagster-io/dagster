import os
import pickle
import uuid

from graphql import parse

from dagster.utils import script_relative_path, merge_dicts
from dagster.utils.test import get_temp_file_name
from dagster.core.object_store import has_filesystem_intermediate, get_filesystem_intermediate
from dagster_pandas import DataFrame

from .execution_queries import (
    SUBSCRIPTION_QUERY,
    START_PIPELINE_EXECUTION_QUERY,
    START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
)

from .utils import sync_execute_get_run_log_data

from .setup import (
    define_context,
    execute_dagster_graphql,
    pandas_hello_world_solids_config,
    pandas_hello_world_solids_config_fs_storage,
)


def test_basic_start_pipeline_execution():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert result.data['startPipelineExecution']['run']['pipeline']['name'] == 'pandas_hello_world'


def test_basic_start_pipeline_execution_config_failure():
    result = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}},
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
            'pipeline': {'name': 'sjkdfkdjkf'},
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 'test.csv'}}}}}},
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
            'pipeline': {'name': 'pandas_hello_world'},
            'config': {
                'solids': {
                    'sum_solid': {
                        'inputs': {'num': {'csv': {'path': script_relative_path('../num.csv')}}}
                    }
                }
            },
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
            assert message['level'] == 'INFO'

    # skip the first one was we know it is not associatied with a step
    for log_message in log_messages[1:]:
        assert log_message['step']['key']


def test_subscription_query_error():
    run_logs = sync_execute_get_run_log_data(
        variables={'pipeline': {'name': 'naughty_programmer_pipeline'}}, raise_on_error=False
    )

    assert run_logs['__typename'] == 'PipelineRunLogsSubscriptionSuccess'

    step_run_log_entry = _get_step_run_log_entry(
        run_logs, 'throw_a_thing.transform', 'ExecutionStepFailureEvent'
    )

    assert step_run_log_entry
    # Confirm that it is the user stack

    assert (
        step_run_log_entry['message']
        == 'DagsterEventType.STEP_FAILURE for step throw_a_thing.transform'
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
        variables={'pipeline': {'name': 'no_config_pipeline'}, 'config': None},
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
            'config': pandas_hello_world_solids_config(),
            'pipeline': {'name': 'pandas_hello_world'},
        },
    )

    assert not result.errors
    assert result.data

    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'INFO'

    sum_solid_output = get_step_output_event(logs, 'sum_solid.transform')
    assert sum_solid_output['step']['key'] == 'sum_solid.transform'


def test_basic_filesystem_sync_execution():
    context = define_context()
    result = execute_dagster_graphql(
        context,
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'config': merge_dicts(
                pandas_hello_world_solids_config(), {'storage': {'filesystem': {}}}
            ),
            'pipeline': {'name': 'pandas_hello_world'},
        },
    )

    assert not result.errors
    assert result.data

    logs = result.data['startPipelineExecution']['run']['logs']['nodes']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'INFO'

    sum_solid_output = get_step_output_event(logs, 'sum_solid.transform')
    assert sum_solid_output['step']['key'] == 'sum_solid.transform'
    assert sum_solid_output['outputName'] == 'result'
    output_path = sum_solid_output['intermediateMaterialization']['path']

    assert os.path.exists(output_path)

    with open(output_path, 'rb') as ff:
        df = pickle.load(ff)
        expected_value_repr = '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
        assert str(df) == expected_value_repr


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
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config_fs_storage(),
            'executionMetadata': {'runId': run_id},
        },
    )

    assert (
        result_one.data['startPipelineExecution']['__typename'] == 'StartPipelineExecutionSuccess'
    )

    snapshot.assert_match(result_one.data)

    expected_value_repr = '''   num1  num2  sum  sum_sq
0     1     2    3       9
1     3     4    7      49'''

    assert has_filesystem_intermediate(run_id, 'sum_solid.inputs.num.read', 'input_thunk_output')
    assert has_filesystem_intermediate(run_id, 'sum_solid.transform')
    assert has_filesystem_intermediate(run_id, 'sum_sq_solid.transform')
    assert (
        str(get_filesystem_intermediate(run_id, 'sum_sq_solid.transform', DataFrame))
        == expected_value_repr
    )

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config_fs_storage(),
            'stepKeys': ['sum_sq_solid.transform'],
            'executionMetadata': {'runId': new_run_id},
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [{'stepKey': 'sum_solid.transform', 'outputName': 'result'}],
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

    assert not get_step_output_event(logs, 'sum_solid.transform')
    assert get_step_output_event(logs, 'sum_sq_solid.transform')

    snapshot.assert_match(result_two.data)

    assert not has_filesystem_intermediate(
        new_run_id, 'sum_solid.inputs.num.read', 'input_thunk_output'
    )
    assert has_filesystem_intermediate(new_run_id, 'sum_solid.transform')
    assert has_filesystem_intermediate(new_run_id, 'sum_sq_solid.transform')
    assert (
        str(get_filesystem_intermediate(new_run_id, 'sum_sq_solid.transform', DataFrame))
        == expected_value_repr
    )


def test_pipeline_reexecution_invalid_step_in_subset():
    run_id = str(uuid.uuid4())
    execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
            'executionMetadata': {'runId': run_id},
        },
    )

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
            'stepKeys': ['nope'],
            'executionMetadata': {'runId': new_run_id},
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [{'stepKey': 'sum_solid.transform', 'outputName': 'result'}],
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
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
            'executionMetadata': {'runId': run_id},
        },
    )

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
            'stepKeys': ['sum_sq_solid.transform'],
            'executionMetadata': {'runId': new_run_id},
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
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
            'executionMetadata': {'runId': run_id},
        },
    )

    new_run_id = str(uuid.uuid4())

    result_two = execute_dagster_graphql(
        define_context(),
        START_PIPELINE_EXECUTION_SNAPSHOT_QUERY,
        variables={
            'pipeline': {'name': 'pandas_hello_world'},
            'config': pandas_hello_world_solids_config(),
            'stepKeys': ['sum_sq_solid.transform'],
            'executionMetadata': {'runId': new_run_id},
            'reexecutionConfig': {
                'previousRunId': run_id,
                'stepOutputHandles': [
                    {'stepKey': 'sum_solid.transform', 'outputName': 'invalid_output'}
                ],
            },
        },
    )

    query_result = result_two.data['startPipelineExecution']
    assert query_result['__typename'] == 'InvalidOutputError'
    assert query_result['stepKey'] == 'sum_solid.transform'
    assert query_result['invalidOutputName'] == 'invalid_output'


def test_basic_start_pipeline_execution_with_materialization():

    with get_temp_file_name() as out_csv_path:

        environment_dict = {
            'solids': {
                'sum_solid': {
                    'inputs': {'num': {'csv': {'path': script_relative_path('../num.csv')}}},
                    'outputs': [{'result': {'csv': {'path': out_csv_path}}}],
                }
            }
        }

        run_logs = sync_execute_get_run_log_data(
            variables={'pipeline': {'name': 'pandas_hello_world'}, 'config': environment_dict}
        )

        step_mat_event = None

        for message in run_logs['messages']:
            if message['__typename'] == 'StepMaterializationEvent':
                # ensure only one event
                assert step_mat_event is None
                step_mat_event = message

        # ensure only one event
        assert step_mat_event
        assert step_mat_event['materialization']['path'] == out_csv_path
