import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Event, Lock
from unittest.mock import Mock, patch

import dagster._check as check
import grpc
import pytest
from dagster._core.errors import DagsterUserCodeProcessError, DagsterUserCodeUnreachableError
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
    CancelExecutionRequest,
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
            cancel_executions = DagsterGrpcClient.cancel_executions
            with (
                patch.object(instance, "get_runs", wraps=instance.get_runs) as lookup,
                patch.object(
                    DagsterGrpcClient,
                    "cancel_executions",
                    autospec=True,
                    side_effect=cancel_executions,
                ) as batch,
            ):
                result = launcher.terminate_runs([run.run_id for run in [*runs, finished]])
            lookup.assert_called_once()
            assert [(call.args[0].port, call.args[1]) for call in batch.call_args_list] == [
                (first.port, [run.run_id for run in runs[:2]]),
                (second.port, [runs[2].run_id]),
            ]
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
    ids = [str(index) for index in range(501)]
    with instance_for_test() as instance, cancellation_server(ids) as (_, client):
        runs = {
            run_id: DagsterRun(
                job_name="job",
                run_id=run_id,
                status=DagsterRunStatus.STARTED,
                tags={GRPC_INFO_TAG: json.dumps({"host": client.host, "port": client.port})},
            )
            for run_id in ids
        }
        launcher = DefaultRunLauncher()
        launcher.register_instance(instance)
        cancel_executions = DagsterGrpcClient.cancel_executions
        with (
            patch.object(
                instance,
                "get_runs",
                side_effect=lambda filters: [runs[run_id] for run_id in filters.run_ids],
            ) as lookup,
            patch.object(instance, "get_run_by_id", side_effect=runs.get),
            patch.object(instance, "report_run_canceling"),
            patch.object(
                DagsterGrpcClient, "cancel_executions", autospec=True, side_effect=cancel_executions
            ) as batch,
        ):
            result = launcher.terminate_runs(ids)
        assert lookup.call_count == 2
        assert [len(call.args[1]) for call in batch.call_args_list] == [500, 1]
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


def test_old_server_failure_does_not_strand_later_requests():
    client = DagsterGrpcClient(host="localhost", port=1234)
    success = serialize_value(
        CancelExecutionResult(success=True, message=None, serializable_error_info=None)
    )
    with (
        patch.object(
            client, "_get_response", side_effect=RpcFailure(grpc.StatusCode.UNIMPLEMENTED)
        ),
        patch.object(
            client, "cancel_execution", side_effect=[success, RuntimeError("one failed"), success]
        ) as single,
    ):
        result = client.cancel_executions(["one", "two", "three"])
    assert [call.args[0].run_id for call in single.call_args_list] == ["one", "two", "three"]
    assert result.results["one"].success
    assert not result.results["two"].success
    assert result.results["two"].serializable_error_info is not None
    assert result.results["three"].success


def test_client_bounds_and_deduplicates_requests():
    ids = [str(index) for index in range(501)]
    with cancellation_server(ids) as (_, client):
        with patch.object(client, "_get_response", wraps=client._get_response) as transport:  # noqa: SLF001
            response = client.cancel_executions([*ids, ids[0]])
        assert transport.call_count == 2
        assert len(response.results) == 501
        assert all(result.success for result in response.results.values())


def test_server_rejects_oversized_request_before_signaling():
    with cancellation_server(["one"]) as (server, client):
        request = dagster_api_pb2.CancelExecutionsRequest(
            serialized_cancel_executions_request=serialize_value(
                CancelExecutionsRequest(run_ids=["one"] * 501)
            )
        )
        with pytest.raises(grpc.RpcError) as raised:
            client._get_response("CancelExecutions", request)  # noqa: SLF001
        assert raised.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        assert not server._termination_events["one"].is_set()  # noqa: SLF001


def test_bound_instance_termination_override_is_preserved():
    launcher = DefaultRunLauncher()
    with patch.object(launcher, "terminate", side_effect=[True, False]) as single:
        assert launcher.terminate_runs(["one", "one", "two"]) == {"one": True, "two": False}
        assert [call.args[0] for call in single.call_args_list] == ["one", "two"]


def test_new_client_builder_override_keeps_single_run_path():
    with instance_for_test() as instance:
        runs = [create_run_for_test(instance, status=DagsterRunStatus.STARTED) for _ in range(2)]
        with cancellation_server([run.run_id for run in runs]) as (_, client):

            class CustomLauncher(DefaultRunLauncher):
                def _get_grpc_client_for_run(self, run):
                    return client

            launcher = CustomLauncher()
            launcher.register_instance(instance)
            with patch.object(client, "cancel_execution", wraps=client.cancel_execution) as single:
                assert all(launcher.terminate_runs([run.run_id for run in runs]).values())
            assert single.call_count == 2


def test_reporting_error_after_canceling_marker_still_sends_request():
    with instance_for_test() as instance:
        run = create_run_for_test(instance, status=DagsterRunStatus.STARTED)
        with cancellation_server([run.run_id]) as (server, client):
            instance.add_run_tags(
                run.run_id, {GRPC_INFO_TAG: json.dumps({"host": client.host, "port": client.port})}
            )
            launcher = DefaultRunLauncher()
            launcher.register_instance(instance)
            report = instance.report_run_canceling

            def fail_after_report(run):
                report(run)
                raise RuntimeError("listener failed")

            with patch.object(instance, "report_run_canceling", side_effect=fail_after_report):
                with pytest.raises(RuntimeError, match="listener failed"):
                    launcher.terminate_runs([run.run_id])
            assert server._termination_events[run.run_id].is_set()  # noqa: SLF001


def test_custom_client_authorization_is_not_grouped_by_endpoint():
    metadata = []
    single = DagsterApiServer.CancelExecution

    def observe(servicer, request, context):
        run_id = deserialize_value(
            request.serialized_cancel_execution_request, CancelExecutionRequest
        ).run_id
        metadata.append((run_id, dict(context.invocation_metadata()).get("tenant")))
        return single(servicer, request, context)

    with patch.object(DagsterApiServer, "CancelExecution", autospec=True, side_effect=observe):
        with instance_for_test() as instance:
            runs = [
                create_run_for_test(instance, status=DagsterRunStatus.STARTED) for _ in range(2)
            ]
            with cancellation_server([run.run_id for run in runs]) as (_, client):

                class CustomLauncher(DefaultRunLauncher):
                    def _get_grpc_client_for_run(self, run):
                        return DagsterGrpcClient(
                            host=client.host, port=client.port, metadata=[("tenant", run.run_id)]
                        )

                launcher = CustomLauncher()
                launcher.register_instance(instance)
                assert all(launcher.terminate_runs([run.run_id for run in runs]).values())
    assert metadata == [(run.run_id, run.run_id) for run in runs]


def test_legacy_server_failure_attempts_every_prepared_run():
    single = DagsterApiServer.CancelExecution

    def unimplemented(servicer, request, context):
        context.abort(grpc.StatusCode.UNIMPLEMENTED, "old server")

    with instance_for_test() as instance:
        runs = [create_run_for_test(instance, status=DagsterRunStatus.STARTED) for _ in range(3)]

        def legacy_cancel(servicer, request, context):
            run_id = deserialize_value(
                request.serialized_cancel_execution_request, CancelExecutionRequest
            ).run_id
            if run_id == runs[1].run_id:
                context.abort(grpc.StatusCode.UNAVAILABLE, "one worker failed")
            return single(servicer, request, context)

        with (
            patch.object(
                DagsterApiServer, "CancelExecutions", autospec=True, side_effect=unimplemented
            ),
            patch.object(
                DagsterApiServer, "CancelExecution", autospec=True, side_effect=legacy_cancel
            ),
            cancellation_server([run.run_id for run in runs]) as (server, client),
        ):
            for run in runs:
                instance.add_run_tags(
                    run.run_id,
                    {GRPC_INFO_TAG: json.dumps({"host": client.host, "port": client.port})},
                )
            launcher = DefaultRunLauncher()
            launcher.register_instance(instance)
            with pytest.raises(DagsterUserCodeProcessError):
                launcher.terminate_runs([run.run_id for run in runs])
            assert server._termination_events[runs[0].run_id].is_set()  # noqa: SLF001
            assert server._termination_events[runs[2].run_id].is_set()  # noqa: SLF001


def test_proxy_rejects_oversized_request_before_forwarding():
    proxy = object.__new__(DagsterProxyApiServicer)
    client = Mock()
    proxy._run_clients = {"one": client}
    context = Mock()
    context.abort.side_effect = RpcFailure(grpc.StatusCode.INVALID_ARGUMENT)
    request = dagster_api_pb2.CancelExecutionsRequest(
        serialized_cancel_executions_request=serialize_value(
            CancelExecutionsRequest(run_ids=["one"] * 501)
        )
    )
    with pytest.raises(grpc.RpcError):
        proxy.CancelExecutions(request, context)
    client.cancel_executions.assert_not_called()
