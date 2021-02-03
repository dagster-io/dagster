import os
import time

from dagster import execute_pipeline
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.grpc.types import CancelExecutionRequest
from dagster.utils import file_relative_path, safe_tempfile_path
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

RUN_CANCELLATION_QUERY = """
mutation($runId: String!, $terminatePolicy: TerminatePipelinePolicy) {
  terminatePipelineExecution(runId: $runId, terminatePolicy:$terminatePolicy){
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
    ... on PythonError {
      message
      stack
    }
  }
}
"""


class TestQueuedRunTermination(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.sqlite_with_queued_run_coordinator_managed_grpc_env()
        ]
    )
):
    def test_cancel_queued_run(self, graphql_context):
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

            assert graphql_context.instance.get_run_by_id(run_id).status == PipelineRunStatus.QUEUED

            result = execute_dagster_graphql(
                graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": run_id}
            )
            assert (
                result.data["terminatePipelineExecution"]["__typename"]
                == "TerminatePipelineExecutionSuccess"
            )

    def test_force_cancel_queued_run(self, graphql_context):
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

            assert graphql_context.instance.get_run_by_id(run_id).status == PipelineRunStatus.QUEUED

            result = execute_dagster_graphql(
                graphql_context,
                RUN_CANCELLATION_QUERY,
                variables={"runId": run_id, "terminatePolicy": "MARK_AS_CANCELED_IMMEDIATELY"},
            )
            assert (
                result.data["terminatePipelineExecution"]["__typename"]
                == "TerminatePipelineExecutionSuccess"
            )


class TestRunVariantTermination(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env()]
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

            result = execute_dagster_graphql(
                graphql_context,
                RUN_CANCELLATION_QUERY,
                variables={"runId": run_id, "terminatePolicy": "MARK_AS_CANCELED_IMMEDIATELY"},
            )

            assert (
                result.data["terminatePipelineExecution"]["__typename"]
                == "TerminatePipelineExecutionSuccess"
            )

            assert result.data["terminatePipelineExecution"]["run"]["runId"] == run_id

            graphql_context.instance.run_launcher.terminate = old_terminate

            # Clean up the run process on the gRPC server
            handles = (
                graphql_context.instance.run_launcher._run_id_to_repository_location_handle_cache.values()  # pylint: disable=protected-access
            )
            for repository_location_handle in handles:
                repository_location_handle.client.cancel_execution(
                    CancelExecutionRequest(run_id=run_id)
                )

    def test_run_finished(self, graphql_context):
        instance = graphql_context.instance

        pipeline = ReconstructableRepository.for_file(
            file_relative_path(__file__, "setup.py"),
            "test_repo",
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
            "could not be terminated due to having status SUCCESS."
            in result.data["terminatePipelineExecution"]["message"]
        )

        # Still fails even if you change the terminate policy to fail immediately
        result = execute_dagster_graphql(
            graphql_context,
            RUN_CANCELLATION_QUERY,
            variables={
                "runId": pipeline_result.run_id,
                "terminatePolicy": "MARK_AS_CANCELED_IMMEDIATELY",
            },
        )

        assert (
            result.data["terminatePipelineExecution"]["__typename"]
            == "TerminatePipelineExecutionFailure"
        )
        assert (
            "could not be terminated due to having status SUCCESS."
            in result.data["terminatePipelineExecution"]["message"]
        )
