from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.core.instance import DagsterInstance

from .utils import define_context, sync_execute_get_run_log_data

COMPUTE_LOGS_QUERY = '''
  query ComputeLogsQuery($runId: ID!, $stepKey: String!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        runId
        computeLogs(stepKey: $stepKey) {
          stdout {
            data
          }
        }
      }
    }
  }
'''
COMPUTE_LOGS_SUBSCRIPTION = '''
  subscription ComputeLogsSubscription($runId: ID!, $stepKey: String!, $cursor: String!) {
    computeLogs(runId: $runId, stepKey: $stepKey, cursor: $cursor) {
      stdout {
        data
      }
    }
  }
'''


def test_get_compute_logs_over_graphql(snapshot):
    payload = sync_execute_get_run_log_data(
        {'executionParams': {'selector': {'name': 'spew_pipeline'}, 'mode': 'default'}}
    )
    run_id = payload['runId']

    result = execute_dagster_graphql(
        define_context(instance=DagsterInstance.local_temp()),
        COMPUTE_LOGS_QUERY,
        variables={'runId': run_id, 'stepKey': 'spew.compute'},
    )
    compute_logs = result.data['pipelineRunOrError']['computeLogs']
    snapshot.assert_match(compute_logs)


def test_compute_logs_subscription_graphql(snapshot):
    payload = sync_execute_get_run_log_data(
        {'executionParams': {'selector': {'name': 'spew_pipeline'}, 'mode': 'default'}}
    )
    run_id = payload['runId']

    subscription = execute_dagster_graphql(
        define_context(instance=DagsterInstance.local_temp()),
        COMPUTE_LOGS_SUBSCRIPTION,
        variables={'runId': run_id, 'stepKey': 'spew.compute', 'cursor': '0:0'},
    )
    results = []
    subscription.subscribe(lambda x: results.append(x.data))
    assert len(results) == 1
    result = results[0]
    assert result['computeLogs']['stdout']['data'] == 'HELLO WORLD\n'
    snapshot.assert_match(results)
