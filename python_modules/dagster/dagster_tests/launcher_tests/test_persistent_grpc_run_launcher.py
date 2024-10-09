import sys
import time

import pytest
from dagster import _seven, file_relative_path
from dagster._core.errors import DagsterLaunchFailedError
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import GRPC_INFO_TAG
from dagster._core.test_utils import instance_for_test, poll_for_finished_run, poll_for_step_start
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import GrpcServerTarget, PythonFileTarget
from dagster._grpc.server import GrpcServerProcess
from dagster._utils import find_free_port
from dagster._utils.merger import merge_dicts

from dagster_tests.launcher_tests.test_default_run_launcher import (
    math_diamond,
    sleepy_job,
    slow_job,
)


def test_run_always_finishes():
    with instance_for_test() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="nope",
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        )
        with GrpcServerProcess(
            instance_ref=instance.get_ref(),
            loadable_target_origin=loadable_target_origin,
            max_workers=4,
            wait_on_exit=False,
        ) as server_process:
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

                remote_job = (
                    workspace.get_code_location("test")
                    .get_repository("nope")
                    .get_full_job("slow_job")
                )

                dagster_run = instance.create_run_for_job(
                    job_def=slow_job,
                    run_config=None,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                )
                run_id = dagster_run.run_id

                assert instance.get_run_by_id(run_id).status == DagsterRunStatus.NOT_STARTED

                instance.launch_run(run_id=run_id, workspace=workspace)

        # Server process now receives shutdown event, run has not finished yet
        dagster_run = instance.get_run_by_id(run_id)
        assert not dagster_run.is_finished
        assert server_process.server_process.poll() is None

        # Server should wait until run finishes, then shutdown
        dagster_run = poll_for_finished_run(instance, run_id)
        assert dagster_run.status == DagsterRunStatus.SUCCESS

        start_time = time.time()
        while server_process.server_process.poll() is None:
            time.sleep(0.05)
            # Verify server process cleans up eventually
            assert time.time() - start_time < 5

        server_process.wait()


def test_run_from_pending_repository():
    run_id = make_new_run_id()
    with instance_for_test() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="pending",
            python_file=file_relative_path(__file__, "pending_repository.py"),
        )
        with GrpcServerProcess(
            instance_ref=instance.get_ref(),
            loadable_target_origin=loadable_target_origin,
            max_workers=4,
            wait_on_exit=False,
        ) as server_process:
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

                code_location = workspace.get_code_location("test2")
                remote_job = code_location.get_repository("pending").get_full_job(
                    "my_cool_asset_job"
                )
                external_execution_plan = code_location.get_external_execution_plan(
                    remote_job=remote_job,
                    run_config={},
                    step_keys_to_execute=None,
                    known_state=None,
                )

                call_counts = instance.run_storage.get_cursor_values(
                    {
                        "compute_cacheable_data_called_a",
                        "compute_cacheable_data_called_b",
                        "get_definitions_called_a",
                        "get_definitions_called_b",
                    }
                )
                assert call_counts.get("compute_cacheable_data_called_a") == "1"
                assert call_counts.get("compute_cacheable_data_called_b") == "1"
                assert call_counts.get("get_definitions_called_a") == "1"
                assert call_counts.get("get_definitions_called_b") == "1"

                # using create run here because we don't have easy access to the underlying
                # pipeline definition
                dagster_run = instance.create_run(
                    job_name="my_cool_asset_job",
                    run_id=run_id,
                    run_config=None,
                    resolved_op_selection=None,
                    step_keys_to_execute=None,
                    status=None,
                    tags=None,
                    root_run_id=None,
                    parent_run_id=None,
                    job_snapshot=remote_job.job_snapshot,
                    execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
                    parent_job_snapshot=remote_job.parent_job_snapshot,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                    asset_selection=None,
                    op_selection=None,
                    asset_check_selection=None,
                    asset_graph=code_location.get_repository(
                        remote_job.repository_handle.repository_name
                    ).asset_graph,
                )

                run_id = dagster_run.run_id

                assert instance.get_run_by_id(run_id).status == DagsterRunStatus.NOT_STARTED

                instance.launch_run(run_id=run_id, workspace=workspace)

        # Server process now receives shutdown event, run has not finished yet
        dagster_run = instance.get_run_by_id(run_id)
        assert not dagster_run.is_finished
        assert server_process.server_process.poll() is None

        # Server should wait until run finishes, then shutdown
        dagster_run = poll_for_finished_run(instance, run_id)
        assert dagster_run.status == DagsterRunStatus.SUCCESS

        start_time = time.time()
        while server_process.server_process.poll() is None:
            time.sleep(0.05)
            # Verify server process cleans up eventually
            assert time.time() - start_time < 5

        server_process.wait()

        # should only have had to get the metadata once for each cacheable asset def
        call_counts = instance.run_storage.get_cursor_values(
            {
                "compute_cacheable_data_called_a",
                "compute_cacheable_data_called_b",
                "get_definitions_called_a",
                "get_definitions_called_b",
            }
        )
        assert call_counts.get("compute_cacheable_data_called_a") == "1"
        assert call_counts.get("compute_cacheable_data_called_b") == "1"
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

            remote_job = (
                workspace.get_code_location("test")
                .get_repository("nope")
                .get_full_job("sleepy_job")
            )

            dagster_run = instance.create_run_for_job(
                job_def=sleepy_job,
                run_config=None,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )

            instance.launch_run(dagster_run.run_id, workspace)

            poll_for_step_start(instance, dagster_run.run_id)

            code_location = workspace.get_code_location("test")
            # Tell the server to shut down once executions finish
            code_location.grpc_server_registry.get_grpc_endpoint(
                code_location.origin
            ).create_client().shutdown_server()

            remote_job = (
                workspace.get_code_location("test")
                .get_repository("nope")
                .get_full_job("math_diamond")
            )

            doomed_to_fail_dagster_run = instance.create_run_for_job(
                job_def=math_diamond,
                run_config=None,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )

            with pytest.raises(DagsterLaunchFailedError):
                instance.launch_run(doomed_to_fail_dagster_run.run_id, workspace)

            launcher = instance.run_launcher

            # Can terminate the run even after the shutdown event has been received
            assert launcher.terminate(dagster_run.run_id)


def test_server_down():
    with instance_for_test() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="nope",
            python_file=file_relative_path(__file__, "test_default_run_launcher.py"),
        )

        with GrpcServerProcess(
            instance_ref=instance.get_ref(),
            loadable_target_origin=loadable_target_origin,
            max_workers=4,
            force_port=True,
            wait_on_exit=True,
        ) as server_process:
            api_client = server_process.create_client()
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

                remote_job = (
                    workspace.get_code_location("test")
                    .get_repository("nope")
                    .get_full_job("sleepy_job")
                )

                dagster_run = instance.create_run_for_job(
                    job_def=sleepy_job,
                    run_config=None,
                    remote_job_origin=remote_job.get_remote_origin(),
                    job_code_origin=remote_job.get_python_origin(),
                )

                instance.launch_run(dagster_run.run_id, workspace)

                poll_for_step_start(instance, dagster_run.run_id)

                launcher = instance.run_launcher

                original_run_tags = instance.get_run_by_id(dagster_run.run_id).tags[GRPC_INFO_TAG]

                # Replace run tags with an invalid port
                instance.add_run_tags(
                    dagster_run.run_id,
                    {
                        GRPC_INFO_TAG: _seven.json.dumps(
                            merge_dicts({"host": "localhost"}, {"port": find_free_port()})
                        )
                    },
                )

                instance.add_run_tags(
                    dagster_run.run_id,
                    {
                        GRPC_INFO_TAG: original_run_tags,
                    },
                )

                assert launcher.terminate(dagster_run.run_id)
