import graphql
import pytest
from dagster_graphql.test.utils import execute_dagster_graphql

from .setup import define_test_context
from .utils import sync_execute_get_events


def get_step_output(logs, step_key):
    for log in logs:
        if log['__typename'] == 'ExecutionStepOutputEvent' and log['step']['key'] == step_key:
            return log


def test_multi_mode_successful():
    add_mode_logs = sync_execute_get_events(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 2}}},
            }
        }
    )
    assert get_step_output(add_mode_logs, 'apply_to_three.compute')

    mult_mode_logs = sync_execute_get_events(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'mult_mode',
                'environmentConfigData': {'resources': {'op': {'config': 2}}},
            }
        }
    )
    assert get_step_output(mult_mode_logs, 'apply_to_three.compute')

    double_adder_mode_logs = sync_execute_get_events(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'double_adder',
                'environmentConfigData': {
                    'resources': {'op': {'config': {'num_one': 2, 'num_two': 4}}}
                },
            }
        }
    )
    get_step_output(double_adder_mode_logs, 'apply_to_three.compute')


MODE_QUERY = '''
query ModesQuery($pipelineName: String!, $mode: String!)
{
  environmentSchemaOrError(selector: {name: $pipelineName}, mode: $mode ) {
    __typename
    ... on EnvironmentSchema {
      rootEnvironmentType {
        key
        ... on CompositeConfigType {
          fields {
            configType {
              key
            }
          }
        }
      }
      allConfigTypes {
        key
      }
    }
  }
}
'''


def execute_modes_query(pipeline_name, mode):
    return execute_dagster_graphql(
        define_test_context(), MODE_QUERY, variables={'pipelineName': pipeline_name, 'mode': mode}
    )


def get_pipeline(result, name):
    for pipeline_data in result.data['pipelinesOrError']['nodes']:
        if pipeline_data['name'] == name:
            return pipeline_data

    raise Exception('not found')


def test_query_multi_mode():
    with pytest.raises(graphql.error.base.GraphQLError):
        execute_modes_query('multi_mode_with_resources', mode=None)

    modeful_result = execute_modes_query('multi_mode_with_resources', mode='add_mode')
    assert modeful_result.data['environmentSchemaOrError']['__typename'] == 'EnvironmentSchema'
