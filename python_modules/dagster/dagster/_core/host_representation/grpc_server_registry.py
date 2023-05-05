from __future__ import annotations

import sys
import threading
import uuid
from contextlib import AbstractContextManager
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    NamedTuple,
    Optional,
    Union,
    cast,
)

import pendulum
from typing_extensions import TypeGuard

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.host_representation.origin import (
    CodeLocationOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.instance import DagsterInstance
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.server import GrpcServerProcess
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient


class GrpcServerEndpoint(
    NamedTuple(
        "_GrpcServerEndpoint",
        [
            ("server_id", str),
            ("host", str),
            ("port", Optional[int]),
            ("socket", Optional[str]),
        ],
    )
):
    def __new__(cls, server_id: str, host: str, port: Optional[int], socket: Optional[str]):
        return super(GrpcServerEndpoint, cls).__new__(
            cls,
            check.str_param(server_id, "server_id"),
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
    server_id: str


class ErrorRegistryEntry(NamedTuple):
    loadable_target_origin: LoadableTargetOrigin
    creation_timestamp: float
    error: SerializableErrorInfo


# Creates local gRPC python processes from ManagedGrpcPythonEnvCodeLocationOrigins and shares
# them between threads.
class GrpcServerRegistry(AbstractContextManager):
    def __init__(
        self,
        instance: DagsterInstance,
        # How long each process should run before a new process should be created the next
        # time a given origin is requested (which will pick up any changes that have been
        # made to the code)
        reload_interval: int,
        # How long the process can live without a heartbeat before it dies. You should ensure
        # that either heartbeat_ttl is greater than reload_interval (so that the process will reload
        # before it ends due to heartbeat failure), or if reload_interval is 0, that any processes
        # returned by this registry have at least one GrpcServerCodeLocation hitting the
        # server with a heartbeat while you want the process to stay running.
        heartbeat_ttl: int,
        # How long to wait for the server to start up and receive connections before timing out
        startup_timeout: int,
        log_level: str = "INFO",
    ):
        self.instance = instance

        # map of servers being currently returned, keyed by origin ID
        self._active_entries: Dict[str, Union[ServerRegistryEntry, ErrorRegistryEntry]] = {}

        self._waited_for_processes = False

        check.invariant(
            heartbeat_ttl > reload_interval,
            (
                "Heartbeat TTL must be larger than reload interval, or processes could die due to"
                " TTL failure before they are reloaded"
            ),
        )

        self._reload_interval = check.int_param(reload_interval, "reload_interval")
        self._heartbeat_ttl = check.int_param(heartbeat_ttl, "heartbeat_ttl")
        self._startup_timeout = check.int_param(startup_timeout, "startup_timeout")

        self._lock = threading.Lock()

        self._all_processes: List[GrpcServerProcess] = []

        self._cleanup_thread_shutdown_event: Optional[threading.Event] = None
        self._cleanup_thread: Optional[threading.Thread] = None

        self._log_level = check.str_param(log_level, "log_level")

        if self._reload_interval > 0:
            self._cleanup_thread_shutdown_event = threading.Event()

            self._cleanup_thread = threading.Thread(
                target=self._clear_old_processes,
                name="grpc-server-registry-cleanup",
                args=(self._cleanup_thread_shutdown_event, self._reload_interval),
            )
            self._cleanup_thread.daemon = True
            self._cleanup_thread.start()

    def supports_origin(
        self, code_location_origin: CodeLocationOrigin
    ) -> TypeGuard[ManagedGrpcPythonEnvCodeLocationOrigin]:
        return isinstance(code_location_origin, ManagedGrpcPythonEnvCodeLocationOrigin)

    @property
    def supports_reload(self) -> bool:
        return True

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

        new_server_id: Optional[str]
        if refresh_server:
            try:
                new_server_id = str(uuid.uuid4())
                server_process = GrpcServerProcess(
                    instance_ref=self.instance.get_ref(),
                    location_name=code_location_origin.location_name,
                    loadable_target_origin=loadable_target_origin,
                    heartbeat=True,
                    heartbeat_timeout=self._heartbeat_ttl,
                    fixed_server_id=new_server_id,
                    startup_timeout=self._startup_timeout,
                    log_level=self._log_level,
                )
                self._all_processes.append(server_process)
                self._active_entries[origin_id] = ServerRegistryEntry(
                    process=server_process,
                    loadable_target_origin=loadable_target_origin,
                    creation_timestamp=pendulum.now("UTC").timestamp(),
                    server_id=new_server_id,
                )
            except Exception:
                self._active_entries[origin_id] = ErrorRegistryEntry(
                    error=serializable_error_info_from_exc_info(sys.exc_info()),
                    loadable_target_origin=loadable_target_origin,
                    creation_timestamp=pendulum.now("UTC").timestamp(),
                )

        active_entry = self._active_entries[origin_id]

        if isinstance(active_entry, ErrorRegistryEntry):
            raise DagsterUserCodeProcessError(
                active_entry.error.to_string(),
                user_code_process_error_infos=[active_entry.error],
            )

        return GrpcServerEndpoint(
            server_id=active_entry.server_id,
            host="localhost",
            port=active_entry.process.port,
            socket=active_entry.process.socket,
        )

    # Clear out processes from the map periodically so that they'll be re-created the next
    # time the origins are requested. Lack of any heartbeats will ensure that the server will
    # eventually die once they're no longer being held by any threads.
    def _clear_old_processes(self, shutdown_event: threading.Event, reload_interval: int) -> None:
        while True:
            shutdown_event.wait(5)
            if shutdown_event.is_set():
                break

            current_time = pendulum.now("UTC").timestamp()
            with self._lock:
                origin_ids_to_clear: List[str] = []

                for origin_id, entry in self._active_entries.items():
                    if (
                        current_time - entry.creation_timestamp > reload_interval
                    ):  # Use a different threshold for errors so they aren't cached as long?
                        origin_ids_to_clear.append(origin_id)

                for origin_id in origin_ids_to_clear:
                    del self._active_entries[origin_id]

                # Remove any dead processes from the all_processes map
                dead_process_indexes: List[int] = []
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

        for process in self._all_processes:
            process.shutdown_server()

        if self.instance.code_server_settings.get("wait_for_local_processes_on_shutdown", False):
            self.wait_for_processes()

    def wait_for_processes(self) -> None:
        # Wait for any processes created by this registry. Generally not needed outside
        # of tests, since the processes have heartbeats and will end on their own once
        # they finish any outstanding executions.
        if self._waited_for_processes:
            return
        self._waited_for_processes = True
        for process in self._all_processes:
            process.wait()
