import os
import sys
import time
from contextlib import contextmanager

import dagster._check as check
import grpc
from dagster._core.errors import DagsterUserCodeProcessError, DagsterUserCodeUnreachableError
from dagster._grpc.client import DEFAULT_GRPC_TIMEOUT
from dagster._grpc.utils import max_rx_bytes, max_send_bytes
from dagster._serdes import serialize_value
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster_shared.serdes.serdes import deserialize_value

from dagster_cloud.pex.grpc.__generated__ import MultiPexApiStub, multi_pex_api_pb2
from dagster_cloud.pex.grpc.types import (
    CreatePexServerArgs,
    CreatePexServerResponse,
    GetCrashedPexServersArgs,
    GetCrashedPexServersResponse,
    GetPexServersArgs,
    GetPexServersResponse,
    ShutdownPexServerArgs,
    ShutdownPexServerResponse,
)


class MultiPexGrpcClient:
    def __init__(self, port: int | None = None, socket: str | None = None, host: str = "localhost"):
        self.port = check.opt_int_param(port, "port")
        self.socket = check.opt_str_param(socket, "socket")
        self.host = check.opt_str_param(host, "host")
        if port:
            self._server_address = host + ":" + str(port)
        elif socket:
            self._server_address = "unix:" + os.path.abspath(socket)
        else:
            check.failed("Must provide either port or socket to MultiPexGrpcClient")

    def create_pex_server(self, create_pex_server_args: CreatePexServerArgs):
        check.inst_param(create_pex_server_args, "create_pex_server_args", CreatePexServerArgs)
        res = self._query(
            "CreatePexServer",
            multi_pex_api_pb2.CreatePexServerRequest,
            create_pex_server_args=serialize_value(create_pex_server_args),
        )
        return self._response_or_error(res.create_pex_server_response, CreatePexServerResponse)

    def get_pex_servers(self, get_pex_servers_args: GetPexServersArgs) -> GetPexServersResponse:
        check.inst_param(get_pex_servers_args, "get_pex_servers_args", GetPexServersArgs)
        res = self._query(
            "GetPexServers",
            multi_pex_api_pb2.GetPexServersRequest,
            get_pex_servers_args=serialize_value(get_pex_servers_args),
        )
        return self._response_or_error(res.get_pex_servers_response, GetPexServersResponse)

    def get_crashed_pex_servers(
        self, get_crashed_pex_servers_args: GetCrashedPexServersArgs
    ) -> GetCrashedPexServersResponse:
        check.inst_param(
            get_crashed_pex_servers_args, "get_crashed_pex_servers_args", GetCrashedPexServersArgs
        )
        res = self._query(
            "GetCrashedPexServers",
            multi_pex_api_pb2.GetCrashedPexServersRequest,
            get_crashed_pex_servers_args=serialize_value(get_crashed_pex_servers_args),
        )
        return self._response_or_error(
            res.get_crashed_pex_servers_response, GetCrashedPexServersResponse
        )

    def shutdown_pex_server(self, shutdown_pex_server_args: ShutdownPexServerArgs):
        check.inst_param(
            shutdown_pex_server_args, "shutdown_pex_server_args", ShutdownPexServerArgs
        )
        res = self._query(
            "ShutdownPexServer",
            multi_pex_api_pb2.ShutdownPexServerRequest,
            shutdown_pex_server_args=serialize_value(shutdown_pex_server_args),
        )
        return self._response_or_error(res.shutdown_pex_server_response, ShutdownPexServerResponse)

    @contextmanager
    def _channel(self):
        options = [
            ("grpc.max_receive_message_length", max_rx_bytes()),
            ("grpc.max_send_message_length", max_send_bytes()),
        ]
        with grpc.insecure_channel(
            self._server_address,
            options=options,
            compression=grpc.Compression.Gzip,
        ) as channel:
            yield channel

    def _response_or_error(self, response, response_type):
        deserialized_response = deserialize_value(response, (response_type, SerializableErrorInfo))
        if isinstance(deserialized_response, SerializableErrorInfo):
            raise DagsterUserCodeProcessError.from_error_info(deserialized_response)
        check.invariant(isinstance(deserialized_response, response_type))
        return deserialized_response

    def _query(self, method, request_type, timeout=DEFAULT_GRPC_TIMEOUT, **kwargs):
        try:
            with self._channel() as channel:
                stub = MultiPexApiStub(channel)
                response = getattr(stub, method)(request_type(**kwargs), timeout=timeout)
            return response
        except Exception as e:
            raise DagsterUserCodeUnreachableError("Could not reach user code server") from e

    def ping(self, echo):
        check.str_param(echo, "echo")
        res = self._query("Ping", multi_pex_api_pb2.PingRequest, echo=echo)
        return res.echo


def wait_for_grpc_server(client, timeout=180):
    start_time = time.time()

    while True:
        try:
            client.ping("")
            return
        except Exception:
            last_error = serializable_error_info_from_exc_info(sys.exc_info())

        if time.time() - start_time > timeout:
            raise Exception(
                f"Timed out after waiting {timeout}s for server. "
                f"Most recent connection error: {last_error}"
            )

        time.sleep(1)
