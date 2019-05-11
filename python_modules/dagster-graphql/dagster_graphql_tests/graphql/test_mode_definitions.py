from .setup import execute_dagster_graphql, define_context
from .utils import sync_execute_get_events


def get_step_output(logs, step_key):
    for log in logs:
        if log['__typename'] == 'ExecutionStepOutputEvent' and log['step']['key'] == step_key:
            return log


def test_multi_mode_successful():
    add_mode_logs = sync_execute_get_events(
        {
            'pipeline': {'name': 'multi_mode_with_resources'},
            'mode': 'add_mode',
            'config': {'resources': {'op': {'config': 2}}},
        }
    )
    assert get_step_output(add_mode_logs, 'apply_to_three.transform')['valueRepr'] == '5'

    mult_mode_logs = sync_execute_get_events(
        {
            'pipeline': {'name': 'multi_mode_with_resources'},
            'mode': 'mult_mode',
            'config': {'resources': {'op': {'config': 2}}},
        }
    )
    assert get_step_output(mult_mode_logs, 'apply_to_three.transform')['valueRepr'] == '6'

    double_adder_mode_logs = sync_execute_get_events(
        {
            'pipeline': {'name': 'multi_mode_with_resources'},
            'mode': 'double_adder',
            'config': {'resources': {'op': {'config': {'num_one': 2, 'num_two': 4}}}},
        }
    )
    assert get_step_output(double_adder_mode_logs, 'apply_to_three.transform')['valueRepr'] == '9'


MODE_QUERY = '''
query ModesQuery($pipelineName: String!, $mode: String)
{
  pipeline(params: { name: $pipelineName }) {
    configTypes(mode: $mode) {
      name
    }
    environmentType(mode: $mode){
      name
      ... on CompositeConfigType {
        fields {
          configType {
            name
          }
        }
      }
    }
    modes {
      name
      description
      resources {
        name
        config {
          configType {
            name
            ... on CompositeConfigType {
              fields {
                name
                configType {
                  name
                }
              }
            }
          }
        }
      }
    }
  }
}
'''


def execute_modes_query(pipeline_name, mode):
    return execute_dagster_graphql(
        define_context(), MODE_QUERY, variables={'pipelineName': pipeline_name, 'mode': mode}
    )


def get_pipeline(result, name):
    for pipeline_data in result.data['pipelinesOrError']['nodes']:
        if pipeline_data['name'] == name:
            return pipeline_data

    raise Exception('not found')


def test_query_multi_mode(snapshot):
    modeless_result = execute_modes_query('multi_mode_with_resources', mode=None)
    snapshot.assert_match(modeless_result.data)

    modeless_result = execute_modes_query('multi_mode_with_resources', mode='add_mode')
    snapshot.assert_match(modeless_result.data)


# delete once https://github.com/dagster-io/dagster/issues/1343 is resolved
def test_multi_mode_default_mode():
    add_mode_logs = sync_execute_get_events(
        {
            'pipeline': {'name': 'multi_mode_with_resources'},
            'config': {'resources': {'op': {'config': 2}}},
        }
    )
    assert get_step_output(add_mode_logs, 'apply_to_three.transform')['valueRepr'] == '5'
