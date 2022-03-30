import os
import time
from typing import Any

import pytest
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import execute_dagster_graphql, infer_pipeline_selector

from dagster import execute_pipeline
from dagster.core.definitions.reconstruct import ReconstructableRepository
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.grpc.types import CancelExecutionRequest
from dagster.utils import file_relative_path, safe_tempfile_path

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

RUN_CANCELLATION_QUERY = """
mutation($runId: String!, $terminatePolicy: TerminateRunPolicy) {
  terminatePipelineExecution(runId: $runId, terminatePolicy:$terminatePolicy){
    __typename
    ... on TerminateRunSuccess{
      run {
        runId
      }
    }
    ... on TerminateRunFailure {
      run {
        runId
      }
      message
    }
    ... on RunNotFoundError {
      runId
    }
    ... on PythonError {
      message
      stack
    }
  }
}
"""

# Legacy query (once published on docs site), that we should try to continue supporting
BACKCOMPAT_LEGACY_TERMINATE_PIPELINE = """
mutation TerminatePipeline($runId: String!) {
  terminatePipelineExecution(runId: $runId){
    __typename
    ... on TerminatePipelineExecutionSuccess{
      run {
        runId
      }
    }
    ... on TerminatePipelineExecutionFailure {
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


QueuedRunCoordinatorTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[GraphQLContextVariant.sqlite_with_queued_run_coordinator_managed_grpc_env()]
)


class TestQueuedRunTermination(QueuedRunCoordinatorTestSuite):
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
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            assert graphql_context.instance.get_run_by_id(run_id).status == PipelineRunStatus.QUEUED

            result = execute_dagster_graphql(
                graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": run_id}
            )
            assert (
                result.data["terminatePipelineExecution"]["__typename"] == "TerminateRunSuccess"
            ), str(result.data)

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
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            assert graphql_context.instance.get_run_by_id(run_id).status == PipelineRunStatus.QUEUED

            result = execute_dagster_graphql(
                graphql_context,
                RUN_CANCELLATION_QUERY,
                variables={"runId": run_id, "terminatePolicy": "MARK_AS_CANCELED_IMMEDIATELY"},
            )
            assert result.data["terminatePipelineExecution"]["__typename"] == "TerminateRunSuccess"


RunTerminationTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[GraphQLContextVariant.sqlite_with_default_run_launcher_managed_grpc_env()]
)


def _exception_terminate(_run_id):
    raise Exception("FAILED TO TERMINATE")


def _return_fail_terminate(_run_id):
    return False


class TestRunVariantTermination(RunTerminationTestSuite):
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
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            assert run_id

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": run_id}
            )
            assert result.data["terminatePipelineExecution"]["__typename"] == "TerminateRunSuccess"

    def test_force_termination(self, graphql_context):
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
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            assert run_id

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context,
                RUN_CANCELLATION_QUERY,
                variables={"runId": run_id, "terminatePolicy": "MARK_AS_CANCELED_IMMEDIATELY"},
            )
            assert result.data["terminatePipelineExecution"]["__typename"] == "TerminateRunSuccess"

            instance = graphql_context.instance
            run = instance.get_run_by_id(run_id)
            assert run.status == PipelineRunStatus.CANCELED

    def test_run_not_found(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": "nope"}
        )
        assert result.data["terminatePipelineExecution"]["__typename"] == "RunNotFoundError"

    @pytest.mark.parametrize(
        argnames=["new_terminate_method", "terminate_result"],
        argvalues=[
            [
                _return_fail_terminate,
                "TerminateRunFailure",
            ],
            [_exception_terminate, "PythonError"],
        ],
    )
    def test_terminate_failed(self, graphql_context, new_terminate_method, terminate_result):
        selector = infer_pipeline_selector(graphql_context, "infinite_loop_pipeline")
        with safe_tempfile_path() as path:
            old_terminate = graphql_context.instance.run_launcher.terminate
            graphql_context.instance.run_launcher.terminate = new_terminate_method
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
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]
            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context, RUN_CANCELLATION_QUERY, variables={"runId": run_id}
            )
            assert result.data["terminatePipelineExecution"]["__typename"] == terminate_result, str(
                result.data
            )

            result = execute_dagster_graphql(
                graphql_context,
                RUN_CANCELLATION_QUERY,
                variables={"runId": run_id, "terminatePolicy": "MARK_AS_CANCELED_IMMEDIATELY"},
            )

            assert result.data["terminatePipelineExecution"]["__typename"] == "TerminateRunSuccess"

            assert result.data["terminatePipelineExecution"]["run"]["runId"] == run_id

            graphql_context.instance.run_launcher.terminate = old_terminate

            # Clean up the run process on the gRPC server
            repository_location = graphql_context.repository_locations[0]
            repository_location.client.cancel_execution(CancelExecutionRequest(run_id=run_id))

            assert (
                graphql_context.instance.get_run_by_id(run_id).status == PipelineRunStatus.CANCELED
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

        assert result.data["terminatePipelineExecution"]["__typename"] == "TerminateRunFailure"
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

        assert result.data["terminatePipelineExecution"]["__typename"] == "TerminateRunFailure"
        assert (
            "could not be terminated due to having status SUCCESS."
            in result.data["terminatePipelineExecution"]["message"]
        )

    def test_backcompat_termination(self, graphql_context):
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
            assert result.data["launchPipelineExecution"]["__typename"] == "LaunchRunSuccess"
            run_id = result.data["launchPipelineExecution"]["run"]["runId"]

            assert run_id

            # ensure the execution has happened
            while not os.path.exists(path):
                time.sleep(0.1)

            result = execute_dagster_graphql(
                graphql_context, BACKCOMPAT_LEGACY_TERMINATE_PIPELINE, variables={"runId": run_id}
            )
            assert result.data["terminatePipelineExecution"]["run"]["runId"] == run_id
