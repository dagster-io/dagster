from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from dagster._core.events import DagsterEventType

from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .utils import sync_execute_get_run_log_data

CAPTURED_LOGS_QUERY = """
  query CapturedLogsQuery($runId: ID!, $fileKey: String!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
        runId
        capturedLogs(fileKey: $fileKey) {
          stdout
        }
      }
    }
  }
"""

CAPTURED_LOGS_SUBSCRIPTION = """
  subscription CapturedLogsSubscription($logKey: [String!]!) {
    capturedLogs(logKey: $logKey) {
      stdout
      stderr
      cursor
    }
  }
"""


class TestComputeLogs(ExecutingGraphQLContextTestMatrix):
    def test_get_compute_logs_over_graphql(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "spew_pipeline")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]

        logs = graphql_context.instance.all_logs(run_id, of_type=DagsterEventType.LOGS_CAPTURED)
        assert len(logs) == 1
        entry = logs[0]
        result = execute_dagster_graphql(
            graphql_context,
            CAPTURED_LOGS_QUERY,
            variables={"runId": run_id, "fileKey": entry.dagster_event.logs_captured_data.file_key},
        )
        stdout = result.data["pipelineRunOrError"]["capturedLogs"]["stdout"]
        snapshot.assert_match(stdout)

    def test_compute_logs_subscription_graphql(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "spew_pipeline")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]
        logs = graphql_context.instance.all_logs(run_id, of_type=DagsterEventType.LOGS_CAPTURED)
        assert len(logs) == 1
        entry = logs[0]
        log_key = [run_id, "compute_logs", entry.dagster_event.logs_captured_data.file_key]

        subscription = execute_dagster_graphql(
            graphql_context,
            CAPTURED_LOGS_SUBSCRIPTION,
            variables={"logKey": log_key},
        )
        results = []
        subscription.subscribe(lambda x: results.append(x.data["capturedLogs"]["stdout"]))

        assert len(results) == 1
        result = results[0]
        assert result == "HELLO WORLD\n"
        snapshot.assert_match(results)
