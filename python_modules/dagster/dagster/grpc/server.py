import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import grpc

from dagster import check, seven
from dagster.core.code_pointer import CodePointer
from dagster.core.definitions.reconstructable import load_def_in_module, load_def_in_python_file
from dagster.core.errors import (
    DagsterSubprocessError,
    PartitionExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_run_iterator
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionTagsData,
    external_repository_data_from_def,
)
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryGrpcServerOrigin
from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.ipc import IPCErrorMessage, open_ipc_subprocess
from dagster.utils import find_free_port, safe_tempfile_path_unmanaged
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import (
    recon_pipeline_from_origin,
    recon_repository_from_origin,
)

from .__generated__ import api_pb2
from .__generated__.api_pb2_grpc import DagsterApiServicer, add_DagsterApiServicer_to_server
from .impl import get_external_pipeline_subset_result, get_external_schedule_execution
from .types import (
    ExecuteRunArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    ListRepositoriesResponse,
    LoadableRepositorySymbol,
    LoadableTargetOrigin,
    PartitionArgs,
    PartitionNamesArgs,
    PipelineSubsetSnapshotArgs,
    ShutdownServerResult,
)
from .utils import get_loadable_targets


class CouldNotBindGrpcServerToAddress(Exception):
    pass


def _execute_run(request):
    try:
        execute_run_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_execute_run_args
        )
        check.inst_param(execute_run_args, 'execute_run_args', ExecuteRunArgs)

        recon_pipeline = recon_pipeline_from_origin(execute_run_args.pipeline_origin)

        instance = DagsterInstance.from_ref(execute_run_args.instance_ref)
        pipeline_run = instance.get_run_by_id(execute_run_args.pipeline_run_id)

        pid = os.getpid()

    except:  # pylint: disable=bare-except
        yield IPCErrorMessage(
            serializable_error_info=serializable_error_info_from_exc_info(sys.exc_info()),
            message='Error during RPC setup for ExecuteRun',
        )
        return

    yield instance.report_engine_event(
        'Started process for pipeline (pid: {pid}).'.format(pid=pid),
        pipeline_run,
        EngineEventData.in_process(pid, marker_end='cli_api_subprocess_init'),
    )

    # This is so nasty but seemingly unavoidable
    # https://amir.rachum.com/blog/2017/03/03/generator-cleanup/
    closed = False
    try:
        for event in _core_execute_run(recon_pipeline, pipeline_run, instance):
            yield event
    except GeneratorExit:
        closed = True
        raise
    finally:
        if not closed:
            yield instance.report_engine_event(
                'Process for pipeline exited (pid: {pid}).'.format(pid=pid), pipeline_run,
            )


def _core_execute_run(recon_pipeline, pipeline_run, instance):
    try:
        for event in execute_run_iterator(recon_pipeline, pipeline_run, instance):
            yield event
    except DagsterSubprocessError as err:
        if not all(
            [err_info.cls_name == 'KeyboardInterrupt' for err_info in err.subprocess_error_infos]
        ):
            yield instance.report_engine_event(
                'An exception was thrown during execution that is likely a framework error, '
                'rather than an error in user code.',
                pipeline_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
            instance.report_run_failed(pipeline_run)
    except Exception:  # pylint: disable=broad-except
        yield instance.report_engine_event(
            'An exception was thrown during execution that is likely a framework error, '
            'rather than an error in user code.',
            pipeline_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        instance.report_run_failed(pipeline_run)


class DagsterApiServer(DagsterApiServicer):
    # The loadable_target_origin is currently Noneable to support instaniating a server.
    # This helps us test the ping methods, and incrementally migrate each method to
    # the target passed in here instead of passing in a target in the argument.
    def __init__(self, shutdown_server_event, loadable_target_origin=None):
        super(DagsterApiServer, self).__init__()

        self._shutdown_server_event = check.inst_param(
            shutdown_server_event, 'shutdown_server_event', seven.ThreadingEventType
        )
        self._loadable_target_origin = check.opt_inst_param(
            loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin
        )

        if loadable_target_origin:
            from dagster.cli.workspace.autodiscovery import LoadableTarget

            if not loadable_target_origin.attribute:
                loadable_targets = get_loadable_targets(
                    loadable_target_origin.python_file,
                    loadable_target_origin.module_name,
                    loadable_target_origin.working_directory,
                )
            elif loadable_target_origin.python_file:
                loadable_targets = [
                    LoadableTarget(
                        loadable_target_origin.attribute,
                        load_def_in_python_file(
                            loadable_target_origin.python_file,
                            loadable_target_origin.attribute,
                            loadable_target_origin.working_directory,
                        ),
                    )
                ]
            else:
                check.invariant(
                    loadable_target_origin.module_name,
                    'if attribute is set, either a file or module must also be set',
                )
                loadable_targets = [
                    LoadableTarget(
                        loadable_target_origin.attribute,
                        load_def_in_module(
                            loadable_target_origin.module_name, loadable_target_origin.attribute,
                        ),
                    )
                ]

            self._loadable_repository_symbols = [
                LoadableRepositorySymbol(
                    attribute=loadable_target.attribute,
                    repository_name=loadable_target.target_definition.name,
                )
                for loadable_target in loadable_targets
            ]
        else:
            self._loadable_repository_symbols = []

    def Ping(self, request, _context):
        echo = request.echo
        return api_pb2.PingReply(echo=echo)

    def StreamingPing(self, request, _context):
        sequence_length = request.sequence_length
        echo = request.echo
        for sequence_number in range(sequence_length):
            yield api_pb2.StreamingPingEvent(sequence_number=sequence_number, echo=echo)

    def ExecutionPlanSnapshot(self, request, _context):
        execution_plan_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_execution_plan_snapshot_args
        )

        check.inst_param(execution_plan_args, 'execution_plan_args', ExecutionPlanSnapshotArgs)

        recon_pipeline = (
            recon_pipeline_from_origin(execution_plan_args.pipeline_origin).subset_for_execution(
                execution_plan_args.solid_selection
            )
            if execution_plan_args.solid_selection
            else recon_pipeline_from_origin(execution_plan_args.pipeline_origin)
        )

        execution_plan_snapshot = snapshot_from_execution_plan(
            create_execution_plan(
                pipeline=recon_pipeline,
                run_config=execution_plan_args.run_config,
                mode=execution_plan_args.mode,
                step_keys_to_execute=execution_plan_args.step_keys_to_execute,
            ),
            execution_plan_args.pipeline_snapshot_id,
        )
        return api_pb2.ExecutionPlanSnapshotReply(
            serialized_execution_plan_snapshot=serialize_dagster_namedtuple(execution_plan_snapshot)
        )

    def ListRepositories(self, request, _context):
        repository_code_pointer_dict = {}
        for loadable_repository_symbol in self._loadable_repository_symbols:
            if self._loadable_target_origin.python_file:
                repository_code_pointer_dict[
                    loadable_repository_symbol.repository_name
                ] = CodePointer.from_python_file(
                    self._loadable_target_origin.python_file,
                    loadable_repository_symbol.attribute,
                    self._loadable_target_origin.working_directory,
                )
            if self._loadable_target_origin.module_name:
                repository_code_pointer_dict[
                    loadable_repository_symbol.repository_name
                ] = CodePointer.from_module(
                    self._loadable_target_origin.module_name, loadable_repository_symbol.attribute,
                )

        return api_pb2.ListRepositoriesReply(
            serialized_list_repositories_response=serialize_dagster_namedtuple(
                ListRepositoriesResponse(
                    self._loadable_repository_symbols,
                    executable_path=self._loadable_target_origin.executable_path
                    if self._loadable_target_origin
                    else None,
                    repository_code_pointer_dict=repository_code_pointer_dict,
                )
            )
        )

    def ExternalPartitionNames(self, request, _context):
        partition_names_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_partition_names_args
        )

        check.inst_param(partition_names_args, 'partition_names_args', PartitionNamesArgs)

        recon_repo = recon_repository_from_origin(partition_names_args.repository_origin)
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

        recon_repo = recon_repository_from_origin(partition_args.repository_origin)
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

        recon_repo = recon_repository_from_origin(partition_args.repository_origin)
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
                    recon_pipeline_from_origin(pipeline_subset_snapshot_args.pipeline_origin),
                    pipeline_subset_snapshot_args.solid_selection,
                )
            )
        )

    def ExternalRepository(self, request, _context):
        repository_origin = deserialize_json_to_dagster_namedtuple(
            request.serialized_repository_python_origin
        )

        check.inst_param(repository_origin, 'repository_origin', RepositoryGrpcServerOrigin)

        recon_repo = recon_repository_from_origin(repository_origin)
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

        return api_pb2.ExternalScheduleExecutionReply(
            serialized_external_schedule_execution_data_or_external_schedule_execution_error=serialize_dagster_namedtuple(
                get_external_schedule_execution(external_schedule_execution_args)
            )
        )

    def ExecuteRun(self, request, _context):
        for dagster_event_or_ipc_error_message in _execute_run(request):
            yield api_pb2.ExecuteRunEvent(
                serialized_dagster_event_or_ipc_error_message=serialize_dagster_namedtuple(
                    dagster_event_or_ipc_error_message
                )
            )

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
    server.stop(grace=None)


class DagsterGrpcServer(object):
    def __init__(
        self, host='localhost', port=None, socket=None, max_workers=1, loadable_target_origin=None
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

        self.server = grpc.server(ThreadPoolExecutor(max_workers=max_workers))
        self._shutdown_server_event = threading.Event()
        add_DagsterApiServicer_to_server(
            DagsterApiServer(
                shutdown_server_event=self._shutdown_server_event,
                loadable_target_origin=loadable_target_origin,
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
            target=server_termination_target, args=[self._shutdown_server_event, self.server],
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
    port, socket, loadable_target_origin=None,
):
    check.invariant((port or socket) and not (port and socket), 'Set only port or socket')
    check.opt_inst_param(loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin)

    subprocess_args = (
        [
            loadable_target_origin.executable_path
            if loadable_target_origin and loadable_target_origin.executable_path
            else sys.executable,
            '-m',
            'dagster.grpc',
        ]
        + (['-p', str(port)] if port else [])
        + (['-s', socket] if socket else [])
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


def open_server_process_on_dynamic_port(
    max_retries=10, loadable_target_origin=None,
):
    server_process = None
    retries = 0
    while server_process is None and retries < max_retries:
        port = find_free_port()
        try:
            server_process = open_server_process(
                port=port, socket=None, loadable_target_origin=loadable_target_origin,
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
    def __init__(self, loadable_target_origin=None, force_port=False, max_retries=10):
        self.port = None
        self.socket = None
        self.server_process = None

        check.opt_inst_param(loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin)
        check.bool_param(force_port, 'force_port')
        check.int_param(max_retries, 'max_retries')

        if seven.IS_WINDOWS or force_port:
            self.server_process, self.port = open_server_process_on_dynamic_port(
                max_retries=max_retries, loadable_target_origin=loadable_target_origin,
            )
        else:
            self.socket = safe_tempfile_path_unmanaged()

            self.server_process = open_server_process(
                port=None, socket=self.socket, loadable_target_origin=loadable_target_origin,
            )

        if self.server_process is None:
            raise CouldNotStartServerProcess(port=self.port, socket=self.socket)

    def create_client(self):
        from dagster.grpc.client import DagsterGrpcClient

        return DagsterGrpcClient(port=self.port, socket=self.socket, host='localhost')

    def __enter__(self):
        return self

    def __del__(self):
        self._dispose()

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._dispose()

    def _dispose(self):
        if self.server_process:
            cleanup_server_process(self.server_process)
            self.server_process = None
        if self.socket:
            if os.path.exists(self.socket):
                os.unlink(self.socket)
            self.socket = None
