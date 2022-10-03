import sys
import time

import pytest
from dagster_tests.core_tests.launcher_tests.test_default_run_launcher import (
    math_diamond,
    sleepy_pipeline,
    slow_pipeline,
)

from dagster import _seven, file_relative_path
from dagster._core.errors import DagsterLaunchFailedError
from dagster._core.storage.pipeline_run import PipelineRunStatus
from dagster._core.storage.tags import GRPC_INFO_TAG
from dagster._core.test_utils import instance_for_test, poll_for_finished_run, poll_for_step_start
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import GrpcServerTarget, PythonFileTarget
from dagster._grpc.server import GrpcServerProcess
from dagster._utils import find_free_port, merge_dicts


def test_run_always_finishes():  # pylint: disable=redefined-outer-name
    with instance_for_test() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="nope",
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        )
        server_process = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin, max_workers=4
        )
        with server_process.create_ephemeral_client():  # Shuts down when leaves context
            with WorkspaceProcessContext(
                instance,
                GrpcServerTarget(
                    host="localhost",
                    socket=server_process.socket,
                    port=server_process.port,
                    location_name="test",
                ),
            ) as workspace_process_context:
                workspace = workspace_process_context.create_request_context()

                external_pipeline = (
                    workspace.get_repository_location("test")
                    .get_repository("nope")
                    .get_full_external_job("slow_pipeline")
                )

                pipeline_run = instance.create_run_for_pipeline(
                    pipeline_def=slow_pipeline,
                    run_config=None,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )
                run_id = pipeline_run.run_id

                assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

                instance.launch_run(run_id=run_id, workspace=workspace)

        # Server process now receives shutdown event, run has not finished yet
        pipeline_run = instance.get_run_by_id(run_id)
        assert not pipeline_run.is_finished
        assert server_process.server_process.poll() is None

        # Server should wait until run finishes, then shutdown
        pipeline_run = poll_for_finished_run(instance, run_id)
        assert pipeline_run.status == PipelineRunStatus.SUCCESS

        start_time = time.time()
        while server_process.server_process.poll() is None:
            time.sleep(0.05)
            # Verify server process cleans up eventually
            assert time.time() - start_time < 5

        server_process.wait()


def test_run_from_pending_repository():
    with instance_for_test() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="pending",
            python_file=file_relative_path(__file__, "pending_repository.py"),
        )
        server_process = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin, max_workers=4
        )
        with server_process.create_ephemeral_client():  # Shuts down when leaves context
            with WorkspaceProcessContext(
                instance,
                GrpcServerTarget(
                    host="localhost",
                    socket=server_process.socket,
                    port=server_process.port,
                    location_name="test2",
                ),
            ) as workspace_process_context:
                workspace = workspace_process_context.create_request_context()

                repo_location = workspace.get_repository_location("test2")
                external_pipeline = repo_location.get_repository("pending").get_full_external_job(
                    "my_cool_asset_job"
                )
                external_execution_plan = repo_location.get_external_execution_plan(
                    external_pipeline=external_pipeline,
                    run_config={},
                    mode="default",
                    step_keys_to_execute=None,
                    known_state=None,
                )

                call_counts = instance.run_storage.kvs_get(
                    {
                        "get_cached_data_called_a",
                        "get_cached_data_called_b",
                        "get_definitions_called_a",
                        "get_definitions_called_b",
                    }
                )
                assert call_counts.get("get_cached_data_called_a") == "1"
                assert call_counts.get("get_cached_data_called_b") == "1"
                assert call_counts.get("get_definitions_called_a") == "1"
                assert call_counts.get("get_definitions_called_b") == "1"

                # using create run here because we don't have easy access to the underlying
                # pipeline definition
                pipeline_run = instance.create_run(
                    pipeline_name="my_cool_asset_job",
                    run_id="xyzabc",
                    run_config=None,
                    mode="default",
                    solids_to_execute=None,
                    step_keys_to_execute=None,
                    status=None,
                    tags=None,
                    root_run_id=None,
                    parent_run_id=None,
                    pipeline_snapshot=external_pipeline.pipeline_snapshot,
                    execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
                    parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )

                run_id = pipeline_run.run_id

                assert instance.get_run_by_id(run_id).status == PipelineRunStatus.NOT_STARTED

                instance.launch_run(run_id=run_id, workspace=workspace)

        # Server process now receives shutdown event, run has not finished yet
        pipeline_run = instance.get_run_by_id(run_id)
        assert not pipeline_run.is_finished
        assert server_process.server_process.poll() is None

        # Server should wait until run finishes, then shutdown
        pipeline_run = poll_for_finished_run(instance, run_id)
        assert pipeline_run.status == PipelineRunStatus.SUCCESS

        start_time = time.time()
        while server_process.server_process.poll() is None:
            time.sleep(0.05)
            # Verify server process cleans up eventually
            assert time.time() - start_time < 5

        server_process.wait()

        # should only have had to get the metadata once for each cacheable asset def
        call_counts = instance.run_storage.kvs_get(
            {
                "get_cached_data_called_a",
                "get_cached_data_called_b",
                "get_definitions_called_a",
                "get_definitions_called_b",
            }
        )
        assert call_counts.get("get_cached_data_called_a") == "1"
        assert call_counts.get("get_cached_data_called_b") == "1"
        # once at initial load time, once inside the run launch process, once for each (3) subprocess
        # upper bound of 5 here because race conditions result in lower count sometimes
        assert int(call_counts.get("get_definitions_called_a")) < 6
        assert int(call_counts.get("get_definitions_called_b")) < 6


def test_terminate_after_shutdown():
    with instance_for_test() as instance:
        with WorkspaceProcessContext(
            instance,
            PythonFileTarget(
                python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
                attribute="nope",
                working_directory=None,
                location_name="test",
            ),
        ) as workspace_process_context:
            workspace = workspace_process_context.create_request_context()

            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_job("sleepy_pipeline")
            )

            pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=sleepy_pipeline,
                run_config=None,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            instance.launch_run(pipeline_run.run_id, workspace)

            poll_for_step_start(instance, pipeline_run.run_id)

            repository_location = workspace.get_repository_location("test")
            # Tell the server to shut down once executions finish
            repository_location.grpc_server_registry.get_grpc_endpoint(
                repository_location.origin
            ).create_client().shutdown_server()

            external_pipeline = (
                workspace.get_repository_location("test")
                .get_repository("nope")
                .get_full_external_job("math_diamond")
            )

            doomed_to_fail_pipeline_run = instance.create_run_for_pipeline(
                pipeline_def=math_diamond,
                run_config=None,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
            )

            with pytest.raises(DagsterLaunchFailedError):
                instance.launch_run(doomed_to_fail_pipeline_run.run_id, workspace)

            launcher = instance.run_launcher

            # Can terminate the run even after the shutdown event has been received
            assert launcher.terminate(pipeline_run.run_id)


def test_server_down():
    with instance_for_test() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="nope",
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        )

        server_process = GrpcServerProcess(
            loadable_target_origin=loadable_target_origin, max_workers=4, force_port=True
        )

        with server_process.create_ephemeral_client() as api_client:
            with WorkspaceProcessContext(
                instance,
                GrpcServerTarget(
                    location_name="test",
                    port=api_client.port,
                    socket=api_client.socket,
                    host=api_client.host,
                ),
            ) as workspace_process_context:
                workspace = workspace_process_context.create_request_context()

                external_pipeline = (
                    workspace.get_repository_location("test")
                    .get_repository("nope")
                    .get_full_external_job("sleepy_pipeline")
                )

                pipeline_run = instance.create_run_for_pipeline(
                    pipeline_def=sleepy_pipeline,
                    run_config=None,
                    external_pipeline_origin=external_pipeline.get_external_origin(),
                    pipeline_code_origin=external_pipeline.get_python_origin(),
                )

                instance.launch_run(pipeline_run.run_id, workspace)

                poll_for_step_start(instance, pipeline_run.run_id)

                launcher = instance.run_launcher

                original_run_tags = instance.get_run_by_id(pipeline_run.run_id).tags[GRPC_INFO_TAG]

                # Replace run tags with an invalid port
                instance.add_run_tags(
                    pipeline_run.run_id,
                    {
                        GRPC_INFO_TAG: _seven.json.dumps(
                            merge_dicts({"host": "localhost"}, {"port": find_free_port()})
                        )
                    },
                )

                instance.add_run_tags(
                    pipeline_run.run_id,
                    {
                        GRPC_INFO_TAG: original_run_tags,
                    },
                )

                assert launcher.terminate(pipeline_run.run_id)

        server_process.wait()
