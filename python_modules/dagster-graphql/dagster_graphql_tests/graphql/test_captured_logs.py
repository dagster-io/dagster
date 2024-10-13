from dagster._core.events import DagsterEventType
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_subscription,
    infer_job_selector,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)
from dagster_graphql_tests.graphql.utils import sync_execute_get_run_log_data

CAPTURED_LOGS_QUERY = """
  query CapturedLogsQuery($logKey: [String!]!) {
    capturedLogs(logKey: $logKey) {
      stdout
      stderr
      cursor
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

CAPTURED_LOGS_EVENT_QUERY = """
  query CapturedLogsEventQuery($runId: ID!) {
    runOrError(runId: $runId) {
      __typename
      ... on Run {
        eventConnection {
          events {
            ... on LogsCapturedEvent {
              message
              timestamp
              fileKey
              stepKeys
              externalStdoutUrl
              externalStderrUrl
            }
          }
        }
      }
    }
  }
"""


class TestCapturedLogs(ExecutingGraphQLContextTestMatrix):
    def test_get_captured_logs_over_graphql(self, graphql_context):
        selector = infer_job_selector(graphql_context, "spew_job")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]

        logs = graphql_context.instance.all_logs(run_id, of_type=DagsterEventType.LOGS_CAPTURED)
        assert len(logs) == 1
        entry = logs[0]
        log_key = [run_id, "compute_logs", entry.dagster_event.logs_captured_data.file_key]

        result = execute_dagster_graphql(
            graphql_context,
            CAPTURED_LOGS_QUERY,
            variables={"logKey": log_key},
        )
        stdout = result.data["capturedLogs"]["stdout"]
        assert stdout == "HELLO WORLD\n"

    def test_captured_logs_subscription_graphql(self, graphql_context):
        selector = infer_job_selector(graphql_context, "spew_job")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]
        logs = graphql_context.instance.all_logs(run_id, of_type=DagsterEventType.LOGS_CAPTURED)
        assert len(logs) == 1
        entry = logs[0]
        log_key = [run_id, "compute_logs", entry.dagster_event.logs_captured_data.file_key]

        results = execute_dagster_graphql_subscription(
            graphql_context,
            CAPTURED_LOGS_SUBSCRIPTION,
            variables={"logKey": log_key},
        )

        assert len(results) == 1
        stdout = results[0].data["capturedLogs"]["stdout"]
        assert stdout == "HELLO WORLD\n"

    def test_captured_logs_event_graphql(self, graphql_context):
        selector = infer_job_selector(graphql_context, "spew_job")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]
        result = execute_dagster_graphql(
            graphql_context,
            CAPTURED_LOGS_EVENT_QUERY,
            variables={"runId": run_id},
        )
        assert result.data["runOrError"]["__typename"] == "Run"
        events = result.data["runOrError"]["eventConnection"]["events"]
        assert len(events) > 0
