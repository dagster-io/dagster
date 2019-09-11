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
