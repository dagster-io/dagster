import os
import sys
from concurrent.futures import ThreadPoolExecutor

import grpc

from dagster import check, seven
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
from dagster.core.origin import RepositoryPythonOrigin
from dagster.core.snap.execution_plan_snapshot import snapshot_from_execution_plan
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.ipc import IPCErrorMessage
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
    ListRepositoriesArgs,
    ListRepositoriesResponse,
    LoadableRepositorySymbol,
    PartitionArgs,
    PartitionNamesArgs,
    PipelineSubsetSnapshotArgs,
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
        list_repositories_args = deserialize_json_to_dagster_namedtuple(
            request.serialized_list_repositories_args
        )

        check.inst_param(list_repositories_args, 'list_repositories_args', ListRepositoriesArgs)

        loadable_targets = get_loadable_targets(
            list_repositories_args.python_file,
            list_repositories_args.module_name,
            list_repositories_args.working_directory,
        )
        return api_pb2.ListRepositoriesReply(
            serialized_list_repositories_response=serialize_dagster_namedtuple(
                ListRepositoriesResponse(
                    [
                        LoadableRepositorySymbol(
                            attribute=loadable_target.attribute,
                            repository_name=loadable_target.target_definition.name,
                        )
                        for loadable_target in loadable_targets
                    ]
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
        repository_python_origin = deserialize_json_to_dagster_namedtuple(
            request.serialized_repository_python_origin
        )

        check.inst_param(
            repository_python_origin, 'repository_python_origin', RepositoryPythonOrigin
        )

        recon_repo = recon_repository_from_origin(repository_python_origin)
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


# This is not a splendid scheme. We could possibly use a sentinel file for this, or send a custom
# signal back to the client process (Unix only, i think, and questionable); or maybe the client
# could poll the ping rpc instead/in addition to this
SERVER_STARTED_TOKEN = 'dagster_grpc_server_started'

SERVER_STARTED_TOKEN_BYTES = b'dagster_grpc_server_started'

SERVER_FAILED_TO_BIND_TOKEN = 'dagster_grpc_server_failed_to_bind'

SERVER_FAILED_TO_BIND_TOKEN_BYTES = b'dagster_grpc_server_failed_to_bind'


class DagsterGrpcServer(object):
    def __init__(self, host='localhost', port=None, socket=None, max_workers=1):
        check.opt_str_param(host, 'host')
        check.opt_int_param(port, 'port')
        check.opt_str_param(socket, 'socket')
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
        add_DagsterApiServicer_to_server(DagsterApiServer(), self.server)

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
            print(SERVER_FAILED_TO_BIND_TOKEN)
            raise CouldNotBindGrpcServerToAddress(socket)
        if port and res != port:
            print(SERVER_FAILED_TO_BIND_TOKEN)
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
        print(SERVER_STARTED_TOKEN)
        sys.stdout.flush()
        self.server.wait_for_termination()
