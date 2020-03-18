import re

from dagster_graphql.test.utils import execute_dagster_graphql

from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_store import build_fs_intermediate_store
from dagster.core.utils import make_new_run_id
from dagster.utils import file_relative_path, merge_dicts
from dagster.utils.test import get_temp_file_name

from .setup import (
    PoorMansDataFrame,
    csv_hello_world_solids_config,
    csv_hello_world_solids_config_fs_storage,
    define_test_context,
)

EXECUTION_PLAN_QUERY = '''
query PipelineQuery($environmentConfigData: EnvironmentConfigData, $pipeline: ExecutionSelector!, $mode: String!) {
  executionPlan(environmentConfigData: $environmentConfigData, pipeline: $pipeline, mode: $mode) {
    __typename
    ... on ExecutionPlan {
      pipeline { name }
      steps {
        key
        solidHandleID
        kind
        inputs {
          name
          type {
            name
          }
          dependsOn {
            key
          }
        }
        outputs {
          name
          type {
            name
          }
        }
        metadata {
          key
          value
        }
      }
    }
    ... on PipelineNotFoundError {
        pipelineName
    }
    ... on PipelineConfigValidationInvalid {
        pipeline { name }
        errors { message }
    }
  }
}
'''

EXECUTE_PLAN_QUERY = '''
mutation ($executionParams: ExecutionParams!) {
    executePlan(executionParams: $executionParams) {
        __typename
        ... on ExecutePlanSuccess {
            pipeline { name }
            hasFailures
            stepEvents {
                __typename
                ... on MessageEvent {
                    message
                }
                step {
                    key
                    metadata {
                       key
                       value
                    }
                }
                ... on ExecutionStepOutputEvent {
                    outputName
                }
                ... on StepMaterializationEvent {
                    materialization {
                        label
                        description
                        metadataEntries {
                            ... on EventPathMetadataEntry {
                                label
                                description
                                path
                            }
                        }
                    }
                }
                ... on ExecutionStepFailureEvent {
                    error {
                        message
                    }
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''


def get_nameset(llist):
    return {item['name'] for item in llist}


def get_named_thing(llist, name):
    for cn in llist:
        if cn['name'] == name:
            return cn

    check.failed('not found')


# for snapshot testing remove any varying values
def clean_log_messages(result_data):
    for idx in range(len(result_data['executePlan']['stepEvents'])):
        message = result_data['executePlan']['stepEvents'][idx].get('message')
        if message is not None:
            result_data['executePlan']['stepEvents'][idx]['message'] = re.sub(
                r'(\d+(\.\d+)?)', '{N}', message
            )
    return result_data


def test_success_whole_execution_plan(snapshot):
    run_id = make_new_run_id()
    instance = DagsterInstance.local_temp()
    instance.create_empty_run(run_id, 'csv_hello_world')
    result = execute_dagster_graphql(
        define_test_context(instance=instance),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': None,
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event
        for step_event in query_result['stepEvents']
        if step_event['step']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(clean_log_messages(result.data))
    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')


def test_success_whole_execution_plan_with_filesystem_config(snapshot):
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    instance.create_empty_run(run_id, 'csv_hello_world')
    result = execute_dagster_graphql(
        define_test_context(instance=instance),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': merge_dicts(
                    csv_hello_world_solids_config(), {'storage': {'filesystem': {}}}
                ),
                'stepKeys': None,
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event
        for step_event in query_result['stepEvents']
        if step_event['step']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(clean_log_messages(result.data))
    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert store.has_intermediate(None, 'sum_sq_solid.compute')


def test_success_whole_execution_plan_with_in_memory_config(snapshot):
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    instance.create_empty_run(run_id, 'csv_hello_world')
    result = execute_dagster_graphql(
        define_test_context(instance=instance),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': merge_dicts(
                    csv_hello_world_solids_config(), {'storage': {'in_memory': {}}}
                ),
                'stepKeys': None,
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event
        for step_event in query_result['stepEvents']
        if step_event['step']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(clean_log_messages(result.data))
    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
    assert not store.has_intermediate(None, 'sum_solid.compute')
    assert not store.has_intermediate(None, 'sum_sq_solid.compute')


def test_successful_one_part_execute_plan(snapshot):
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    instance.create_empty_run(run_id, 'csv_hello_world')

    result = execute_dagster_graphql(
        define_test_context(instance=instance),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_solid.compute'],
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False

    step_events = query_result['stepEvents']

    assert [se['__typename'] for se in step_events] == [
        'ExecutionStepStartEvent',
        'ExecutionStepInputEvent',
        'ExecutionStepOutputEvent',
        'ObjectStoreOperationEvent',
        'ExecutionStepSuccessEvent',
    ]

    assert step_events[1]['step']['key'] == 'sum_solid.compute'
    assert step_events[2]['outputName'] == 'result'

    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), '''
        '''OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]'''
    )

    assert step_events[3]['step']['key'] == 'sum_solid.compute'
    assert step_events[4]['step']['key'] == 'sum_solid.compute'

    snapshot.assert_match(clean_log_messages(result.data))

    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
    assert store.has_intermediate(None, 'sum_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_solid.compute', PoorMansDataFrame).obj)
        == expected_value_repr
    )


def test_successful_two_part_execute_plan(snapshot):
    run_id = make_new_run_id()
    instance = DagsterInstance.local_temp()
    instance.create_empty_run(run_id, 'csv_hello_world')
    result_one = execute_dagster_graphql(
        define_test_context(instance=instance),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_solid.compute'],
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    assert result_one.data['executePlan']['__typename'] == 'ExecutePlanSuccess'

    snapshot.assert_match(clean_log_messages(result_one.data))

    result_two = execute_dagster_graphql(
        define_test_context(instance=instance),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {'runId': run_id},
                'mode': 'default',
            }
        },
    )

    query_result = result_two.data['executePlan']
    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = query_result['stepEvents']
    assert [se['__typename'] for se in step_events] == [
        'ExecutionStepStartEvent',
        'ObjectStoreOperationEvent',
        'ExecutionStepInputEvent',
        'ExecutionStepOutputEvent',
        'ObjectStoreOperationEvent',
        'ExecutionStepSuccessEvent',
    ]
    assert step_events[0]['step']['key'] == 'sum_sq_solid.compute'
    assert step_events[1]['step']['key'] == 'sum_sq_solid.compute'
    assert step_events[2]['step']['key'] == 'sum_sq_solid.compute'
    assert step_events[3]['outputName'] == 'result'
    assert step_events[4]['step']['key'] == 'sum_sq_solid.compute'

    snapshot.assert_match(clean_log_messages(result_two.data))

    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), '''
        '''('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), '''
        '''('sum_sq', 49)])]'''
    )

    store = build_fs_intermediate_store(instance.intermediates_directory, run_id)
    assert store.has_intermediate(None, 'sum_sq_solid.compute')
    assert (
        str(store.get_intermediate(None, 'sum_sq_solid.compute', PoorMansDataFrame).obj)
        == expected_value_repr
    )


def test_invalid_config_fetch_execute_plan(snapshot):
    result = execute_dagster_graphql(
        define_test_context(),
        EXECUTION_PLAN_QUERY,
        variables={
            'pipeline': {'name': 'csv_hello_world'},
            'environmentConfigData': {
                'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}
            },
            'mode': 'default',
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['executionPlan']['__typename'] == 'PipelineConfigValidationInvalid'
    assert len(result.data['executionPlan']['errors']) == 1
    assert (
        'Invalid scalar at path root:solids:sum_solid:inputs:num'
        in result.data['executionPlan']['errors'][0]['message']
    )
    result.data['executionPlan']['errors'][0][
        'message'
    ] = 'Invalid scalar at path root:solids:sum_solid:inputs:num'
    snapshot.assert_match(result.data)


def test_invalid_config_execute_plan(snapshot):
    result = execute_dagster_graphql(
        define_test_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'csv_hello_world'},
                'environmentConfigData': {
                    'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}
                },
                'stepKeys': [
                    'sum_solid.num.input_thunk',
                    'sum_solid.compute',
                    'sum_sq_solid.compute',
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
                'mode': 'default',
            }
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['executePlan']['__typename'] == 'PipelineConfigValidationInvalid'
    assert len(result.data['executePlan']['errors']) == 1
    assert (
        'Invalid scalar at path root:solids:sum_solid:inputs:num'
        in result.data['executePlan']['errors'][0]['message']
    )
    result.data['executePlan']['errors'][0][
        'message'
    ] = 'Invalid scalar at path root:solids:sum_solid:inputs:num'
    snapshot.assert_match(result.data)


def test_pipeline_not_found_error_execute_plan(snapshot):

    result = execute_dagster_graphql(
        define_test_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': {'name': 'nope'},
                'environmentConfigData': {
                    'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 'ok'}}}}}
                },
                'stepKeys': [
                    'sum_solid.num.input_thunk',
                    'sum_solid.compute',
                    'sum_sq_solid.compute',
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
                'mode': 'default',
            }
        },
    )

    assert result.data['executePlan']['__typename'] == 'PipelineNotFoundError'
    assert result.data['executePlan']['pipelineName'] == 'nope'
    snapshot.assert_match(result.data)


def test_basic_execute_plan_with_materialization():
    with get_temp_file_name() as out_csv_path:

        environment_dict = {
            'solids': {
                'sum_solid': {
                    'inputs': {'num': file_relative_path(__file__, '../data/num.csv')},
                    'outputs': [{'result': out_csv_path}],
                }
            }
        }

        instance = DagsterInstance.ephemeral()

        result = execute_dagster_graphql(
            define_test_context(instance=instance),
            EXECUTION_PLAN_QUERY,
            variables={
                'pipeline': {'name': 'csv_hello_world'},
                'environmentConfigData': environment_dict,
                'mode': 'default',
            },
        )

        steps_data = result.data['executionPlan']['steps']

        assert [step_data['key'] for step_data in steps_data] == [
            'sum_solid.compute',
            'sum_sq_solid.compute',
        ]

        run_id = make_new_run_id()
        instance.create_empty_run(run_id, 'csv_hello_world')

        result = execute_dagster_graphql(
            define_test_context(instance=instance),
            EXECUTE_PLAN_QUERY,
            variables={
                'executionParams': {
                    'selector': {'name': 'csv_hello_world'},
                    'environmentConfigData': environment_dict,
                    'stepKeys': ['sum_solid.compute', 'sum_sq_solid.compute'],
                    'executionMetadata': {'runId': run_id},
                    'mode': 'default',
                }
            },
        )

        assert result.data

        step_mat_event = None

        for message in result.data['executePlan']['stepEvents']:
            if message['__typename'] == 'StepMaterializationEvent':
                # ensure only one event
                assert step_mat_event is None
                step_mat_event = message

        # ensure only one event
        assert step_mat_event
        assert step_mat_event['materialization']
        assert len(step_mat_event['materialization']['metadataEntries']) == 1
        metadata_entry = step_mat_event['materialization']['metadataEntries'][0]
        assert metadata_entry['path'] == out_csv_path
