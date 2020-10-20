from dagster_graphql.client.query import LAUNCH_TRIGGERED_EXECUTION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository_selector

from .graphql_context_test_suite import OutOfProcessExecutingGraphQLContextTestMatrix


class TestTriggerRuns(OutOfProcessExecutingGraphQLContextTestMatrix):
    def test_get_partition_runs(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_TRIGGERED_EXECUTION,
            variables={
                "triggerSelector": {
                    "repositoryName": repository_selector["repositoryName"],
                    "repositoryLocationName": repository_selector["repositoryLocationName"],
                    "jobName": "job_no_config",
                }
            },
        )
        assert not result.errors
        assert result.data["triggerExecution"]["__typename"] == "TriggerExecutionSuccess"
        assert len(result.data["triggerExecution"]["launchedRunIds"]) == 1
