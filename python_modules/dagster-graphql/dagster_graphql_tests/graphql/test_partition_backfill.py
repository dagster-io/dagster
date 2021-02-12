import os

from dagster.seven import get_system_temp_directory
from dagster_graphql.client.query import LAUNCH_PARTITION_BACKFILL_MUTATION
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    execute_dagster_graphql_and_finish_runs,
    infer_repository_selector,
)

from .graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    GraphQLContextVariant,
    make_graphql_context_test_suite,
)
from .utils import (
    get_all_logs_for_finished_run_via_subscription,
    step_did_fail,
    step_did_not_run,
    step_did_succeed,
)

PARTITION_PROGRESS_QUERY = """
  query PartitionProgressQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        __typename
        backfillId
        status
        isPersisted
        numRequested
        numTotal
        fromFailure
        reexecutionSteps
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
"""


class TestPartitionBackfill(ExecutingGraphQLContextTestMatrix):
    def test_launch_full_pipeline_backfill(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integer_partition",
                    },
                    "partitionNames": ["2", "3"],
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context, PARTITION_PROGRESS_QUERY, variables={"backfillId": backfill_id}
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["isPersisted"]
        assert result.data["partitionBackfillOrError"]["numRequested"] == 0
        assert result.data["partitionBackfillOrError"]["numTotal"] == 2

    def test_launch_full_pipeline_backfill_synchronous(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        result = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": {
                        "repositorySelector": repository_selector,
                        "partitionSetName": "integer_partition",
                    },
                    "partitionNames": ["2", "3"],
                    "forceSynchronousSubmission": True,
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2

    def test_launch_partial_backfill(self, graphql_context):
        # execute a full pipeline, without the failure environment variable
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_integer_partition",
        }

        # reexecute a partial pipeline
        partial_steps = ["after_failure"]
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                    "reexecutionSteps": partial_steps,
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context, PARTITION_PROGRESS_QUERY, variables={"backfillId": backfill_id}
        )

        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["isPersisted"]
        assert result.data["partitionBackfillOrError"]["numRequested"] == 0
        assert result.data["partitionBackfillOrError"]["numTotal"] == 2
        assert result.data["partitionBackfillOrError"]["reexecutionSteps"] == ["after_failure"]

    def test_launch_partial_backfill_synchronous(self, graphql_context):
        # execute a full pipeline, without the failure environment variable
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_integer_partition",
        }

        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                    "forceSynchronousSubmission": True,
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2
        for run_id in result.data["launchPartitionBackfill"]["launchedRunIds"]:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                "pipelineRunLogs"
            ]["messages"]
            assert step_did_succeed(logs, "always_succeed")
            assert step_did_succeed(logs, "conditionally_fail")
            assert step_did_succeed(logs, "after_failure")

        # reexecute a partial pipeline
        partial_steps = ["after_failure"]
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                    "reexecutionSteps": partial_steps,
                    "forceSynchronousSubmission": True,
                }
            },
        )
        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2
        for run_id in result.data["launchPartitionBackfill"]["launchedRunIds"]:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                "pipelineRunLogs"
            ]["messages"]
            assert step_did_not_run(logs, "always_succeed")
            assert step_did_not_run(logs, "conditionally_fail")
            assert step_did_succeed(logs, "after_failure")


class TestLaunchBackfillFromFailure(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env(),
        ]
    )
):
    def test_launch_from_failure(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_integer_partition",
        }

        # trigger failure in the conditionally_fail solid

        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PARTITION_BACKFILL_MUTATION,
                    variables={
                        "backfillParams": {
                            "selector": partition_set_selector,
                            "partitionNames": ["2", "3"],
                        }
                    },
                )
        finally:
            os.remove(output_file)

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"

        # re-execute from failure (without the failure file)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                    "fromFailure": True,
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        backfill_id = result.data["launchPartitionBackfill"]["backfillId"]

        result = execute_dagster_graphql(
            graphql_context, PARTITION_PROGRESS_QUERY, variables={"backfillId": backfill_id}
        )
        assert not result.errors
        assert result.data
        assert result.data["partitionBackfillOrError"]["__typename"] == "PartitionBackfill"
        assert result.data["partitionBackfillOrError"]["status"] == "REQUESTED"
        assert result.data["partitionBackfillOrError"]["isPersisted"]
        assert result.data["partitionBackfillOrError"]["numRequested"] == 0
        assert result.data["partitionBackfillOrError"]["numTotal"] == 2
        assert result.data["partitionBackfillOrError"]["fromFailure"]

    def test_launch_from_failure_synchronous(self, graphql_context):
        repository_selector = infer_repository_selector(graphql_context)
        partition_set_selector = {
            "repositorySelector": repository_selector,
            "partitionSetName": "chained_integer_partition",
        }

        # trigger failure in the conditionally_fail solid

        output_file = os.path.join(
            get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail"
        )
        try:
            with open(output_file, "w"):
                result = execute_dagster_graphql_and_finish_runs(
                    graphql_context,
                    LAUNCH_PARTITION_BACKFILL_MUTATION,
                    variables={
                        "backfillParams": {
                            "selector": partition_set_selector,
                            "partitionNames": ["2", "3"],
                            "forceSynchronousSubmission": True,
                        }
                    },
                )
        finally:
            os.remove(output_file)

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2
        for run_id in result.data["launchPartitionBackfill"]["launchedRunIds"]:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                "pipelineRunLogs"
            ]["messages"]
            assert step_did_succeed(logs, "always_succeed")
            assert step_did_fail(logs, "conditionally_fail")
            assert step_did_not_run(logs, "after_failure")

        # re-execute from failure (without the failure file)
        result = execute_dagster_graphql_and_finish_runs(
            graphql_context,
            LAUNCH_PARTITION_BACKFILL_MUTATION,
            variables={
                "backfillParams": {
                    "selector": partition_set_selector,
                    "partitionNames": ["2", "3"],
                    "fromFailure": True,
                    "forceSynchronousSubmission": True,
                }
            },
        )

        assert not result.errors
        assert result.data
        assert result.data["launchPartitionBackfill"]["__typename"] == "PartitionBackfillSuccess"
        assert len(result.data["launchPartitionBackfill"]["launchedRunIds"]) == 2
        for run_id in result.data["launchPartitionBackfill"]["launchedRunIds"]:
            logs = get_all_logs_for_finished_run_via_subscription(graphql_context, run_id)[
                "pipelineRunLogs"
            ]["messages"]
            assert step_did_not_run(logs, "always_succeed")
            assert step_did_succeed(logs, "conditionally_fail")
            assert step_did_succeed(logs, "after_failure")
