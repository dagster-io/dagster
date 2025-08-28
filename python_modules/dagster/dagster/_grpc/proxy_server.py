import logging
import sys
import threading
import time
from contextlib import ExitStack
from typing import TYPE_CHECKING, Optional

from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

import dagster._check as check
from dagster._core.instance import InstanceRef
from dagster._core.remote_origin import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.remote_representation.grpc_server_registry import GrpcServerRegistry
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.__generated__ import dagster_api_pb2
from dagster._grpc.__generated__.dagster_api_pb2_grpc import DagsterApiServicer
from dagster._grpc.client import (
    DEFAULT_GRPC_TIMEOUT,
    DEFAULT_REPOSITORY_GRPC_TIMEOUT,
    DEFAULT_SENSOR_GRPC_TIMEOUT,
)
from dagster._grpc.constants import GrpcServerCommand
from dagster._grpc.types import (
    CancelExecutionRequest,
    CancelExecutionResult,
    ExecuteExternalJobArgs,
    SensorExecutionArgs,
    ShutdownServerResult,
    StartRunResult,
)
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.error import serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient

CLEANUP_TICK = 1


class DagsterProxyApiServicer(DagsterApiServicer):
    """Service that implements the dagster gRPC API by opening up a "dagster api grpc" subprocess, and proxying
    all gRPC calls to the server running in that subprocess. This allows us to reload code by
    restarting the subprocess without needing to restart the parent process.
    """

    def __init__(
        self,
        loadable_target_origin: LoadableTargetOrigin,
        fixed_server_id: Optional[str],
        container_image: Optional[str],
        container_context: Optional[dict],
        inject_env_vars_from_instance: bool,
        location_name: Optional[str],
        log_level: str,
        startup_timeout: int,
        server_termination_event: threading.Event,
        instance_ref: Optional[InstanceRef],
        logger: logging.Logger,
        server_heartbeat: bool,
        server_heartbeat_timeout: int,
        defs_state_info: Optional[DefsStateInfo],
    ):
        super().__init__()

        self._loadable_target_origin = loadable_target_origin
        self._fixed_server_id = fixed_server_id
        self._container_image = container_image
        self._container_context = container_context
        self._inject_env_vars_from_instance = inject_env_vars_from_instance
        self._instance_ref = instance_ref
        self._location_name = location_name
        self._log_level = log_level
        self._logger = logger

        self._client = None
        self._load_error = None
        self._client_heartbeat_shutdown_event = None
        self._client_heartbeat_thread = None

        self._exit_stack = ExitStack()

        self._reload_lock = threading.Lock()

        self._grpc_server_registry = self._exit_stack.enter_context(
            GrpcServerRegistry(
                instance_ref=self._instance_ref,
                server_command=GrpcServerCommand.API_GRPC,
                heartbeat_ttl=30,
                startup_timeout=startup_timeout,
                log_level=self._log_level,
                inject_env_vars_from_instance=self._inject_env_vars_from_instance,
                container_image=self._container_image,
                container_context=self._container_context,
                wait_for_processes_on_shutdown=True,
                additional_timeout_msg="Set from --startup-timeout command line argument. ",
                defs_state_info=defs_state_info,
            )
        )
        self._origin = ManagedGrpcPythonEnvCodeLocationOrigin(
            loadable_target_origin=self._loadable_target_origin, location_name=location_name
        )

        self._server_termination_event = server_termination_event

        # Client tells the server to shutdown by calling ShutdownServer (or by failing to send a
        # hearbeat, at which point this event is set. The cleanup thread will then set the server
        # termination event once all current executions have finished, which will stop the server)
        self._shutdown_once_executions_finish_event = threading.Event()
        self.__cleanup_thread = threading.Thread(
            target=self._cleanup_thread,
            args=(),
            name="code-server-cleanup",
            daemon=True,
        )

        self.__last_heartbeat_time = time.time()
        self.__server_heartbeat_thread = None

        # Map runs to the client that launched them, so that we can route
        # termination requests
        self._run_clients: dict[str, DagsterGrpcClient] = {}

        self._reload_location()

        # Wait for the code server to have started before starting the heartbeat clock,
        # since the code loading and the server being ready is what will trigger the
        # heartbeats coming in from the client

        if server_heartbeat:
            self.__server_heartbeat_thread = threading.Thread(
                target=self._server_heartbeat_thread,
                args=(server_heartbeat_timeout,),
                name="grpc-server-heartbeat",
                daemon=True,
            )
            self.__server_heartbeat_thread.start()

        self.__cleanup_thread.start()

    def _reload_location(self):
        from dagster._grpc.client import client_heartbeat_thread

        try:
            endpoint = self._grpc_server_registry.reload_grpc_endpoint(self._origin)
            self._load_error = None
            self._client = endpoint.create_client()
        except Exception:
            # Server crashed when starting up
            self._load_error = serializable_error_info_from_exc_info(sys.exc_info())
            self._logger.exception("Failure while loading code")

        if self._client:
            self._client_heartbeat_shutdown_event = threading.Event()
            self._client_heartbeat_thread = threading.Thread(
                target=client_heartbeat_thread,
                args=(
                    self._client,
                    self._client_heartbeat_shutdown_event,
                ),
                name="grpc-client-heartbeat",
                daemon=True,
            )
            self._client_heartbeat_thread.start()

    def ReloadCode(self, request, context):
        with self._reload_lock:  # can only call this method once at a time
            old_heartbeat_shutdown_event = self._client_heartbeat_shutdown_event
            old_heartbeat_thread = self._client_heartbeat_thread
            old_client = self._client

            self._reload_location()  # Creates and starts a new heartbeat thread

        if old_client:
            old_client.shutdown_server()

        if old_heartbeat_shutdown_event:
            old_heartbeat_shutdown_event.set()

        if old_heartbeat_thread:
            old_heartbeat_thread.join()

        return dagster_api_pb2.ReloadCodeReply()

    def cleanup(self):
        # In case ShutdownServer was not called
        self._shutdown_once_executions_finish_event.set()
        self._grpc_server_registry.shutdown_all_processes()

        if self._client_heartbeat_shutdown_event:
            self._client_heartbeat_shutdown_event.set()
            self._client_heartbeat_shutdown_event = None

        if self._client_heartbeat_thread:
            self._client_heartbeat_thread.join()
            self._client_heartbeat_thread = None

        if self.__server_heartbeat_thread:
            self.__server_heartbeat_thread.join()
            self.__server_heartbeat_thread = None

        self._exit_stack.close()

        self.__cleanup_thread.join()

    def _cleanup_thread(self) -> None:
        while True:
            self._server_termination_event.wait(CLEANUP_TICK)
            if self._server_termination_event.is_set():
                break

            if self._shutdown_once_executions_finish_event.is_set():
                if self._grpc_server_registry.are_all_servers_shut_down():
                    self._server_termination_event.set()
                    self._grpc_server_registry.shutdown_all_processes()

    def _get_grpc_client(self):
        return self._client

    def _query(self, api_name: str, request, _context, timeout: int = DEFAULT_GRPC_TIMEOUT):
        if not self._client:
            raise Exception("No available client to code server")
        return check.not_none(self._client)._get_response(api_name, request, timeout)  # noqa

    def _server_heartbeat_thread(self, heartbeat_timeout: int) -> None:
        while True:
            if self._server_termination_event.is_set():
                break

            self._shutdown_once_executions_finish_event.wait(heartbeat_timeout)
            if self._shutdown_once_executions_finish_event.is_set():
                break

            if self.__last_heartbeat_time < time.time() - heartbeat_timeout:
                self._logger.warning(
                    f"No heartbeat received in {heartbeat_timeout} seconds, shutting down"
                )
                self._shutdown_once_executions_finish_event.set()
                self._grpc_server_registry.shutdown_all_processes()

    def _streaming_query(
        self, api_name: str, request, _context, timeout: int = DEFAULT_GRPC_TIMEOUT
    ):
        if not self._client:
            raise Exception("No available client to code server")
        return check.not_none(self._client)._get_streaming_response(api_name, request, timeout)  # noqa

    def ExecutionPlanSnapshot(self, request, context):
        return self._query("ExecutionPlanSnapshot", request, context)

    def ListRepositories(self, request, context):
        if self._load_error:
            return dagster_api_pb2.ListRepositoriesReply(
                serialized_list_repositories_response_or_error=serialize_value(self._load_error)
            )
        return self._query("ListRepositories", request, context)

    def Ping(self, request, context):
        return self._query("Ping", request, context)

    def GetServerId(self, request, context) -> dagster_api_pb2.GetServerIdReply:
        return (
            dagster_api_pb2.GetServerIdReply(server_id=self._fixed_server_id)
            if self._fixed_server_id
            else self._query("GetServerId", request, context)
        )

    def GetCurrentImage(self, request, context):
        return self._query("GetCurrentImage", request, context)

    def StreamingExternalRepository(self, request, context):
        return self._streaming_query(
            "StreamingExternalRepository", request, context, timeout=DEFAULT_REPOSITORY_GRPC_TIMEOUT
        )

    def Heartbeat(self, request, context):
        self.__last_heartbeat_time = time.time()
        echo = request.echo
        return dagster_api_pb2.PingReply(echo=echo)

    def StreamingPing(self, request, context):
        return self._streaming_query("StreamingPing", request, context)

    def ExternalPartitionNames(self, request, context):
        return self._query("ExternalPartitionNames", request, context)

    def ExternalNotebookData(self, request, context):
        return self._query("ExternalNotebookData", request, context)

    def ExternalPartitionConfig(self, request, context):
        return self._query("ExternalPartitionConfig", request, context)

    def ExternalPartitionTags(self, request, context):
        return self._query("ExternalPartitionTags", request, context)

    def ExternalPartitionSetExecutionParams(self, request, context):
        return self._streaming_query("ExternalPartitionSetExecutionParams", request, context)

    def ExternalPipelineSubsetSnapshot(self, request, context):
        return self._query("ExternalPipelineSubsetSnapshot", request, context)

    def ExternalRepository(self, request, context):
        return self._query("ExternalRepository", request, context)

    def ExternalJob(self, request, context):
        return self._query("ExternalJob", request, context)

    def ExternalScheduleExecution(self, request, context):
        return self._streaming_query("ExternalScheduleExecution", request, context)

    def SyncExternalScheduleExecution(self, request, context):
        return self._query("SyncExternalScheduleExecution", request, context)

    def ExternalSensorExecution(self, request, context):
        sensor_execution_args = deserialize_value(
            request.serialized_external_sensor_execution_args,
            SensorExecutionArgs,
        )
        return self._streaming_query(
            "ExternalSensorExecution",
            request,
            context,
            sensor_execution_args.timeout or DEFAULT_GRPC_TIMEOUT,
        )

    def SyncExternalSensorExecution(self, request, context):
        sensor_execution_args = deserialize_value(
            request.serialized_external_sensor_execution_args,
            SensorExecutionArgs,
        )
        return self._query(
            "SyncExternalSensorExecution",
            request,
            context,
            sensor_execution_args.timeout or DEFAULT_SENSOR_GRPC_TIMEOUT,
        )

    def ShutdownServer(self, request, context):
        try:
            self._shutdown_once_executions_finish_event.set()
            self._grpc_server_registry.shutdown_all_processes()
            return dagster_api_pb2.ShutdownServerReply(
                serialized_shutdown_server_result=serialize_value(
                    ShutdownServerResult(success=True, serializable_error_info=None)
                )
            )
        except:
            return dagster_api_pb2.ShutdownServerReply(
                serialized_shutdown_server_result=serialize_value(
                    ShutdownServerResult(
                        success=False,
                        serializable_error_info=serializable_error_info_from_exc_info(
                            sys.exc_info()
                        ),
                    )
                )
            )

    def CancelExecution(self, request, context):
        try:
            cancel_execution_request = deserialize_value(
                request.serialized_cancel_execution_request,
                CancelExecutionRequest,
            )

            run_id = cancel_execution_request.run_id

            client = self._run_clients.get(run_id)
            if not client:
                raise Exception(f"Could not find a server for run {run_id}")

            return client._get_response("CancelExecution", request)  # noqa
        except:
            serializable_error_info = serializable_error_info_from_exc_info(sys.exc_info())

            return dagster_api_pb2.CancelExecutionReply(
                serialized_cancel_execution_result=serialize_value(
                    CancelExecutionResult(
                        success=False,
                        message=None,
                        serializable_error_info=serializable_error_info,
                    )
                )
            )

    def CanCancelExecution(self, request, context):
        return self._query("CanCancelExecution", request, context)

    def StartRun(self, request, context):
        if self._shutdown_once_executions_finish_event.is_set():
            return dagster_api_pb2.StartRunReply(
                serialized_start_run_result=serialize_value(
                    StartRunResult(
                        success=False,
                        message="Tried to start a run on a server after telling it to shut down",
                        serializable_error_info=None,
                    )
                )
            )

        execute_external_job_args = deserialize_value(
            request.serialized_execute_run_args,
            ExecuteExternalJobArgs,
        )

        run_id = execute_external_job_args.run_id

        client = self._client

        self._run_clients[run_id] = client  # pyright: ignore[reportArgumentType]
        return client._get_response("StartRun", request)  # noqa  # pyright: ignore[reportOptionalMemberAccess]
