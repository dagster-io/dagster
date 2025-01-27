import json
import logging
import os
import re
import subprocess
import threading
import time
from unittest import mock

import dagster._check as check
import dagster._seven as seven
import pytest
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.test_utils import instance_for_test
from dagster._core.utils import FuturesAwareThreadPoolExecutor
from dagster._grpc import DagsterGrpcClient, DagsterGrpcServer, ephemeral_grpc_api_client
from dagster._grpc.server import (
    DagsterCodeServerUtilizationMetrics,
    GrpcServerCommand,
    GrpcServerProcess,
    open_server_process,
)
from dagster._serdes.ipc import interrupt_ipc_subprocess_pid
from dagster._utils import find_free_port, safe_tempfile_path


def _cleanup_process(process):
    interrupt_ipc_subprocess_pid(process.pid)
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        print("subprocess did not terminate in 30s, killing")  # noqa: T201
        process.kill()


@pytest.mark.skipif(not seven.IS_WINDOWS, reason="Windows-only test")
def test_server_socket_on_windows():
    with safe_tempfile_path() as skt:
        with pytest.raises(check.CheckError, match=re.escape("`socket` not supported")):
            DagsterGrpcServer(
                server_termination_event=threading.Event(),
                dagster_api_servicer=mock.MagicMock(),
                logger=logging.getLogger("dagster.code_server"),
                socket=skt,
                threadpool_executor=FuturesAwareThreadPoolExecutor(),
            )


def test_server_port_and_socket():
    with safe_tempfile_path() as skt:
        with pytest.raises(
            check.CheckError,
            match=re.escape("You must pass one and only one of `port` or `socket`."),
        ):
            DagsterGrpcServer(
                server_termination_event=threading.Event(),
                dagster_api_servicer=mock.MagicMock(),
                logger=logging.getLogger("dagster.code_server"),
                socket=skt,
                port=find_free_port(),
                threadpool_executor=FuturesAwareThreadPoolExecutor(),
            )


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_server_socket():
    with instance_for_test() as instance:
        with safe_tempfile_path() as skt:
            server_process = open_server_process(
                instance.get_ref(), port=None, socket=skt, server_command=GrpcServerCommand.API_GRPC
            )
            try:
                assert DagsterGrpcClient(socket=skt).ping("foobar") == {
                    "echo": "foobar",
                    "serialized_server_utilization_metrics": "",
                }
            finally:
                interrupt_ipc_subprocess_pid(server_process.pid)
                server_process.terminate()
                server_process.wait()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_process_killed_after_server_finished():
    with instance_for_test() as instance:
        raw_process = None
        try:
            with GrpcServerProcess(instance_ref=instance.get_ref()) as server_process:
                client = server_process.create_client()
                raw_process = server_process.server_process
                socket = client.socket
                assert socket and os.path.exists(socket)

            # Verify server process cleans up eventually

            start_time = time.time()
            while raw_process.poll() is None:
                time.sleep(0.05)
                # Verify server process cleans up eventually
                assert time.time() - start_time < 5

            # verify socket is cleaned up
            assert not os.path.exists(socket)
        finally:
            raw_process.terminate()  # pyright: ignore[reportOptionalMemberAccess]
            raw_process.wait()  # pyright: ignore[reportOptionalMemberAccess]


def test_server_port():
    with instance_for_test() as instance:
        port = find_free_port()
        server_process = open_server_process(
            instance.get_ref(), port=port, socket=None, server_command=GrpcServerCommand.API_GRPC
        )
        assert server_process is not None

        try:
            assert DagsterGrpcClient(port=port).ping("foobar") == {
                "echo": "foobar",
                "serialized_server_utilization_metrics": "",
            }
        finally:
            _cleanup_process(server_process)


def test_client_bad_port():
    port = find_free_port()
    with pytest.raises(DagsterUserCodeUnreachableError) as exc_info:
        DagsterGrpcClient(port=port).ping("foobar")
    assert "failed to connect to all addresses" in str(exc_info.getrepr())


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_client_bad_socket():
    with safe_tempfile_path() as bad_socket:
        with pytest.raises(DagsterUserCodeUnreachableError) as exc_info:
            DagsterGrpcClient(socket=bad_socket).ping("foobar")
        assert "failed to connect to all addresses" in str(exc_info.getrepr())


@pytest.mark.skipif(not seven.IS_WINDOWS, reason="Windows-only test")
def test_client_socket_on_windows():
    with safe_tempfile_path() as skt:
        with pytest.raises(check.CheckError, match=re.escape("`socket` not supported.")):
            DagsterGrpcClient(socket=skt)


def test_client_port():
    port = find_free_port()
    assert DagsterGrpcClient(port=port)


def test_client_port_bad_host():
    port = find_free_port()
    with pytest.raises(check.CheckError, match="Must provide a hostname"):
        DagsterGrpcClient(port=port, host=None)  # pyright: ignore[reportArgumentType]


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_client_socket():
    with safe_tempfile_path() as skt:
        assert DagsterGrpcClient(socket=skt)


def test_client_port_and_socket():
    port = find_free_port()
    with safe_tempfile_path() as skt:
        with pytest.raises(
            check.CheckError,
            match=re.escape("You must pass one and only one of `port` or `socket`."),
        ):
            DagsterGrpcClient(port=port, socket=skt)


def test_ephemeral_client():
    with ephemeral_grpc_api_client() as api_client:
        assert api_client.ping("foo") == {
            "echo": "foo",
            "serialized_server_utilization_metrics": "",
        }


def test_streaming():
    with ephemeral_grpc_api_client() as api_client:
        results = [result for result in api_client.streaming_ping(sequence_length=10, echo="foo")]
        assert len(results) == 10
        for sequence_number, result in enumerate(results):
            assert result["sequence_number"] == sequence_number
            assert result["echo"] == "foo"


def test_get_server_id():
    with ephemeral_grpc_api_client() as api_client:
        assert api_client.get_server_id()


def create_server_process():
    port = find_free_port()
    with instance_for_test() as instance:
        server_process = open_server_process(instance.get_ref(), port=port, socket=None)
        assert server_process is not None
        return port, server_process


def test_fixed_server_id():
    port = find_free_port()
    with instance_for_test() as instance:
        server_process = open_server_process(
            instance.get_ref(), port=port, socket=None, fixed_server_id="fixed_id"
        )
        assert server_process is not None

        try:
            api_client = DagsterGrpcClient(port=port)
            assert api_client.get_server_id() == "fixed_id"
        finally:
            _cleanup_process(server_process)


def test_detect_server_restart():
    # Create first server and query ID
    port, server_process = create_server_process()
    try:
        api_client = DagsterGrpcClient(port=port)
        server_id_one = api_client.get_server_id()
        assert server_id_one
    finally:
        _cleanup_process(server_process)

    server_process.communicate(timeout=5)
    with pytest.raises(DagsterUserCodeUnreachableError):
        api_client.get_server_id()

    # Create second server and query ID
    port, server_process = create_server_process()
    try:
        api_client = DagsterGrpcClient(port=port)
        server_id_two = api_client.get_server_id()
        assert server_id_two
    finally:
        _cleanup_process(server_process)

    assert server_id_one != server_id_two


def test_ping_metrics_retrieval():
    with instance_for_test() as instance:
        port = find_free_port()
        server_process = open_server_process(
            instance.get_ref(), port=port, socket=None, enable_metrics=True
        )
        assert server_process is not None

        try:
            result = DagsterGrpcClient(port=port).ping("foobar")
            assert result["echo"] == "foobar"
            metrics = json.loads(result["serialized_server_utilization_metrics"])
            assert all(
                key in metrics for key in DagsterCodeServerUtilizationMetrics.__annotations__
            )
        finally:
            _cleanup_process(server_process)
