from dagster.core.utils import make_new_run_id
from dagster_graphql.client.query import (
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
    LAUNCH_PIPELINE_REEXECUTION_MUTATION,
)
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import ExecutingGraphQLContextTestMatrix
from .setup import csv_hello_world_solids_config, csv_hello_world_solids_config_fs_storage

RUN_QUERY = """
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on PipelineRun {
        status
      }
    }
  }
"""


class TestReexecution(ExecutingGraphQLContextTestMatrix):
    def test_full_pipeline_reexecution_fs_storage(self, graphql_context, snapshot):
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
        run_id = make_new_run_id()
        result_one = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config_fs_storage(),
                    "executionMetadata": {"runId": run_id},
                    "mode": "default",
                }
            },
        )

        assert (
            result_one.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
        )

        result_one.data["launchPipelineExecution"]["run"]["runId"] = "<runId dummy value>"
        result_one.data["launchPipelineExecution"]["run"][
            "runConfigYaml"
        ] = "<runConfigYaml dummy value>"

        snapshot.assert_match(result_one.data)

        # reexecution
        new_run_id = make_new_run_id()

        result_two = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config_fs_storage(),
                    "executionMetadata": {
                        "runId": new_run_id,
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                    },
                    "mode": "default",
                }
            },
        )

        query_result = result_two.data["launchPipelineReexecution"]
        assert query_result["__typename"] == "LaunchPipelineRunSuccess"
        assert query_result["run"]["rootRunId"] == run_id
        assert query_result["run"]["parentRunId"] == run_id

    def test_full_pipeline_reexecution_in_memory_storage(self, graphql_context, snapshot):
        run_id = make_new_run_id()
        selector = infer_pipeline_selector(graphql_context, "csv_hello_world")
        result_one = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "executionMetadata": {"runId": run_id},
                    "mode": "default",
                }
            },
        )

        assert (
            result_one.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
        )

        result_one.data["launchPipelineExecution"]["run"]["runId"] = "<runId dummy value>"
        result_one.data["launchPipelineExecution"]["run"][
            "runConfigYaml"
        ] = "<runConfigYaml dummy value>"

        snapshot.assert_match(result_one.data)

        # reexecution
        new_run_id = make_new_run_id()

        result_two = execute_dagster_graphql(
            graphql_context,
            LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": csv_hello_world_solids_config(),
                    "executionMetadata": {
                        "runId": new_run_id,
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                    },
                    "mode": "default",
                }
            },
        )

        query_result = result_two.data["launchPipelineReexecution"]
        assert query_result["__typename"] == "LaunchPipelineRunSuccess"
        assert query_result["run"]["rootRunId"] == run_id
        assert query_result["run"]["parentRunId"] == run_id

    def test_pipeline_reexecution_successful_launch(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "no_config_pipeline")
        run_id = make_new_run_id()
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": {"intermediate_storage": {"filesystem": {}}},
                    "executionMetadata": {"runId": run_id},
                    "mode": "default",
                }
            },
        )

        assert result.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
        assert result.data["launchPipelineExecution"]["run"]["status"] == "STARTING"

        graphql_context.instance.run_launcher.join()

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "PipelineRun"
        assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"

        # reexecution
        new_run_id = make_new_run_id()
        result = execute_dagster_graphql(
            context=graphql_context,
            query=LAUNCH_PIPELINE_REEXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": {"intermediate_storage": {"filesystem": {}}},
                    "executionMetadata": {
                        "runId": new_run_id,
                        "rootRunId": run_id,
                        "parentRunId": run_id,
                    },
                    "mode": "default",
                }
            },
        )
        assert result.data["launchPipelineReexecution"]["__typename"] == "LaunchPipelineRunSuccess"

        graphql_context.instance.run_launcher.join()

        result = execute_dagster_graphql(
            context=graphql_context, query=RUN_QUERY, variables={"runId": new_run_id}
        )
        assert result.data["pipelineRunOrError"]["__typename"] == "PipelineRun"
        assert result.data["pipelineRunOrError"]["status"] == "SUCCESS"
