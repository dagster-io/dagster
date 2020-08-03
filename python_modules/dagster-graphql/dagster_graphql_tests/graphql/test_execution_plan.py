import re

from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from dagster import check
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.storage.intermediate_storage import build_fs_intermediate_storage
from dagster.utils import file_relative_path, merge_dicts
from dagster.utils.test import get_temp_file_name

from .graphql_context_test_suite import ReadonlyGraphQLContextTestMatrix
from .setup import (
    PoorMansDataFrame,
    csv_hello_world,
    csv_hello_world_solids_config,
    csv_hello_world_solids_config_fs_storage,
)

EXECUTION_PLAN_QUERY = '''
query PipelineQuery($runConfigData: RunConfigData, $pipeline: PipelineSelector!, $mode: String!) {
  executionPlanOrError(runConfigData: $runConfigData, pipeline: $pipeline, mode: $mode) {
    __typename
    ... on ExecutionPlan {
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
        pipelineName
        errors { message }
    }
    ... on PythonError {
        message
        stack
        cause {
            message
            stack
        }
    }
  }
}
'''

EXECUTE_PLAN_QUERY = '''
mutation ($executionParams: ExecutionParams!, $retries: Retries) {
    executePlan(executionParams: $executionParams, retries: $retries) {
        __typename
        ... on ExecutePlanSuccess {
            pipeline { name }
            hasFailures
            stepEvents {
                __typename
                ... on MessageEvent {
                    message
                }
                stepKey
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
            pipelineName
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PythonError {
            message
            stack
            cause {
                message
                stack
            }
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


def test_success_whole_execution_plan(graphql_context, snapshot):
    run_config = csv_hello_world_solids_config_fs_storage()
    pipeline_run = graphql_context.instance.create_run_for_pipeline(
        pipeline_def=csv_hello_world, run_config=run_config
    )
    selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': run_config,
                'stepKeys': None,
                'executionMetadata': {'runId': pipeline_run.run_id},
                'mode': 'default',
            },
        },
    )

    query_result = result.data['executePlan']
    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['stepKey']: step_event
        for step_event in query_result['stepEvents']
        if step_event['stepKey']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(clean_log_messages(result.data))
    intermediate_storage = build_fs_intermediate_storage(
        graphql_context.instance.intermediates_directory, pipeline_run.run_id
    )
    assert intermediate_storage.has_intermediate(None, StepOutputHandle('sum_solid.compute'))
    assert intermediate_storage.has_intermediate(None, StepOutputHandle('sum_sq_solid.compute'))


def test_success_whole_execution_plan_with_filesystem_config(graphql_context, snapshot):
    instance = graphql_context.instance
    selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
    run_config = merge_dicts(csv_hello_world_solids_config(), {'storage': {'filesystem': {}}})
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=csv_hello_world, run_config=run_config
    )
    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': run_config,
                'stepKeys': None,
                'executionMetadata': {'runId': pipeline_run.run_id},
                'mode': 'default',
            },
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['stepKey']: step_event
        for step_event in query_result['stepEvents']
        if step_event['stepKey']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(clean_log_messages(result.data))
    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )
    assert intermediate_storage.has_intermediate(None, StepOutputHandle('sum_solid.compute'))
    assert intermediate_storage.has_intermediate(None, StepOutputHandle('sum_sq_solid.compute'))


def test_success_whole_execution_plan_with_in_memory_config(graphql_context, snapshot):
    instance = graphql_context.instance
    selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
    run_config = merge_dicts(csv_hello_world_solids_config(), {'storage': {'in_memory': {}}})
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=csv_hello_world, run_config=run_config
    )
    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': run_config,
                'stepKeys': None,
                'executionMetadata': {'runId': pipeline_run.run_id},
                'mode': 'default',
            },
        },
    )

    query_result = result.data['executePlan']

    assert query_result['__typename'] == 'ExecutePlanSuccess'
    assert query_result['pipeline']['name'] == 'csv_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['stepKey']: step_event
        for step_event in query_result['stepEvents']
        if step_event['stepKey']
    }
    assert 'sum_solid.compute' in step_events
    assert 'sum_sq_solid.compute' in step_events

    snapshot.assert_match(clean_log_messages(result.data))
    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )
    assert not intermediate_storage.has_intermediate(None, StepOutputHandle('sum_solid.compute'))
    assert not intermediate_storage.has_intermediate(None, StepOutputHandle('sum_sq_solid.compute'))


def test_successful_one_part_execute_plan(graphql_context, snapshot):
    instance = graphql_context.instance
    run_config = csv_hello_world_solids_config_fs_storage()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=csv_hello_world, run_config=run_config
    )
    selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')

    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': run_config,
                'stepKeys': ['sum_solid.compute'],
                'executionMetadata': {'runId': pipeline_run.run_id},
                'mode': 'default',
            },
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

    assert step_events[1]['stepKey'] == 'sum_solid.compute'
    assert step_events[2]['outputName'] == 'result'

    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), '''
        '''OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]'''
    )

    assert step_events[3]['stepKey'] == 'sum_solid.compute'
    assert step_events[4]['stepKey'] == 'sum_solid.compute'

    snapshot.assert_match(clean_log_messages(result.data))

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )
    assert intermediate_storage.has_intermediate(None, StepOutputHandle('sum_solid.compute'))
    assert (
        str(
            intermediate_storage.get_intermediate(
                None, PoorMansDataFrame, StepOutputHandle('sum_solid.compute')
            ).obj
        )
        == expected_value_repr
    )


def test_successful_two_part_execute_plan(graphql_context, snapshot):
    instance = graphql_context.instance
    run_config = csv_hello_world_solids_config_fs_storage()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=csv_hello_world, run_config=run_config
    )
    selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
    result_one = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': run_config,
                'stepKeys': ['sum_solid.compute'],
                'executionMetadata': {'runId': pipeline_run.run_id},
                'mode': 'default',
            },
        },
    )

    assert result_one.data['executePlan']['__typename'] == 'ExecutePlanSuccess'

    snapshot.assert_match(clean_log_messages(result_one.data))

    result_two = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': csv_hello_world_solids_config_fs_storage(),
                'stepKeys': ['sum_sq_solid.compute'],
                'executionMetadata': {'runId': pipeline_run.run_id},
                'mode': 'default',
            },
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
    assert step_events[0]['stepKey'] == 'sum_sq_solid.compute'
    assert step_events[1]['stepKey'] == 'sum_sq_solid.compute'
    assert step_events[2]['stepKey'] == 'sum_sq_solid.compute'
    assert step_events[3]['outputName'] == 'result'
    assert step_events[4]['stepKey'] == 'sum_sq_solid.compute'

    snapshot.assert_match(clean_log_messages(result_two.data))

    expected_value_repr = (
        '''[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3), '''
        '''('sum_sq', 9)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7), '''
        '''('sum_sq', 49)])]'''
    )

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )

    assert intermediate_storage.has_intermediate(None, StepOutputHandle('sum_sq_solid.compute'))
    assert (
        str(
            intermediate_storage.get_intermediate(
                None, PoorMansDataFrame, StepOutputHandle('sum_sq_solid.compute')
            ).obj
        )
        == expected_value_repr
    )


class TestExecutionPlan(ReadonlyGraphQLContextTestMatrix):
    def test_invalid_config_fetch_execute_plan(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
        result = execute_dagster_graphql(
            graphql_context,
            EXECUTION_PLAN_QUERY,
            variables={
                'pipeline': selector,
                'runConfigData': {
                    'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}
                },
                'mode': 'default',
            },
        )

        assert not result.errors
        assert result.data
        assert (
            result.data['executionPlanOrError']['__typename'] == 'PipelineConfigValidationInvalid'
        )
        assert len(result.data['executionPlanOrError']['errors']) == 1
        assert (
            'Invalid scalar at path root:solids:sum_solid:inputs:num'
            in result.data['executionPlanOrError']['errors'][0]['message']
        )
        result.data['executionPlanOrError']['errors'][0][
            'message'
        ] = 'Invalid scalar at path root:solids:sum_solid:inputs:num'
        snapshot.assert_match(result.data)


def test_invalid_config_execute_plan(graphql_context, snapshot):
    selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': {
                    'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}
                },
                'stepKeys': [
                    'sum_solid.num.input_thunk',
                    'sum_solid.compute',
                    'sum_sq_solid.compute',
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
                'mode': 'default',
            },
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


def test_pipeline_not_found_error_execute_plan(graphql_context, snapshot):
    selector = infer_pipeline_selector(graphql_context, 'nope')
    result = execute_dagster_graphql(
        graphql_context,
        EXECUTE_PLAN_QUERY,
        variables={
            'executionParams': {
                'selector': selector,
                'runConfigData': {
                    'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 'ok'}}}}}
                },
                'stepKeys': [
                    'sum_solid.num.input_thunk',
                    'sum_solid.compute',
                    'sum_sq_solid.compute',
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
                'mode': 'default',
            },
        },
    )

    assert result.data['executePlan']['__typename'] == 'PipelineNotFoundError'
    assert result.data['executePlan']['pipelineName'] == 'nope'
    snapshot.assert_match(result.data)


def test_basic_execute_plan_with_materialization(graphql_context):
    selector = infer_pipeline_selector(graphql_context, 'csv_hello_world')
    with get_temp_file_name() as out_csv_path:

        run_config = {
            'solids': {
                'sum_solid': {
                    'inputs': {'num': file_relative_path(__file__, '../data/num.csv')},
                    'outputs': [{'result': out_csv_path}],
                }
            }
        }

        result = execute_dagster_graphql(
            graphql_context,
            EXECUTION_PLAN_QUERY,
            variables={'pipeline': selector, 'runConfigData': run_config, 'mode': 'default',},
        )

        steps_data = result.data['executionPlanOrError']['steps']

        assert set([step_data['key'] for step_data in steps_data]) == set(
            ['sum_solid.compute', 'sum_sq_solid.compute',]
        )

        instance = graphql_context.instance

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=csv_hello_world, run_config=run_config
        )

        result = execute_dagster_graphql(
            graphql_context,
            EXECUTE_PLAN_QUERY,
            variables={
                'executionParams': {
                    'selector': selector,
                    'runConfigData': run_config,
                    'stepKeys': ['sum_solid.compute', 'sum_sq_solid.compute'],
                    'executionMetadata': {'runId': pipeline_run.run_id},
                    'mode': 'default',
                },
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
