from typing import Any
from unittest.mock import patch

from dagster._core.test_utils import wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.client.query import (
    LAUNCH_MULTIPLE_RUNS_MUTATION,
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
)
from dagster_graphql.test.utils import GqlResult, execute_dagster_graphql, infer_job_selector

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
LaunchFailTestSuite: Any = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_non_launchable_variants()
)
ReadOnlyTestSuite: Any = make_graphql_context_test_suite(
    context_variants=GraphQLContextVariant.all_readonly_variants()
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

    def test_run_launcher_unauthorized(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")

        with patch.object(graphql_context, "has_permission_for_location", return_value=False):
            with patch.object(graphql_context, "was_permission_checked", return_value=True):
                result = execute_dagster_graphql(
                    context=graphql_context,
                    query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
                    variables={"executionParams": {"selector": selector, "mode": "default"}},
                )
                assert result.data["launchPipelineExecution"]["__typename"] == "UnauthorizedError"


class TestMultipleLaunch(BaseTestSuite):
    def test_multiple_run_launcher_same_job(self, graphql_context: WorkspaceRequestContext):
        selector = infer_job_selector(graphql_context, "no_config_job")

        # test with multiple of the same job
        executionParamsList = [
            {"selector": selector, "mode": "default"},
            {"selector": selector, "mode": "default"},
            {"selector": selector, "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert "launchMultipleRuns" in result.data
        launches = result.data["launchMultipleRuns"]

        assert launches["__typename"] == "LaunchMultipleRunsResult"
        assert "launchMultipleRunsResult" in launches
        results = launches["launchMultipleRunsResult"]

        for result in results:
            assert result["__typename"] == "LaunchRunSuccess"

    def test_multiple_run_launcher_multiple_jobs(self, graphql_context: WorkspaceRequestContext):
        selectors = [
            infer_job_selector(graphql_context, "no_config_job"),
            infer_job_selector(graphql_context, "more_complicated_config", ["noop_op"]),
        ]

        # test with multiple of the same job
        executionParamsList = [
            {"selector": selectors[0], "mode": "default"},
            {"selector": selectors[1], "mode": "default"},
            {"selector": selectors[0], "mode": "default"},
            {"selector": selectors[1], "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert "launchMultipleRuns" in result.data
        launches = result.data["launchMultipleRuns"]

        assert launches["__typename"] == "LaunchMultipleRunsResult"
        assert "launchMultipleRunsResult" in launches
        results = launches["launchMultipleRunsResult"]

        for result in results:
            assert result["__typename"] == "LaunchRunSuccess"

    def test_multiple_launch_failure_unauthorized(self, graphql_context: WorkspaceRequestContext):
        executionParamsList = [
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
        ]

        # mock no permissions
        with patch.object(graphql_context, "has_permission_for_location", return_value=False):
            result = execute_dagster_graphql(
                context=graphql_context,
                query=LAUNCH_MULTIPLE_RUNS_MUTATION,
                variables={"executionParamsList": executionParamsList},
            )
            assert "launchMultipleRuns" in result.data
            result_data = result.data["launchMultipleRuns"]

            assert result_data["__typename"] == "LaunchMultipleRunsResult"
            assert "launchMultipleRunsResult" in result_data

            results = result_data["launchMultipleRunsResult"]

            for result in results:
                assert result["__typename"] == "UnauthorizedError"


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


class TestFailedMultipleLaunch(LaunchFailTestSuite):
    def test_multiple_launch_failure(self, graphql_context: WorkspaceRequestContext):
        executionParamsList = [
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert "launchMultipleRuns" in result.data
        result_data = result.data["launchMultipleRuns"]

        assert result_data["__typename"] == "LaunchMultipleRunsResult"
        results = result_data["launchMultipleRunsResult"]

        assert len(results) == 2

        for run_result in results:
            assert run_result["__typename"] == "PythonError"
            assert run_result["message"].startswith(
                "NotImplementedError: The entire purpose of this is to throw on launch"
            )
            assert run_result["className"] == "NotImplementedError"


class TestFailedMultipleLaunchReadOnly(ReadOnlyTestSuite):
    def test_multiple_launch_failure_readonly(self, graphql_context: WorkspaceRequestContext):
        executionParamsList = [
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
            {"selector": infer_job_selector(graphql_context, "no_config_job"), "mode": "default"},
        ]

        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )
        assert "launchMultipleRuns" in result.data
        result_data = result.data["launchMultipleRuns"]

        assert result_data["__typename"] == "LaunchMultipleRunsResult"
        assert "launchMultipleRunsResult" in result_data

        results = result_data["launchMultipleRunsResult"]

        for result in results:
            assert result["__typename"] == "UnauthorizedError"


class TestSuccessAndFailureMultipleLaunch(BaseTestSuite):
    def test_launch_multiple_runs_success_and_failure(
        self, graphql_context: WorkspaceRequestContext
    ):
        launchSuccessExecutionParams = [
            {
                "selector": {
                    "repositoryLocationName": "test_location",
                    "repositoryName": "test_repo",
                    "pipelineName": "no_config_job",
                    "solidSelection": None,
                    "assetSelection": None,
                    "assetCheckSelection": None,
                },
                "mode": "default",
            },
            {
                "selector": {
                    "repositoryLocationName": "test_location",
                    "repositoryName": "test_repo",
                    "pipelineName": "no_config_job",
                    "solidSelection": None,
                    "assetSelection": None,
                    "assetCheckSelection": None,
                },
                "mode": "default",
            },
        ]

        pipelineNotFoundExecutionParams = [
            {
                "selector": {
                    "repositoryLocationName": "test_location",
                    "repositoryName": "test_dict_repo",
                    "pipelineName": "no_config_job",
                    "solidSelection": None,
                    "assetSelection": None,
                    "assetCheckSelection": None,
                },
                "mode": "default",
            },
            {
                "selector": {
                    "repositoryLocationName": "test_location",
                    "repositoryName": "test_dict_repo",
                    "pipelineName": "no_config_job",
                    "solidSelection": None,
                    "assetSelection": None,
                    "assetCheckSelection": None,
                },
                "mode": "default",
            },
        ]

        executionParamsList = [executionParams for executionParams in launchSuccessExecutionParams]
        executionParamsList.extend(
            [executionParams for executionParams in pipelineNotFoundExecutionParams]
        )

        result: GqlResult = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_MULTIPLE_RUNS_MUTATION,
            variables={"executionParamsList": executionParamsList},
        )

        assert "launchMultipleRuns" in result.data
        result_data = result.data["launchMultipleRuns"]

        assert result_data["__typename"] == "LaunchMultipleRunsResult"
        results = result_data["launchMultipleRunsResult"]

        assert len(results) == 4

        assert results[0]["__typename"] == "LaunchRunSuccess"
        assert results[1]["__typename"] == "LaunchRunSuccess"
        assert results[2]["__typename"] == "PipelineNotFoundError"
        assert results[3]["__typename"] == "PipelineNotFoundError"
