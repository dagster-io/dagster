from __future__ import annotations

import math
import multiprocessing
import os
import queue
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.synchronize import Event as MPEvent
from subprocess import Popen
from threading import Event as ThreadingEventType
from time import sleep
from typing import Any, Dict, Iterator, List, Mapping, NamedTuple, Optional, Sequence, Tuple, cast

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

import dagster._check as check
import dagster._seven as seven
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.reconstruct import ReconstructableRepository
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.host_representation.external_data import (
    ExternalRepositoryErrorData,
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster._core.host_representation.origin import ExternalRepositoryOrigin
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.origin import DEFAULT_DAGSTER_ENTRY_POINT, get_python_environment_entry_point
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.autodiscovery import LoadableTarget
from dagster._serdes import deserialize_as, serialize_dagster_namedtuple, whitelist_for_serdes
from dagster._serdes.ipc import IPCErrorMessage, ipc_write_stream, open_ipc_subprocess
from dagster._utils import (
    find_free_port,
    frozenlist,
    get_run_crash_explanation,
    safe_tempfile_path_unmanaged,
)
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

from .__generated__ import api_pb2
from .__generated__.api_pb2_grpc import DagsterApiServicer, add_DagsterApiServicer_to_server
from .impl import (
    RunInSubprocessComplete,
    StartRunInSubprocessSuccessful,
    get_external_execution_plan_snapshot,
    get_external_pipeline_subset_result,
    get_external_schedule_execution,
    get_external_sensor_execution,
    get_notebook_data,
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
    GetCurrentRunsResult,
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
from .utils import get_loadable_targets, max_rx_bytes, max_send_bytes

EVENT_QUEUE_POLL_INTERVAL = 0.1

CLEANUP_TICK = 0.5

STREAMING_CHUNK_SIZE = 4000000


class CouldNotBindGrpcServerToAddress(Exception):
    pass


class LoadedRepositories:
    def __init__(
        self,
        loadable_target_origin: Optional[LoadableTargetOrigin],
        entry_point: Sequence[str],
        container_image: Optional[str] = None,
    ):
        self._loadable_target_origin = loadable_target_origin

        self._code_pointers_by_repo_name: Dict[str, CodePointer] = {}
        self._recon_repos_by_name: Dict[str, ReconstructableRepository] = {}
        self._repo_defs_by_name: Dict[str, RepositoryDefinition] = {}
        self._loadable_repository_symbols: List[LoadableRepositorySymbol] = []

        if not loadable_target_origin:
            # empty workspace
            return

        loadable_targets = get_loadable_targets(
            loadable_target_origin.python_file,
            loadable_target_origin.module_name,
            loadable_target_origin.package_name,
            loadable_target_origin.working_directory,
            loadable_target_origin.attribute,
        )
        for loadable_target in loadable_targets:
            pointer = _get_code_pointer(loadable_target_origin, loadable_target)
            recon_repo = ReconstructableRepository(
                pointer,
                container_image,
                sys.executable,
                entry_point=entry_point,
            )
            repo_def = recon_repo.get_definition()
            # force load of all lazy constructed code artifacts to prevent
            # any thread-safety issues loading them later on when serving
            # definitions from multiple threads
            repo_def.load_all_definitions()

            self._code_pointers_by_repo_name[repo_def.name] = pointer
            self._recon_repos_by_name[repo_def.name] = recon_repo
            self._repo_defs_by_name[repo_def.name] = repo_def
            self._loadable_repository_symbols.append(
                LoadableRepositorySymbol(
                    attribute=loadable_target.attribute,
                    repository_name=repo_def.name,
                )
            )

    @property
    def loadable_repository_symbols(self) -> Sequence[LoadableRepositorySymbol]:
        return self._loadable_repository_symbols

    @property
    def code_pointers_by_repo_name(self) -> Mapping[str, CodePointer]:
        return self._code_pointers_by_repo_name

    @property
    def definitions_by_name(self) -> Mapping[str, RepositoryDefinition]:
        return self._repo_defs_by_name

    @property
    def reconstructables_by_name(self) -> Mapping[str, ReconstructableRepository]:
        return self._recon_repos_by_name


def _get_code_pointer(
    loadable_target_origin: LoadableTargetOrigin,
    loadable_repository_symbol: LoadableTarget,
) -> CodePointer:
    if loadable_target_origin.python_file:
        return CodePointer.from_python_file(
            loadable_target_origin.python_file,
            loadable_repository_symbol.attribute,
            loadable_target_origin.working_directory,
        )
    elif loadable_target_origin.package_name:
        return CodePointer.from_python_package(
            loadable_target_origin.package_name,
            loadable_repository_symbol.attribute,
            loadable_target_origin.working_directory,
        )
    elif loadable_target_origin.module_name:
        return CodePointer.from_module(
            loadable_target_origin.module_name,
            loadable_repository_symbol.attribute,
            loadable_target_origin.working_directory,
        )
    else:
        check.failed("Invalid loadable target origin")


class DagsterApiServer(DagsterApiServicer):
    # The loadable_target_origin is currently Noneable to support instaniating a server.
    # This helps us test the ping methods, and incrementally migrate each method to
    # the target passed in here instead of passing in a target in the argument.
    def __init__(
        self,
        server_termination_event: ThreadingEventType,
        loadable_target_origin: Optional[LoadableTargetOrigin] = None,
        heartbeat: bool = False,
        heartbeat_timeout: int = 30,
        lazy_load_user_code: bool = False,
        fixed_server_id: Optional[str] = None,
        entry_point: Optional[Sequence[str]] = None,
        container_image: Optional[str] = None,
        container_context: Optional[dict] = None,
        inject_env_vars_from_instance: Optional[bool] = False,
        instance_ref: Optional[InstanceRef] = None,
        location_name: Optional[str] = None,
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

        self._mp_ctx = multiprocessing.get_context("spawn")

        # Each server is initialized with a unique UUID. This UUID is used by clients to track when
        # servers are replaced and is used for cache invalidation and reloading.
        self._server_id = check.opt_str_param(fixed_server_id, "fixed_server_id", str(uuid.uuid4()))

        # Client tells the server to shutdown by calling ShutdownServer (or by failing to send a
        # hearbeat, at which point this event is set. The cleanup thread will then set the server
        # termination event once all current executions have finished, which will stop the server)
        self._shutdown_once_executions_finish_event = threading.Event()

        self._executions: Dict[str, Tuple[multiprocessing.Process, InstanceRef]] = {}
        self._termination_events: Dict[str, MPEvent] = {}
        self._termination_times: Dict[str, float] = {}
        self._execution_lock = threading.Lock()

        self._serializable_load_error = None

        self._entry_point = (
            frozenlist(check.sequence_param(entry_point, "entry_point", of_type=str))  # type: ignore
            if entry_point is not None
            else DEFAULT_DAGSTER_ENTRY_POINT
        )

        self._container_image = check.opt_str_param(container_image, "container_image")
        self._container_context = check.opt_dict_param(container_context, "container_context")

        try:
            if inject_env_vars_from_instance:
                # If arguments indicate it wants to load env vars, use the passed-in instance
                # ref (or the dagster.yaml on the filesystem if no instance ref is provided)
                with DagsterInstance.from_ref(
                    instance_ref
                ) if instance_ref else DagsterInstance.get() as instance:
                    instance.inject_env_vars(location_name)

            self._loaded_repositories: Optional[LoadedRepositories] = LoadedRepositories(
                loadable_target_origin,
                self._entry_point,
                self._container_image,
            )
        except Exception:
            if not lazy_load_user_code:
                raise
            self._loaded_repositories = None
            self._serializable_load_error = serializable_error_info_from_exc_info(sys.exc_info())

        self.__last_heartbeat_time = time.time()
        if heartbeat:
            self.__heartbeat_thread: Optional[threading.Thread] = threading.Thread(
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

    def cleanup(self) -> None:
        if self.__heartbeat_thread:
            self.__heartbeat_thread.join()
        self.__cleanup_thread.join()

    def _heartbeat_thread(self, heartbeat_timeout: float) -> None:
        while True:
            self._shutdown_once_executions_finish_event.wait(heartbeat_timeout)
            if self._shutdown_once_executions_finish_event.is_set():
                break

            if self.__last_heartbeat_time < time.time() - heartbeat_timeout:
                self._shutdown_once_executions_finish_event.set()

    def _cleanup_thread(self) -> None:
        while True:
            self._server_termination_event.wait(CLEANUP_TICK)
            if self._server_termination_event.is_set():
                break

            self._check_for_orphaned_runs()

    def _check_for_orphaned_runs(self) -> None:
        with self._execution_lock:
            runs_to_clear = []
            for run_id, (process, instance_ref) in self._executions.items():
                if not process.is_alive():
                    with DagsterInstance.from_ref(instance_ref) as instance:
                        runs_to_clear.append(run_id)

                        run = instance.get_run_by_id(run_id)
                        if not run or run.is_finished:
                            continue

                        message = get_run_crash_explanation(
                            prefix=f"Run execution process for {run.run_id}",
                            exit_code=check.not_none(process.exitcode),
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
    def _clear_run(self, run_id: str) -> None:
        del self._executions[run_id]
        del self._termination_events[run_id]
        if run_id in self._termination_times:
            del self._termination_times[run_id]

    def _get_repo_for_origin(
        self,
        external_repo_origin: ExternalRepositoryOrigin,
    ) -> RepositoryDefinition:
        loaded_repos = check.not_none(self._loaded_repositories)
        if external_repo_origin.repository_name not in loaded_repos.definitions_by_name:
            raise Exception(
                f'Could not find a repository called "{external_repo_origin.repository_name}"'
            )
        return loaded_repos.definitions_by_name[external_repo_origin.repository_name]

    def Ping(self, request, _context) -> api_pb2.PingReply:  # type: ignore  # fmt: skip
        echo = request.echo
        return api_pb2.PingReply(echo=echo)

    def StreamingPing(self, request, _context) -> Iterator[api_pb2.StreamingPingEvent]:  # type: ignore  # fmt: skip
        sequence_length = request.sequence_length
        echo = request.echo
        for sequence_number in range(sequence_length):
            yield api_pb2.StreamingPingEvent(sequence_number=sequence_number, echo=echo)

    def Heartbeat(self, request, _context) -> api_pb2.PingReply:  # type: ignore  # fmt: skip
        self.__last_heartbeat_time = time.time()
        echo = request.echo
        return api_pb2.PingReply(echo=echo)

    def GetServerId(self, _request, _context) -> api_pb2.GetServerIdReply:  # type: ignore  # fmt: skip
        return api_pb2.GetServerIdReply(server_id=self._server_id)

    def ExecutionPlanSnapshot(self, request, _context):
        execution_plan_args = deserialize_as(
            request.serialized_execution_plan_snapshot_args,
            ExecutionPlanSnapshotArgs,
        )

        execution_plan_snapshot_or_error = get_external_execution_plan_snapshot(
            self._get_repo_for_origin(
                execution_plan_args.pipeline_origin.external_repository_origin
            ),
            execution_plan_args.pipeline_origin.pipeline_name,
            execution_plan_args,
        )
        return api_pb2.ExecutionPlanSnapshotReply(
            serialized_execution_plan_snapshot=serialize_dagster_namedtuple(
                execution_plan_snapshot_or_error
            )
        )

    def ListRepositories(
        self, request, _context
    ) -> api_pb2.ListRepositoriesReply:  # type: ignore  # fmt: skip
        if self._serializable_load_error:
            return api_pb2.ListRepositoriesReply(
                serialized_list_repositories_response_or_error=serialize_dagster_namedtuple(
                    self._serializable_load_error
                )
            )
        loaded_repositories = check.not_none(self._loaded_repositories)
        response = ListRepositoriesResponse(
            loaded_repositories.loadable_repository_symbols,
            executable_path=self._loadable_target_origin.executable_path
            if self._loadable_target_origin
            else None,
            repository_code_pointer_dict=loaded_repositories.code_pointers_by_repo_name,
            entry_point=self._entry_point,
            container_image=self._container_image,
            container_context=self._container_context,
        )

        return api_pb2.ListRepositoriesReply(
            serialized_list_repositories_response_or_error=serialize_dagster_namedtuple(response)
        )

    def ExternalPartitionNames(
        self, request, _context
    ) -> api_pb2.ExternalPartitionNamesReply:  # type: ignore  # fmt: skip
        partition_names_args = deserialize_as(
            request.serialized_partition_names_args,
            PartitionNamesArgs,
        )
        return api_pb2.ExternalPartitionNamesReply(
            serialized_external_partition_names_or_external_partition_execution_error=serialize_dagster_namedtuple(
                get_partition_names(
                    self._get_repo_for_origin(partition_names_args.repository_origin),
                    partition_names_args.partition_set_name,
                )
            )
        )

    def ExternalNotebookData(
        self, request, _context
    ) -> api_pb2.ExternalNotebookDataReply:  # type: ignore  # fmt: skip
        notebook_path = request.notebook_path
        check.str_param(notebook_path, "notebook_path")
        return api_pb2.ExternalNotebookDataReply(content=get_notebook_data(notebook_path))

    def ExternalPartitionSetExecutionParams(self, request, _context):
        args = deserialize_as(
            request.serialized_partition_set_execution_param_args,
            PartitionSetExecutionParamArgs,
        )

        serialized_data = serialize_dagster_namedtuple(
            get_partition_set_execution_param_data(
                self._get_repo_for_origin(args.repository_origin),
                partition_set_name=args.partition_set_name,
                partition_names=args.partition_names,
            )
        )

        yield from self._split_serialized_data_into_chunk_events(serialized_data)

    def ExternalPartitionConfig(self, request, _context):
        args = deserialize_as(request.serialized_partition_args, PartitionArgs)

        return api_pb2.ExternalPartitionConfigReply(
            serialized_external_partition_config_or_external_partition_execution_error=serialize_dagster_namedtuple(
                get_partition_config(
                    self._get_repo_for_origin(args.repository_origin),
                    args.partition_set_name,
                    args.partition_name,
                )
            )
        )

    def ExternalPartitionTags(
        self, request, _context
    ) -> api_pb2.ExternalPartitionTagsReply:  # type: ignore  # fmt: skip
        partition_args = deserialize_as(request.serialized_partition_args, PartitionArgs)

        return api_pb2.ExternalPartitionTagsReply(
            serialized_external_partition_tags_or_external_partition_execution_error=serialize_dagster_namedtuple(
                get_partition_tags(
                    self._get_repo_for_origin(partition_args.repository_origin),
                    partition_args.partition_set_name,
                    partition_args.partition_name,
                )
            )
        )

    def ExternalPipelineSubsetSnapshot(
        self, request: Any, _context
    ) -> api_pb2.ExternalPipelineSubsetSnapshotReply:  # type: ignore  # fmt: skip
        pipeline_subset_snapshot_args = deserialize_as(
            request.serialized_pipeline_subset_snapshot_args,
            PipelineSubsetSnapshotArgs,
        )

        return api_pb2.ExternalPipelineSubsetSnapshotReply(
            serialized_external_pipeline_subset_result=serialize_dagster_namedtuple(
                get_external_pipeline_subset_result(
                    self._get_repo_for_origin(
                        pipeline_subset_snapshot_args.pipeline_origin.external_repository_origin
                    ),
                    pipeline_subset_snapshot_args.pipeline_origin.pipeline_name,
                    pipeline_subset_snapshot_args.solid_selection,
                    pipeline_subset_snapshot_args.asset_selection,
                )
            )
        )

    def _get_serialized_external_repository_data(self, request):
        try:
            repository_origin = deserialize_as(
                request.serialized_repository_python_origin,
                ExternalRepositoryOrigin,
            )

            return serialize_dagster_namedtuple(
                external_repository_data_from_def(
                    self._get_repo_for_origin(repository_origin),
                    defer_snapshots=request.defer_snapshots,
                )
            )
        except Exception:
            return serialize_dagster_namedtuple(
                ExternalRepositoryErrorData(serializable_error_info_from_exc_info(sys.exc_info()))
            )

    def ExternalRepository(self, request, _context):
        serialized_external_repository_data = self._get_serialized_external_repository_data(request)
        return api_pb2.ExternalRepositoryReply(
            serialized_external_repository_data=serialized_external_repository_data,
        )

    def ExternalJob(
        self, request, _context
    ) -> api_pb2.ExternalJobReply:  # type: ignore  # fmt: skip
        try:
            repository_origin = deserialize_as(
                request.serialized_repository_origin,
                ExternalRepositoryOrigin,
            )

            job_def = self._get_repo_for_origin(repository_origin).get_pipeline(request.job_name)
            ser_job_data = serialize_dagster_namedtuple(external_pipeline_data_from_def(job_def))
            return api_pb2.ExternalJobReply(serialized_job_data=ser_job_data)
        except Exception:
            return api_pb2.ExternalJobReply(
                serialized_error=serialize_dagster_namedtuple(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
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
        args = deserialize_as(
            request.serialized_external_schedule_execution_args,
            ExternalScheduleExecutionArgs,
        )
        serialized_schedule_data = serialize_dagster_namedtuple(
            get_external_schedule_execution(
                self._get_repo_for_origin(args.repository_origin),
                args.instance_ref,
                args.schedule_name,
                args.scheduled_execution_timestamp,
                args.scheduled_execution_timezone,
            )
        )

        yield from self._split_serialized_data_into_chunk_events(serialized_schedule_data)

    def ExternalSensorExecution(self, request, _context):
        args = deserialize_as(
            request.serialized_external_sensor_execution_args,
            SensorExecutionArgs,
        )

        serialized_sensor_data = serialize_dagster_namedtuple(
            get_external_sensor_execution(
                self._get_repo_for_origin(args.repository_origin),
                args.instance_ref,
                args.sensor_name,
                args.last_completion_time,
                args.last_run_key,
                args.cursor,
            )
        )

        yield from self._split_serialized_data_into_chunk_events(serialized_sensor_data)

    def ShutdownServer(self, request, _context) -> api_pb2.ShutdownServerReply:  # type: ignore  # fmt: skip
        try:
            self._shutdown_once_executions_finish_event.set()
            return api_pb2.ShutdownServerReply(
                serialized_shutdown_server_result=serialize_dagster_namedtuple(
                    ShutdownServerResult(success=True, serializable_error_info=None)
                )
            )
        except:
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
            cancel_execution_request = deserialize_as(
                request.serialized_cancel_execution_request,
                CancelExecutionRequest,
            )
            with self._execution_lock:
                if cancel_execution_request.run_id in self._executions:
                    self._termination_events[cancel_execution_request.run_id].set()
                    self._termination_times[cancel_execution_request.run_id] = time.time()
                    success = True

        except:
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

    def CanCancelExecution(self, request, _context) -> api_pb2.CanCancelExecutionReply:  # type: ignore  # fmt: skip
        can_cancel_execution_request = deserialize_as(
            request.serialized_can_cancel_execution_request,
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

    def StartRun(self, request, _context) -> api_pb2.StartRunReply:  # type: ignore  # fmt: skip
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
            execute_external_pipeline_args = deserialize_as(
                request.serialized_execute_run_args,
                ExecuteExternalPipelineArgs,
            )
            run_id = execute_external_pipeline_args.pipeline_run_id

            # reconstructable required for handing execution off to subprocess
            recon_repo = check.not_none(self._loaded_repositories).reconstructables_by_name[
                execute_external_pipeline_args.pipeline_origin.external_repository_origin.repository_name
            ]
            recon_pipeline = recon_repo.get_reconstructable_pipeline(
                execute_external_pipeline_args.pipeline_origin.pipeline_name
            )

        except:
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

        event_queue = self._mp_ctx.Queue()
        termination_event = self._mp_ctx.Event()
        execution_process = self._mp_ctx.Process(
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
                # Cast here to convert `SpawnProcess` from event into regular `Process`-- not sure
                # why not recognized as subclass, multiprocessing typing is a little rough.
                cast(multiprocessing.Process, execution_process),
                check.not_none(execute_external_pipeline_args.instance_ref),
            )
            self._termination_events[run_id] = termination_event

        success = None
        message = None
        serializable_error_info = None

        while success is None:
            sleep(EVENT_QUEUE_POLL_INTERVAL)
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

    def GetCurrentImage(self, request, _context):
        return api_pb2.GetCurrentImageReply(
            serialized_current_image=serialize_dagster_namedtuple(
                GetCurrentImageResult(
                    current_image=self._container_image, serializable_error_info=None
                )
            )
        )

    def GetCurrentRuns(self, request, context) -> api_pb2.GetCurrentRunsReply:  # type: ignore  # fmt: skip
        with self._execution_lock:
            return api_pb2.GetCurrentRunsReply(
                serialized_current_runs=serialize_dagster_namedtuple(
                    GetCurrentRunsResult(
                        current_runs=list(self._executions.keys()), serializable_error_info=None
                    )
                )
            )


@whitelist_for_serdes
class GrpcServerStartedEvent(NamedTuple("_GrpcServerStartedEvent", [])):
    pass


@whitelist_for_serdes
class GrpcServerFailedToBindEvent(NamedTuple("_GrpcServerFailedToBindEvent", [])):
    pass


@whitelist_for_serdes
class GrpcServerLoadErrorEvent(
    NamedTuple("GrpcServerLoadErrorEvent", [("error_info", SerializableErrorInfo)])
):
    def __new__(cls, error_info: SerializableErrorInfo):
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
        entry_point=None,
        container_image=None,
        container_context=None,
        inject_env_vars_from_instance=False,
        instance_ref=None,
        location_name=None,
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
            (
                "max_workers must be greater than 1 or set to None if heartbeat is True. "
                "If set to None, the server will use the gRPC default."
            ),
        )

        check.opt_bool_param(inject_env_vars_from_instance, "inject_env_vars_from_instance")
        check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
        check.opt_str_param(location_name, "location_name")

        self.server = grpc.server(
            ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="grpc-server-rpc-handler",
            ),
            compression=grpc.Compression.Gzip,
            options=[
                ("grpc.max_send_message_length", max_send_bytes()),
                ("grpc.max_receive_message_length", max_rx_bytes()),
            ],
        )
        self._server_termination_event = threading.Event()

        try:
            self._api_servicer = DagsterApiServer(
                server_termination_event=self._server_termination_event,
                loadable_target_origin=loadable_target_origin,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                lazy_load_user_code=lazy_load_user_code,
                fixed_server_id=fixed_server_id,
                entry_point=entry_point,
                container_image=container_image,
                container_context=container_context,
                inject_env_vars_from_instance=inject_env_vars_from_instance,
                instance_ref=instance_ref,
                location_name=location_name,
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


def wait_for_grpc_server(server_process, client, subprocess_args, timeout=60):
    start_time = time.time()

    last_error = None

    while True:
        try:
            client.ping("")
            return
        except DagsterUserCodeUnreachableError:
            last_error = serializable_error_info_from_exc_info(sys.exc_info())

        if timeout > 0 and (time.time() - start_time > timeout):
            raise Exception(
                f"Timed out waiting for gRPC server to start after {timeout}s with arguments:"
                f" \"{' '.join(subprocess_args)}\". Most recent connection error: {str(last_error)}"
            )

        if server_process.poll() is not None:
            raise Exception(
                f"gRPC server exited with return code {server_process.returncode} while starting up"
                f" with the command: \"{' '.join(subprocess_args)}\""
            )

        sleep(0.1)


def open_server_process(
    instance_ref: InstanceRef,
    port: Optional[int],
    socket: Optional[str],
    location_name: Optional[str] = None,
    loadable_target_origin: Optional[LoadableTargetOrigin] = None,
    max_workers: Optional[int] = None,
    heartbeat: bool = False,
    heartbeat_timeout: int = 30,
    fixed_server_id: Optional[str] = None,
    startup_timeout: int = 20,
    cwd: Optional[str] = None,
    log_level: str = "INFO",
    env: Optional[Dict[str, str]] = None,
):
    check.invariant((port or socket) and not (port and socket), "Set only port or socket")
    check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
    check.opt_int_param(max_workers, "max_workers")

    from dagster._core.test_utils import get_mocked_system_timezone

    mocked_system_timezone = get_mocked_system_timezone()

    executable_path = loadable_target_origin.executable_path if loadable_target_origin else None

    subprocess_args = (
        get_python_environment_entry_point(executable_path or sys.executable)
        + ["api", "grpc"]
        + ["--lazy-load-user-code"]
        + (["--port", str(port)] if port else [])
        + (["--socket", socket] if socket else [])
        + (["-n", str(max_workers)] if max_workers else [])
        + (["--heartbeat"] if heartbeat else [])
        + (["--heartbeat-timeout", str(heartbeat_timeout)] if heartbeat_timeout else [])
        + (["--fixed-server-id", fixed_server_id] if fixed_server_id else [])
        + (["--override-system-timezone", mocked_system_timezone] if mocked_system_timezone else [])
        + (["--log-level", log_level])
        # only use the Python environment if it has been explicitly set in the workspace
        + (["--use-python-environment-entry-point"] if executable_path else [])
        + (["--inject-env-vars-from-instance"])
        + (["--instance-ref", serialize_dagster_namedtuple(instance_ref)])
        + (["--location-name", location_name] if location_name else [])
    )

    if loadable_target_origin:
        subprocess_args += loadable_target_origin.get_cli_args()

    server_process = open_ipc_subprocess(subprocess_args, cwd=cwd, env=env)

    from dagster._grpc.client import DagsterGrpcClient

    client = DagsterGrpcClient(
        port=port,
        socket=socket,
        host="localhost",
    )

    try:
        wait_for_grpc_server(server_process, client, subprocess_args, timeout=startup_timeout)
    except:
        if server_process.poll() is None:
            server_process.terminate()
        raise

    return server_process


def _open_server_process_on_dynamic_port(
    instance_ref: InstanceRef,
    location_name: Optional[str] = None,
    max_retries: int = 10,
    loadable_target_origin: Optional[LoadableTargetOrigin] = None,
    max_workers: Optional[int] = None,
    heartbeat: bool = False,
    heartbeat_timeout: int = 30,
    fixed_server_id: Optional[str] = None,
    startup_timeout: int = 20,
    cwd: Optional[str] = None,
    log_level: str = "INFO",
    env: Optional[Dict[str, str]] = None,
) -> Tuple[Optional[Popen[str]], Optional[int]]:
    server_process = None
    retries = 0
    port = None
    while server_process is None and retries < max_retries:
        port = find_free_port()
        try:
            server_process = open_server_process(
                instance_ref=instance_ref,
                location_name=location_name,
                port=port,
                socket=None,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                fixed_server_id=fixed_server_id,
                startup_timeout=startup_timeout,
                cwd=cwd,
                log_level=log_level,
                env=env,
            )
        except CouldNotBindGrpcServerToAddress:
            pass

        retries += 1

    return server_process, port


class GrpcServerProcess:
    def __init__(
        self,
        instance_ref: InstanceRef,
        location_name: Optional[str] = None,
        loadable_target_origin: Optional[LoadableTargetOrigin] = None,
        force_port: bool = False,
        max_retries: int = 10,
        max_workers: Optional[int] = None,
        heartbeat: bool = False,
        heartbeat_timeout: int = 30,
        fixed_server_id: Optional[str] = None,
        startup_timeout: int = 20,
        cwd: Optional[str] = None,
        log_level: str = "INFO",
        env: Optional[Dict[str, str]] = None,
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
        check.opt_str_param(fixed_server_id, "fixed_server_id")
        check.int_param(startup_timeout, "startup_timeout")
        check.invariant(
            max_workers is None or max_workers > 1 if heartbeat else True,
            (
                "max_workers must be greater than 1 or set to None if heartbeat is True. "
                "If set to None, the server will use the gRPC default."
            ),
        )

        if seven.IS_WINDOWS or force_port:
            self.server_process, self.port = _open_server_process_on_dynamic_port(
                instance_ref=instance_ref,
                location_name=location_name,
                max_retries=max_retries,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                fixed_server_id=fixed_server_id,
                startup_timeout=startup_timeout,
                cwd=cwd,
                log_level=log_level,
                env=env,
            )
        else:
            self.socket = safe_tempfile_path_unmanaged()

            self.server_process = open_server_process(
                instance_ref=instance_ref,
                location_name=location_name,
                port=None,
                socket=self.socket,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
                fixed_server_id=fixed_server_id,
                startup_timeout=startup_timeout,
                cwd=cwd,
                log_level=log_level,
                env=env,
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
        from dagster._grpc.client import EphemeralDagsterGrpcClient

        return EphemeralDagsterGrpcClient(
            port=self.port, socket=self.socket, server_process=self.server_process
        )
