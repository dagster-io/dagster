import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Event, Lock
from unittest.mock import Mock, patch

import dagster._check as check
import grpc
import pytest
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.launcher.base import RunLauncher
from dagster._core.launcher.default_run_launcher import DefaultRunLauncher
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import GRPC_INFO_TAG
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._grpc.__generated__ import dagster_api_pb2
from dagster._grpc.__generated__.dagster_api_pb2_grpc import add_DagsterApiServicer_to_server
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.proxy_server import DagsterProxyApiServicer
from dagster._grpc.server import DagsterApiServer
from dagster._grpc.types import (
    CancelExecutionResult,
    CancelExecutionsRequest,
    CancelExecutionsResult,
)
from dagster._serdes import deserialize_value, serialize_value


@contextmanager
def cancellation_server(run_ids):
    servicer = object.__new__(DagsterApiServer)
    servicer._execution_lock = Lock()
    servicer._executions = dict.fromkeys(run_ids)
    servicer._termination_events = {run_id: Event() for run_id in run_ids}
    servicer._termination_times = {}
    executor = ThreadPoolExecutor(max_workers=2)
    server = grpc.server(executor)
    add_DagsterApiServicer_to_server(servicer, server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    try:
        yield servicer, DagsterGrpcClient(host="127.0.0.1", port=port)
    finally:
        server.stop(grace=None).wait()
        executor.shutdown(wait=True)


def test_native_batch_rpc_preserves_per_worker_results():
    with cancellation_server(["one", "two"]) as (server, client):
        with patch.object(client, "_get_response", wraps=client._get_response) as transport:  # noqa: SLF001
            result = client.cancel_executions(["one", "missing", "two"])
        assert transport.call_count == 1
        assert {run_id: item.success for run_id, item in result.results.items()} == {
            "one": True,
            "missing": False,
            "two": True,
        }
        assert all(signal.is_set() for signal in server._termination_events.values())  # noqa: SLF001
        assert set(server._termination_times) == {"one", "two"}  # noqa: SLF001


class RpcFailure(grpc.RpcError):
    def __init__(self, status):
        self.status = status

    def code(self):
        return self.status


@pytest.mark.parametrize("status", [grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED])
def test_uncertain_transport_error_never_replays(status):
    client = DagsterGrpcClient(host="localhost", port=1234)
    with (
        patch.object(client, "_get_response", side_effect=RpcFailure(status)),
        patch.object(client, "cancel_execution") as single,
    ):
        with pytest.raises(DagsterUserCodeUnreachableError):
            client.cancel_executions(["one", "two"])
        single.assert_not_called()


def test_old_server_uses_single_rpc_fallback():
    client = DagsterGrpcClient(host="localhost", port=1234)
    result = serialize_value(
        CancelExecutionResult(success=True, message=None, serializable_error_info=None)
    )
    with (
        patch.object(
            client, "_get_response", side_effect=RpcFailure(grpc.StatusCode.UNIMPLEMENTED)
        ),
        patch.object(client, "cancel_execution", return_value=result) as single,
    ):
        response = client.cancel_executions(["one", "two"])
    assert single.call_count == 2
    assert all(item.success for item in response.results.values())


def test_empty_batch_does_not_contact_server():
    client = DagsterGrpcClient(host="localhost", port=1234)
    with patch.object(client, "_get_response") as transport:
        assert not client.cancel_executions([]).results
        transport.assert_not_called()


def test_proxy_routes_runs_to_original_server_generations():
    with cancellation_server(["one"]) as (_, first), cancellation_server(["two"]) as (_, second):
        proxy = object.__new__(DagsterProxyApiServicer)
        proxy._run_clients = {"one": first, "two": second}
        request = dagster_api_pb2.CancelExecutionsRequest(
            serialized_cancel_executions_request=serialize_value(
                CancelExecutionsRequest(run_ids=["two", "missing", "one"])
            )
        )
        response = deserialize_value(
            proxy.CancelExecutions(request, None).serialized_cancel_executions_result,
            CancelExecutionsResult,
        )
        assert response.results["one"].success
        assert response.results["two"].success
        assert not response.results["missing"].success
        assert response.results["missing"].serializable_error_info is not None


def test_default_launcher_groups_servers_and_skips_finished_runs():
    with instance_for_test() as instance:
        runs = [create_run_for_test(instance, status=DagsterRunStatus.STARTED) for _ in range(3)]
        finished = create_run_for_test(instance, status=DagsterRunStatus.SUCCESS)
        with (
            cancellation_server([runs[0].run_id, runs[1].run_id]) as (_, first),
            cancellation_server([runs[2].run_id]) as (_, second),
        ):
            launcher = DefaultRunLauncher()
            launcher.register_instance(instance)
            clients = {runs[0].run_id: first, runs[1].run_id: first, runs[2].run_id: second}
            for run_id, client in clients.items():
                instance.add_run_tags(
                    run_id, {GRPC_INFO_TAG: json.dumps({"host": client.host, "port": client.port})}
                )
            with (
                patch.object(instance, "get_runs", wraps=instance.get_runs) as lookup,
                patch.object(
                    launcher,
                    "_get_grpc_client_for_run",
                    side_effect=lambda run: clients.get(run.run_id),
                ),
                patch.object(
                    first, "cancel_executions", wraps=first.cancel_executions
                ) as first_batch,
                patch.object(
                    second, "cancel_executions", wraps=second.cancel_executions
                ) as second_batch,
            ):
                result = launcher.terminate_runs([run.run_id for run in [*runs, finished]])
            lookup.assert_called_once()
            first_batch.assert_called_once_with([run.run_id for run in runs[:2]])
            second_batch.assert_called_once_with([runs[2].run_id])
            assert result == {**{run.run_id: True for run in runs}, finished.run_id: False}
            assert all(
                instance.get_run_by_id(run.run_id).status == DagsterRunStatus.CANCELING
                for run in runs
            )


def test_single_termination_override_is_preserved():
    class CustomLauncher(DefaultRunLauncher):
        def terminate(self, run_id):
            return run_id == "one"

    launcher = CustomLauncher()
    assert launcher.terminate_runs(["one", "two"]) == {"one": True, "two": False}
    with patch.object(launcher, "terminate", side_effect=[True, RuntimeError("failed")]) as single:
        with pytest.raises(RuntimeError, match="failed"):
            RunLauncher.terminate_runs(launcher, ["one", "two", "three"])
        assert single.call_count == 2


def test_batch_worker_error_does_not_skip_other_workers():
    with cancellation_server(["broken", "healthy"]) as (server, client):
        server._termination_events["broken"] = Mock(  # noqa: SLF001
            set=Mock(side_effect=RuntimeError("signal failed"))
        )
        response = client.cancel_executions(["broken", "healthy"])
        assert not response.results["broken"].success
        assert response.results["broken"].serializable_error_info is not None
        assert response.results["healthy"].success


def test_native_unimplemented_endpoint_falls_back():
    def unimplemented(request, context):
        context.abort(grpc.StatusCode.UNIMPLEMENTED, "old server")

    # Bind an older server's behavior when registering the handlers, over a real channel.
    with patch.object(DagsterApiServer, "CancelExecutions", side_effect=unimplemented):
        with cancellation_server(["one", "two"]) as (_, client):
            with patch.object(client, "cancel_execution", wraps=client.cancel_execution) as single:
                result = client.cancel_executions(["one", "two"])
            assert single.call_count == 2
            assert all(item.success for item in result.results.values())


def test_incomplete_batch_response_is_rejected():
    client = DagsterGrpcClient(host="localhost", port=1234)
    response = dagster_api_pb2.CancelExecutionsReply(
        serialized_cancel_executions_result=serialize_value(CancelExecutionsResult(results={}))
    )
    with patch.object(client, "_get_response", return_value=response):
        with pytest.raises(check.CheckError, match="Incomplete batch cancellation response"):
            client.cancel_executions(["one"])


def test_default_launcher_bounds_batch_size():
    runs = {
        str(index): DagsterRun(job_name="job", run_id=str(index), status=DagsterRunStatus.STARTED)
        for index in range(501)
    }
    with instance_for_test() as instance, cancellation_server(list(runs)) as (_, client):
        launcher = DefaultRunLauncher()
        launcher.register_instance(instance)
        with (
            patch.object(
                instance,
                "get_runs",
                side_effect=lambda filters: [runs[run_id] for run_id in filters.run_ids],
            ) as lookup,
            patch.object(instance, "get_run_by_id", side_effect=runs.get),
            patch.object(instance, "report_run_canceling"),
            patch.object(launcher, "_get_grpc_client_for_run", return_value=client),
            patch.object(client, "cancel_executions", wraps=client.cancel_executions) as batch,
        ):
            result = launcher.terminate_runs(list(runs))
        assert lookup.call_count == 2
        assert [len(call.args[0]) for call in batch.call_args_list] == [500, 1]
        assert len(result) == 501
        assert all(result.values())


def test_custom_termination_client_override_is_preserved():
    with instance_for_test() as instance:
        runs = [create_run_for_test(instance, status=DagsterRunStatus.STARTED) for _ in range(2)]
        with cancellation_server([run.run_id for run in runs]) as (_, client):

            class CustomLauncher(DefaultRunLauncher):
                def _get_grpc_client_for_termination(self, run_id):
                    return client

            launcher = CustomLauncher()
            launcher.register_instance(instance)
            with patch.object(client, "cancel_execution", wraps=client.cancel_execution) as single:
                assert all(launcher.terminate_runs([run.run_id for run in runs]).values())
            assert single.call_count == 2


def test_run_finishing_after_bulk_lookup_is_not_canceled():
    with instance_for_test() as instance:
        runs = [create_run_for_test(instance, status=DagsterRunStatus.STARTED) for _ in range(2)]
        with cancellation_server([run.run_id for run in runs]) as (server, client):
            for run in runs:
                instance.add_run_tags(
                    run.run_id,
                    {GRPC_INFO_TAG: json.dumps({"host": client.host, "port": client.port})},
                )
            launcher = DefaultRunLauncher()
            launcher.register_instance(instance)
            get_runs = instance.get_runs

            def finishing_get_runs(filters):
                snapshot = get_runs(filters)
                instance.report_dagster_event(
                    DagsterEvent(DagsterEventType.RUN_SUCCESS.value, job_name=runs[1].job_name),
                    runs[1].run_id,
                )
                return snapshot

            with patch.object(instance, "get_runs", side_effect=finishing_get_runs):
                result = launcher.terminate_runs([run.run_id for run in runs])
            assert result == {runs[0].run_id: True, runs[1].run_id: False}
            assert instance.get_run_by_id(runs[1].run_id).status == DagsterRunStatus.SUCCESS
            assert not server._termination_events[runs[1].run_id].is_set()  # noqa: SLF001


def test_preparation_failure_sends_already_prepared_requests():
    with instance_for_test() as instance:
        runs = [create_run_for_test(instance, status=DagsterRunStatus.STARTED) for _ in range(2)]
        with cancellation_server([run.run_id for run in runs]) as (server, client):
            for run in runs:
                instance.add_run_tags(
                    run.run_id,
                    {GRPC_INFO_TAG: json.dumps({"host": client.host, "port": client.port})},
                )
            launcher = DefaultRunLauncher()
            launcher.register_instance(instance)
            report = instance.report_run_canceling

            def failing_report(run):
                if run.run_id == runs[1].run_id:
                    raise RuntimeError("preparation failed")
                report(run)

            with patch.object(instance, "report_run_canceling", side_effect=failing_report):
                with pytest.raises(RuntimeError, match="preparation failed"):
                    launcher.terminate_runs([run.run_id for run in runs])
            assert server._termination_events[runs[0].run_id].is_set()  # noqa: SLF001
            assert not server._termination_events[runs[1].run_id].is_set()  # noqa: SLF001
            assert instance.get_run_by_id(runs[1].run_id).status == DagsterRunStatus.STARTED
