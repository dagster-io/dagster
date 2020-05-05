import uuid

import pytest
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.test.utils import execute_dagster_graphql
from graphql import parse

from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.utils import make_new_run_id
from dagster.utils import file_relative_path, merge_dicts
from dagster.utils.test import get_temp_file_name

from .execution_queries import (
    START_PIPELINE_EXECUTION_FOR_CREATED_RUN_QUERY,
    START_PIPELINE_EXECUTION_QUERY,
    SUBSCRIPTION_QUERY,
)
from .setup import csv_hello_world, csv_hello_world_solids_config, define_test_context
from .utils import sync_execute_get_run_log_data


def test_basic_start_pipeline_execution():
    result = execute_dagster_graphql(
        define_test_context(),
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
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineRunSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert result.data['startPipelineExecution']['run']['pipeline']['name'] == 'csv_hello_world'


def test_basic_start_pipeline_execution_with_preset():
    result = execute_dagster_graphql(
        define_test_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {'selector': {'name': 'csv_hello_world'}, 'preset': 'test_inline'}
        },
    )

    assert not result.errors
    assert result.data

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineRunSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert result.data['startPipelineExecution']['run']['pipeline']['name'] == 'csv_hello_world'


def test_basic_start_pipeline_execution_with_pipeline_def_tags():
    result = execute_dagster_graphql(
        define_test_context(),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {'selector': {'name': 'hello_world_with_tags'}, 'mode': 'default',},
        },
    )

    assert not result.errors
    assert result.data['startPipelineExecution']['run']['tags'] == [
        {'key': 'tag_key', 'value': 'tag_value'}
    ]

    # just test existence
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineRunSuccess'
    assert uuid.UUID(result.data['startPipelineExecution']['run']['runId'])
    assert (
        result.data['startPipelineExecution']['run']['pipeline']['name'] == 'hello_world_with_tags'
    )


def test_basic_start_pipeline_execution_with_non_existent_preset():
    with pytest.raises(UserFacingGraphQLError) as exc_info:
        execute_dagster_graphql(
            define_test_context(),
            START_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'csv_hello_world'},
                    'preset': 'undefined_preset',
                }
            },
        )

    assert (
        exc_info.value.dauphin_error.message
        == 'Preset undefined_preset not found in pipeline csv_hello_world.'
    )


def test_basic_start_pipeline_execution_with_preset_failure():

    with pytest.raises(check.CheckError):
        execute_dagster_graphql(
            define_test_context(),
            START_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'csv_hello_world', 'solidSubset': 'sum_sq_solid'},
                    'preset': 'test_inline',
                }
            },
        )

    with pytest.raises(check.CheckError):
        execute_dagster_graphql(
            define_test_context(),
            START_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'csv_hello_world'},
                    'preset': 'test_inline',
                    'environmentConfigData': csv_hello_world_solids_config(),
                }
            },
        )

    with pytest.raises(check.CheckError):
        execute_dagster_graphql(
            define_test_context(),
            START_PIPELINE_EXECUTION_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'csv_hello_world'},
                    'preset': 'test_inline',
                    'mode': 'default',
                }
            },
        )


def test_basic_start_pipeline_execution_config_failure():
    result = execute_dagster_graphql(
        define_test_context(),
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
        define_test_context(),
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
                        'sum_solid': {
                            'inputs': {'num': file_relative_path(__file__, '../data/num.csv')}
                        }
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
        }
    )

    assert run_logs['__typename'] == 'PipelineRunLogsSubscriptionSuccess'

    step_run_log_entry = _get_step_run_log_entry(
        run_logs, 'throw_a_thing.compute', 'ExecutionStepFailureEvent'
    )

    assert step_run_log_entry
    # Confirm that it is the user stack

    assert step_run_log_entry['message'] == 'Execution of step "throw_a_thing.compute" failed.'
    assert step_run_log_entry['error']
    assert step_run_log_entry['level'] == 'ERROR'
    assert isinstance(step_run_log_entry['error']['stack'], list)

    assert 'bad programmer' in step_run_log_entry['error']['stack'][-1]


def test_subscribe_bad_run_id():
    context = define_test_context()
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
        == 'PipelineRunLogsSubscriptionFailure'
    )
    assert subscribe_result.data['pipelineRunLogs']['missingRunId'] == 'nope'


def _get_step_run_log_entry(pipeline_run_logs, step_key, typename):
    for message_data in pipeline_run_logs['messages']:
        if message_data['__typename'] == typename:
            if message_data['step']['key'] == step_key:
                return message_data


def test_basic_sync_execution_no_config():
    result = sync_execute_get_run_log_data(
        variables={
            'executionParams': {
                'selector': {'name': 'no_config_pipeline'},
                'environmentConfigData': None,
                'mode': 'default',
            }
        },
    )
    logs = result['messages']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')


def test_basic_inmemory_sync_execution():
    result = sync_execute_get_run_log_data(
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'mode': 'default',
                'environmentConfigData': csv_hello_world_solids_config(),
            }
        },
    )

    logs = result['messages']
    assert isinstance(logs, list)
    assert has_event_of_type(logs, 'PipelineStartEvent')
    assert has_event_of_type(logs, 'PipelineSuccessEvent')
    assert not has_event_of_type(logs, 'PipelineFailureEvent')

    assert first_event_of_type(logs, 'PipelineStartEvent')['level'] == 'DEBUG'

    sum_solid_output = get_step_output_event(logs, 'sum_solid.compute')
    assert sum_solid_output['step']['key'] == 'sum_solid.compute'


def test_basic_filesystem_sync_execution():
    result = sync_execute_get_run_log_data(
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

    logs = result['messages']
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


def test_basic_start_pipeline_execution_with_tags():
    instance = DagsterInstance.ephemeral()
    result = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'executionMetadata': {'tags': [{'key': 'dagster/test_key', 'value': 'test_value'}]},
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineRunSuccess'

    run = result.data['startPipelineExecution']['run']
    run_id = run['runId']
    assert len(run['tags']) > 0
    assert any([x['key'] == 'dagster/test_key' and x['value'] == 'test_value' for x in run['tags']])

    # Check run storage
    runs_with_tag = instance.get_runs(
        filters=PipelineRunsFilter(tags={'dagster/test_key': 'test_value'})
    )
    assert len(runs_with_tag) == 1
    assert runs_with_tag[0].run_id == run_id


def test_basic_start_pipeline_execution_with_materialization():

    with get_temp_file_name() as out_csv_path:

        environment_dict = {
            'solids': {
                'sum_solid': {
                    'inputs': {'num': file_relative_path(__file__, '../data/num.csv')},
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


def test_start_pipeline_execution_with_start_disabled():
    instance = DagsterInstance.local_temp(
        overrides={'dagit': {'execution_manager': {'disabled': True}}}
    )
    result = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_EXECUTION_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config(),
                'executionMetadata': {'tags': [{'key': 'dagster/test_key', 'value': 'test_value'}]},
                'mode': 'default',
            }
        },
    )

    assert result.data
    assert result.data['startPipelineExecution']['__typename'] == 'StartPipelineRunDisabledError'


def test_start_pipeline_execution_for_created_run():
    instance = DagsterInstance.local_temp()

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=csv_hello_world, environment_dict=csv_hello_world_solids_config()
    )

    result = execute_dagster_graphql(
        define_test_context(instance=instance),
        START_PIPELINE_EXECUTION_FOR_CREATED_RUN_QUERY,
        variables={'runId': pipeline_run.run_id},
    )
    assert result.data
    assert (
        result.data['startPipelineExecutionForCreatedRun']['__typename']
        == 'StartPipelineRunSuccess'
    )


def test_start_pipeline_execution_for_created_run_not_found():
    run_id = make_new_run_id()
    result = execute_dagster_graphql(
        define_test_context(),
        START_PIPELINE_EXECUTION_FOR_CREATED_RUN_QUERY,
        variables={'runId': run_id},
    )

    assert result.data
    assert (
        result.data['startPipelineExecutionForCreatedRun']['__typename']
        == 'PipelineRunNotFoundError'
    )
