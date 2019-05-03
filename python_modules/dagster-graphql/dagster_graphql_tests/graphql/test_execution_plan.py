import uuid
from dagster import check
from dagster.core.object_store import has_filesystem_intermediate, get_filesystem_intermediate
from dagster.utils import merge_dicts, script_relative_path
from dagster.utils.test import get_temp_file_name


from dagster_pandas import DataFrame

from .setup import (
    define_context,
    execute_dagster_graphql,
    pandas_hello_world_solids_config,
    pandas_hello_world_solids_config_fs_storage,
)


EXECUTION_PLAN_QUERY = '''
query PipelineQuery($config: PipelineConfig, $pipeline: ExecutionSelector!) {
  executionPlan(config: $config, pipeline: $pipeline) {
    __typename
    ... on ExecutionPlan {
      pipeline { name }
      steps {
        key
        name
        solidHandle
        kind
        inputs {
          name
          type {
            name
          }
          dependsOn {
            name
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
  }
}
'''

EXECUTE_PLAN_QUERY = '''
mutation (
    $pipelineName: String!
    $config: PipelineConfig
    $stepKeys: [String!]
    $executionMetadata: ExecutionMetadata
) {
    executePlan(
        pipelineName: $pipelineName
        config: $config
        stepKeys: $stepKeys
        executionMetadata: $executionMetadata
    ) {
        __typename
        ... on ExecutePlanSuccess {
            pipeline { name }
            hasFailures
            stepEvents {
                __typename
                step {
                    key
                    metadata {
                       key
                       value
                    }
                }
                ... on ExecutionStepOutputEvent {
                    outputName
                    valueRepr
                }
                ... on StepMaterializationEvent {
                    materialization {
                        path
                        description
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


def test_success_whole_execution_plan(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config_fs_storage(),
            'stepKeys': None,
            'executionMetadata': {'runId': run_id},
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'pandas_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }
    assert 'sum_solid.transform' in step_events
    assert 'sum_sq_solid.transform' in step_events

    snapshot.assert_match(result.data)
    assert has_filesystem_intermediate(run_id, 'sum_solid.transform')
    assert has_filesystem_intermediate(run_id, 'sum_sq_solid.transform')


def test_success_whole_execution_plan_with_filesystem_config(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': merge_dicts(
                pandas_hello_world_solids_config(), {'storage': {'filesystem': {}}}
            ),
            'stepKeys': None,
            'executionMetadata': {'runId': run_id},
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'pandas_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }
    assert 'sum_solid.transform' in step_events
    assert 'sum_sq_solid.transform' in step_events

    snapshot.assert_match(result.data)
    assert has_filesystem_intermediate(run_id, 'sum_solid.transform')
    assert has_filesystem_intermediate(run_id, 'sum_sq_solid.transform')


def test_success_whole_execution_plan_with_in_memory_config(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': merge_dicts(
                pandas_hello_world_solids_config(), {'storage': {'in_memory': {}}}
            ),
            'stepKeys': None,
            'executionMetadata': {'runId': run_id},
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'pandas_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }
    assert 'sum_solid.transform' in step_events
    assert 'sum_sq_solid.transform' in step_events

    snapshot.assert_match(result.data)
    assert not has_filesystem_intermediate(run_id, 'sum_solid.transform')
    assert not has_filesystem_intermediate(run_id, 'sum_sq_solid.transform')


def test_successful_one_part_execute_plan(snapshot):
    run_id = str(uuid.uuid4())
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config_fs_storage(),
            'stepKeys': ['sum_solid.inputs.num.read', 'sum_solid.transform'],
            'executionMetadata': {'runId': run_id},
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'pandas_hello_world'
    assert query_result['hasFailures'] is False

    step_events = query_result['stepEvents']
    # 0-2 are sum_solid.num.input_thunk
    assert step_events[3]['step']['key'] == 'sum_solid.transform'
    assert step_events[4]['__typename'] == 'ExecutionStepOutputEvent'
    assert step_events[4]['outputName'] == 'result'
    expected_value_repr = '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
    assert step_events[4]['valueRepr'] == expected_value_repr
    assert step_events[5]['__typename'] == 'ExecutionStepSuccessEvent'

    snapshot.assert_match(result.data)

    assert has_filesystem_intermediate(run_id, 'sum_solid.transform')
    assert (
        str(get_filesystem_intermediate(run_id, 'sum_solid.transform', DataFrame))
        == expected_value_repr
    )


def test_successful_two_part_execute_plan(snapshot):
    run_id = str(uuid.uuid4())
    result_one = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config_fs_storage(),
            'stepKeys': ['sum_solid.inputs.num.read', 'sum_solid.transform'],
            'executionMetadata': {'runId': run_id},
        },
    )

    assert result_one.data['executePlan']['__typename'] == 'ExecutePlanSuccess'

    snapshot.assert_match(result_one.data)

    result_two = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config_fs_storage(),
            'stepKeys': ['sum_sq_solid.transform'],
            'executionMetadata': {'runId': run_id},
        },
    )

    query_result = result_two.data['executePlan']
    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'pandas_hello_world'
    assert query_result['hasFailures'] is False
    step_events = query_result['stepEvents']
    assert step_events[0]['__typename'] == 'ExecutionStepStartEvent'
    assert step_events[0]['step']['key'] == 'sum_sq_solid.transform'
    assert step_events[1]['__typename'] == 'ExecutionStepOutputEvent'
    assert step_events[1]['outputName'] == 'result'
    assert step_events[2]['__typename'] == 'ExecutionStepSuccessEvent'

    snapshot.assert_match(result_two.data)

    expected_value_repr = '''   num1  num2  sum  sum_sq
0     1     2    3       9
1     3     4    7      49'''

    assert has_filesystem_intermediate(run_id, 'sum_sq_solid.transform')
    assert (
        str(get_filesystem_intermediate(run_id, 'sum_sq_solid.transform', DataFrame))
        == expected_value_repr
    )


def test_invalid_config_execute_plan(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}},
            'stepKeys': [
                'sum_solid.num.input_thunk',
                'sum_solid.transform',
                'sum_sq_solid.transform',
            ],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['executePlan']['__typename'] == 'PipelineConfigValidationInvalid'
    snapshot.assert_match(result.data)


def test_pipeline_not_found_error_execute_plan(snapshot):

    result = execute_dagster_graphql(
        define_context(),
        EXECUTE_PLAN_QUERY,
        variables={
            'pipelineName': 'nope',
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 'ok'}}}}}},
            'stepKeys': [
                'sum_solid.num.input_thunk',
                'sum_solid.transform',
                'sum_sq_solid.transform',
            ],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert result.data['executePlan']['__typename'] == 'PipelineNotFoundError'
    assert result.data['executePlan']['pipelineName'] == 'nope'
    snapshot.assert_match(result.data)


def test_pipeline_with_execution_metadata(snapshot):
    environment_dict = {'solids': {'solid_metadata_creation': {'config': {'str_value': 'foobar'}}}}
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        variables={'pipeline': {'name': 'pipeline_with_step_metadata'}, 'config': environment_dict},
    )

    steps_data = result.data['executionPlan']['steps']
    assert len(steps_data) == 1
    step_data = steps_data[0]
    assert step_data['key'] == 'solid_metadata_creation.transform'
    assert len(step_data['metadata']) == 1
    assert step_data['metadata'][0] == {'key': 'computed', 'value': 'foobar1'}

    snapshot.assert_match(result.data)


def test_basic_execute_plan_with_materialization():
    with get_temp_file_name() as out_csv_path:

        environment_dict = {
            'solids': {
                'sum_solid': {
                    'inputs': {'num': {'csv': {'path': script_relative_path('../num.csv')}}},
                    'outputs': [{'result': {'csv': {'path': out_csv_path}}}],
                }
            }
        }

        result = execute_dagster_graphql(
            define_context(),
            EXECUTION_PLAN_QUERY,
            variables={'pipeline': {'name': 'pandas_hello_world'}, 'config': environment_dict},
        )

        steps_data = result.data['executionPlan']['steps']

        assert [step_data['key'] for step_data in steps_data] == [
            'sum_solid.inputs.num.read',
            'sum_solid.transform',
            'sum_solid.outputs.result.materialize.0',
            'sum_solid.outputs.result.materialize.join',
            'sum_sq_solid.transform',
        ]

        result = execute_dagster_graphql(
            define_context(),
            EXECUTE_PLAN_QUERY,
            variables={
                'pipelineName': 'pandas_hello_world',
                'config': environment_dict,
                'stepKeys': [
                    'sum_solid.inputs.num.read',
                    'sum_solid.transform',
                    'sum_solid.outputs.result.materialize.0',
                    'sum_solid.outputs.result.materialize.join',
                    'sum_sq_solid.transform',
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
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
        assert step_mat_event['materialization']['path'] == out_csv_path
