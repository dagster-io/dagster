import os
import time

from dagster import execute_pipeline
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.utils import safe_tempfile_path
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

RUN_CANCELLATION_QUERY = """
mutation($runId: String!) {
  terminatePipelineExecution(runId: $runId){
    __typename
    ... on TerminatePipelineExecutionSuccess{
      run {
        runId
      }
    }
    ... on TerminatePipelineExecutionFailure {
      run {
        runId
      }
      message
    }
    ... on PipelineRunNotFoundError {
      runId
    }
  }
}
"""


class TestRunVariantTermination(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.sqlite_with_default_run_launcher_in_process_env()]
    )
):
    def test_basic_termination(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "infinite_loop_pipeline")
        with safe_tempfile_path() as path:
            result = execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_MUTATION,
                variables={
                    "executionParams": {
                        "selector": selector,
                        "mode": "default",
                        "runConfigData": {"solids": {"loop": {"config": {"file": path}}}},
                    }
                },
            )

            assert not result.errors
            assert result.data

            # just test existence
            assert (
                result.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
            )
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            assert run_id

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": run_id}
            )

            assert (
                result.data["terminatePipelineExecution"]["__typename"]
                == "TerminatePipelineExecutionSuccess"
            )

    def test_run_not_found(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": "nope"}
        )
        assert result.data["terminatePipelineExecution"]["__typename"] == "PipelineRunNotFoundError"

    def test_terminate_failed(self, graphql_context):
        selector = infer_pipeline_selector(graphql_context, "infinite_loop_pipeline")
        with safe_tempfile_path() as path:
            old_terminate = graphql_context.instance.run_launcher.terminate
            graphql_context.instance.run_launcher.terminate = lambda _run_id: False
            result = execute_dagster_graphql(
                graphql_context,
                LAUNCH_PIPELINE_EXECUTION_MUTATION,
                variables={
                    "executionParams": {
                        "selector": selector,
                        "mode": "default",
                        "runConfigData": {"solids": {"loop": {"config": {"file": path}}}},
                    }
                },
            )

            assert not result.errors
            assert result.data

            # just test existence
            assert (
                result.data["launchPipelineExecution"]["__typename"] == "LaunchPipelineRunSuccess"
            )
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]
            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": run_id}
            )
            assert (
                result.data["terminatePipelineExecution"]["__typename"]
                == "TerminatePipelineExecutionFailure"
            )
            assert result.data["terminatePipelineExecution"]["message"].startswith(
                "Unable to terminate run"
            )

            graphql_context.instance.run_launcher.terminate = old_terminate

            result = execute_dagster_graphql(
                graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": run_id}
            )

            assert (
                result.data["terminatePipelineExecution"]["__typename"]
                == "TerminatePipelineExecutionSuccess"
            )

    def test_run_finished(self, graphql_context):
        instance = graphql_context.instance
        pipeline = graphql_context.get_repository_location(
            IN_PROCESS_NAME
        ).get_reconstructable_pipeline("noop_pipeline")

        pipeline_result = execute_pipeline(pipeline, instance=instance)
        assert pipeline_result.success
        assert pipeline_result.run_id

        time.sleep(0.05)  # guarantee execution finish

        result = execute_dagster_graphql(
            graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": pipeline_result.run_id}
        )

        assert (
            result.data["terminatePipelineExecution"]["__typename"]
            == "TerminatePipelineExecutionFailure"
        )
        assert (
            "is not in a started state. Current status is SUCCESS"
            in result.data["terminatePipelineExecution"]["message"]
        )
