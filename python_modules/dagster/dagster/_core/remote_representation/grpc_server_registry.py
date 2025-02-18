import sys
import threading
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Union, cast

from typing_extensions import TypeGuard

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError, DagsterUserCodeUnreachableError
from dagster._core.instance import InstanceRef
from dagster._core.remote_representation.origin import (
    CodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.server import GrpcServerCommand, GrpcServerProcess
from dagster._time import get_current_timestamp
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient


class GrpcServerEndpoint(
    NamedTuple(
        "_GrpcServerEndpoint",
        [
            ("host", str),
            ("port", Optional[int]),
            ("socket", Optional[str]),
        ],
    )
):
    def __new__(cls, host: str, port: Optional[int], socket: Optional[str]):
        return super().__new__(
            cls,
            check.str_param(host, "host"),
            check.opt_int_param(port, "port"),
            check.opt_str_param(socket, "socket"),
        )

    def create_client(self) -> "DagsterGrpcClient":
        from dagster._grpc.client import DagsterGrpcClient

        return DagsterGrpcClient(port=self.port, socket=self.socket, host=self.host)


class ServerRegistryEntry(NamedTuple):
    loadable_target_origin: LoadableTargetOrigin
    creation_timestamp: float
    process: GrpcServerProcess


class ErrorRegistryEntry(NamedTuple):
    loadable_target_origin: LoadableTargetOrigin
    creation_timestamp: float
    error: SerializableErrorInfo


# Creates local gRPC python processes from ManagedGrpcPythonEnvCodeLocationOrigins and shares
# them between threads.
class GrpcServerRegistry(AbstractContextManager):
    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        server_command: GrpcServerCommand,
        # How long the process can live without a heartbeat before it dies. You should ensure
        # that any processes returned by this registry have at least one
        # GrpcServerCodeLocation hitting the server with a heartbeat while you want the
        # process to stay running.
        heartbeat_ttl: int,
        # How long to wait for the server to start up and receive connections before timing out
        startup_timeout: int,
        wait_for_processes_on_shutdown: bool,
        log_level: str = "INFO",
        inject_env_vars_from_instance: bool = True,
        container_image: Optional[str] = None,
        container_context: Optional[dict[str, Any]] = None,
        additional_timeout_msg: Optional[str] = None,
    ):
        self.instance_ref = instance_ref
        self.server_command = server_command

        # map of servers being currently returned, keyed by origin ID
        self._active_entries: dict[str, Union[ServerRegistryEntry, ErrorRegistryEntry]] = {}

        self._waited_for_processes = False

        self._heartbeat_ttl = check.int_param(heartbeat_ttl, "heartbeat_ttl")
        self._startup_timeout = check.int_param(startup_timeout, "startup_timeout")
        self._additional_timeout_msg = check.opt_str_param(
            additional_timeout_msg, "additional_timeout_msg"
        )

        self._lock = threading.Lock()

        self._all_processes: list[GrpcServerProcess] = []

        self._cleanup_thread_shutdown_event: Optional[threading.Event] = None
        self._cleanup_thread: Optional[threading.Thread] = None

        self._log_level = check.str_param(log_level, "log_level")
        self._inject_env_vars_from_instance = inject_env_vars_from_instance
        self._container_image = container_image
        self._container_context = container_context

        self._wait_for_processes_on_shutdown = wait_for_processes_on_shutdown

        self._cleanup_thread_shutdown_event = threading.Event()

        self._cleanup_thread = threading.Thread(
            target=self._clear_old_processes,
            name="grpc-server-registry-cleanup",
            args=(self._cleanup_thread_shutdown_event,),
            daemon=True,
        )
        self._cleanup_thread.start()

    def supports_origin(
        self, code_location_origin: CodeLocationOrigin
    ) -> TypeGuard[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin)

    @property
    def supports_reload(self) -> bool:
        return True

    def clear_all_grpc_endpoints(self):
        # Free the map entry for all origins so that subsequent calls to _get_grpc_endpoint wil
        # create a new process
        with self._lock:
            self._active_entries.clear()

    def reload_grpc_endpoint(
        self, code_location_origin: ManagedGrpcPythonEnvCodeLocationOrigin
    ) -> GrpcServerEndpoint:
        check.inst_param(code_location_origin, "code_location_origin", CodeLocationOrigin)
        with self._lock:
            origin_id = code_location_origin.get_id()
            if origin_id in self._active_entries:
                # Free the map entry for this origin so that _get_grpc_endpoint will create
                # a new process
                del self._active_entries[origin_id]

            return self._get_grpc_endpoint(code_location_origin)

    def get_grpc_endpoint(
        self, code_location_origin: ManagedGrpcPythonEnvCodeLocationOrigin
    ) -> GrpcServerEndpoint:
        check.inst_param(code_location_origin, "code_location_origin", CodeLocationOrigin)

        with self._lock:
            return self._get_grpc_endpoint(code_location_origin)

    def _get_loadable_target_origin(
        self, code_location_origin: ManagedGrpcPythonEnvCodeLocationOrigin
    ) -> LoadableTargetOrigin:
        check.inst_param(
            code_location_origin,
            "code_location_origin",
            ManagedGrpcPythonEnvCodeLocationOrigin,
        )
        return code_location_origin.loadable_target_origin

    def _get_grpc_endpoint(
        self, code_location_origin: ManagedGrpcPythonEnvCodeLocationOrigin
    ) -> GrpcServerEndpoint:
        origin_id = code_location_origin.get_id()
        loadable_target_origin = self._get_loadable_target_origin(code_location_origin)
        if not loadable_target_origin:
            raise Exception(
                "No Python file/module information available for location"
                f" {code_location_origin.location_name}"
            )

        if origin_id not in self._active_entries:
            refresh_server = True
        else:
            active_entry = self._active_entries[origin_id]
            refresh_server = loadable_target_origin != active_entry.loadable_target_origin

        if refresh_server:
            try:
                server_process = GrpcServerProcess(
                    instance_ref=self.instance_ref,
                    server_command=self.server_command,
                    location_name=code_location_origin.location_name,
                    loadable_target_origin=loadable_target_origin,
                    heartbeat=True,
                    heartbeat_timeout=self._heartbeat_ttl,
                    startup_timeout=self._startup_timeout,
                    log_level=self._log_level,
                    inject_env_vars_from_instance=self._inject_env_vars_from_instance,
                    container_image=self._container_image,
                    container_context=self._container_context,
                    additional_timeout_msg=self._additional_timeout_msg,
                )
                self._all_processes.append(server_process)
                self._active_entries[origin_id] = ServerRegistryEntry(
                    process=server_process,
                    loadable_target_origin=loadable_target_origin,
                    creation_timestamp=get_current_timestamp(),
                )
            except Exception:
                self._active_entries[origin_id] = ErrorRegistryEntry(
                    error=serializable_error_info_from_exc_info(sys.exc_info()),
                    loadable_target_origin=loadable_target_origin,
                    creation_timestamp=get_current_timestamp(),
                )

        active_entry = self._active_entries[origin_id]

        if isinstance(active_entry, ErrorRegistryEntry):
            raise DagsterUserCodeProcessError(
                active_entry.error.to_string(),
                user_code_process_error_infos=[active_entry.error],
            )

        return GrpcServerEndpoint(
            host="localhost",
            port=active_entry.process.port,
            socket=active_entry.process.socket,
        )

    # Clear out processes from the map periodically so that they'll be re-created the next
    # time the origins are requested. Lack of any heartbeats will ensure that the server will
    # eventually die once they're no longer being held by any threads.
    def _clear_old_processes(self, shutdown_event: threading.Event) -> None:
        while True:
            shutdown_event.wait(5)
            if shutdown_event.is_set():
                break

            with self._lock:
                # Remove any dead processes from the all_processes map
                dead_process_indexes: list[int] = []
                for index in range(len(self._all_processes)):
                    process = self._all_processes[index]
                    if process.server_process.poll() is not None:
                        dead_process_indexes.append(index)

                for index in reversed(dead_process_indexes):
                    self._all_processes[index].wait()
                    del self._all_processes[index]

    def __exit__(self, exception_type, exception_value, traceback):
        if self._cleanup_thread:
            cast(threading.Event, self._cleanup_thread_shutdown_event).set()
            self._cleanup_thread.join()

        self.shutdown_all_processes()

        if self._wait_for_processes_on_shutdown:
            self.wait_for_processes()

    def shutdown_all_processes(self):
        for process in self._all_processes:
            process.shutdown_server()

    def are_all_servers_shut_down(self) -> bool:
        for process in self._all_processes:
            try:
                process.create_client().ping("")
                return False
            except DagsterUserCodeUnreachableError:
                pass
        return True

    def wait_for_processes(self) -> None:
        # Wait for any processes created by this registry. Generally not needed outside
        # of tests, since the processes have heartbeats and will end on their own once
        # they finish any outstanding executions.
        if self._waited_for_processes:
            return
        self._waited_for_processes = True
        for process in self._all_processes:
            process.wait()
