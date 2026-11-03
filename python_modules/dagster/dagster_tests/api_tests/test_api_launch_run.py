import threading
from unittest.mock import MagicMock

import dagster as dg
from dagster._core.remote_representation.handle import JobHandle
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import create_run_for_test, poll_for_event, poll_for_finished_run
from dagster._grpc.__generated__ import dagster_api_pb2
from dagster._grpc.impl import IPCErrorMessage
from dagster._grpc.server import DagsterApiServer, ExecuteExternalJobArgs
from dagster._grpc.types import StartRunResult
from dagster._serdes import serialize_value
from dagster._utils.error import SerializableErrorInfo

from dagster_tests.api_tests.utils import get_bar_repo_code_location


def _check_event_log_contains(event_log, expected_type_and_message):
    types_and_messages = [
        (e.dagster_event.event_type_value, e.message) for e in event_log if e.is_dagster_event
    ]
    for expected_event_type, expected_message_fragment in expected_type_and_message:
        assert any(
            event_type == expected_event_type and expected_message_fragment in message
            for event_type, message in types_and_messages
        )


def test_start_run_preserves_ipc_error_when_cleanup_wins_race():
    with dg.instance_for_test() as instance:
        with get_bar_repo_code_location(instance) as code_location:
            job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
            run_id = create_run_for_test(instance, "foo").run_id
            execute_args = ExecuteExternalJobArgs(
                job_origin=job_handle.get_remote_origin(),
                run_id=run_id,
                instance_ref=instance.get_ref(),
            )
            request = dagster_api_pb2.StartRunRequest(
                serialized_execute_run_args=serialize_value(execute_args)
            )
            original_error = SerializableErrorInfo(
                message="original IPC exception", stack=[], cls_name="OriginalError"
            )

            event_queue = MagicMock()
            execution_process = MagicMock()
            termination_event = MagicMock()
            multiprocessing_context = MagicMock()
            multiprocessing_context.Queue.return_value = event_queue
            multiprocessing_context.Event.return_value = termination_event
            multiprocessing_context.Process.return_value = execution_process

            reconstructable_repository = MagicMock()
            loaded_repositories = MagicMock()
            loaded_repositories.reconstructables_by_name = {
                execute_args.job_origin.repository_origin.repository_name: (
                    reconstructable_repository
                )
            }

            server = DagsterApiServer.__new__(DagsterApiServer)
            server._shutdown_once_executions_finish_event = threading.Event()  # noqa: SLF001
            server._loaded_repositories = loaded_repositories  # noqa: SLF001
            server._mp_ctx = multiprocessing_context  # noqa: SLF001
            server._execution_lock = threading.Lock()  # noqa: SLF001
            server._executions = {}  # noqa: SLF001
            server._termination_events = {}  # noqa: SLF001
            server._termination_times = {}  # noqa: SLF001

            def cleanup_then_return_ipc_error():
                with server._execution_lock:  # noqa: SLF001
                    server._clear_run(run_id)  # noqa: SLF001
                return IPCErrorMessage(
                    serializable_error_info=original_error,
                    message="startup failed",
                )

            event_queue.get_nowait.side_effect = cleanup_then_return_ipc_error

            reply = server.StartRun(request, MagicMock())
            result = dg.deserialize_value(reply.serialized_start_run_result, StartRunResult)

            assert not result.success
            assert result.message == "startup failed"
            assert result.serializable_error_info == original_error
            assert server._executions == {}  # noqa: SLF001
            assert server._termination_events == {}  # noqa: SLF001


def test_launch_run_with_unloadable_job_grpc():
    with dg.instance_for_test() as instance:
        with get_bar_repo_code_location(instance) as code_location:
            job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
            api_client = code_location.client

            run = create_run_for_test(instance, "foo")
            run_id = run.run_id

            original_origin = job_handle.get_remote_origin()

            # point the api to a pipeline that cannot be loaded
            res = dg.deserialize_value(
                api_client.start_run(
                    ExecuteExternalJobArgs(
                        job_origin=original_origin._replace(job_name="i_am_fake_pipeline"),
                        run_id=run_id,
                        instance_ref=instance.get_ref(),
                    )
                ),
                StartRunResult,
            )

            assert res.success
            finished_run = poll_for_finished_run(instance, run_id)

            assert finished_run
            assert finished_run.run_id == run_id
            assert finished_run.status == DagsterRunStatus.FAILURE

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for run exited"
            )
            event_records = instance.all_logs(run_id)
            _check_event_log_contains(
                event_records,
                [
                    ("ENGINE_EVENT", "Started process for run"),
                    ("ENGINE_EVENT", "Could not load job definition"),
                    (
                        "PIPELINE_FAILURE",
                        "This run has been marked as failed from outside the execution context",
                    ),
                    ("ENGINE_EVENT", "Process for run exited"),
                ],
            )


def test_launch_run_grpc():
    with dg.instance_for_test() as instance:
        with get_bar_repo_code_location(instance) as code_location:
            job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
            api_client = code_location.client

            run = create_run_for_test(instance, "foo")
            run_id = run.run_id

            res = dg.deserialize_value(
                api_client.start_run(
                    ExecuteExternalJobArgs(
                        job_origin=job_handle.get_remote_origin(),
                        run_id=run_id,
                        instance_ref=instance.get_ref(),
                    )
                ),
                StartRunResult,
            )

            assert res.success
            finished_run = poll_for_finished_run(instance, run_id)

            assert finished_run
            assert finished_run.run_id == run_id
            assert finished_run.status == DagsterRunStatus.SUCCESS

            poll_for_event(
                instance, run_id, event_type="ENGINE_EVENT", message="Process for run exited"
            )
            event_records = instance.all_logs(run_id)
            _check_event_log_contains(
                event_records,
                [
                    ("ENGINE_EVENT", msg)
                    for msg in [
                        "Started process for run",
                        "Executing steps using multiprocess executor",
                        "Multiprocess executor: parent process exiting",
                        "Process for run exited",
                    ]
                ],
            )


def test_launch_unloadable_run_grpc():
    with dg.instance_for_test() as instance:
        with get_bar_repo_code_location(instance) as code_location:
            job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
            api_client = code_location.client

            run = create_run_for_test(instance, "foo")
            run_id = run.run_id

            with dg.instance_for_test() as other_instance:
                res = dg.deserialize_value(
                    api_client.start_run(
                        ExecuteExternalJobArgs(
                            job_origin=job_handle.get_remote_origin(),
                            run_id=run_id,
                            instance_ref=other_instance.get_ref(),
                        )
                    ),
                    StartRunResult,
                )

                assert not res.success
                assert (
                    f"gRPC server could not load run {run_id} in order to execute it. "
                    "Make sure that the gRPC server has access to your run storage."
                    in res.serializable_error_info.message  # ty: ignore[unresolved-attribute]
                )
