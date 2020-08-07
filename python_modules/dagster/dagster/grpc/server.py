import os
import queue
import subprocess
import sys
import threading
import time
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
    ExternalPartitionNamesData,
    ExternalPartitionTagsData,
    external_repository_data_from_def,
)
from dagster.core.origin import PipelineOrigin, RepositoryGrpcServerOrigin, RepositoryOrigin
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.ipc import IPCErrorMessage, open_ipc_subprocess
from dagster.seven import multiprocessing
from dagster.utils import find_free_port, safe_tempfile_path_unmanaged
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import recon_repository_from_origin

from .__generated__ import api_pb2
from .__generated__.api_pb2_grpc import DagsterApiServicer, add_DagsterApiServicer_to_server
from .impl import (
    RunInSubprocessComplete,
    StartRunInSubprocessSuccessful,
    execute_run_in_subprocess,
    get_external_execution_plan_snapshot,
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
    ExternalScheduleExecutionArgs,
    GetCurrentImageResult,
    ListRepositoriesResponse,
    LoadableRepositorySymbol,
    LoadableTargetOrigin,
    PartitionArgs,
    PartitionNamesArgs,
    PipelineSubsetSnapshotArgs,
    ShutdownServerResult,
    StartRunResult,
)
from .utils import get_loadable_targets

EVENT_QUEUE_POLL_INTERVAL = 0.1


class CouldNotBindGrpcServerToAddress(Exception):
    pass


def heartbeat_thread(heartbeat_timeout, last_heartbeat_time, shutdown_event):
    while True:
        time.sleep(heartbeat_timeout)
        if last_heartbeat_time < time.time() - heartbeat_timeout:
            shutdown_event.set()


class LazyRepositorySymbolsAndCodePointers:
    '''Enables lazily loading user code at RPC-time so that it doesn't interrupt startup and
    we can gracefully handle user code errors.'''

    def __init__(self, loadable_target_origin):
        self._loadable_target_origin = loadable_target_origin
        self._loadable_repository_symbols = None
        self._code_pointers_by_repo_name = None

    def _load(self):
        self._loadable_repository_symbols = load_loadable_repository_symbols(
            self._loadable_target_origin
        )
        self._code_pointers_by_repo_name = build_code_pointers_by_repo_name(
            self._loadable_target_origin, self._loadable_repository_symbols
        )

    @property
    def loadable_repository_symbols(self):
        if self._loadable_repository_symbols is None:
            self._load()

        return self._loadable_repository_symbols

    @property
    def code_pointers_by_repo_name(self):
        if self._code_pointers_by_repo_name is None:
            self._load()

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
        shutdown_server_event,
        loadable_target_origin=None,
        heartbeat=False,
        heartbeat_timeout=30,
    ):
        super(DagsterApiServer, self).__init__()

        check.bool_param(heartbeat, 'heartbeat')
        check.int_param(heartbeat_timeout, 'heartbeat_timeout')
        check.invariant(heartbeat_timeout > 0, 'heartbeat_timeout must be greater than 0')

        self._shutdown_server_event = check.inst_param(
            shutdown_server_event, 'shutdown_server_event', seven.ThreadingEventType
        )
        self._loadable_target_origin = check.opt_inst_param(
            loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin
        )

        self._shutdown_server_event = check.inst_param(
            shutdown_server_event, 'shutdown_server_event', seven.ThreadingEventType
        )
        # Dict[str, multiprocessing.Process] of run_id to execute_run process
        self._executions = {}
        # Dict[str, multiprocessing.Event]
        self._termination_events = {}
        self._execution_lock = threading.Lock()

        self._repository_symbols_and_code_pointers = LazyRepositorySymbolsAndCodePointers(
            loadable_target_origin
        )

        self.__last_heartbeat_time = time.time()
        if heartbeat:
            self.__heartbeat_thread = threading.Thread(
                target=heartbeat_thread,
                args=(heartbeat_timeout, self.__last_heartbeat_time, self._shutdown_server_event),
            )
            self.__heartbeat_thread.daemon = True
            self.__heartbeat_thread.start()
        else:
            self.__heartbeat_thread = None

    def _recon_repository_from_origin(self, repository_origin):
        check.inst_param(
            repository_origin, 'repository_origin', RepositoryOrigin,
        )

        if isinstance(repository_origin, RepositoryGrpcServerOrigin):
            return ReconstructableRepository(
                self._repository_symbols_and_code_pointers.code_pointers_by_repo_name[
                    repository_origin.repository_name
                ]
            )
        return recon_repository_from_origin(repository_origin)

    def _recon_pipeline_from_origin(self, pipeline_origin):
        check.inst_param(pipeline_origin, 'pipeline_origin', PipelineOrigin)
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

        check.inst_param(execution_plan_args, 'execution_plan_args', ExecutionPlanSnapshotArgs)
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

        check.inst_param(partition_names_args, 'partition_names_args', PartitionNamesArgs)

        recon_repo = self._recon_repository_from_origin(partition_names_args.repository_origin)
        definition = recon_repo.get_definition()
        partition_set_def = definition.get_partition_set_def(
            partition_names_args.partition_set_name
        )
        try:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: 'Error occurred during the execution of the partition generation function for '
                'partition set {partition_set_name}'.format(
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

    def ExternalPartitionConfig(self, request, _context):
        partition_args = deserialize_json_to_dagster_namedtuple(request.serialized_partition_args)

        check.inst_param(partition_args, 'partition_args', PartitionArgs)

        recon_repo = self._recon_repository_from_origin(partition_args.repository_origin)
        definition = recon_repo.get_definition()
        partition_set_def = definition.get_partition_set_def(partition_args.partition_set_name)
        partition = partition_set_def.get_partition(partition_args.partition_name)
        try:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: 'Error occurred during the evaluation of the `run_config_for_partition` '
                'function for partition set {partition_set_name}'.format(
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

        check.inst_param(partition_args, 'partition_args', PartitionArgs)

        recon_repo = self._recon_repository_from_origin(partition_args.repository_origin)
        definition = recon_repo.get_definition()
        partition_set_def = definition.get_partition_set_def(partition_args.partition_set_name)
        partition = partition_set_def.get_partition(partition_args.partition_name)
        try:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: 'Error occurred during the evaluation of the `tags_for_partition` function for '
                'partition set {partition_set_name}'.format(
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
            'pipeline_subset_snapshot_args',
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

    def ExternalRepository(self, request, _context):
        repository_origin = deserialize_json_to_dagster_namedtuple(
            request.serialized_repository_python_origin
        )

        check.inst_param(repository_origin, 'repository_origin', RepositoryOrigin)

        recon_repo = self._recon_repository_from_origin(repository_origin)
        return api_pb2.ExternalRepositoryReply(
            serialized_external_repository_data=serialize_dagster_namedtuple(
                external_repository_data_from_def(recon_repo.get_definition())
            )
        )

    def ExternalScheduleExecution(self, request, _context):
        external_schedule_execution_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_external_schedule_execution_args
        )

        check.inst_param(
            external_schedule_execution_args,
            'external_schedule_execution_args',
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

    def ExecuteRun(self, request, _context):
        try:
            execute_run_args = deserialize_json_to_dagster_namedtuple(
                request.serialized_execute_run_args
            )
            check.inst_param(execute_run_args, 'execute_run_args', ExecuteRunArgs)

            run_id = execute_run_args.pipeline_run_id

            recon_pipeline = self._recon_pipeline_from_origin(execute_run_args.pipeline_origin)

        except:  # pylint: disable=bare-except
            yield api_pb2.ExecuteRunEvent(
                serialized_dagster_event_or_ipc_error_message=serialize_dagster_namedtuple(
                    IPCErrorMessage(
                        serializable_error_info=serializable_error_info_from_exc_info(
                            sys.exc_info()
                        ),
                        message='Error during RPC setup for ExecuteRun',
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
            self._executions[run_id] = execution_process
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
                                    'GRPC server: Subprocess for {run_id} terminated unexpectedly'
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
            self._shutdown_server_event.set()
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
            can_cancel = can_cancel_execution_request.run_id in self._executions

        return api_pb2.CanCancelExecutionReply(
            serialized_can_cancel_execution_result=serialize_dagster_namedtuple(
                CanCancelExecutionResult(can_cancel=can_cancel)
            )
        )

    def StartRun(self, request, _context):
        execute_run_args = check.inst(
            deserialize_json_to_dagster_namedtuple(request.serialized_execute_run_args),
            ExecuteRunArgs,
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
            self._executions[run_id] = execution_process
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
                        'GRPC server: Subprocess for {run_id} terminated unexpectedly with '
                        'exit code {exit_code}'.format(
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
        current_image = os.getenv('DAGSTER_CURRENT_IMAGE')
        serializable_error_info = None

        if not current_image:
            serializable_error_info = 'DAGSTER_CURRENT_IMAGE is not set.'
        return api_pb2.GetCurrentImageReply(
            serialized_current_image=serialize_dagster_namedtuple(
                GetCurrentImageResult(
                    current_image=current_image, serializable_error_info=serializable_error_info
                )
            )
        )


# This is not a splendid scheme. We could possibly use a sentinel file for this, or send a custom
# signal back to the client process (Unix only, i think, and questionable); or maybe the client
# could poll the ping rpc instead/in addition to this
SERVER_STARTED_TOKEN = 'dagster_grpc_server_started'

SERVER_STARTED_TOKEN_BYTES = b'dagster_grpc_server_started'

SERVER_FAILED_TO_BIND_TOKEN = 'dagster_grpc_server_failed_to_bind'

SERVER_FAILED_TO_BIND_TOKEN_BYTES = b'dagster_grpc_server_failed_to_bind'


def server_termination_target(termination_event, server):
    while not termination_event.is_set():
        time.sleep(0.1)
    # We could make this grace period configurable if we set it in the ShutdownServer handler
    server.stop(grace=5)


class DagsterGrpcServer(object):
    def __init__(
        self,
        host='localhost',
        port=None,
        socket=None,
        max_workers=1,
        loadable_target_origin=None,
        heartbeat=False,
        heartbeat_timeout=30,
    ):
        check.opt_str_param(host, 'host')
        check.opt_int_param(port, 'port')
        check.opt_str_param(socket, 'socket')
        check.int_param(max_workers, 'max_workers')
        check.opt_inst_param(loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin)
        check.invariant(
            port is not None if seven.IS_WINDOWS else True,
            'You must pass a valid `port` on Windows: `socket` not supported.',
        )
        check.invariant(
            (port or socket) and not (port and socket),
            'You must pass one and only one of `port` or `socket`.',
        )
        check.invariant(
            host is not None if port else True, 'Must provide a host when serving on a port',
        )
        check.bool_param(heartbeat, 'heartbeat')
        check.int_param(heartbeat_timeout, 'heartbeat_timeout')
        check.invariant(heartbeat_timeout > 0, 'heartbeat_timeout must be greater than 0')
        check.invariant(
            max_workers > 1 if heartbeat else True,
            "max_workers must be greater than 1 if heartbeat is True",
        )

        self.server = grpc.server(ThreadPoolExecutor(max_workers=max_workers))
        self._shutdown_server_event = threading.Event()
        add_DagsterApiServicer_to_server(
            DagsterApiServer(
                shutdown_server_event=self._shutdown_server_event,
                loadable_target_origin=loadable_target_origin,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
            ),
            self.server,
        )

        if port:
            server_address = host + ':' + str(port)
        else:
            server_address = 'unix:' + os.path.abspath(socket)

        # grpc.Server.add_insecure_port returns:
        # - 0 on failure
        # - port number when a port is successfully bound
        # - 1 when a UDS is successfully bound
        res = self.server.add_insecure_port(server_address)
        if socket and res != 1:
            print(SERVER_FAILED_TO_BIND_TOKEN)  # pylint: disable=print-call
            raise CouldNotBindGrpcServerToAddress(socket)
        if port and res != port:
            print(SERVER_FAILED_TO_BIND_TOKEN)  # pylint: disable=print-call
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
        print(SERVER_STARTED_TOKEN)  # pylint: disable=print-call
        sys.stdout.flush()
        server_termination_thread = threading.Thread(
            target=server_termination_target,
            args=[self._shutdown_server_event, self.server],
            name='grpc-server-termination',
        )

        server_termination_thread.daemon = True

        server_termination_thread.start()

        self.server.wait_for_termination()


class CouldNotStartServerProcess(Exception):
    def __init__(self, port=None, socket=None):
        super(CouldNotStartServerProcess, self).__init__(
            'Could not start server with '
            + (
                'port {port}'.format(port=port)
                if port is not None
                else 'socket {socket}'.format(socket=socket)
            )
        )


def wait_for_grpc_server(server_process, timeout=3):
    total_time = 0
    backoff = 0.01
    for line in iter(server_process.stdout.readline, ''):
        if line.rstrip() == SERVER_FAILED_TO_BIND_TOKEN_BYTES:
            raise CouldNotBindGrpcServerToAddress()
        elif line.rstrip() != SERVER_STARTED_TOKEN_BYTES:
            time.sleep(backoff)
            total_time += backoff
            backoff = backoff * 2
            if total_time > timeout:
                return False
        else:
            return True


def open_server_process(
    port, socket, loadable_target_origin=None, max_workers=1, heartbeat=False, heartbeat_timeout=30
):
    check.invariant((port or socket) and not (port and socket), 'Set only port or socket')
    check.opt_inst_param(loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin)
    check.int_param(max_workers, 'max_workers')

    subprocess_args = (
        [
            loadable_target_origin.executable_path
            if loadable_target_origin and loadable_target_origin.executable_path
            else sys.executable,
            '-m',
            'dagster.grpc',
        ]
        + (['--port', str(port)] if port else [])
        + (['--socket', socket] if socket else [])
        + ['-n', str(max_workers)]
        + (['--heartbeat'] if heartbeat else [])
        + (['--heartbeat-timeout', str(heartbeat_timeout)] if heartbeat_timeout else [])
    )

    if loadable_target_origin:
        subprocess_args += (
            (
                ['-f', loadable_target_origin.python_file]
                if loadable_target_origin.python_file
                else []
            )
            + (
                ['-m', loadable_target_origin.module_name]
                if loadable_target_origin.module_name
                else []
            )
            + (
                ['-d', loadable_target_origin.working_directory]
                if loadable_target_origin.working_directory
                else []
            )
            + (['-a', loadable_target_origin.attribute] if loadable_target_origin.attribute else [])
        )

    server_process = open_ipc_subprocess(subprocess_args, stdout=subprocess.PIPE)

    ready = wait_for_grpc_server(server_process)

    if ready:
        return server_process
    else:
        if server_process.poll() is None:
            server_process.terminate()
        return None


def open_server_process_on_dynamic_port(max_retries=10, loadable_target_origin=None, max_workers=1):
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
    ):
        self.port = None
        self.socket = None
        self.server_process = None

        check.opt_inst_param(loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin)
        check.bool_param(force_port, 'force_port')
        check.int_param(max_retries, 'max_retries')
        check.int_param(max_workers, 'max_workers')
        check.bool_param(heartbeat, 'heartbeat')
        check.int_param(heartbeat_timeout, 'heartbeat_timeout')
        check.invariant(heartbeat_timeout > 0, 'heartbeat_timeout must be greater than 0')
        check.invariant(
            max_workers > 1 if heartbeat else True,
            "max_workers must be greater than 1 if heartbeat is True",
        )

        if seven.IS_WINDOWS or force_port:
            self.server_process, self.port = open_server_process_on_dynamic_port(
                max_retries=max_retries,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
            )
        else:
            # Who will clean this up now
            self.socket = safe_tempfile_path_unmanaged()

            self.server_process = open_server_process(
                port=None,
                socket=self.socket,
                loadable_target_origin=loadable_target_origin,
                max_workers=max_workers,
                heartbeat=heartbeat,
                heartbeat_timeout=heartbeat_timeout,
            )

        if self.server_process is None:
            raise CouldNotStartServerProcess(port=self.port, socket=self.socket)

    def wait(self):
        self.server_process.wait()

    def create_ephemeral_client(self):
        from dagster.grpc.client import EphemeralDagsterGrpcClient

        return EphemeralDagsterGrpcClient(
            port=self.port, socket=self.socket, server_process=self.server_process
        )
