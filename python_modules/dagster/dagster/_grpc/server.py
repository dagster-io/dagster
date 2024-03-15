import json
import logging
import math
import multiprocessing
import os
import queue
import sys
import threading
import time
import uuid
import warnings
from contextlib import ExitStack
from functools import update_wrapper
from threading import Event as ThreadingEventType
from time import sleep
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    cast,
)

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

import dagster._check as check
import dagster._seven as seven
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.reconstruct import ReconstructableRepository
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.errors import (
    DagsterUserCodeLoadError,
    DagsterUserCodeUnreachableError,
    user_code_error_boundary,
)
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.libraries import DagsterLibraryRegistry
from dagster._core.origin import DEFAULT_DAGSTER_ENTRY_POINT, get_python_environment_entry_point
from dagster._core.remote_representation.external_data import (
    ExternalJobSubsetResult,
    ExternalPartitionExecutionErrorData,
    ExternalRepositoryErrorData,
    ExternalScheduleExecutionErrorData,
    ExternalSensorExecutionErrorData,
    external_job_data_from_def,
    external_repository_data_from_def,
)
from dagster._core.remote_representation.origin import ExternalRepositoryOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import FuturesAwareThreadPoolExecutor, RequestUtilizationMetrics
from dagster._core.workspace.autodiscovery import LoadableTarget
from dagster._serdes import deserialize_value, serialize_value
from dagster._serdes.ipc import IPCErrorMessage, open_ipc_subprocess
from dagster._utils import (
    find_free_port,
    get_run_crash_explanation,
    safe_tempfile_path_unmanaged,
)
from dagster._utils.container import (
    ContainerUtilizationMetrics,
    retrieve_containerized_utilization_metrics,
)
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.typed_dict import init_optional_typeddict

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
    ExecuteExternalJobArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    GetCurrentImageResult,
    GetCurrentRunsResult,
    JobSubsetSnapshotArgs,
    ListRepositoriesResponse,
    LoadableRepositorySymbol,
    PartitionArgs,
    PartitionNamesArgs,
    PartitionSetExecutionParamArgs,
    SensorExecutionArgs,
    ShutdownServerResult,
    StartRunResult,
)
from .utils import (
    default_grpc_server_shutdown_grace_period,
    get_loadable_targets,
    max_rx_bytes,
    max_send_bytes,
)

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event as MPEvent
    from subprocess import Popen

EVENT_QUEUE_POLL_INTERVAL = 0.1

CLEANUP_TICK = 0.5

STREAMING_CHUNK_SIZE = 4000000

UTILIZATION_METRICS_RETRIEVAL_INTERVAL = 30

_METRICS_LOCK = threading.Lock()
METRICS_RETRIEVAL_FUNCTIONS = set()


class GrpcApiMetrics(TypedDict):
    current_request_count: Optional[int]


class DagsterCodeServerUtilizationMetrics(TypedDict):
    container_utilization: ContainerUtilizationMetrics
    request_utilization: RequestUtilizationMetrics
    per_api_metrics: Dict[str, GrpcApiMetrics]


_UTILIZATION_METRICS = init_optional_typeddict(DagsterCodeServerUtilizationMetrics)


def _update_threadpool_metrics(executor: FuturesAwareThreadPoolExecutor) -> None:
    with _METRICS_LOCK:
        _UTILIZATION_METRICS.update(
            {
                "request_utilization": executor.get_current_utilization_metrics(),
            }
        )


def _record_utilization_metrics(logger: logging.Logger) -> None:
    with _METRICS_LOCK:
        last_cpu_measurement_time = _UTILIZATION_METRICS["container_utilization"][
            "measurement_timestamp"
        ]
        last_cpu_measurement = _UTILIZATION_METRICS["container_utilization"]["cpu_usage"]
        utilization_metrics = retrieve_containerized_utilization_metrics(
            logger, last_cpu_measurement_time, last_cpu_measurement
        )
        for key, val in utilization_metrics.items():
            _UTILIZATION_METRICS["container_utilization"][key] = val


class CouldNotBindGrpcServerToAddress(Exception):
    pass


def _get_request_count(api_name: str) -> Optional[int]:
    if api_name not in _UTILIZATION_METRICS["per_api_metrics"]:
        return None
    return _UTILIZATION_METRICS["per_api_metrics"][api_name]["current_request_count"]


def _set_request_count(api_name: str, value: Any) -> None:
    if api_name not in _UTILIZATION_METRICS["per_api_metrics"]:
        _UTILIZATION_METRICS["per_api_metrics"][api_name] = init_optional_typeddict(GrpcApiMetrics)
    _UTILIZATION_METRICS["per_api_metrics"][api_name]["current_request_count"] = value


def retrieve_metrics():
    class _MetricsRetriever:
        def __call__(self, fn: Callable[..., Any]) -> Callable:
            api_call = fn.__name__
            METRICS_RETRIEVAL_FUNCTIONS.add(api_call)

            def wrapper(self: "DagsterApiServer", request: Any, context: grpc.ServicerContext):
                if not self._enable_metrics:
                    # If metrics retrieval is disabled, short circuit to just calling the underlying function.
                    return fn(self, request, context)
                # Only record utilization metrics on ping, so as to not over-burden with IO.
                if fn.__name__ == "Ping":
                    _update_threadpool_metrics(self._server_threadpool_executor)
                    _record_utilization_metrics(self._logger)
                with _METRICS_LOCK:
                    cur_request_count = _get_request_count(api_call)
                    _set_request_count(api_call, cur_request_count + 1 if cur_request_count else 1)

                res = fn(self, request, context)

                with _METRICS_LOCK:
                    cur_request_count = _get_request_count(api_call)
                    _set_request_count(api_call, cur_request_count - 1 if cur_request_count else 0)

                return res

            update_wrapper(wrapper, fn)
            return wrapper

    return _MetricsRetriever()


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

        with user_code_error_boundary(
            DagsterUserCodeLoadError,
            lambda: "Error occurred during the loading of Dagster definitions in\n"
            + ", ".join(
                [f"{k}={v}" for k, v in loadable_target_origin._asdict().items() if v is not None]
            ),
        ):
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
            with user_code_error_boundary(
                DagsterUserCodeLoadError,
                lambda: "Error occurred during the loading of Dagster definitions in "
                + pointer.describe(),
            ):
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
        logger: logging.Logger,
        server_threadpool_executor: FuturesAwareThreadPoolExecutor,
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
        enable_metrics: bool = False,
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
        self._logger = logger

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
            check.sequence_param(entry_point, "entry_point", of_type=str)
            if entry_point is not None
            else DEFAULT_DAGSTER_ENTRY_POINT
        )

        self._container_image = check.opt_str_param(container_image, "container_image")
        self._container_context = check.opt_dict_param(container_context, "container_context")

        # When will this be set in a gRPC server?
        #  - When running `dagster dev` (or `dagster-webserver`) in the gRPC server subprocesses that are spun up
        #  - When running code in Dagster Cloud on 1.1 or later
        # When will it not be set?
        #  - When running your own grpc server with `dagster api grpc`
        #  - When using an integration that spins up gRPC servers (for example, the Dagster Helm
        #    chart or the deploy_docker example)
        self._instance_ref = check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
        self._exit_stack = ExitStack()

        self._enable_metrics = check.bool_param(enable_metrics, "enable_metrics")
        self._server_threadpool_executor = server_threadpool_executor

        try:
            if inject_env_vars_from_instance:
                from dagster._cli.utils import get_instance_for_cli

                # If arguments indicate it wants to load env vars, use the passed-in instance
                # ref (or the dagster.yaml on the filesystem if no instance ref is provided)
                self._instance = self._exit_stack.enter_context(
                    get_instance_for_cli(instance_ref=instance_ref)
                )
                self._instance.inject_env_vars(location_name)

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
            self._logger.exception("Error while importing code")

        self.__last_heartbeat_time = time.time()
        if heartbeat:
            self.__heartbeat_thread: Optional[threading.Thread] = threading.Thread(
                target=self._heartbeat_thread,
                args=(heartbeat_timeout,),
                name="grpc-server-heartbeat",
                daemon=True,
            )
            self.__heartbeat_thread.start()
        else:
            self.__heartbeat_thread = None

        self.__cleanup_thread = threading.Thread(
            target=self._cleanup_thread,
            args=(),
            name="grpc-server-cleanup",
            daemon=True,
        )

        self.__cleanup_thread.start()

    def cleanup(self) -> None:
        # In case ShutdownServer was not called
        self._shutdown_once_executions_finish_event.set()
        if self.__heartbeat_thread:
            self.__heartbeat_thread.join()
        self.__cleanup_thread.join()

        self._exit_stack.close()

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

    def ReloadCode(
        self, _request: api_pb2.ReloadCodeRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ReloadCodeReply:
        self._logger.warn(
            "Reloading definitions from a code server launched via `dagster api grpc` "
            "without restarting the process is not currently supported. To enable this functionality, "
            "launch the code server with the `dagster code-server start` command instead."
        )

        return api_pb2.ReloadCodeReply()

    @retrieve_metrics()
    def Ping(self, request, _context: grpc.ServicerContext) -> api_pb2.PingReply:
        echo = request.echo

        return api_pb2.PingReply(
            echo=echo,
            serialized_server_utilization_metrics=json.dumps(_UTILIZATION_METRICS)
            if self._enable_metrics
            else "",
        )

    def StreamingPing(
        self, request: api_pb2.StreamingPingRequest, _context: grpc.ServicerContext
    ) -> Iterator[api_pb2.StreamingPingEvent]:
        sequence_length = request.sequence_length
        echo = request.echo
        for sequence_number in range(sequence_length):
            yield api_pb2.StreamingPingEvent(sequence_number=sequence_number, echo=echo)

    def Heartbeat(
        self, request: api_pb2.StreamingPingRequest, _context: grpc.ServicerContext
    ) -> api_pb2.PingReply:
        self.__last_heartbeat_time = time.time()
        echo = request.echo
        return api_pb2.PingReply(echo=echo)

    def GetServerId(
        self, _request: api_pb2.Empty, _context: grpc.ServicerContext
    ) -> api_pb2.GetServerIdReply:
        return api_pb2.GetServerIdReply(server_id=self._server_id)

    def ExecutionPlanSnapshot(
        self, request: api_pb2.ExecutionPlanSnapshotRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExecutionPlanSnapshotReply:
        execution_plan_args = deserialize_value(
            request.serialized_execution_plan_snapshot_args,
            ExecutionPlanSnapshotArgs,
        )

        execution_plan_snapshot_or_error = get_external_execution_plan_snapshot(
            self._get_repo_for_origin(execution_plan_args.job_origin.external_repository_origin),
            execution_plan_args.job_origin.job_name,
            execution_plan_args,
        )
        return api_pb2.ExecutionPlanSnapshotReply(
            serialized_execution_plan_snapshot=serialize_value(execution_plan_snapshot_or_error)
        )

    def ListRepositories(
        self, request: api_pb2.ListRepositoriesRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ListRepositoriesReply:
        if self._serializable_load_error:
            return api_pb2.ListRepositoriesReply(
                serialized_list_repositories_response_or_error=serialize_value(
                    self._serializable_load_error
                )
            )
        try:
            loaded_repositories = check.not_none(self._loaded_repositories)
            serialized_response = serialize_value(
                ListRepositoriesResponse(
                    loaded_repositories.loadable_repository_symbols,
                    executable_path=(
                        self._loadable_target_origin.executable_path
                        if self._loadable_target_origin
                        else None
                    ),
                    repository_code_pointer_dict=loaded_repositories.code_pointers_by_repo_name,
                    entry_point=self._entry_point,
                    container_image=self._container_image,
                    container_context=self._container_context,
                    dagster_library_versions=DagsterLibraryRegistry.get(),
                )
            )
        except Exception:
            serialized_response = serialize_value(
                serializable_error_info_from_exc_info(sys.exc_info())
            )

        return api_pb2.ListRepositoriesReply(
            serialized_list_repositories_response_or_error=serialized_response
        )

    def ExternalPartitionNames(
        self, request: api_pb2.ExternalPartitionNamesRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalPartitionNamesReply:
        try:
            partition_names_args = deserialize_value(
                request.serialized_partition_names_args,
                PartitionNamesArgs,
            )
            serialized_response = serialize_value(
                get_partition_names(
                    self._get_repo_for_origin(partition_names_args.repository_origin),
                    partition_names_args.partition_set_name,
                )
            )
        except Exception:
            serialized_response = serialize_value(
                ExternalPartitionExecutionErrorData(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

        return api_pb2.ExternalPartitionNamesReply(
            serialized_external_partition_names_or_external_partition_execution_error=serialized_response
        )

    def ExternalNotebookData(
        self, request: api_pb2.ExternalNotebookDataRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalNotebookDataReply:
        notebook_path = request.notebook_path
        check.str_param(notebook_path, "notebook_path")
        return api_pb2.ExternalNotebookDataReply(content=get_notebook_data(notebook_path))

    def ExternalPartitionSetExecutionParams(
        self,
        request: api_pb2.ExternalPartitionSetExecutionParamsRequest,
        _context: grpc.ServicerContext,
    ) -> Iterable[api_pb2.StreamingChunkEvent]:
        try:
            args = deserialize_value(
                request.serialized_partition_set_execution_param_args,
                PartitionSetExecutionParamArgs,
            )

            instance_ref = args.instance_ref if args.instance_ref else self._instance_ref

            serialized_data = serialize_value(
                get_partition_set_execution_param_data(
                    self._get_repo_for_origin(args.repository_origin),
                    partition_set_name=args.partition_set_name,
                    partition_names=args.partition_names,
                    instance_ref=instance_ref,
                )
            )
        except Exception:
            serialized_data = serialize_value(
                ExternalPartitionExecutionErrorData(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

        yield from self._split_serialized_data_into_chunk_events(serialized_data)

    def ExternalPartitionConfig(
        self, request: api_pb2.ExternalPartitionConfigRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalPartitionConfigReply:
        try:
            args = deserialize_value(request.serialized_partition_args, PartitionArgs)

            instance_ref = args.instance_ref if args.instance_ref else self._instance_ref

            serialized_data = serialize_value(
                get_partition_config(
                    self._get_repo_for_origin(args.repository_origin),
                    args.partition_set_name,
                    args.partition_name,
                    instance_ref=instance_ref,
                )
            )
        except Exception:
            serialized_data = serialize_value(
                ExternalPartitionExecutionErrorData(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

        return api_pb2.ExternalPartitionConfigReply(
            serialized_external_partition_config_or_external_partition_execution_error=serialized_data
        )

    def ExternalPartitionTags(
        self, request: api_pb2.ExternalPartitionTagsRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalPartitionTagsReply:
        try:
            partition_args = deserialize_value(request.serialized_partition_args, PartitionArgs)

            instance_ref = (
                partition_args.instance_ref if partition_args.instance_ref else self._instance_ref
            )

            serialized_data = serialize_value(
                get_partition_tags(
                    self._get_repo_for_origin(partition_args.repository_origin),
                    partition_args.partition_set_name,
                    partition_args.partition_name,
                    instance_ref=instance_ref,
                )
            )
        except Exception:
            serialized_data = serialize_value(
                ExternalPartitionExecutionErrorData(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

        return api_pb2.ExternalPartitionTagsReply(
            serialized_external_partition_tags_or_external_partition_execution_error=serialized_data
        )

    def ExternalPipelineSubsetSnapshot(
        self, request: api_pb2.ExternalPipelineSubsetSnapshotRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalPipelineSubsetSnapshotReply:
        try:
            job_subset_snapshot_args = deserialize_value(
                request.serialized_pipeline_subset_snapshot_args,
                JobSubsetSnapshotArgs,
            )
            serialized_external_pipeline_subset_result = serialize_value(
                get_external_pipeline_subset_result(
                    self._get_repo_for_origin(
                        job_subset_snapshot_args.job_origin.external_repository_origin
                    ),
                    job_subset_snapshot_args.job_origin.job_name,
                    job_subset_snapshot_args.op_selection,
                    job_subset_snapshot_args.asset_selection,
                    job_subset_snapshot_args.asset_check_selection,
                    job_subset_snapshot_args.include_parent_snapshot,
                )
            )
        except Exception:
            serialized_external_pipeline_subset_result = serialize_value(
                ExternalJobSubsetResult(
                    success=False, error=serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

        return api_pb2.ExternalPipelineSubsetSnapshotReply(
            serialized_external_pipeline_subset_result=serialized_external_pipeline_subset_result
        )

    def _get_serialized_external_repository_data(
        self, request: api_pb2.ExternalRepositoryRequest
    ) -> str:
        try:
            repository_origin = deserialize_value(
                request.serialized_repository_python_origin,
                ExternalRepositoryOrigin,
            )

            return serialize_value(
                external_repository_data_from_def(
                    self._get_repo_for_origin(repository_origin),
                    defer_snapshots=request.defer_snapshots,
                )
            )
        except Exception:
            return serialize_value(
                ExternalRepositoryErrorData(serializable_error_info_from_exc_info(sys.exc_info()))
            )

    def ExternalRepository(
        self, request: api_pb2.ExternalRepositoryRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalRepositoryReply:
        serialized_external_repository_data = self._get_serialized_external_repository_data(request)

        return api_pb2.ExternalRepositoryReply(
            serialized_external_repository_data=serialized_external_repository_data,
        )

    def ExternalJob(
        self, request: api_pb2.ExternalJobRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalJobReply:
        try:
            repository_origin = deserialize_value(
                request.serialized_repository_origin,
                ExternalRepositoryOrigin,
            )

            job_def = self._get_repo_for_origin(repository_origin).get_job(request.job_name)
            ser_job_data = serialize_value(
                external_job_data_from_def(job_def, include_parent_snapshot=True)
            )
            return api_pb2.ExternalJobReply(serialized_job_data=ser_job_data)
        except Exception:
            return api_pb2.ExternalJobReply(
                serialized_error=serialize_value(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

    def StreamingExternalRepository(
        self, request: api_pb2.ExternalRepositoryRequest, _context: grpc.ServicerContext
    ) -> Iterable[api_pb2.StreamingExternalRepositoryEvent]:
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

    def _split_serialized_data_into_chunk_events(
        self, serialized_data: str
    ) -> Iterable[api_pb2.StreamingChunkEvent]:
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

    def ExternalScheduleExecution(
        self, request: api_pb2.ExternalScheduleExecutionRequest, _context: grpc.ServicerContext
    ) -> Iterable[api_pb2.StreamingChunkEvent]:
        yield from self._split_serialized_data_into_chunk_events(
            self._external_schedule_execution(request)
        )

    def SyncExternalScheduleExecution(self, request, _context: grpc.ServicerContext):
        return api_pb2.ExternalScheduleExecutionReply(
            serialized_schedule_result=self._external_schedule_execution(request)
        )

    def _external_schedule_execution(
        self, request: api_pb2.ExternalScheduleExecutionRequest
    ) -> str:
        try:
            args = deserialize_value(
                request.serialized_external_schedule_execution_args,
                ExternalScheduleExecutionArgs,
            )
            return serialize_value(
                get_external_schedule_execution(
                    self._get_repo_for_origin(args.repository_origin),
                    args.instance_ref,
                    args.schedule_name,
                    args.scheduled_execution_timestamp,
                    args.scheduled_execution_timezone,
                    args.log_key,
                )
            )
        except Exception:
            return serialize_value(
                ExternalScheduleExecutionErrorData(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

    def _external_sensor_execution(self, request: api_pb2.ExternalSensorExecutionRequest) -> str:
        try:
            args = deserialize_value(
                request.serialized_external_sensor_execution_args,
                SensorExecutionArgs,
            )

            return serialize_value(
                get_external_sensor_execution(
                    self._get_repo_for_origin(args.repository_origin),
                    args.instance_ref,
                    args.sensor_name,
                    args.last_tick_completion_time,
                    args.last_run_key,
                    args.cursor,
                    args.log_key,
                    args.last_sensor_start_time,
                )
            )
        except Exception:
            return serialize_value(
                ExternalSensorExecutionErrorData(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

    @retrieve_metrics()
    def SyncExternalSensorExecution(
        self, request: api_pb2.ExternalSensorExecutionRequest, _context: grpc.ServicerContext
    ) -> api_pb2.ExternalSensorExecutionReply:
        return api_pb2.ExternalSensorExecutionReply(
            serialized_sensor_result=self._external_sensor_execution(request)
        )

    @retrieve_metrics()
    def ExternalSensorExecution(
        self, request: api_pb2.ExternalSensorExecutionRequest, _context: grpc.ServicerContext
    ) -> Iterable[api_pb2.StreamingChunkEvent]:
        yield from self._split_serialized_data_into_chunk_events(
            self._external_sensor_execution(request)
        )

    def ShutdownServer(
        self, request: api_pb2.Empty, _context: grpc.ServicerContext
    ) -> api_pb2.ShutdownServerReply:
        try:
            self._shutdown_once_executions_finish_event.set()
            return api_pb2.ShutdownServerReply(
                serialized_shutdown_server_result=serialize_value(
                    ShutdownServerResult(success=True, serializable_error_info=None)
                )
            )
        except:
            self._logger.exception("Failed to shut down server")
            return api_pb2.ShutdownServerReply(
                serialized_shutdown_server_result=serialize_value(
                    ShutdownServerResult(
                        success=False,
                        serializable_error_info=serializable_error_info_from_exc_info(
                            sys.exc_info()
                        ),
                    )
                )
            )

    def CancelExecution(
        self, request: api_pb2.CancelExecutionRequest, _context: grpc.ServicerContext
    ) -> api_pb2.CancelExecutionReply:
        success = False
        message = None
        serializable_error_info = None
        try:
            cancel_execution_request = deserialize_value(
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
            serialized_cancel_execution_result=serialize_value(
                CancelExecutionResult(
                    success=success,
                    message=message,
                    serializable_error_info=serializable_error_info,
                )
            )
        )

    def CanCancelExecution(
        self, request: api_pb2.CanCancelExecutionRequest, _context: grpc.ServicerContext
    ) -> api_pb2.CanCancelExecutionReply:
        can_cancel_execution_request = deserialize_value(
            request.serialized_can_cancel_execution_request,
            CanCancelExecutionRequest,
        )
        with self._execution_lock:
            run_id = can_cancel_execution_request.run_id
            can_cancel = (
                run_id in self._executions and not self._termination_events[run_id].is_set()
            )

        return api_pb2.CanCancelExecutionReply(
            serialized_can_cancel_execution_result=serialize_value(
                CanCancelExecutionResult(can_cancel=can_cancel)
            )
        )

    def StartRun(
        self, request: api_pb2.StartRunRequest, _context: grpc.ServicerContext
    ) -> api_pb2.StartRunReply:
        if self._shutdown_once_executions_finish_event.is_set():
            return api_pb2.StartRunReply(
                serialized_start_run_result=serialize_value(
                    StartRunResult(
                        success=False,
                        message="Tried to start a run on a server after telling it to shut down",
                        serializable_error_info=None,
                    )
                )
            )

        try:
            execute_external_job_args = deserialize_value(
                request.serialized_execute_run_args,
                ExecuteExternalJobArgs,
            )
            run_id = execute_external_job_args.run_id

            # reconstructable required for handing execution off to subprocess
            recon_repo = check.not_none(self._loaded_repositories).reconstructables_by_name[
                execute_external_job_args.job_origin.external_repository_origin.repository_name
            ]
            recon_job = recon_repo.get_reconstructable_job(
                execute_external_job_args.job_origin.job_name
            )

        except:
            return api_pb2.StartRunReply(
                serialized_start_run_result=serialize_value(
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
                recon_job,
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
                check.not_none(execute_external_job_args.instance_ref),
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
                        f"GRPC server: Subprocess for {run_id} terminated unexpectedly with "
                        f"exit code {execution_process.exitcode}"
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
            serialized_start_run_result=serialize_value(
                StartRunResult(
                    success=success,
                    message=message,
                    serializable_error_info=serializable_error_info,
                )
            )
        )

    def GetCurrentImage(
        self, request: api_pb2.Empty, _context: grpc.ServicerContext
    ) -> api_pb2.GetCurrentImageReply:
        return api_pb2.GetCurrentImageReply(
            serialized_current_image=serialize_value(
                GetCurrentImageResult(
                    current_image=self._container_image, serializable_error_info=None
                )
            )
        )

    def GetCurrentRuns(
        self, request: api_pb2.Empty, _context: grpc.ServicerContext
    ) -> api_pb2.GetCurrentRunsReply:
        with self._execution_lock:
            return api_pb2.GetCurrentRunsReply(
                serialized_current_runs=serialize_value(
                    GetCurrentRunsResult(
                        current_runs=list(self._executions.keys()), serializable_error_info=None
                    )
                )
            )


def server_termination_target(termination_event, server, logger):
    termination_event.wait()

    shutdown_grace_period = default_grpc_server_shutdown_grace_period()

    logger.info(
        f"Stopping server once all current RPC calls terminate or {shutdown_grace_period} seconds"
        " pass"
    )
    finished_shutting_down_rpcs_event = server.stop(grace=shutdown_grace_period)
    finished_shutting_down_rpcs_event.wait(shutdown_grace_period + 5)
    if not finished_shutting_down_rpcs_event.is_set():
        logger.warning("Server did not shut down cleanly")


class DagsterGrpcServer:
    def __init__(
        self,
        server_termination_event: threading.Event,
        dagster_api_servicer: DagsterApiServicer,
        logger: logging.Logger,
        threadpool_executor: FuturesAwareThreadPoolExecutor,
        host="localhost",
        port: Optional[int] = None,
        socket: Optional[str] = None,
        enable_metrics: bool = False,
    ):
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

        self._logger = logger

        self._enable_metrics = check.bool_param(enable_metrics, "enable_metrics")

        self._threadpool_executor = threadpool_executor
        if self._enable_metrics:
            _update_threadpool_metrics(self._threadpool_executor)

        self.server = grpc.server(
            self._threadpool_executor,
            compression=grpc.Compression.Gzip,
            options=[
                ("grpc.max_send_message_length", max_send_bytes()),
                ("grpc.max_receive_message_length", max_rx_bytes()),
            ],
        )
        self._server_termination_event = server_termination_event
        self._api_servicer = dagster_api_servicer

        # Create a health check servicer
        self._health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(self._health_servicer, self.server)

        add_DagsterApiServicer_to_server(self._api_servicer, self.server)

        if port:
            server_address = host + ":" + str(port)
        else:
            server_address = "unix:" + os.path.abspath(check.not_none(socket))

        # grpc.Server.add_insecure_port returns:
        # - 0 on failure
        # - port number when a port is successfully bound
        # - 1 when a UDS is successfully bound
        res = self.server.add_insecure_port(server_address)
        if socket and res != 1:
            raise CouldNotBindGrpcServerToAddress(socket)
        if port and res != port:
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

        self._health_servicer.set("DagsterApi", health_pb2.HealthCheckResponse.SERVING)

        server_termination_thread = threading.Thread(
            target=server_termination_target,
            args=[self._server_termination_event, self.server, self._logger],
            name="grpc-server-termination",
            daemon=True,
        )

        server_termination_thread.start()

        try:
            self.server.wait_for_termination()
        finally:
            self._api_servicer.cleanup()
            server_termination_thread.join()


class CouldNotStartServerProcess(Exception):
    def __init__(self, port=None, socket=None):
        super(CouldNotStartServerProcess, self).__init__(
            "Could not start server with "
            + (f"port {port}" if port is not None else f"socket {socket}")
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
                f" \"{' '.join(subprocess_args)}\". Most recent connection error: {last_error}"
            )

        if server_process.poll() is not None:
            raise Exception(
                f"gRPC server exited with return code {server_process.returncode} while starting up"
                f" with the command: \"{' '.join(subprocess_args)}\""
            )

        sleep(0.1)


def open_server_process(
    instance_ref: Optional[InstanceRef],
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
    inject_env_vars_from_instance: bool = True,
    container_image: Optional[str] = None,
    container_context: Optional[Dict[str, Any]] = None,
    enable_metrics: bool = False,
):
    check.invariant((port or socket) and not (port and socket), "Set only port or socket")
    check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
    check.opt_int_param(max_workers, "max_workers")

    executable_path = loadable_target_origin.executable_path if loadable_target_origin else None

    subprocess_args = [
        *get_python_environment_entry_point(executable_path or sys.executable),
        *["api", "grpc"],
        *["--lazy-load-user-code"],
        *(["--port", str(port)] if port else []),
        *(["--socket", socket] if socket else []),
        *(["-n", str(max_workers)] if max_workers else []),
        *(["--heartbeat"] if heartbeat else []),
        *(["--heartbeat-timeout", str(heartbeat_timeout)] if heartbeat_timeout else []),
        *(["--fixed-server-id", fixed_server_id] if fixed_server_id else []),
        *(["--log-level", log_level]),
        # only use the Python environment if it has been explicitly set in the workspace,
        *(["--use-python-environment-entry-point"] if executable_path else []),
        *(["--inject-env-vars-from-instance"] if inject_env_vars_from_instance else []),
        *(["--instance-ref", serialize_value(instance_ref)] if instance_ref else []),
        *(["--location-name", location_name] if location_name else []),
        *(["--container-image", container_image] if container_image else []),
        *(["--container-context", json.dumps(container_context)] if container_context else []),
        *(["--enable-metrics"] if enable_metrics else []),
    ]

    if loadable_target_origin:
        subprocess_args += loadable_target_origin.get_cli_args()

    env = {
        **(env or os.environ),
    }

    # Unset click environment variables in the current environment
    # that might conflict with arguments that we're using
    if port and "DAGSTER_GRPC_SOCKET" in env:
        del env["DAGSTER_GRPC_SOCKET"]

    if socket and "DAGSTER_GRPC_PORT" in env:
        del env["DAGSTER_GRPC_PORT"]

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
    max_retries: int = 10,
    **kwargs,
) -> Tuple[Optional["Popen[str]"], Optional[int]]:
    server_process = None
    retries = 0
    port = None
    while server_process is None and retries < max_retries:
        port = find_free_port()
        try:
            server_process = open_server_process(port=port, socket=None, **kwargs)
        except CouldNotBindGrpcServerToAddress:
            pass

        retries += 1

    return server_process, port


class GrpcServerProcess:
    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
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
        wait_on_exit=False,
        inject_env_vars_from_instance: bool = True,
        container_image: Optional[str] = None,
        container_context: Optional[Dict[str, Any]] = None,
    ):
        self.port = None
        self.socket = None
        self._waited = False
        self._shutdown = False
        self._heartbeat = heartbeat
        self._server_process = None

        self.loadable_target_origin = check.opt_inst_param(
            loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
        )
        check.bool_param(force_port, "force_port")
        check.int_param(max_retries, "max_retries")
        check.opt_int_param(max_workers, "max_workers")
        check.int_param(heartbeat_timeout, "heartbeat_timeout")
        check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")
        check.opt_str_param(fixed_server_id, "fixed_server_id")
        check.int_param(startup_timeout, "startup_timeout")
        check.invariant(
            max_workers is None or max_workers > 1 if heartbeat else True,
            "max_workers must be greater than 1 or set to None if heartbeat is True. "
            "If set to None, the server will use the gRPC default.",
        )

        if seven.IS_WINDOWS or force_port:
            server_process, self.port = _open_server_process_on_dynamic_port(
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
                inject_env_vars_from_instance=inject_env_vars_from_instance,
                container_image=container_image,
                container_context=container_context,
            )
        else:
            self.socket = safe_tempfile_path_unmanaged()

            server_process = open_server_process(
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
                inject_env_vars_from_instance=inject_env_vars_from_instance,
                container_image=container_image,
                container_context=container_context,
            )

        if server_process is None:
            raise CouldNotStartServerProcess(port=self.port, socket=self.socket)
        else:
            self._server_process = server_process

        self._wait_on_exit = wait_on_exit

    @property
    def server_process(self):
        return check.not_none(self._server_process)

    @property
    def pid(self):
        return self.server_process.pid

    def wait(self, timeout=30):
        self._waited = True
        if self.server_process.poll() is None:
            seven.wait_for_process(self.server_process, timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.shutdown_server()

        if self._wait_on_exit:
            self.wait()

    def shutdown_server(self):
        if self._server_process and not self._shutdown:
            self._shutdown = True
            if self.server_process.poll() is None:
                try:
                    self.create_client().shutdown_server()
                except DagsterUserCodeUnreachableError:
                    pass

    def __del__(self):
        if self._server_process and self._shutdown is False and not self._heartbeat:
            warnings.warn(
                "GrpcServerProcess without a heartbeat is being destroyed without signalling to the"
                " server that it should shut down. This may result in server processes living"
                " longer than they need to. To fix this, wrap the GrpcServerProcess in a"
                " contextmanager or call shutdown_server on it."
            )

        if (
            self._server_process
            and not self._waited
            and os.getenv("STRICT_GRPC_SERVER_PROCESS_WAIT")
        ):
            warnings.warn(
                "GrpcServerProcess is being destroyed without waiting for the process to "
                + "fully terminate. This can cause test instability."
            )

    def create_client(self):
        from dagster._grpc.client import DagsterGrpcClient

        return DagsterGrpcClient(port=self.port, socket=self.socket)
