import pickle
import pandas as pd

from dagster import check
from dagster.utils import script_relative_path
from dagster.utils.test import get_temp_file_name

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

START_EXECUTION_PLAN_QUERY = '''
mutation (
    $pipelineName: String!
    $config: PipelineConfig
    $stepExecutions: [StepExecution!]!
    $executionMetadata: ExecutionMetadata!
) {
    startSubplanExecution(
        pipelineName: $pipelineName
        config: $config
        stepExecutions: $stepExecutions
        executionMetadata: $executionMetadata
    ) {
        __typename
        ... on StartSubplanExecutionSuccess {
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
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on StartSubplanExecutionInvalidStepError {
            invalidStepKey
        }
        ... on StartSubplanExecutionInvalidInputError {
            stepKey
            invalidInputName
        }
        ... on StartSubplanExecutionInvalidOutputError {
            stepKey
            invalidOutputName
        }
        ... on InvalidSubplanMissingInputError {
            stepKey
            missingInputName
        }
        ... on PythonError {
            message
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


def test_query_execution_plan_snapshot(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {'config': pandas_hello_world_solids_config(), 'pipeline': {'name': 'pandas_hello_world'}},
    )

    assert not result.errors
    assert result.data

    snapshot.assert_match(result.data)


def test_query_execution_plan():
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {'config': pandas_hello_world_solids_config(), 'pipeline': {'name': 'pandas_hello_world'}},
    )

    assert not result.errors
    assert result.data

    plan_data = result.data['executionPlan']

    names = get_nameset(plan_data['steps'])
    assert len(names) == 3

    assert names == set(
        ['sum_solid.num.input_thunk', 'sum_solid.transform', 'sum_sq_solid.transform']
    )

    assert result.data['executionPlan']['pipeline']['name'] == 'pandas_hello_world'

    cn = get_named_thing(plan_data['steps'], 'sum_solid.transform')

    assert cn['kind'] == 'TRANSFORM'
    assert cn['solid']['name'] == 'sum_solid'

    assert get_nameset(cn['inputs']) == set(['num'])

    sst_input = get_named_thing(cn['inputs'], 'num')
    assert sst_input['type']['name'] == 'PandasDataFrame'

    assert sst_input['dependsOn']['name'] == 'sum_solid.num.input_thunk'

    sst_output = get_named_thing(cn['outputs'], 'result')
    assert sst_output['type']['name'] == 'PandasDataFrame'


def test_query_execution_plan_errors():
    result = execute_dagster_graphql(
        define_context(),
        EXECUTION_PLAN_QUERY,
        {'config': 2334893, 'pipeline': {'name': 'pandas_hello_world'}},
    )

    assert not result.errors
    assert result.data
    assert result.data['executionPlan']['__typename'] == 'PipelineConfigValidationInvalid'

    result = execute_dagster_graphql(
        define_context(), EXECUTION_PLAN_QUERY, {'config': 2334893, 'pipeline': {'name': 'nope'}}
    )

    assert not result.errors
    assert result.data
    assert result.data['executionPlan']['__typename'] == 'PipelineNotFoundError'
    assert result.data['executionPlan']['pipelineName'] == 'nope'


def test_successful_start_subplan(snapshot):

    with get_temp_file_name() as num_df_file:
        with get_temp_file_name() as out_df_file:
            num_df = pd.read_csv(script_relative_path('../num.csv'))

            with open(num_df_file, 'wb') as ff:
                pickle.dump(num_df, ff)

            result = execute_dagster_graphql(
                define_context(),
                START_EXECUTION_PLAN_QUERY,
                variables={
                    'pipelineName': 'pandas_hello_world',
                    'config': pandas_hello_world_solids_config(),
                    'stepExecutions': [
                        {
                            'stepKey': 'sum_solid.transform',
                            'marshalledInputs': [{'inputName': 'num', 'key': num_df_file}],
                            'marshalledOutputs': [{'outputName': 'result', 'key': out_df_file}],
                        }
                    ],
                    'executionMetadata': {'runId': 'kdjkfjdfd'},
                },
            )

            with open(out_df_file, 'rb') as ff:
                out_df = pickle.load(ff)
            assert out_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}

    query_result = result.data['startSubplanExecution']

    assert query_result['__typename'] == 'StartSubplanExecutionSuccess'
    assert query_result['pipeline']['name'] == 'pandas_hello_world'
    assert query_result['hasFailures'] is False
    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }

    assert 'sum_solid.transform' in step_events

    assert step_events['sum_solid.transform']['__typename'] == 'SuccessfulStepOutputEvent'
    assert step_events['sum_solid.transform']['success'] is True
    assert step_events['sum_solid.transform']['outputName'] == 'result'
    assert (
        step_events['sum_solid.transform']['valueRepr']
        == '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
    )

    snapshot.assert_match(result.data)


def test_user_error_pipeline(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'naughty_programmer_pipeline',
            'config': {},
            'stepExecutions': [{'stepKey': 'throw_a_thing.transform'}],
            'executionMetadata': {'runId': 'dljkfdlkfld'},
        },
    )

    assert result.data

    query_result = result.data['startSubplanExecution']
    assert query_result['__typename'] == 'StartSubplanExecutionSuccess'
    assert query_result['pipeline']['name'] == 'naughty_programmer_pipeline'
    assert query_result['hasFailures'] is True

    step_events = {
        step_event['step']['key']: step_event for step_event in query_result['stepEvents']
    }

    assert 'throw_a_thing.transform' in step_events
    assert step_events['throw_a_thing.transform']['__typename'] == 'StepFailureEvent'
    assert step_events['throw_a_thing.transform']['success'] is False
    snapshot.assert_match(result.data)


def test_start_subplan_pipeline_not_found(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'nope',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [{'stepKey': 'sum_solid.transform'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert result.data['startSubplanExecution']['__typename'] == 'PipelineNotFoundError'
    assert result.data['startSubplanExecution']['pipelineName'] == 'nope'
    snapshot.assert_match(result.data)


def test_start_subplan_invalid_config(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': {'solids': {'sum_solid': {'inputs': {'num': {'csv': {'path': 384938439}}}}}},
            'stepExecutions': [{'stepKey': 'sum_solid.transform'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startSubplanExecution']['__typename'] == 'PipelineConfigValidationInvalid'
    snapshot.assert_match(result.data)


def test_start_subplan_invalid_step_keys(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [{'stepKey': 'nope'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert result.data
    assert (
        result.data['startSubplanExecution']['__typename']
        == 'StartSubplanExecutionInvalidStepError'
    )

    assert result.data['startSubplanExecution']['invalidStepKey'] == 'nope'
    snapshot.assert_match(result.data)


def test_start_subplan_invalid_input_name(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [
                {
                    'stepKey': 'sum_solid.transform',
                    'marshalledInputs': [{'inputName': 'nope', 'key': 'nope'}],
                }
            ],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert result.data
    assert (
        result.data['startSubplanExecution']['__typename']
        == 'StartSubplanExecutionInvalidInputError'
    )

    assert result.data['startSubplanExecution']['stepKey'] == 'sum_solid.transform'
    assert result.data['startSubplanExecution']['invalidInputName'] == 'nope'
    snapshot.assert_match(result.data)


def test_start_subplan_invalid_output_name(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [
                {
                    'stepKey': 'sum_solid.transform',
                    'marshalledOutputs': [{'outputName': 'nope', 'key': 'nope'}],
                }
            ],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert result.data
    assert (
        result.data['startSubplanExecution']['__typename']
        == 'StartSubplanExecutionInvalidOutputError'
    )

    assert result.data['startSubplanExecution']['stepKey'] == 'sum_solid.transform'
    assert result.data['startSubplanExecution']['invalidOutputName'] == 'nope'
    snapshot.assert_match(result.data)


# Currently this raises a normal python error because the file not found
# error is hit outside the execution plan system
def test_start_subplan_invalid_input_path():
    hardcoded_uuid = '160b56ba-c9a6-4111-ab4e-a7ab364eb031'

    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [
                {
                    'stepKey': 'sum_solid.transform',
                    'marshalledInputs': [{'inputName': 'num', 'key': hardcoded_uuid}],
                }
            ],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startSubplanExecution']['__typename'] == 'PythonError'


# Currently this raises a normal python error because the file not found
# error is hit outside the execution plan system
def test_start_subplan_invalid_output_path():
    with get_temp_file_name() as num_df_file:
        num_df = pd.read_csv(script_relative_path('../num.csv'))

        with open(num_df_file, 'wb') as ff:
            pickle.dump(num_df, ff)

        hardcoded_uuid = '160b56ba-c9a6-4111-ab4e-a7ab364eb031'

        result = execute_dagster_graphql(
            define_context(),
            START_EXECUTION_PLAN_QUERY,
            variables={
                'pipelineName': 'pandas_hello_world',
                'config': pandas_hello_world_solids_config(),
                'stepExecutions': [
                    {
                        'stepKey': 'sum_solid.transform',
                        'marshalledInputs': [{'inputName': 'num', 'key': num_df_file}],
                        'marshalledOutputs': [
                            {
                                'outputName': 'result',
                                # guaranteed to not exist
                                'key': '{uuid}/{uuid}'.format(uuid=hardcoded_uuid),
                            }
                        ],
                    }
                ],
                'executionMetadata': {'runId': 'kdjkfjdfd'},
            },
        )

        assert not result.errors
        assert result.data
        assert result.data['startSubplanExecution']['__typename'] == 'PythonError'


def test_invalid_subplan_missing_inputs(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'pandas_hello_world',
            'config': pandas_hello_world_solids_config(),
            'stepExecutions': [{'stepKey': 'sum_solid.transform'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert not result.errors
    assert result.data
    assert result.data['startSubplanExecution']['__typename'] == 'InvalidSubplanMissingInputError'
    assert result.data['startSubplanExecution']['stepKey'] == 'sum_solid.transform'
    snapshot.assert_match(result.data)


def test_user_code_error_subplan(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        START_EXECUTION_PLAN_QUERY,
        variables={
            'pipelineName': 'naughty_programmer_pipeline',
            'config': {},
            'stepExecutions': [{'stepKey': 'throw_a_thing.transform'}],
            'executionMetadata': {'runId': 'kdjkfjdfd'},
        },
    )

    assert not result.errors
    assert result.data

    snapshot.assert_match(result.data)
