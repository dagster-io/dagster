import math
import os
import queue
import sys
import tempfile
import threading
import time
import uuid
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from threading import Event as ThreadingEventType

import grpc
from dagster import check, seven
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import (
    ReconstructableRepository,
    repository_def_from_target_def,
)
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.external_data import external_repository_data_from_def
from dagster.core.host_representation.origin import ExternalPipelineOrigin, ExternalRepositoryOrigin
from dagster.core.instance import DagsterInstance
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster.serdes.ipc import (
    IPCErrorMessage,
    ipc_write_stream,
    open_ipc_subprocess,
    read_unary_response,
)
from dagster.seven import multiprocessing
from dagster.utils import find_free_port, safe_tempfile_path_unmanaged
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from .__generated__ import api_pb2
from .__generated__.api_pb2_grpc import DagsterApiServicer, add_DagsterApiServicer_to_server
from .impl import (
    RunInSubprocessComplete,
    StartRunInSubprocessSuccessful,
    get_external_execution_plan_snapshot,
    get_external_pipeline_subset_result,
    get_external_schedule_execution,
    get_external_sensor_execution,
    get_partition_config,
    get_partition_names,
    get_partition_set_execution_param_data,
    get_partition_tags,
    start_run_in_subprocess,
)
from .types import (
    CanCancelExecutionRequest,
    CanCancelExecutionResult,
    CancelExecutionRequest,
    CancelExecutionResult,
    ExecuteExternalPipelineArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    GetCurrentImageResult,
    ListRepositoriesResponse,
    LoadableRepositorySymbol,
    PartitionArgs,
    PartitionNamesArgs,
    PartitionSetExecutionParamArgs,
    PipelineSubsetSnapshotArgs,
    SensorExecutionArgs,
    ShutdownServerResult,
    StartRunResult,
)
from .utils import get_loadable_targets

EVENT_QUEUE_POLL_INTERVAL = 0.1

CLEANUP_TICK = 0.5

STREAMING_CHUNK_SIZE = 4000000


class CouldNotBindGrpcServerToAddress(Exception):
    pass


class LazyRepositorySymbolsAndCodePointers:
    """Enables lazily loading user code at RPC-time so that it doesn't interrupt startup and
    we can gracefully handle user code errors."""

    def __init__(self, loadable_target_origin):
        self._loadable_target_origin = loadable_target_origin
        self._loadable_repository_symbols = None
        self._code_pointers_by_repo_name = None

    def load(self):
        self._loadable_repository_symbols = load_loadable_repository_symbols(
            self._loadable_target_origin
        )
        self._code_pointers_by_repo_name = build_code_pointers_by_repo_name(
            self._loadable_target_origin, self._loadable_repository_symbols
        )

    @property
    def loadable_repository_symbols(self):
        if self._loadable_repository_symbols is None:
            self.load()

        return self._loadable_repository_symbols

    @property
    def code_pointers_by_repo_name(self):
        if self._code_pointers_by_repo_name is None:
            self.load()

        return self._code_pointers_by_repo_name


def load_loadable_repository_symbols(loadable_target_origin):
    if loadable_target_origin:
        loadable_targets = get_loadable_targets(
            loadable_target_origin.python_file,
            loadable_target_origin.module_name,
            loadable_target_origin.package_name,
            loadable_target_origin.working_directory,
            loadable_target_origin.attribute,
        )
        return [
            LoadableRepositorySymbol(
                attribute=loadable_target.attribute,
                repository_name=repository_def_from_target_def(
                    loadable_target.target_definition
                ).name,
            )
            for loadable_target in loadable_targets
        ]
    else:
        return []


def build_code_pointers_by_repo_name(loadable_target_origin, loadable_repository_symbols):
    repository_code_pointer_dict = {}
    for loadable_repository_symbol in loadable_repository_symbols:
        if loadable_target_origin.python_file:
            repository_code_pointer_dict[
                loadable_repository_symbol.repository_name
            ] = CodePointer.from_python_file(
                loadable_target_origin.python_file,
                loadable_repository_symbol.attribute,
                loadable_target_origin.working_directory,
            )
        elif loadable_target_origin.package_name:
            repository_code_pointer_dict[
                loadable_repository_symbol.repository_name
            ] = CodePointer.from_python_package(
                loadable_target_origin.package_name,
                loadable_repository_symbol.attribute,
            )
        else:
            repository_code_pointer_dict[
                loadable_repository_symbol.repository_name
            ] = CodePointer.from_module(
                loadable_target_origin.module_name,
                loadable_repository_symbol.attribute,
            )

    return repository_code_pointer_dict


class DagsterApiServer(DagsterApiServicer):
    # The loadable_target_origin is currently Noneable to support instaniating a server.
    # This helps us test the ping methods, and incrementally migrate each method to
    # the target passed in here instead of passing in a target in the argument.
    def __init__(
        self,
        server_termination_event,
        loadable_target_origin=None,
        heartbeat=False,
        heartbeat_timeout=30,
        lazy_load_user_code=False,
        fixed_server_id=None,
    ):
        super(DagsterApiServer, self).__init__()

        check.bool_param(heartbeat, "heartbeat")
        check.int_param(heartbeat_timeout, "heartbeat_timeout")
        check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")

        self._server_termination_event = check.inst_param(
            server_termination_event, "server_termination_event", ThreadingEventType
        )
        self._loadable_target_origin = check.opt_inst_param(
            loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
        )

        # Each server is initialized with a unique UUID. This UUID is used by clients to track when
        # servers are replaced and is used for cache invalidation and reloading.
        self._server_id = check.opt_str_param(fixed_server_id, "fixed_server_id", str(uuid.uuid4()))

        # Client tells the server to shutdown by calling ShutdownServer (or by failing to send a
        # hearbeat, at which point this event is set. The cleanup thread will then set the server
        # termination event once all current executions have finished, which will stop the server)
        self._shutdown_once_executions_finish_event = threading.Event()

        # Dict[str, (multiprocessing.Process, DagsterInstance)]
        self._executions = {}
        # Dict[str, multiprocessing.Event]
        self._termination_events = {}
        self._termination_times = {}
        self._execution_lock = threading.Lock()

        self._repository_symbols_and_code_pointers = LazyRepositorySymbolsAndCodePointers(
            loadable_target_origin
        )
        if not lazy_load_user_code:
            self._repository_symbols_and_code_pointers.load()

        self.__last_heartbeat_time = time.time()
        if heartbeat:
            self.__heartbeat_thread = threading.Thread(
                target=self._heartbeat_thread,
                args=(heartbeat_timeout,),
                name="grpc-server-heartbeat",
            )
            self.__heartbeat_thread.daemon = True
            self.__heartbeat_thread.start()
        else:
            self.__heartbeat_thread = None

        self.__cleanup_thread = threading.Thread(
            target=self._cleanup_thread, args=(), name="grpc-server-cleanup"
        )
        self.__cleanup_thread.daemon = True

        self.__cleanup_thread.start()

    def cleanup(self):
        if self.__heartbeat_thread:
            self.__heartbeat_thread.join()
        self.__cleanup_thread.join()

    def _heartbeat_thread(self, heartbeat_timeout):
        while True:
            self._shutdown_once_executions_finish_event.wait(heartbeat_timeout)
            if self._shutdown_once_executions_finish_event.is_set():
                break

            if self.__last_heartbeat_time < time.time() - heartbeat_timeout:
                self._shutdown_once_executions_finish_event.set()

    def _cleanup_thread(self):
        while True:
            self._server_termination_event.wait(CLEANUP_TICK)
            if self._server_termination_event.is_set():
                break

            self._check_for_orphaned_runs()

    def _check_for_orphaned_runs(self):
        with self._execution_lock:
            runs_to_clear = []
            for run_id, (process, instance_ref) in self._executions.items():
                if not process.is_alive():
                    with DagsterInstance.from_ref(instance_ref) as instance:
                        runs_to_clear.append(run_id)

                        run = instance.get_run_by_id(run_id)
                        if not run or run.is_finished:
                            continue

                        # the process died in an unexpected manner. inform the system
                        message = (
                            "Pipeline execution process for {run_id} unexpectedly exited.".format(
                                run_id=run.run_id
                            )
                        )
                        instance.report_engine_event(message, run, cls=self.__class__)
                        instance.report_run_failed(run)

            for run_id in runs_to_clear:
                self._clear_run(run_id)

            # Once there are no more running executions after we have received a request to
            # shut down, terminate the server
            if self._shutdown_once_executions_finish_event.is_set():
                if len(self._executions) == 0:
                    self._server_termination_event.set()

    # Assumes execution lock is being held
    def _clear_run(self, run_id):
        del self._executions[run_id]
        del self._termination_events[run_id]
        if run_id in self._termination_times:
            del self._termination_times[run_id]

    def _recon_repository_from_origin(self, external_repository_origin):
        check.inst_param(
            external_repository_origin,
            "external_repository_origin",
            ExternalRepositoryOrigin,
        )

        return ReconstructableRepository(
            self._repository_symbols_and_code_pointers.code_pointers_by_repo_name[
                external_repository_origin.repository_name
            ],
            self._get_current_image(),
        )

    def _recon_pipeline_from_origin(self, external_pipeline_origin):
        check.inst_param(
            external_pipeline_origin, "external_pipeline_origin", ExternalPipelineOrigin
        )
        recon_repo = self._recon_repository_from_origin(
            external_pipeline_origin.external_repository_origin
        )
        return recon_repo.get_reconstructable_pipeline(external_pipeline_origin.pipeline_name)

    def Ping(self, request, _context):
        echo = request.echo
        return api_pb2.PingReply(echo=echo)

    def StreamingPing(self, request, _context):
        sequence_length = request.sequence_length
        echo = request.echo
        for sequence_number in range(sequence_length):
            yield api_pb2.StreamingPingEvent(sequence_number=sequence_number, echo=echo)

    def Heartbeat(self, request, _context):
        self.__last_heartbeat_time = time.time()
        echo = request.echo
        return api_pb2.PingReply(echo=echo)

    def GetServerId(self, _request, _context):
        return api_pb2.GetServerIdReply(server_id=self._server_id)

    def ExecutionPlanSnapshot(self, request, _context):
        execution_plan_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_execution_plan_snapshot_args
        )

        check.inst_param(execution_plan_args, "execution_plan_args", ExecutionPlanSnapshotArgs)
        recon_pipeline = self._recon_pipeline_from_origin(execution_plan_args.pipeline_origin)
        execution_plan_snapshot_or_error = get_external_execution_plan_snapshot(
            recon_pipeline, execution_plan_args
        )
        return api_pb2.ExecutionPlanSnapshotReply(
            serialized_execution_plan_snapshot=serialize_dagster_namedtuple(
                execution_plan_snapshot_or_error
            )
        )

    def ListRepositories(self, request, _context):
        try:
            response = ListRepositoriesResponse(
                self._repository_symbols_and_code_pointers.loadable_repository_symbols,
                executable_path=self._loadable_target_origin.executable_path
                if self._loadable_target_origin
                else None,
                repository_code_pointer_dict=(
                    self._repository_symbols_and_code_pointers.code_pointers_by_repo_name
                ),
            )
        except Exception:  # pylint: disable=broad-except
            response = serializable_error_info_from_exc_info(sys.exc_info())

        return api_pb2.ListRepositoriesReply(
            serialized_list_repositories_response_or_error=serialize_dagster_namedtuple(response)
        )

    def ExternalPartitionNames(self, request, _context):
        partition_names_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_partition_names_args
        )

        check.inst_param(partition_names_args, "partition_names_args", PartitionNamesArgs)

        recon_repo = self._recon_repository_from_origin(partition_names_args.repository_origin)

        return api_pb2.ExternalPartitionNamesReply(
            serialized_external_partition_names_or_external_partition_execution_error=serialize_dagster_namedtuple(
                get_partition_names(
                    recon_repo,
                    partition_names_args.partition_set_name,
                )
            )
        )

    def ExternalPartitionSetExecutionParams(self, request, _context):
        args = deserialize_json_to_dagster_namedtuple(
            request.serialized_partition_set_execution_param_args
        )

        check.inst_param(
            args,
            "args",
            PartitionSetExecutionParamArgs,
        )

        recon_repo = self._recon_repository_from_origin(args.repository_origin)
        serialized_data = serialize_dagster_namedtuple(
            get_partition_set_execution_param_data(
                recon_repo=recon_repo,
                partition_set_name=args.partition_set_name,
                partition_names=args.partition_names,
            )
        )

        yield from self._split_serialized_data_into_chunk_events(serialized_data)

    def ExternalPartitionConfig(self, request, _context):
        args = deserialize_json_to_dagster_namedtuple(request.serialized_partition_args)

        check.inst_param(args, "args", PartitionArgs)

        recon_repo = self._recon_repository_from_origin(args.repository_origin)

        return api_pb2.ExternalPartitionConfigReply(
            serialized_external_partition_config_or_external_partition_execution_error=serialize_dagster_namedtuple(
                get_partition_config(recon_repo, args.partition_set_name, args.partition_name)
            )
        )

    def ExternalPartitionTags(self, request, _context):
        partition_args = deserialize_json_to_dagster_namedtuple(request.serialized_partition_args)

        check.inst_param(partition_args, "partition_args", PartitionArgs)

        recon_repo = self._recon_repository_from_origin(partition_args.repository_origin)

        return api_pb2.ExternalPartitionTagsReply(
            serialized_external_partition_tags_or_external_partition_execution_error=serialize_dagster_namedtuple(
                get_partition_tags(
                    recon_repo, partition_args.partition_set_name, partition_args.partition_name
                )
            )
        )

    def ExternalPipelineSubsetSnapshot(self, request, _context):
        pipeline_subset_snapshot_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_pipeline_subset_snapshot_args
        )

        check.inst_param(
            pipeline_subset_snapshot_args,
            "pipeline_subset_snapshot_args",
            PipelineSubsetSnapshotArgs,
        )

        return api_pb2.ExternalPipelineSubsetSnapshotReply(
            serialized_external_pipeline_subset_result=serialize_dagster_namedtuple(
                get_external_pipeline_subset_result(
                    self._recon_pipeline_from_origin(pipeline_subset_snapshot_args.pipeline_origin),
                    pipeline_subset_snapshot_args.solid_selection,
                )
            )
        )

    def _get_serialized_external_repository_data(self, request):
        repository_origin = deserialize_json_to_dagster_namedtuple(
            request.serialized_repository_python_origin
        )

        check.inst_param(repository_origin, "repository_origin", ExternalRepositoryOrigin)
        recon_repo = self._recon_repository_from_origin(repository_origin)
        return serialize_dagster_namedtuple(
            external_repository_data_from_def(recon_repo.get_definition())
        )

    def ExternalRepository(self, request, _context):
        serialized_external_repository_data = self._get_serialized_external_repository_data(request)
        return api_pb2.ExternalRepositoryReply(
            serialized_external_repository_data=serialized_external_repository_data,
        )

    def StreamingExternalRepository(self, request, _context):
        serialized_external_repository_data = self._get_serialized_external_repository_data(request)

        num_chunks = int(
            math.ceil(float(len(serialized_external_repository_data)) / STREAMING_CHUNK_SIZE)
        )

        for i in range(num_chunks):
            start_index = i * STREAMING_CHUNK_SIZE
            end_index = min(
                (i + 1) * STREAMING_CHUNK_SIZE,
                len(serialized_external_repository_data),
            )

            yield api_pb2.StreamingExternalRepositoryEvent(
                sequence_number=i,
                serialized_external_repository_chunk=serialized_external_repository_data[
                    start_index:end_index
                ],
            )

    def _split_serialized_data_into_chunk_events(self, serialized_data):
        num_chunks = int(math.ceil(float(len(serialized_data)) / STREAMING_CHUNK_SIZE))
        for i in range(num_chunks):
            start_index = i * STREAMING_CHUNK_SIZE
            end_index = min(
                (i + 1) * STREAMING_CHUNK_SIZE,
                len(serialized_data),
            )

            yield api_pb2.StreamingChunkEvent(
                sequence_number=i,
                serialized_chunk=serialized_data[start_index:end_index],
            )

    def ExternalScheduleExecution(self, request, _context):
        args = deserialize_json_to_dagster_namedtuple(
            request.serialized_external_schedule_execution_args
        )

        check.inst_param(
            args,
            "args",
            ExternalScheduleExecutionArgs,
        )

        recon_repo = self._recon_repository_from_origin(args.repository_origin)
        serialized_schedule_data = serialize_dagster_namedtuple(
            get_external_schedule_execution(
                recon_repo,
                args.instance_ref,
                args.schedule_name,
                args.scheduled_execution_timestamp,
                args.scheduled_execution_timezone,
            )
        )

        yield from self._split_serialized_data_into_chunk_events(serialized_schedule_data)

    def ExternalSensorExecution(self, request, _context):
        args = deserialize_json_to_dagster_namedtuple(
            request.serialized_external_sensor_execution_args
        )

        check.inst_param(args, "args", SensorExecutionArgs)

        recon_repo = self._recon_repository_from_origin(args.repository_origin)
        serialized_sensor_data = serialize_dagster_namedtuple(
            get_external_sensor_execution(
                recon_repo,
                args.instance_ref,
                args.sensor_name,
                args.last_completion_time,
                args.last_run_key,
            )
        )

        yield from self._split_serialized_data_into_chunk_events(serialized_sensor_data)

    def ShutdownServer(self, request, _context):
        try:
            self._shutdown_once_executions_finish_event.set()
            return api_pb2.ShutdownServerReply(
                serialized_shutdown_server_result=serialize_dagster_namedtuple(
                    ShutdownServerResult(success=True, serializable_error_info=None)
                )
            )
        except:  # pylint: disable=bare-except
            return api_pb2.ShutdownServerReply(
                serialized_shutdown_server_result=serialize_dagster_namedtuple(
                    ShutdownServerResult(
                        success=False,
                        serializable_error_info=serializable_error_info_from_exc_info(
                            sys.exc_info()
                        ),
                    )
                )
            )

    def CancelExecution(self, request, _context):
        success = False
        message = None
        serializable_error_info = None
        try:
            cancel_execution_request = check.inst(
                deserialize_json_to_dagster_namedtuple(request.serialized_cancel_execution_request),
                CancelExecutionRequest,
            )
            with self._execution_lock:
                if cancel_execution_request.run_id in self._executions:
                    self._termination_events[cancel_execution_request.run_id].set()
                    self._termination_times[cancel_execution_request.run_id] = time.time()
                    success = True

        except:  # pylint: disable=bare-except
            serializable_error_info = serializable_error_info_from_exc_info(sys.exc_info())

        return api_pb2.CancelExecutionReply(
            serialized_cancel_execution_result=serialize_dagster_namedtuple(
                CancelExecutionResult(
                    success=success,
                    message=message,
                    serializable_error_info=serializable_error_info,
                )
            )
        )

    def CanCancelExecution(self, request, _context):
        can_cancel_execution_request = check.inst(
            deserialize_json_to_dagster_namedtuple(request.serialized_can_cancel_execution_request),
            CanCancelExecutionRequest,
        )
        with self._execution_lock:
            run_id = can_cancel_execution_request.run_id
            can_cancel = (
                run_id in self._executions and not self._termination_events[run_id].is_set()
            )

        return api_pb2.CanCancelExecutionReply(
            serialized_can_cancel_execution_result=serialize_dagster_namedtuple(
                CanCancelExecutionResult(can_cancel=can_cancel)
            )
        )

    def StartRun(self, request, _context):
        if self._shutdown_once_executions_finish_event.is_set():
            return api_pb2.StartRunReply(
                serialized_start_run_result=serialize_dagster_namedtuple(
                    StartRunResult(
                        success=False,
                        message="Tried to start a run on a server after telling it to shut down",
                        serializable_error_info=None,
                    )
                )
            )

        try:
            execute_run_args = check.inst(
                deserialize_json_to_dagster_namedtuple(request.serialized_execute_run_args),
                ExecuteExternalPipelineArgs,
            )
            run_id = execute_run_args.pipeline_run_id
            recon_pipeline = self._recon_pipeline_from_origin(execute_run_args.pipeline_origin)

        except:  # pylint: disable=bare-except
            return api_pb2.StartRunReply(
                serialized_start_run_result=serialize_dagster_namedtuple(
                    StartRunResult(
                        success=False,
                        message=None,
                        serializable_error_info=serializable_error_info_from_exc_info(
                            sys.exc_info()
                        ),
                    )
                )
            )

        event_queue = multiprocessing.Queue()
        termination_event = multiprocessing.Event()
        execution_process = multiprocessing.Process(
            target=start_run_in_subprocess,
            args=[
                request.serialized_execute_run_args,
                recon_pipeline,
                event_queue,
                termination_event,
            ],
        )

        with self._execution_lock:
            execution_process.start()
            self._executions[run_id] = (
                execution_process,
                execute_run_args.instance_ref,
            )
            self._termination_events[run_id] = termination_event

        success = None
        message = None
        serializable_error_info = None

        while success is None:
            time.sleep(EVENT_QUEUE_POLL_INTERVAL)
            # We use `get_nowait()` instead of `get()` so that we can handle the case where the
            # execution process has died unexpectedly -- `get()` would hang forever in that case
            try:
                dagster_event_or_ipc_error_message_or_done = event_queue.get_nowait()
            except queue.Empty:
                if not execution_process.is_alive():
                    # subprocess died unexpectedly
                    success = False
                    message = (
                        "GRPC server: Subprocess for {run_id} terminated unexpectedly with "
                        "exit code {exit_code}".format(
                            run_id=run_id,
                            exit_code=execution_process.exitcode,
                        )
                    )
                    serializable_error_info = serializable_error_info_from_exc_info(sys.exc_info())
            else:
                if isinstance(
                    dagster_event_or_ipc_error_message_or_done, StartRunInSubprocessSuccessful
                ):
                    success = True
                elif isinstance(
                    dagster_event_or_ipc_error_message_or_done, RunInSubprocessComplete
                ):
                    continue
                if isinstance(dagster_event_or_ipc_error_message_or_done, IPCErrorMessage):
                    success = False
                    message = dagster_event_or_ipc_error_message_or_done.message
                    serializable_error_info = (
                        dagster_event_or_ipc_error_message_or_done.serializable_error_info
                    )

        # Ensure that if the run failed, we remove it from the executions map before
        # returning so that CanCancel will never return True
        if not success:
            with self._execution_lock:
                self._clear_run(run_id)

        return api_pb2.StartRunReply(
            serialized_start_run_result=serialize_dagster_namedtuple(
                StartRunResult(
                    success=success,
                    message=message,
                    serializable_error_info=serializable_error_info,
                )
            )
        )

    def _get_current_image(self):
        return os.getenv("DAGSTER_CURRENT_IMAGE")

    def GetCurrentImage(self, request, _context):
        return api_pb2.GetCurrentImageReply(
            serialized_current_image=serialize_dagster_namedtuple(
                GetCurrentImageResult(
                    current_image=self._get_current_image(), serializable_error_info=None
                )
            )
        )


@whitelist_for_serdes
class GrpcServerStartedEvent(namedtuple("GrpcServerStartedEvent", "")):
    pass


@whitelist_for_serdes
class GrpcServerFailedToBindEvent(namedtuple("GrpcServerStartedEvent", "")):
    pass


@whitelist_for_serdes
class GrpcServerLoadErrorEvent(namedtuple("GrpcServerLoadErrorEvent", "error_info")):
    def __new__(cls, error_info):
        return super(GrpcServerLoadErrorEvent, cls).__new__(
            cls,
            check.inst_param(error_info, "error_info", SerializableErrorInfo),
        )


def server_termination_target(termination_event, server):
    termination_event.wait()
    # We could make this grace period configurable if we set it in the ShutdownServer handler
    server.stop(grace=5)


class DagsterGrpcServer:
    def __init__(
        self,
        host="localhost",
        port=None,
        socket=None,
        max_workers=None,
        loadable_target_origin=None,
        heartbeat=False,
        heartbeat_timeout=30,
        lazy_load_user_code=False,
        ipc_output_file=None,
        fixed_server_id=None,
    ):
        check.opt_str_param(host, "host")
        check.opt_int_param(port, "port")
        check.opt_str_param(socket, "socket")
        check.opt_int_param(max_workers, "max_workers")
        check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
        check.invariant(
            port is not None if seven.IS_WINDOWS else True,
            "You must pass a valid `port` on Windows: `socket` not supported.",
        )
        check.invariant(
            (port or socket) and not (port and socket),
            "You must pass one and only one of `port` or `socket`.",
        )
        check.invariant(
            host is not None if port else True,
            "Must provide a host when serving on a port",
        )
        check.bool_param(heartbeat, "heartbeat")
        check.int_param(heartbeat_timeout, "heartbeat_timeout")
        self._ipc_output_file = check.opt_str_param(ipc_output_file, "ipc_output_file")
        check.opt_str_param(fixed_server_id, "fixed_server_id")

        check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")
        check.invariant(
            max_workers is None or max_workers > 1 if heartbeat else True,
            "max_workers must be greater than 1 or set to None if heartbeat is True. "
            "If set to None, the server will use the gRPC default.",
        )

        self.server = grpc.server(ThreadPoolExecutor(max_workers=max_workers))
        self._server_termination_event = threading.Event()

        try:
            self._api_servicer = DagsterApiServer(
                server_termination_event=self._server_termination_event,
                loadable_target_origin=loadable_target_origin,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                lazy_load_user_code=lazy_load_user_code,
                fixed_server_id=fixed_server_id,
            )
        except Exception:
            if self._ipc_output_file:
                with ipc_write_stream(self._ipc_output_file) as ipc_stream:
                    ipc_stream.send(
                        GrpcServerLoadErrorEvent(
                            error_info=serializable_error_info_from_exc_info(sys.exc_info())
                        )
                    )
            raise

        # Create a health check servicer
        self._health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(self._health_servicer, self.server)

        add_DagsterApiServicer_to_server(self._api_servicer, self.server)

        if port:
            server_address = host + ":" + str(port)
        else:
            server_address = "unix:" + os.path.abspath(socket)

        # grpc.Server.add_insecure_port returns:
        # - 0 on failure
        # - port number when a port is successfully bound
        # - 1 when a UDS is successfully bound
        res = self.server.add_insecure_port(server_address)
        if socket and res != 1:
            if self._ipc_output_file:
                with ipc_write_stream(self._ipc_output_file) as ipc_stream:
                    ipc_stream.send(GrpcServerFailedToBindEvent())
            raise CouldNotBindGrpcServerToAddress(socket)
        if port and res != port:
            if self._ipc_output_file:
                with ipc_write_stream(self._ipc_output_file) as ipc_stream:
                    ipc_stream.send(GrpcServerFailedToBindEvent())
            raise CouldNotBindGrpcServerToAddress(port)

    def serve(self):
        # Unfortunately it looks like ports bind late (here) and so this can fail with an error
        # from C++ like:
        #
        #    E0625 08:46:56.180112000 4697443776 server_chttp2.cc:40]
        #    {"created":"@1593089216.180085000","description":"Only 1 addresses added out of total
        #    2 resolved","file":"src/core/ext/transport/chttp2/server/chttp2_server.cc",
        #    "file_line":406,"referenced_errors":[{"created":"@1593089216.180083000","description":
        #    "Unable to configure socket","fd":6,"file":
        #    "src/core/lib/iomgr/tcp_server_utils_posix_common.cc","file_line":217,
        #    "referenced_errors":[{"created":"@1593089216.180079000",
        #    "description":"Address already in use","errno":48,"file":
        #    "src/core/lib/iomgr/tcp_server_utils_posix_common.cc","file_line":190,"os_error":
        #    "Address already in use","syscall":"bind"}]}]}
        #
        # This is printed to stdout and there is no return value from server.start or exception
        # raised in Python that we can use to handle this. The standard recipes for hijacking C
        # stdout (so we could inspect this output and respond accordingly), e.g.
        # https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/, don't seem
        # to work (at least on Mac OS X) against grpc, and in any case would involve a huge
        # cross-version and cross-platform maintenance burden. We have an issue open against grpc,
        # https://github.com/grpc/grpc/issues/23315, and our own tracking issue at

        self.server.start()

        # Note: currently this is hardcoded as serving, since both services are cohosted
        # pylint: disable=no-member
        self._health_servicer.set("DagsterApi", health_pb2.HealthCheckResponse.SERVING)

        if self._ipc_output_file:
            with ipc_write_stream(self._ipc_output_file) as ipc_stream:
                ipc_stream.send(GrpcServerStartedEvent())

        server_termination_thread = threading.Thread(
            target=server_termination_target,
            args=[self._server_termination_event, self.server],
            name="grpc-server-termination",
        )

        server_termination_thread.daemon = True

        server_termination_thread.start()

        self.server.wait_for_termination()

        server_termination_thread.join()

        self._api_servicer.cleanup()


class CouldNotStartServerProcess(Exception):
    def __init__(self, port=None, socket=None):
        super(CouldNotStartServerProcess, self).__init__(
            "Could not start server with "
            + (
                "port {port}".format(port=port)
                if port is not None
                else "socket {socket}".format(socket=socket)
            )
        )


def wait_for_grpc_server(server_process, ipc_output_file, timeout=60):
    event = read_unary_response(ipc_output_file, timeout=timeout, ipc_process=server_process)

    if isinstance(event, GrpcServerFailedToBindEvent):
        raise CouldNotBindGrpcServerToAddress()
    elif isinstance(event, GrpcServerLoadErrorEvent):
        raise DagsterUserCodeProcessError(
            event.error_info.to_string(), user_code_process_error_infos=[event.error_info]
        )
    elif isinstance(event, GrpcServerStartedEvent):
        return True
    else:
        raise Exception(
            "Received unexpected IPC event from gRPC Server: {event}".format(event=event)
        )


def open_server_process(
    port,
    socket,
    loadable_target_origin=None,
    max_workers=None,
    heartbeat=False,
    heartbeat_timeout=30,
    lazy_load_user_code=False,
    fixed_server_id=None,
):
    check.invariant((port or socket) and not (port and socket), "Set only port or socket")
    check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
    check.opt_int_param(max_workers, "max_workers")

    from dagster.core.test_utils import get_mocked_system_timezone

    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(
            temp_dir, "grpc-server-startup-{uuid}".format(uuid=uuid.uuid4().hex)
        )

        mocked_system_timezone = get_mocked_system_timezone()

        subprocess_args = (
            [
                loadable_target_origin.executable_path
                if loadable_target_origin and loadable_target_origin.executable_path
                else sys.executable,
                "-m",
                "dagster.grpc",
            ]
            + (["--port", str(port)] if port else [])
            + (["--socket", socket] if socket else [])
            + (["-n", str(max_workers)] if max_workers else [])
            + (["--heartbeat"] if heartbeat else [])
            + (["--heartbeat-timeout", str(heartbeat_timeout)] if heartbeat_timeout else [])
            + (["--lazy-load-user-code"] if lazy_load_user_code else [])
            + (["--ipc-output-file", output_file])
            + (["--fixed-server-id", fixed_server_id] if fixed_server_id else [])
            + (
                ["--override-system-timezone", mocked_system_timezone]
                if mocked_system_timezone
                else []
            )
        )

        if loadable_target_origin:
            subprocess_args += loadable_target_origin.get_cli_args()

        server_process = open_ipc_subprocess(subprocess_args)

        try:
            wait_for_grpc_server(server_process, output_file)
        except:
            if server_process.poll() is None:
                server_process.terminate()
            raise

        return server_process


def open_server_process_on_dynamic_port(
    max_retries=10,
    loadable_target_origin=None,
    max_workers=None,
    heartbeat=False,
    heartbeat_timeout=30,
    lazy_load_user_code=False,
    fixed_server_id=None,
):
    server_process = None
    retries = 0
    while server_process is None and retries < max_retries:
        port = find_free_port()
        try:
            server_process = open_server_process(
                port=port,
                socket=None,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                lazy_load_user_code=lazy_load_user_code,
                fixed_server_id=fixed_server_id,
            )
        except CouldNotBindGrpcServerToAddress:
            pass

        retries += 1

    return server_process, port


class GrpcServerProcess:
    def __init__(
        self,
        loadable_target_origin=None,
        force_port=False,
        max_retries=10,
        max_workers=None,
        heartbeat=False,
        heartbeat_timeout=30,
        lazy_load_user_code=False,
        fixed_server_id=None,
    ):
        self.port = None
        self.socket = None
        self.server_process = None

        self.loadable_target_origin = check.opt_inst_param(
            loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
        )
        check.bool_param(force_port, "force_port")
        check.int_param(max_retries, "max_retries")
        check.opt_int_param(max_workers, "max_workers")
        check.bool_param(heartbeat, "heartbeat")
        check.int_param(heartbeat_timeout, "heartbeat_timeout")
        check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")
        check.bool_param(lazy_load_user_code, "lazy_load_user_code")
        check.opt_str_param(fixed_server_id, "fixed_server_id")
        check.invariant(
            max_workers is None or max_workers > 1 if heartbeat else True,
            "max_workers must be greater than 1 or set to None if heartbeat is True. "
            "If set to None, the server will use the gRPC default.",
        )

        if seven.IS_WINDOWS or force_port:
            self.server_process, self.port = open_server_process_on_dynamic_port(
                max_retries=max_retries,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                lazy_load_user_code=lazy_load_user_code,
                fixed_server_id=fixed_server_id,
            )
        else:
            self.socket = safe_tempfile_path_unmanaged()

            self.server_process = open_server_process(
                port=None,
                socket=self.socket,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                lazy_load_user_code=lazy_load_user_code,
                fixed_server_id=fixed_server_id,
            )

        if self.server_process is None:
            raise CouldNotStartServerProcess(port=self.port, socket=self.socket)

    @property
    def pid(self):
        return self.server_process.pid

    def wait(self, timeout=30):
        if self.server_process.poll() is None:
            seven.wait_for_process(self.server_process, timeout=timeout)

    def create_ephemeral_client(self):
        from dagster.grpc.client import EphemeralDagsterGrpcClient

        return EphemeralDagsterGrpcClient(
            port=self.port, socket=self.socket, server_process=self.server_process
        )
