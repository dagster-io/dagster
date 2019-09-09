import copy

from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.instance import DagsterInstance

from .utils import define_context, sync_execute_get_run_log_data

RUNS_QUERY = '''
query PipelineRunsRootQuery($name: String!) {
  pipeline(params: { name: $name }) {
    name
    runs {
      ...RunHistoryRunFragment
    }
  }
}

fragment RunHistoryRunFragment on PipelineRun {
  runId
  status
  pipeline {
    name
  }
  logs {
    nodes {
      __typename
      ... on MessageEvent {
        timestamp
      }
    }
  }
  executionPlan {
    steps {
      key
    }
  }
  environmentConfigYaml
  mode
}
'''


def _get_runs_data(result, run_id):
    for run_data in result.data['pipeline']['runs']:
        if run_data['runId'] == run_id:
            # so caller can delete keys
            return copy.deepcopy(run_data)

    raise Exception('nope')


def test_get_runs_over_graphql():
    payload_one = sync_execute_get_run_log_data(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 2}}},
            }
        }
    )
    run_id_one = payload_one['runId']

    payload_two = sync_execute_get_run_log_data(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 3}}},
            }
        }
    )

    run_id_two = payload_two['runId']

    read_context = define_context(instance=DagsterInstance.local_temp())

    result = execute_dagster_graphql(
        read_context, RUNS_QUERY, variables={'name': 'multi_mode_with_resources'}
    )

    run_one_data = _get_runs_data(result, run_id_one)
    assert [log['__typename'] for log in run_one_data['logs']['nodes']] == [
        msg['__typename'] for msg in payload_one['messages']
    ]

    run_two_data = _get_runs_data(result, run_id_two)
    assert [log['__typename'] for log in run_two_data['logs']['nodes']] == [
        msg['__typename'] for msg in payload_two['messages']
    ]
