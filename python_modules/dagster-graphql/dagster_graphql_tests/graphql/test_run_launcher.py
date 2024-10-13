from typing import Any

from dagster._core.test_utils import wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_job_selector

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)

RUN_QUERY = """
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on Run {
      status
      stats {
        ... on RunStatsSnapshot {
          stepsSucceeded
        }
      }
      startTime
      endTime
    }
  }
}
"""


BaseTestSuite: Any = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_executing_variants()
)


class TestBasicLaunch(BaseTestSuite):
    def test_run_launcher(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )

        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert result.data["launchPipelineExecution"]["run"]["status"] == "STARTING"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        wait_for_runs_to_finish(graphql_context.instance)

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "Run"
        assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"

    def test_run_launcher_subset(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "more_complicated_config", ["noop_op"])
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                }
            },
        )

        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
        assert result.data["launchPipelineExecution"]["run"]["status"] == "STARTING"

        run_id = result.data["launchPipelineExecution"]["run"]["runId"]

        wait_for_runs_to_finish(graphql_context.instance)

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "Run"
        assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"
        assert result.data["pipelineRunOrError"]["stats"]["stepsSucceeded"] == 1


LaunchFailTestSuite: Any = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_non_launchable_variants()
)


class TestFailedLaunch(LaunchFailTestSuite):
    def test_launch_failure(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={"executionParams": {"selector": selector, "mode": "default"}},
        )
        assert result.data["launchPipelineExecution"]["__typename"] != "LaunchRunSuccess"

        # fetch the most recent run, which should be this one that just failed to launch
        run = graphql_context.instance.get_runs(limit=1)[0]

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": run.run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "Run"
        assert result.data["pipelineRunOrError"]["status"] == "FAILURE"
        assert result.data["pipelineRunOrError"]["startTime"]
        assert result.data["pipelineRunOrError"]["endTime"]
