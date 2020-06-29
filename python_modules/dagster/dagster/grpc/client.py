import os
import subprocess
import time
from contextlib import contextmanager

import grpc

from dagster import check, seven
from dagster.serdes.ipc import interrupt_ipc_subprocess, open_ipc_subprocess
from dagster.utils import find_free_port, safe_tempfile_path

from .__generated__ import DagsterApiStub, api_pb2
from .server import (
    SERVER_FAILED_TO_BIND_TOKEN_BYTES,
    SERVER_STARTED_TOKEN_BYTES,
    CouldNotBindGrpcServerToAddress,
)


class CouldNotStartServerProcess(Exception):
    def __init__(self, port=None, socket=None):
        super(CouldNotStartServerProcess, self).__init__(
            'Could not start server with '
            + (
                'port {port}'.format(port=port)
                if port is not None
                else 'socket {socket}'.format(socket=socket)
            )
        )


class DagsterGrpcClient(object):
    def __init__(self, port=None, socket=None, server_process=None, host='localhost'):
        check.opt_int_param(port, 'port')
        check.opt_str_param(socket, 'socket')
        check.opt_str_param(host, 'host')
        check.invariant(
            port is not None if seven.IS_WINDOWS else True,
            'You must pass a valid `port` on Windows: `socket` not supported.',
        )
        check.invariant(
            (port or socket) and not (port and socket),
            'You must pass one and only one of `port` or `socket`.',
        )
        check.invariant(
            host is not None if port else True, 'Must provide a hostname',
        )

        if port:
            self._server_address = host + ':' + str(port)
        else:
            self._server_address = 'unix:' + os.path.abspath(socket)

        self._server_process = check.opt_inst_param(
            server_process, 'server_process', subprocess.Popen
        )

    def _query(self, method, request_type, **kwargs):
        with grpc.insecure_channel(self._server_address) as channel:
            stub = DagsterApiStub(channel)
            response = getattr(stub, method)(request_type(**kwargs))
        # TODO need error handling here
        return response

    def _streaming_query(self, method, request_type, **kwargs):
        with grpc.insecure_channel(self._server_address) as channel:
            stub = DagsterApiStub(channel)
            response_stream = getattr(stub, method)(request_type(**kwargs))
            for response in response_stream:
                yield response

    def terminate_server_process(self):
        if self._server_process is not None:
            interrupt_ipc_subprocess(self._server_process)
            self._server_process = None

    def ping(self, echo):
        check.str_param(echo, 'echo')
        res = self._query('Ping', api_pb2.PingRequest, echo=echo)
        return res.echo


def _wait_for_grpc_server(server_process, timeout=3):
    total_time = 0
    backoff = 0.01
    for line in iter(server_process.stdout.readline, ''):
        print(line)
        if line.rstrip() == SERVER_FAILED_TO_BIND_TOKEN_BYTES:
            raise CouldNotBindGrpcServerToAddress()
        elif line.rstrip() != SERVER_STARTED_TOKEN_BYTES:
            time.sleep(backoff)
            total_time += backoff
            backoff = backoff * 2
            if total_time > timeout:
                return False
        else:
            return True


def open_server_process(port, socket):
    check.invariant((port or socket) and not (port and socket), 'Set only port or socket')

    server_process = open_ipc_subprocess(
        ['dagster', 'api', 'grpc']
        + (['-p', str(port)] if port else [])
        + (['-f', socket] if socket else []),
        stdout=subprocess.PIPE,
    )
    ready = _wait_for_grpc_server(server_process)

    if ready:
        return server_process
    else:
        if server_process.poll() is None:
            interrupt_ipc_subprocess(server_process)
        return None


def open_server_process_on_dynamic_port(max_retries=10):
    server_process = None
    retries = 0
    while server_process is None and retries < max_retries:
        port = find_free_port()
        try:
            server_process = open_server_process(port=port, socket=None)
        except CouldNotBindGrpcServerToAddress:
            pass

        retries += 1

    return server_process, port


@contextmanager
def ephemeral_grpc_api_client(force_port=False):
    if seven.IS_WINDOWS or force_port:
        port = find_free_port()
        server_process = open_server_process(port=port, socket=None)

        if server_process is None:
            raise CouldNotStartServerProcess(port=port, socket=None)

        client = DagsterGrpcClient(port=port, server_process=server_process)

        try:
            yield client
        finally:
            client.terminate_server_process()

    else:
        with safe_tempfile_path() as socket:
            server_process = open_server_process(port=None, socket=socket)

            if server_process is None:
                raise CouldNotStartServerProcess(port=None, socket=socket)

            client = DagsterGrpcClient(socket=socket, server_process=server_process)

            try:
                yield client
            finally:
                client.terminate_server_process()
