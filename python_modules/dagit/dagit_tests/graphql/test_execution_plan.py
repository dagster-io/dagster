import uuid
from dagster import check
from dagster.core.object_store import has_filesystem_intermediate, get_filesystem_intermediate
from dagster.utils import merge_dicts

from dagster_pandas import DataFrame

from .setup import execute_dagster_graphql, define_context, pandas_hello_world_solids_config


EXECUTION_PLAN_QUERY = '''
query PipelineQuery($config: PipelineConfig, $pipeline: ExecutionSelector!) {
  executionPlan(config: $config, pipeline: $pipeline) {
    __typename
    ... on ExecutionPlan {
      pipeline { name }
      steps {
        name
        solid {
          name
        }
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
      }
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
            'config': pandas_hello_world_solids_config(),
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
            'config': pandas_hello_world_solids_config(),
            'stepKeys': ['sum_solid.num.input_thunk', 'sum_solid.transform'],
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
    assert step_events['sum_solid.transform']['__typename'] == 'SuccessfulStepOutputEvent'
    assert step_events['sum_solid.transform']['success'] is True
    assert step_events['sum_solid.transform']['outputName'] == 'result'
    expected_value_repr = '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
    assert step_events['sum_solid.transform']['valueRepr'] == expected_value_repr

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
            'config': pandas_hello_world_solids_config(),
            'stepKeys': ['sum_solid.num.input_thunk', 'sum_solid.transform'],
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
            'config': pandas_hello_world_solids_config(),
            'stepKeys': ['sum_sq_solid.transform'],
            'executionMetadata': {'runId': run_id},
        },
    )

    query_result = result_two.data['executePlan']
    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'pandas_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }
    assert 'sum_sq_solid.transform' in step_events
    assert step_events['sum_sq_solid.transform']['__typename'] == 'SuccessfulStepOutputEvent'
    assert step_events['sum_sq_solid.transform']['success'] is True
    assert step_events['sum_sq_solid.transform']['outputName'] == 'result'

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


EXECUTE_PLAN_QUERY = '''
mutation (
    $pipelineName: String!
    $config: PipelineConfig
    $stepKeys: [String!]
    $executionMetadata: ExecutionMetadata!
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
                success
                step { key }
                ... on SuccessfulStepOutputEvent {
                    outputName
                    valueRepr
                }
                ... on StepFailureEvent {
                    errorMessage
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
