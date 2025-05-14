import logging
import os
import threading
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager, ExitStack
from typing import Any, Union, cast

from typing_extensions import Self

import dagster._check as check
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.remote_representation.origin import (
    GrpcServerCodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.workspace.context import WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL
from dagster._core.workspace.load_target import WorkspaceLoadTarget
from dagster._grpc.server import INCREASE_TIMEOUT_DAGSTER_YAML_MSG, GrpcServerCommand


def get_auto_restart_code_server_interval() -> int:
    return int(os.getenv("DAGSTER_CODE_SERVER_AUTO_RESTART_INTERVAL", "30"))


class ProxyServerManager(AbstractContextManager):
    """Context manager that manages the lifecycle of a set of proxy code servers targeting a passed-in load target."""

    def __init__(
        self,
        instance: DagsterInstance,
        workspace_load_target: WorkspaceLoadTarget,
        code_server_log_level: str = "INFO",
    ) -> None:
        self._stack = ExitStack()

        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._workspace_load_target = check.inst_param(
            workspace_load_target, "workspace_load_target", WorkspaceLoadTarget
        )
        self._origins = cast(
            "Sequence[Union[GrpcServerCodeLocationOrigin, ManagedGrpcPythonEnvCodeLocationOrigin]]",
            self._workspace_load_target.create_origins(),
        )

        self._grpc_server_registry: GrpcServerRegistry = self._stack.enter_context(
            GrpcServerRegistry(
                instance_ref=self._instance.get_ref(),
                server_command=GrpcServerCommand.CODE_SERVER_START,
                heartbeat_ttl=WEBSERVER_GRPC_SERVER_HEARTBEAT_TTL,
                startup_timeout=instance.code_server_process_startup_timeout,
                log_level=code_server_log_level,
                wait_for_processes_on_shutdown=instance.wait_for_local_code_server_processes_on_shutdown,
                additional_timeout_msg=INCREASE_TIMEOUT_DAGSTER_YAML_MSG,
            )
        )

        self.__shutdown_event = threading.Event()

        self.__process_monitoring_thread = threading.Thread(
            target=self.process_monitoring_thread, daemon=True
        )
        self.__process_monitoring_thread.start()
        self._initialize_endpoints()

    def _initialize_endpoints(self) -> None:
        """Initialize the endpoints for the code server processes."""
        for origin in self._origins:
            # Calling get_grpc_endpoint will start the server process if it is not already running.
            if isinstance(origin, ManagedGrpcPythonEnvCodeLocationOrigin):
                self._grpc_server_registry.get_grpc_endpoint(origin)

    def process_monitoring_thread(self) -> None:
        """Thread responsible for monitoring the code server processes.
        - If the proxy servers exit unexpectedly, restarts them.
        - Heartbeats the proxy servers to let them know that the caller process is still alive.
        """
        while True:
            self.__shutdown_event.wait(get_auto_restart_code_server_interval())
            if self.__shutdown_event.is_set():
                break
            for origin in self._origins:
                # We only process managed gRPC servers here.
                if isinstance(origin, ManagedGrpcPythonEnvCodeLocationOrigin):
                    process = self._grpc_server_registry.get_grpc_server_process(origin)
                    if not process:
                        # Waiting for the process to start
                        continue
                    if process.server_process and process.server_process.poll() is not None:
                        logging.getLogger(__name__).warning(
                            f"Code server process has exited with code {process.server_process.poll()}. Restarting the code server process."
                        )
                        process.start_server_process()
                        continue
                    client = process.create_client()
                    try:
                        client.heartbeat("ping")
                    except DagsterUserCodeUnreachableError:
                        continue

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        self.__shutdown_event.set()
        self.__process_monitoring_thread.join()
        self._stack.close()

    def get_code_server_specs(self) -> Sequence[Mapping[str, Mapping[str, Any]]]:
        result = []
        for origin in self._origins:
            if isinstance(origin, ManagedGrpcPythonEnvCodeLocationOrigin):
                grpc_endpoint = self._grpc_server_registry.get_grpc_endpoint(origin)
                server_spec = {
                    "location_name": origin.location_name,
                    "socket": grpc_endpoint.socket,
                    "port": grpc_endpoint.port,
                    "host": grpc_endpoint.host,
                    "additional_metadata": origin.loadable_target_origin.as_dict,
                }
            else:
                server_spec = {
                    "location_name": origin.location_name,
                    "host": origin.host,
                    "port": origin.port,
                    "socket": origin.socket,
                    "additional_metadata": origin.additional_metadata,
                }
            result.append({"grpc_server": {k: v for k, v in server_spec.items() if v is not None}})
        return result
