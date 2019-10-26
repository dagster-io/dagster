import copy

from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.instance import DagsterInstance

from .utils import define_context, sync_execute_get_run_log_data

RUNS_QUERY = '''
query PipelineRunsRootQuery($name: String!) {
  pipeline(params: { name: $name }) {
    ...on PipelineReference { name }
    ... on Pipeline {
      runs {
        ...RunHistoryRunFragment
      }
    }
  }
}

fragment RunHistoryRunFragment on PipelineRun {
  runId
  status
  pipeline {
    ...on PipelineReference { name }
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
  canCancel
}
'''

DELETE_RUN_MUTATION = '''
mutation DeleteRun($runId: String!) {
  deletePipelineRun(runId: $runId) {
    __typename
    ... on DeletePipelineRunSuccess {
      runId
    }
    ... on PythonError {
      message
    }
  }
}
'''


def _get_runs_data(result, run_id):
    for run_data in result.data['pipeline']['runs']:
        if run_data['runId'] == run_id:
            # so caller can delete keys
            return copy.deepcopy(run_data)

    return None


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
    run_id_one = payload_one['run']['runId']

    payload_two = sync_execute_get_run_log_data(
        {
            'executionParams': {
                'selector': {'name': 'multi_mode_with_resources'},
                'mode': 'add_mode',
                'environmentConfigData': {'resources': {'op': {'config': 3}}},
            }
        }
    )

    run_id_two = payload_two['run']['runId']

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

    # delete the second run
    result = execute_dagster_graphql(
        read_context, DELETE_RUN_MUTATION, variables={'runId': run_id_two}
    )
    assert result.data['deletePipelineRun']['__typename'] == 'DeletePipelineRunSuccess'
    assert result.data['deletePipelineRun']['runId'] == run_id_two

    # query it back out
    result = execute_dagster_graphql(
        read_context, RUNS_QUERY, variables={'name': 'multi_mode_with_resources'}
    )

    # first is the same
    run_one_data = _get_runs_data(result, run_id_one)
    assert [log['__typename'] for log in run_one_data['logs']['nodes']] == [
        msg['__typename'] for msg in payload_one['messages']
    ]

    # second is gone
    run_two_data = _get_runs_data(result, run_id_two)
    assert run_two_data is None

    # try to delete the second run again
    execute_dagster_graphql(read_context, DELETE_RUN_MUTATION, variables={'runId': run_id_two})

    result = execute_dagster_graphql(
        read_context, DELETE_RUN_MUTATION, variables={'runId': run_id_two}
    )
    assert result.data['deletePipelineRun']['__typename'] == 'PipelineRunNotFoundError'
