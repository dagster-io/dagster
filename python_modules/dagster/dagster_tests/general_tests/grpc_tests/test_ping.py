import os
import re
import time

import grpc
import pytest
from dagster import check, seven
from dagster.grpc import DagsterGrpcClient, DagsterGrpcServer, ephemeral_grpc_api_client
from dagster.grpc.server import GrpcServerProcess, open_server_process
from dagster.serdes.ipc import interrupt_ipc_subprocess_pid
from dagster.utils import find_free_port, safe_tempfile_path


def server_thread_runnable(**kwargs):
    def _runnable():
        server = DagsterGrpcServer(**kwargs)
        server.serve()

    return _runnable


@pytest.mark.skipif(not seven.IS_WINDOWS, reason="Windows-only test")
def test_server_socket_on_windows():
    with safe_tempfile_path() as skt:
        with pytest.raises(check.CheckError, match=re.escape("`socket` not supported")):
            DagsterGrpcServer(socket=skt)


def test_server_port_and_socket():
    with safe_tempfile_path() as skt:
        with pytest.raises(
            check.CheckError,
            match=re.escape("You must pass one and only one of `port` or `socket`."),
        ):
            DagsterGrpcServer(socket=skt, port=find_free_port())


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_server_socket():
    with safe_tempfile_path() as skt:
        server_process = open_server_process(port=None, socket=skt)
        try:
            assert DagsterGrpcClient(socket=skt).ping("foobar") == "foobar"
        finally:
            interrupt_ipc_subprocess_pid(server_process.pid)


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_process_killed_after_client_finished():

    server_process = GrpcServerProcess()

    with server_process.create_ephemeral_client() as client:
        socket = client.socket
        assert socket and os.path.exists(socket)

    start_time = time.time()
    while server_process.server_process.poll() is None:
        time.sleep(0.05)
        # Verify server process cleans up eventually
        assert time.time() - start_time < 1

    # verify socket is cleaned up
    assert not os.path.exists(socket)


def test_server_port():
    port = find_free_port()
    server_process = open_server_process(port=port, socket=None)
    assert server_process is not None

    try:
        assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
    finally:
        if server_process is not None:
            interrupt_ipc_subprocess_pid(server_process.pid)


def test_client_bad_port():
    port = find_free_port()
    with pytest.raises(grpc.RpcError, match="failed to connect to all addresses"):
        DagsterGrpcClient(port=port).ping("foobar")


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_client_bad_socket():
    with safe_tempfile_path() as bad_socket:
        with pytest.raises(grpc.RpcError, match="failed to connect to all addresses"):
            DagsterGrpcClient(socket=bad_socket).ping("foobar")


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
        DagsterGrpcClient(port=port, host=None)


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
        assert api_client.ping("foo") == "foo"


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
    server_process = open_server_process(port=port, socket=None)
    assert server_process is not None
    return port, server_process


def test_fixed_server_id():
    port = find_free_port()
    server_process = open_server_process(port=port, socket=None, fixed_server_id="fixed_id")
    assert server_process is not None

    try:
        api_client = DagsterGrpcClient(port=port)
        assert api_client.get_server_id() == "fixed_id"
    finally:
        interrupt_ipc_subprocess_pid(server_process.pid)


def test_detect_server_restart():
    # Create first server and query ID
    port, server_process = create_server_process()
    try:
        api_client = DagsterGrpcClient(port=port)
        server_id_one = api_client.get_server_id()
        assert server_id_one
    finally:
        interrupt_ipc_subprocess_pid(server_process.pid)

    seven.wait_for_process(server_process, timeout=5)
    with pytest.raises(grpc._channel._InactiveRpcError):  # pylint: disable=protected-access
        api_client.get_server_id()

    # Create second server and query ID
    port, server_process = create_server_process()
    try:
        api_client = DagsterGrpcClient(port=port)
        server_id_two = api_client.get_server_id()
        assert server_id_two
    finally:
        interrupt_ipc_subprocess_pid(server_process.pid)

    assert server_id_one != server_id_two
