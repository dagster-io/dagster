from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import OutOfProcessExecutingGraphQLContextTestMatrix
from .utils import sync_execute_get_run_log_data

COMPUTE_LOGS_QUERY = """
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
"""
COMPUTE_LOGS_SUBSCRIPTION = """
  subscription ComputeLogsSubscription($runId: ID!, $stepKey: String!, $ioType: ComputeIOType!, $cursor: String!) {
    computeLogs(runId: $runId, stepKey: $stepKey, ioType: $ioType, cursor: $cursor) {
      data
    }
  }
"""


class TestComputeLogs(OutOfProcessExecutingGraphQLContextTestMatrix):
    def test_get_compute_logs_over_graphql(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "spew_pipeline")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]

        result = execute_dagster_graphql(
            graphql_context,
            COMPUTE_LOGS_QUERY,
            variables={"runId": run_id, "stepKey": "spew"},
        )
        compute_logs = result.data["pipelineRunOrError"]["computeLogs"]
        snapshot.assert_match(compute_logs)

    def test_compute_logs_subscription_graphql(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "spew_pipeline")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]

        subscription = execute_dagster_graphql(
            graphql_context,
            COMPUTE_LOGS_SUBSCRIPTION,
            variables={
                "runId": run_id,
                "stepKey": "spew",
                "ioType": "STDOUT",
                "cursor": "0",
            },
        )
        results = []
        subscription.subscribe(lambda x: results.append(x.data))
        assert len(results) == 1
        result = results[0]
        assert result["computeLogs"]["data"] == "HELLO WORLD\n"
        snapshot.assert_match(results)
