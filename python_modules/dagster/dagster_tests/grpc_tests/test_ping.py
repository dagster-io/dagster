import re

import grpc
import pytest

from dagster import check, seven
from dagster.grpc import DagsterGrpcClient, DagsterGrpcServer, ephemeral_grpc_api_client
from dagster.grpc.client import open_server_process
from dagster.serdes.ipc import interrupt_ipc_subprocess
from dagster.utils import find_free_port, safe_tempfile_path


def server_thread_runnable(**kwargs):
    def _runnable():
        server = DagsterGrpcServer(**kwargs)
        server.serve()

    return _runnable


@pytest.mark.skipif(not seven.IS_WINDOWS, reason='Windows-only test')
def test_server_socket_on_windows():
    with safe_tempfile_path() as skt:
        with pytest.raises(check.CheckError, match=re.escape('`socket` not supported')):
            DagsterGrpcServer(socket=skt)


def test_server_port_and_socket():
    with safe_tempfile_path() as skt:
        with pytest.raises(
            check.CheckError,
            match=re.escape('You must pass one and only one of `port` or `socket`.'),
        ):
            DagsterGrpcServer(socket=skt, port=find_free_port())


@pytest.mark.skipif(seven.IS_WINDOWS, reason='Unix-only test')
def test_server_socket():
    with safe_tempfile_path() as skt:
        server_process = open_server_process(port=None, socket=skt)
        try:
            assert DagsterGrpcClient(socket=skt).ping('foobar') == 'foobar'
        finally:
            interrupt_ipc_subprocess(server_process)


def test_server_port():
    port = find_free_port()
    server_process = open_server_process(port=port, socket=None)
    assert server_process is not None

    try:
        assert DagsterGrpcClient(port=port).ping('foobar') == 'foobar'
    finally:
        if server_process is not None:
            interrupt_ipc_subprocess(server_process)


def test_client_bad_port():
    port = find_free_port()
    with pytest.raises(grpc.RpcError, match='failed to connect to all addresses'):
        DagsterGrpcClient(port=port).ping('foobar')


@pytest.mark.skipif(seven.IS_WINDOWS, reason='Unix-only test')
def test_client_bad_socket():
    with safe_tempfile_path() as bad_socket:
        with pytest.raises(grpc.RpcError, match='failed to connect to all addresses'):
            DagsterGrpcClient(socket=bad_socket).ping('foobar')


@pytest.mark.skipif(not seven.IS_WINDOWS, reason='Windows-only test')
def test_client_socket_on_windows():
    with safe_tempfile_path() as skt:
        with pytest.raises(check.CheckError, match=re.escape('`socket` not supported.')):
            DagsterGrpcClient(socket=skt)


def test_client_port():
    port = find_free_port()
    assert DagsterGrpcClient(port=port)


def test_client_port_bad_host():
    port = find_free_port()
    with pytest.raises(check.CheckError, match='Must provide a hostname'):
        DagsterGrpcClient(port=port, host=None)


@pytest.mark.skipif(seven.IS_WINDOWS, reason='Unix-only test')
def test_client_socket():
    with safe_tempfile_path() as skt:
        assert DagsterGrpcClient(socket=skt)


def test_client_port_and_socket():
    port = find_free_port()
    with safe_tempfile_path() as skt:
        with pytest.raises(
            check.CheckError,
            match=re.escape('You must pass one and only one of `port` or `socket`.'),
        ):
            DagsterGrpcClient(port=port, socket=skt)


def test_ephemeral_client():
    with ephemeral_grpc_api_client() as api_client:
        assert api_client.ping('foo') == 'foo'
