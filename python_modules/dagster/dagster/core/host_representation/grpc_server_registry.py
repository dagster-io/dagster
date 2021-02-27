import sys
import threading
import uuid
from abc import abstractmethod
from collections import namedtuple
from contextlib import AbstractContextManager

import pendulum
from dagster import check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.origin import ManagedGrpcPythonEnvRepositoryLocationOrigin
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


# Daemons in different threads can use a shared GrpcServerRegistry to ensure that
# a single GrpcServerProcess is created for each origin
class GrpcServerRegistry(AbstractContextManager):
    @abstractmethod
    def supports_origin(self, repository_location_origin):
        pass

    @abstractmethod
    def get_grpc_endpoint(self, repository_location_origin):
        pass


DEFAULT_PROCESS_CLEANUP_INTERVAL = 60
DEFAULT_PROCESS_HEARTBEAT_INTERVAL = 120

# GrpcServerRegistry that creates local gRPC python processes from
# ManagedGrpcPythonEnvRepositoryLocationOrigins and shares them between threads.
class ProcessGrpcServerRegistry(GrpcServerRegistry):
    def __init__(
        self,
        # Whether to wait on exit for any created processes to finish, primarily useful for test
        # cleanup
        wait_for_processes_on_exit=False,
        # How often to reload created processes in a background thread
        cleanup_interval=DEFAULT_PROCESS_CLEANUP_INTERVAL,
        # How long the process can live without a heartbeat. Should be higher than
        # cleanup_interval to ensure that processes don't quit before they are reloaded.
        heartbeat_interval=DEFAULT_PROCESS_HEARTBEAT_INTERVAL,
    ):
        # (GrpcServerProcess or SerializableErrorInfo, creation timestamp, server ID) tuples, keyed
        # by origin ID
        self._active_grpc_processes_or_errors = {}

        self._cleanup_interval = check.int_param(cleanup_interval, "cleanup_interval")
        self._heartbeat_interval = check.int_param(heartbeat_interval, "heartbeat_interval")

        self._wait_for_processes_on_exit = wait_for_processes_on_exit

        self._lock = threading.Lock()

        self._all_processes = []

        self._cleanup_thread_shutdown_event = threading.Event()

        self._cleanup_thread = threading.Thread(
            target=self._clear_old_processes,
            name="grpc-server-registry-cleanup",
            args=(self._cleanup_thread_shutdown_event, self._cleanup_interval),
        )
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()

    def supports_origin(self, repository_location_origin):
        return isinstance(repository_location_origin, ManagedGrpcPythonEnvRepositoryLocationOrigin)

    def get_grpc_endpoint(self, repository_location_origin):
        check.inst_param(
            repository_location_origin,
            "repository_location_origin",
            ManagedGrpcPythonEnvRepositoryLocationOrigin,
        )

        origin_id = repository_location_origin.get_id()

        with self._lock:
            if not origin_id in self._active_grpc_processes_or_errors:
                try:
                    new_server_id = str(uuid.uuid4())
                    server_process = GrpcServerProcess(
                        loadable_target_origin=repository_location_origin.loadable_target_origin,
                        heartbeat=True,
                        heartbeat_timeout=self._heartbeat_interval,
                        fixed_server_id=new_server_id,
                    )
                    self._all_processes.append(server_process)
                except Exception:  # pylint: disable=broad-except
                    server_process = serializable_error_info_from_exc_info(sys.exc_info())
                    new_server_id = None

                self._active_grpc_processes_or_errors[origin_id] = (
                    server_process,
                    pendulum.now("UTC").timestamp(),
                    new_server_id,
                )

            process, _creation_timestamp, server_id = self._active_grpc_processes_or_errors[
                origin_id
            ]

            if isinstance(process, SerializableErrorInfo):
                raise DagsterUserCodeProcessError(
                    process.to_string(), user_code_process_error_infos=[process]
                )

            return GrpcServerEndpoint(
                server_id=server_id, host="localhost", port=process.port, socket=process.socket
            )

    # Clear out processes from the map periodically so that they'll be re-created the next
    # time the origins are requested. Lack of any heartbeats will ensure that the server will
    # eventually die once they're no longer being held by any threads.
    def _clear_old_processes(self, shutdown_event, cleanup_interval):
        while True:
            shutdown_event.wait(5)
            if shutdown_event.is_set():
                break

            current_time = pendulum.now("UTC").timestamp()
            with self._lock:
                origin_ids_to_clear = []

                for origin_id, entry in self._active_grpc_processes_or_errors.items():
                    _process_or_error, creation_timestamp, _server_id = entry

                    if (
                        current_time - creation_timestamp > cleanup_interval
                    ):  # Use a different threshold for errors so they aren't cached as long?
                        origin_ids_to_clear.append(origin_id)

                for origin_id in origin_ids_to_clear:
                    del self._active_grpc_processes_or_errors[origin_id]

                # Remove any dead processes from the all_processes map
                dead_process_indexes = []
                for index in range(len(self._all_processes)):
                    process = self._all_processes[index]
                    if not process.server_process.poll() is None:
                        dead_process_indexes.append(index)

                for index in reversed(dead_process_indexes):
                    del self._all_processes[index]

    def __exit__(self, exception_type, exception_value, traceback):
        self._cleanup_thread_shutdown_event.set()
        self._cleanup_thread.join()

        for process in self._all_processes:
            process.create_ephemeral_client().cleanup_server()

        if self._wait_for_processes_on_exit:
            for process in self._all_processes:
                process.wait()
