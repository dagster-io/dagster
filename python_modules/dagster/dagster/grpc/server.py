import math
import os
import queue
import sys
import threading
import time
import uuid
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import grpc
from dagster import check, seven
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import (
    ReconstructableRepository,
    repository_def_from_target_def,
)
from dagster.core.errors import PartitionExecutionError, user_code_error_boundary
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionExecutionParamData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
    external_repository_data_from_def,
)
from dagster.core.instance import DagsterInstance
from dagster.core.origin import PipelineOrigin, RepositoryGrpcServerOrigin, RepositoryOrigin
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
from dagster.seven import get_system_temp_directory, multiprocessing
from dagster.utils import find_free_port, safe_tempfile_path_unmanaged
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import recon_repository_from_origin
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from .__generated__ import api_pb2
from .__generated__.api_pb2_grpc import DagsterApiServicer, add_DagsterApiServicer_to_server
from .impl import (
    RunInSubprocessComplete,
    StartRunInSubprocessSuccessful,
    execute_run_in_subprocess,
    get_external_execution_plan_snapshot,
    get_external_job_params,
    get_external_pipeline_subset_result,
    get_external_schedule_execution,
    start_run_in_subprocess,
)
from .types import (
    CanCancelExecutionRequest,
    CanCancelExecutionResult,
    CancelExecutionRequest,
    CancelExecutionResult,
    ExecuteRunArgs,
    ExecutionPlanSnapshotArgs,
    ExternalJobArgs,
    ExternalScheduleExecutionArgs,
    GetCurrentImageResult,
    ListRepositoriesResponse,
    LoadableRepositorySymbol,
    PartitionArgs,
    PartitionNamesArgs,
    PartitionSetExecutionParamArgs,
    PipelineSubsetSnapshotArgs,
    ShutdownServerResult,
    StartRunResult,
)
from .utils import get_loadable_targets

EVENT_QUEUE_POLL_INTERVAL = 0.1

CLEANUP_TICK = 0.5

STREAMING_EXTERNAL_REPOSITORY_CHUNK_SIZE = 4000000


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
        if loadable_target_origin.module_name:
            repository_code_pointer_dict[
                loadable_repository_symbol.repository_name
            ] = CodePointer.from_module(
                loadable_target_origin.module_name, loadable_repository_symbol.attribute,
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
    ):
        super(DagsterApiServer, self).__init__()

        check.bool_param(heartbeat, "heartbeat")
        check.int_param(heartbeat_timeout, "heartbeat_timeout")
        check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")

        self._server_termination_event = check.inst_param(
            server_termination_event, "server_termination_event", seven.ThreadingEventType
        )
        self._loadable_target_origin = check.opt_inst_param(
            loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin
        )

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
                target=self._heartbeat_thread, args=(heartbeat_timeout,),
            )
            self.__heartbeat_thread.daemon = True
            self.__heartbeat_thread.start()
        else:
            self.__heartbeat_thread = None

        self.__cleanup_thread = threading.Thread(target=self._cleanup_thread, args=(),)
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
                        message = "Pipeline execution process for {run_id} unexpectedly exited.".format(
                            run_id=run.run_id
                        )
                        instance.report_engine_event(message, run, cls=self.__class__)
                        instance.report_run_failed(run)

            for run_id in runs_to_clear:
                del self._executions[run_id]
                del self._termination_events[run_id]
                if run_id in self._termination_times:
                    del self._termination_times[run_id]

            # Once there are no more running executions after we have received a request to
            # shut down, terminate the server
            if self._shutdown_once_executions_finish_event.is_set():
                if len(self._executions) == 0:
                    self._server_termination_event.set()

    def _recon_repository_from_origin(self, repository_origin):
        check.inst_param(
            repository_origin, "repository_origin", RepositoryOrigin,
        )

        if isinstance(repository_origin, RepositoryGrpcServerOrigin):
            return ReconstructableRepository(
                self._repository_symbols_and_code_pointers.code_pointers_by_repo_name[
                    repository_origin.repository_name
                ]
            )
        return recon_repository_from_origin(repository_origin)

    def _recon_pipeline_from_origin(self, pipeline_origin):
        check.inst_param(pipeline_origin, "pipeline_origin", PipelineOrigin)
        recon_repo = self._recon_repository_from_origin(pipeline_origin.repository_origin)
        return recon_repo.get_reconstructable_pipeline(pipeline_origin.pipeline_name)

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
        definition = recon_repo.get_definition()
        partition_set_def = definition.get_partition_set_def(
            partition_names_args.partition_set_name
        )
        try:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: "Error occurred during the execution of the partition generation function for "
                "partition set {partition_set_name}".format(
                    partition_set_name=partition_set_def.name
                ),
            ):
                return api_pb2.ExternalPartitionNamesReply(
                    serialized_external_partition_names_or_external_partition_execution_error=serialize_dagster_namedtuple(
                        ExternalPartitionNamesData(
                            partition_names=partition_set_def.get_partition_names()
                        )
                    )
                )
        except PartitionExecutionError:
            return api_pb2.ExternalPartitionNamesReply(
                serialized_external_partition_names_or_external_partition_execution_error=serialize_dagster_namedtuple(
                    ExternalPartitionExecutionErrorData(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    )
                )
            )

    def ExternalPartitionSetExecutionParams(self, request, _context):
        partition_set_execution_param_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_partition_set_execution_param_args
        )

        check.inst_param(
            partition_set_execution_param_args,
            "partition_set_execution_param_args",
            PartitionSetExecutionParamArgs,
        )

        recon_repo = self._recon_repository_from_origin(
            partition_set_execution_param_args.repository_origin
        )
        definition = recon_repo.get_definition()
        partition_set_def = definition.get_partition_set_def(
            partition_set_execution_param_args.partition_set_name
        )

        try:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: "Error occurred during the partition generation for partition set "
                "{partition_set_name}".format(partition_set_name=partition_set_def.name),
            ):
                all_partitions = partition_set_def.get_partitions()
            partitions = [
                partition
                for partition in all_partitions
                if partition.name in partition_set_execution_param_args.partition_names
            ]

            partition_data = []
            for partition in partitions:

                def _error_message_fn(partition_set_name, partition_name):
                    return lambda: (
                        "Error occurred during the partition config and tag generation for "
                        "partition set {partition_set_name}::{partition_name}".format(
                            partition_set_name=partition_set_name, partition_name=partition_name
                        )
                    )

                with user_code_error_boundary(
                    PartitionExecutionError,
                    _error_message_fn(partition_set_def.name, partition.name),
                ):
                    run_config = partition_set_def.run_config_for_partition(partition)
                    tags = partition_set_def.tags_for_partition(partition)

                partition_data.append(
                    ExternalPartitionExecutionParamData(
                        name=partition.name, tags=tags, run_config=run_config,
                    )
                )

            return api_pb2.ExternalPartitionSetExecutionParamsReply(
                serialized_external_partition_set_execution_param_data_or_external_partition_execution_error=serialize_dagster_namedtuple(
                    ExternalPartitionSetExecutionParamData(partition_data=partition_data)
                )
            )

        except PartitionExecutionError:
            return api_pb2.ExternalPartitionSetExecutionParamsReply(
                ExternalPartitionExecutionErrorData(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

    def ExternalPartitionConfig(self, request, _context):
        partition_args = deserialize_json_to_dagster_namedtuple(request.serialized_partition_args)

        check.inst_param(partition_args, "partition_args", PartitionArgs)

        recon_repo = self._recon_repository_from_origin(partition_args.repository_origin)
        definition = recon_repo.get_definition()
        partition_set_def = definition.get_partition_set_def(partition_args.partition_set_name)
        partition = partition_set_def.get_partition(partition_args.partition_name)
        try:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: "Error occurred during the evaluation of the `run_config_for_partition` "
                "function for partition set {partition_set_name}".format(
                    partition_set_name=partition_set_def.name
                ),
            ):
                run_config = partition_set_def.run_config_for_partition(partition)
                return api_pb2.ExternalPartitionConfigReply(
                    serialized_external_partition_config_or_external_partition_execution_error=serialize_dagster_namedtuple(
                        ExternalPartitionConfigData(name=partition.name, run_config=run_config)
                    )
                )
        except PartitionExecutionError:
            return api_pb2.ExternalPartitionConfigReply(
                serialized_external_partition_config_or_external_partition_execution_error=serialize_dagster_namedtuple(
                    ExternalPartitionExecutionErrorData(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    )
                )
            )

    def ExternalPartitionTags(self, request, _context):
        partition_args = deserialize_json_to_dagster_namedtuple(request.serialized_partition_args)

        check.inst_param(partition_args, "partition_args", PartitionArgs)

        recon_repo = self._recon_repository_from_origin(partition_args.repository_origin)
        definition = recon_repo.get_definition()
        partition_set_def = definition.get_partition_set_def(partition_args.partition_set_name)
        partition = partition_set_def.get_partition(partition_args.partition_name)
        try:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: "Error occurred during the evaluation of the `tags_for_partition` function for "
                "partition set {partition_set_name}".format(
                    partition_set_name=partition_set_def.name
                ),
            ):
                tags = partition_set_def.tags_for_partition(partition)
                return api_pb2.ExternalPartitionTagsReply(
                    serialized_external_partition_tags_or_external_partition_execution_error=serialize_dagster_namedtuple(
                        ExternalPartitionTagsData(name=partition.name, tags=tags)
                    )
                )
        except PartitionExecutionError:
            return api_pb2.ExternalPartitionTagsReply(
                serialized_external_partition_tags_or_external_partition_execution_error=serialize_dagster_namedtuple(
                    ExternalPartitionExecutionErrorData(
                        serializable_error_info_from_exc_info(sys.exc_info())
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

        check.inst_param(repository_origin, "repository_origin", RepositoryOrigin)
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
            math.ceil(
                float(len(serialized_external_repository_data))
                / STREAMING_EXTERNAL_REPOSITORY_CHUNK_SIZE
            )
        )

        for i in range(num_chunks):
            start_index = i * STREAMING_EXTERNAL_REPOSITORY_CHUNK_SIZE
            end_index = min(
                (i + 1) * STREAMING_EXTERNAL_REPOSITORY_CHUNK_SIZE,
                len(serialized_external_repository_data),
            )

            yield api_pb2.StreamingExternalRepositoryEvent(
                sequence_number=i,
                serialized_external_repository_chunk=serialized_external_repository_data[
                    start_index:end_index
                ],
            )

    def ExternalScheduleExecution(self, request, _context):
        external_schedule_execution_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_external_schedule_execution_args
        )

        check.inst_param(
            external_schedule_execution_args,
            "external_schedule_execution_args",
            ExternalScheduleExecutionArgs,
        )

        recon_repo = self._recon_repository_from_origin(
            external_schedule_execution_args.repository_origin
        )

        return api_pb2.ExternalScheduleExecutionReply(
            serialized_external_schedule_execution_data_or_external_schedule_execution_error=serialize_dagster_namedtuple(
                get_external_schedule_execution(recon_repo, external_schedule_execution_args)
            )
        )

    def ExternalJobParams(self, request, _context):
        external_job_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_external_job_args
        )
        check.inst_param(
            external_job_args, "external_job_args", ExternalJobArgs,
        )

        recon_repo = self._recon_repository_from_origin(external_job_args.repository_origin)
        return api_pb2.ExternalJobParamsReply(
            serialized_external_job_params_or_external_job_params_error_data=serialize_dagster_namedtuple(
                get_external_job_params(recon_repo, external_job_args)
            )
        )

    def ExecuteRun(self, request, _context):
        if self._shutdown_once_executions_finish_event.is_set():
            yield api_pb2.ExecuteRunEvent(
                serialized_dagster_event_or_ipc_error_message=serialize_dagster_namedtuple(
                    IPCErrorMessage(
                        serializable_error_info=None,
                        message="Tried to start a run on a server after telling it to shut down",
                    )
                )
            )

        try:
            execute_run_args = deserialize_json_to_dagster_namedtuple(
                request.serialized_execute_run_args
            )
            check.inst_param(execute_run_args, "execute_run_args", ExecuteRunArgs)

            run_id = execute_run_args.pipeline_run_id

            recon_pipeline = self._recon_pipeline_from_origin(execute_run_args.pipeline_origin)

        except:  # pylint: disable=bare-except
            yield api_pb2.ExecuteRunEvent(
                serialized_dagster_event_or_ipc_error_message=serialize_dagster_namedtuple(
                    IPCErrorMessage(
                        serializable_error_info=serializable_error_info_from_exc_info(
                            sys.exc_info()
                        ),
                        message="Error during RPC setup for ExecuteRun",
                    )
                )
            )
            return

        event_queue = multiprocessing.Queue()
        termination_event = multiprocessing.Event()
        execution_process = multiprocessing.Process(
            target=execute_run_in_subprocess,
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

        done = False
        while not done:
            try:
                # We use `get_nowait()` instead of `get()` so that we can handle the case where the
                # execution process has died unexpectedly -- `get()` would hang forever in that case
                dagster_event_or_ipc_error_message_or_done = event_queue.get_nowait()
            except queue.Empty:
                if not execution_process.is_alive():
                    # subprocess died unexpectedly
                    yield api_pb2.ExecuteRunEvent(
                        serialized_dagster_event_or_ipc_error_message=serialize_dagster_namedtuple(
                            IPCErrorMessage(
                                serializable_error_info=serializable_error_info_from_exc_info(
                                    sys.exc_info()
                                ),
                                message=(
                                    "GRPC server: Subprocess for {run_id} terminated unexpectedly"
                                ).format(run_id=run_id),
                            )
                        )
                    )
                    done = True
                time.sleep(EVENT_QUEUE_POLL_INTERVAL)
            else:
                if isinstance(dagster_event_or_ipc_error_message_or_done, RunInSubprocessComplete):
                    done = True
                elif isinstance(
                    dagster_event_or_ipc_error_message_or_done, StartRunInSubprocessSuccessful
                ):
                    continue
                else:
                    yield api_pb2.ExecuteRunEvent(
                        serialized_dagster_event_or_ipc_error_message=serialize_dagster_namedtuple(
                            dagster_event_or_ipc_error_message_or_done
                        )
                    )

        with self._execution_lock:
            if run_id in self._executions:
                del self._executions[run_id]
            if run_id in self._termination_events:
                del self._termination_events[run_id]

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
                ExecuteRunArgs,
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
                            run_id=run_id, exit_code=execution_process.exitcode,
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
            self._check_for_orphaned_runs()

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
        current_image = os.getenv("DAGSTER_CURRENT_IMAGE")
        serializable_error_info = None

        if not current_image:
            serializable_error_info = "DAGSTER_CURRENT_IMAGE is not set."
        return api_pb2.GetCurrentImageReply(
            serialized_current_image=serialize_dagster_namedtuple(
                GetCurrentImageResult(
                    current_image=current_image, serializable_error_info=serializable_error_info
                )
            )
        )


@whitelist_for_serdes
class GrpcServerStartedEvent(namedtuple("GrpcServerStartedEvent", "")):
    pass


@whitelist_for_serdes
class GrpcServerFailedToBindEvent(namedtuple("GrpcServerStartedEvent", "")):
    pass


def server_termination_target(termination_event, server):
    termination_event.wait()
    # We could make this grace period configurable if we set it in the ShutdownServer handler
    server.stop(grace=5)


class DagsterGrpcServer(object):
    def __init__(
        self,
        host="localhost",
        port=None,
        socket=None,
        max_workers=1,
        loadable_target_origin=None,
        heartbeat=False,
        heartbeat_timeout=30,
        lazy_load_user_code=False,
        ipc_output_file=None,
    ):
        check.opt_str_param(host, "host")
        check.opt_int_param(port, "port")
        check.opt_str_param(socket, "socket")
        check.int_param(max_workers, "max_workers")
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
            host is not None if port else True, "Must provide a host when serving on a port",
        )
        check.bool_param(heartbeat, "heartbeat")
        check.int_param(heartbeat_timeout, "heartbeat_timeout")
        self._ipc_output_file = check.opt_str_param(ipc_output_file, "ipc_output_file")

        check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")
        check.invariant(
            max_workers > 1 if heartbeat else True,
            "max_workers must be greater than 1 if heartbeat is True",
        )

        self.server = grpc.server(ThreadPoolExecutor(max_workers=max_workers))
        self._server_termination_event = threading.Event()

        self._api_servicer = DagsterApiServer(
            server_termination_event=self._server_termination_event,
            loadable_target_origin=loadable_target_origin,
            heartbeat=heartbeat,
            heartbeat_timeout=heartbeat_timeout,
            lazy_load_user_code=lazy_load_user_code,
        )

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


def wait_for_grpc_server(ipc_output_file, timeout=15):
    event = read_unary_response(ipc_output_file, timeout=timeout)

    if isinstance(event, GrpcServerFailedToBindEvent):
        raise CouldNotBindGrpcServerToAddress()
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
    max_workers=1,
    heartbeat=False,
    heartbeat_timeout=30,
    lazy_load_user_code=False,
):
    check.invariant((port or socket) and not (port and socket), "Set only port or socket")
    check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
    check.int_param(max_workers, "max_workers")

    output_file = os.path.join(
        get_system_temp_directory(), "grpc-server-startup-{uuid}".format(uuid=uuid.uuid4().hex)
    )

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
        + ["-n", str(max_workers)]
        + (["--heartbeat"] if heartbeat else [])
        + (["--heartbeat-timeout", str(heartbeat_timeout)] if heartbeat_timeout else [])
        + (["--lazy-load-user-code"] if lazy_load_user_code else [])
        + (["--ipc-output-file", output_file])
    )

    if loadable_target_origin:
        subprocess_args += (
            (
                (
                    ["-f", loadable_target_origin.python_file,]
                    + (
                        ["-d", loadable_target_origin.working_directory]
                        if loadable_target_origin.working_directory
                        else ["--empty-working-directory"]
                    )
                )
                if loadable_target_origin.python_file
                else []
            )
            + (
                ["-m", loadable_target_origin.module_name]
                if loadable_target_origin.module_name
                else []
            )
            + (["-a", loadable_target_origin.attribute] if loadable_target_origin.attribute else [])
        )

    server_process = open_ipc_subprocess(subprocess_args)

    try:
        wait_for_grpc_server(output_file)
    except:
        if server_process.poll() is None:
            server_process.terminate()
        raise

    return server_process


def open_server_process_on_dynamic_port(
    max_retries=10, loadable_target_origin=None, max_workers=1, lazy_load_user_code=False
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
                lazy_load_user_code=lazy_load_user_code,
            )
        except CouldNotBindGrpcServerToAddress:
            pass

        retries += 1

    return server_process, port


def cleanup_server_process(server_process, timeout=3):
    start_time = time.time()
    while server_process.poll() is None and (time.time() - start_time) < timeout:
        time.sleep(0.05)

    if server_process.poll() is None:
        server_process.terminate()
        server_process.wait()


class GrpcServerProcess(object):
    def __init__(
        self,
        loadable_target_origin=None,
        force_port=False,
        max_retries=10,
        max_workers=1,
        heartbeat=False,
        heartbeat_timeout=30,
        lazy_load_user_code=False,
    ):
        self.port = None
        self.socket = None
        self.server_process = None

        check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
        check.bool_param(force_port, "force_port")
        check.int_param(max_retries, "max_retries")
        check.int_param(max_workers, "max_workers")
        check.bool_param(heartbeat, "heartbeat")
        check.int_param(heartbeat_timeout, "heartbeat_timeout")
        check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")
        check.bool_param(lazy_load_user_code, "lazy_load_user_code")
        check.invariant(
            max_workers > 1 if heartbeat else True,
            "max_workers must be greater than 1 if heartbeat is True",
        )

        if seven.IS_WINDOWS or force_port:
            self.server_process, self.port = open_server_process_on_dynamic_port(
                max_retries=max_retries,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                lazy_load_user_code=lazy_load_user_code,
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
            )

        if self.server_process is None:
            raise CouldNotStartServerProcess(port=self.port, socket=self.socket)

    def wait(self, timeout=30):
        if self.server_process.poll() is None:
            seven.wait_for_process(self.server_process, timeout=timeout)

    def create_ephemeral_client(self):
        from dagster.grpc.client import EphemeralDagsterGrpcClient

        return EphemeralDagsterGrpcClient(
            port=self.port, socket=self.socket, server_process=self.server_process
        )
