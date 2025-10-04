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

    def test_captured_logs_with_invalid_utf8(self, graphql_context):
        """Test that captured logs handle invalid UTF-8 sequences gracefully.

        This test verifies the fix for issue #32251 where invalid UTF-8 bytes
        in stderr would cause GraphQL query failures.
        """
        import os

        # Create a unique log key for this test
        log_key = ["test_invalid_utf8", "compute_logs", "test_step"]

        # Write binary data with invalid UTF-8 to stderr
        compute_log_manager = graphql_context.instance.compute_log_manager
        stderr_path = compute_log_manager.get_captured_local_path(log_key, "err")

        # Ensure directory exists
        os.makedirs(os.path.dirname(stderr_path), exist_ok=True)

        # Write test data with invalid UTF-8 sequences
        with open(stderr_path, "wb") as f:
            f.write(b"Valid text before\n")
            f.write(b"\xff\xfe")  # Invalid UTF-8 sequence
            f.write(b"\nValid text after\n")

        try:
            # Query should not raise an exception
            result = execute_dagster_graphql(
                graphql_context,
                CAPTURED_LOGS_QUERY,
                variables={"logKey": log_key},
            )

            # Verify we got a result (not an error)
            assert result.data is not None
            assert result.data["capturedLogs"] is not None

            # Stderr should contain the replacement character (�)
            stderr = result.data["capturedLogs"]["stderr"]
            assert stderr is not None
            assert "Valid text before" in stderr
            assert "Valid text after" in stderr
            # The invalid bytes should be replaced with replacement character
            assert "\ufffd" in stderr or "�" in stderr

        finally:
            # Cleanup test file
            if os.path.exists(stderr_path):
                os.remove(stderr_path)

    def test_captured_logs_subscription_with_invalid_utf8(self, graphql_context):
        """Test that captured logs subscription handles invalid UTF-8 gracefully.

        This test verifies the fix works for GraphQL subscriptions as well as queries.
        """
        import os

        # Create a unique log key for this test
        log_key = ["test_invalid_utf8_sub", "compute_logs", "test_step"]

        # Write binary data with invalid UTF-8 to stderr
        compute_log_manager = graphql_context.instance.compute_log_manager
        stderr_path = compute_log_manager.get_captured_local_path(log_key, "err")

        # Ensure directory exists
        os.makedirs(os.path.dirname(stderr_path), exist_ok=True)

        # Write test data simulating partial multi-byte UTF-8 at chunk boundary
        with open(stderr_path, "wb") as f:
            # Write valid text
            f.write(b"Subscription test\n")
            # Add invalid UTF-8 (partial 4-byte sequence)
            f.write(b"\xf0\x9f")  # First 2 bytes of 4-byte emoji, incomplete
            f.write(b"\nMore text\n")

        try:
            # Subscription should not raise an exception
            results = execute_dagster_graphql_subscription(
                graphql_context,
                CAPTURED_LOGS_SUBSCRIPTION,
                variables={"logKey": log_key},
            )

            # Verify we got results
            assert len(results) > 0

            # First result should contain data
            assert results[0].data is not None
            assert results[0].data["capturedLogs"] is not None

            # Stderr should be readable
            stderr = results[0].data["capturedLogs"]["stderr"]
            assert stderr is not None
            assert "Subscription test" in stderr
            assert "More text" in stderr

        finally:
            # Cleanup test file
            if os.path.exists(stderr_path):
                os.remove(stderr_path)
