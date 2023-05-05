from dagster._core.events import DagsterEventType
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_subscription,
    infer_pipeline_selector,
)

from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
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


class TestComputeLogs(ExecutingGraphQLContextTestMatrix):
    def test_get_compute_logs_over_graphql(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "spew_job")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]
        logs = graphql_context.instance.all_logs(run_id, of_type=DagsterEventType.LOGS_CAPTURED)
        assert len(logs) == 1
        entry = logs[0]
        file_key = entry.dagster_event.logs_captured_data.file_key
        result = execute_dagster_graphql(
            graphql_context,
            COMPUTE_LOGS_QUERY,
            variables={"runId": run_id, "stepKey": file_key},
        )
        compute_logs = result.data["pipelineRunOrError"]["computeLogs"]
        snapshot.assert_match(compute_logs)

    def test_compute_logs_subscription_graphql(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "spew_job")
        payload = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        run_id = payload["run"]["runId"]
        logs = graphql_context.instance.all_logs(run_id, of_type=DagsterEventType.LOGS_CAPTURED)
        assert len(logs) == 1
        entry = logs[0]
        file_key = entry.dagster_event.logs_captured_data.file_key

        results = execute_dagster_graphql_subscription(
            graphql_context,
            COMPUTE_LOGS_SUBSCRIPTION,
            variables={
                "runId": run_id,
                "stepKey": file_key,
                "ioType": "STDOUT",
                "cursor": "0",
            },
        )

        assert len(results) == 1
        result = results[0]
        assert result.data["computeLogs"]["data"] == "HELLO WORLD\n"
        snapshot.assert_match([result.data])
