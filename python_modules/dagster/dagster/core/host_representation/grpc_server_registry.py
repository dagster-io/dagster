import sys
import threading
import uuid
from abc import abstractmethod, abstractproperty
from collections import namedtuple
from contextlib import AbstractContextManager

import pendulum
from dagster import check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.origin import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    RepositoryLocationOrigin,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.server import GrpcServerProcess
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


class GrpcServerEndpoint(namedtuple("_GrpcServerEndpoint", "server_id host port socket")):
    def __new__(cls, server_id, host, port, socket):
        return super(GrpcServerEndpoint, cls).__new__(
            cls,
            check.str_param(server_id, "server_id"),
            check.str_param(host, "host"),
            check.opt_int_param(port, "port"),
            check.opt_str_param(socket, "socket"),
        )

    def create_client(self):
        return DagsterGrpcClient(port=self.port, socket=self.socket, host=self.host)


# Daemons in different threads can use a shared GrpcServerRegistry to ensure that
# a single GrpcServerProcess is created for each origin
class GrpcServerRegistry(AbstractContextManager):
    @abstractmethod
    def supports_origin(self, repository_location_origin):
        pass

    @abstractmethod
    def get_grpc_endpoint(self, repository_location_origin):
        pass

    @abstractmethod
    def reload_grpc_endpoint(self, repository_location_origin):
        pass

    @abstractproperty
    def supports_reload(self):
        pass


DEFAULT_PROCESS_CLEANUP_INTERVAL = 60
DEFAULT_PROCESS_HEARTBEAT_INTERVAL = 120


class ProcessRegistryEntry(
    namedtuple(
        "_ProcessRegistryEntry",
        "process_or_error loadable_target_origin creation_timestamp server_id",
    )
):
    def __new__(cls, process_or_error, loadable_target_origin, creation_timestamp, server_id):
        return super(ProcessRegistryEntry, cls).__new__(
            cls,
            check.inst_param(
                process_or_error, "process_or_error", (GrpcServerProcess, SerializableErrorInfo)
            ),
            check.inst_param(
                loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
            ),
            check.float_param(creation_timestamp, "creation_timestamp"),
            check.opt_str_param(server_id, "server_id"),
        )


# GrpcServerRegistry that creates local gRPC python processes from
# ManagedGrpcPythonEnvRepositoryLocationOrigins and shares them between threads.
class ProcessGrpcServerRegistry(GrpcServerRegistry):
    def __init__(
        self,
        # How often to reload created processes in a background thread
        reload_interval=DEFAULT_PROCESS_CLEANUP_INTERVAL,
        # How long the process can live without a heartbeat before it dies. You should ensure
        # that either heartbeat_ttl is greater than reload_interval (so that the process will reload
        # before it ends due to heartbeat failure), or if reload_interval is 0, that any processes
        # returned by this registry have at least one GrpcServerRepositoryLocation hitting the
        # server with a heartbeat while you want the process to stay running.
        heartbeat_ttl=DEFAULT_PROCESS_HEARTBEAT_INTERVAL,
    ):
        # ProcessRegistryEntry map of servers being currently returned, keyed by origin ID
        self._active_entries = {}

        self._waited_for_processes = False

        check.invariant(
            heartbeat_ttl > reload_interval,
            "Heartbeat TTL must be larger than reload interval, or processes could die due to TTL failure before they are reloaded",
        )

        self._reload_interval = check.int_param(reload_interval, "reload_interval")
        self._heartbeat_ttl = check.int_param(heartbeat_ttl, "heartbeat_ttl")

        self._lock = threading.Lock()

        self._all_processes = []

        self._cleanup_thread_shutdown_event = None
        self._cleanup_thread = None

        if self._reload_interval > 0:
            self._cleanup_thread_shutdown_event = threading.Event()

            self._cleanup_thread = threading.Thread(
                target=self._clear_old_processes,
                name="grpc-server-registry-cleanup",
                args=(self._cleanup_thread_shutdown_event, self._reload_interval),
            )
            self._cleanup_thread.daemon = True
            self._cleanup_thread.start()

    def supports_origin(self, repository_location_origin):
        return isinstance(repository_location_origin, ManagedGrpcPythonEnvRepositoryLocationOrigin)

    @property
    def supports_reload(self):
        return True

    def reload_grpc_endpoint(self, repository_location_origin):
        check.inst_param(
            repository_location_origin, "repository_location_origin", RepositoryLocationOrigin
        )
        with self._lock:
            origin_id = repository_location_origin.get_id()
            if origin_id in self._active_entries:
                # Free the map entry for this origin so that _get_grpc_endpoint will create
                # a new process
                del self._active_entries[origin_id]

            return self._get_grpc_endpoint(repository_location_origin)

    def get_grpc_endpoint(self, repository_location_origin):
        check.inst_param(
            repository_location_origin, "repository_location_origin", RepositoryLocationOrigin
        )

        with self._lock:
            return self._get_grpc_endpoint(repository_location_origin)

    def _get_loadable_target_origin(self, repository_location_origin):
        check.inst_param(
            repository_location_origin,
            "repository_location_origin",
            ManagedGrpcPythonEnvRepositoryLocationOrigin,
        )
        return repository_location_origin.loadable_target_origin

    def _get_grpc_endpoint(self, repository_location_origin):
        origin_id = repository_location_origin.get_id()
        loadable_target_origin = self._get_loadable_target_origin(repository_location_origin)
        if not loadable_target_origin:
            raise Exception(
                f"No Python file/module information available for location {repository_location_origin.location_name}"
            )

        if not origin_id in self._active_entries:
            refresh_server = True
        else:
            active_entry = self._active_entries[origin_id]
            refresh_server = loadable_target_origin != active_entry.loadable_target_origin

        if refresh_server:
            try:
                new_server_id = str(uuid.uuid4())
                server_process = GrpcServerProcess(
                    loadable_target_origin=loadable_target_origin,
                    heartbeat=True,
                    heartbeat_timeout=self._heartbeat_ttl,
                    fixed_server_id=new_server_id,
                )
                self._all_processes.append(server_process)
            except Exception:  # pylint: disable=broad-except
                server_process = serializable_error_info_from_exc_info(sys.exc_info())
                new_server_id = None

            self._active_entries[origin_id] = ProcessRegistryEntry(
                process_or_error=server_process,
                loadable_target_origin=loadable_target_origin,
                creation_timestamp=pendulum.now("UTC").timestamp(),
                server_id=new_server_id,
            )

        active_entry = self._active_entries[origin_id]

        if isinstance(active_entry.process_or_error, SerializableErrorInfo):
            raise DagsterUserCodeProcessError(
                active_entry.process_or_error.to_string(),
                user_code_process_error_infos=[active_entry.process_or_error],
            )

        return GrpcServerEndpoint(
            server_id=active_entry.server_id,
            host="localhost",
            port=active_entry.process_or_error.port,
            socket=active_entry.process_or_error.socket,
        )

    # Clear out processes from the map periodically so that they'll be re-created the next
    # time the origins are requested. Lack of any heartbeats will ensure that the server will
    # eventually die once they're no longer being held by any threads.
    def _clear_old_processes(self, shutdown_event, reload_interval):
        while True:
            shutdown_event.wait(5)
            if shutdown_event.is_set():
                break

            current_time = pendulum.now("UTC").timestamp()
            with self._lock:
                origin_ids_to_clear = []

                for origin_id, entry in self._active_entries.items():
                    if (
                        current_time - entry.creation_timestamp > reload_interval
                    ):  # Use a different threshold for errors so they aren't cached as long?
                        origin_ids_to_clear.append(origin_id)

                for origin_id in origin_ids_to_clear:
                    del self._active_entries[origin_id]

                # Remove any dead processes from the all_processes map
                dead_process_indexes = []
                for index in range(len(self._all_processes)):
                    process = self._all_processes[index]
                    if not process.server_process.poll() is None:
                        dead_process_indexes.append(index)

                for index in reversed(dead_process_indexes):
                    del self._all_processes[index]

    def __exit__(self, exception_type, exception_value, traceback):
        if self._cleanup_thread:
            self._cleanup_thread_shutdown_event.set()
            self._cleanup_thread.join()

        for process in self._all_processes:
            process.create_ephemeral_client().cleanup_server()

    def wait_for_processes(self):
        # Wait for any processes created by this registry. Generally not needed outside
        # of tests, since the processes have heartbeats and will end on their own once
        # they finish any outstanding executions.
        if self._waited_for_processes:
            return
        self._waited_for_processes = True
        for process in self._all_processes:
            process.wait()
