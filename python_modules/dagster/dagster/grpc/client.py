import os
import subprocess
import sys
import time
from contextlib import contextmanager

import grpc

from dagster import check, seven
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryPythonOrigin
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.serdes.ipc import open_ipc_subprocess
from dagster.utils import find_free_port, safe_tempfile_path
from dagster.utils.error import serializable_error_info_from_exc_info

from .__generated__ import DagsterApiStub, api_pb2
from .server import (
    SERVER_FAILED_TO_BIND_TOKEN_BYTES,
    SERVER_STARTED_TOKEN_BYTES,
    CouldNotBindGrpcServerToAddress,
)
from .types import (
    ExecuteRunArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    ListRepositoriesArgs,
    PartitionArgs,
    PartitionNamesArgs,
    PipelineSubsetSnapshotArgs,
)


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


class DagsterGrpcClient(object):
    def __init__(self, port=None, socket=None, server_process=None, host='localhost'):
        check.opt_int_param(port, 'port')
        check.opt_str_param(socket, 'socket')
        check.opt_str_param(host, 'host')
        check.invariant(
            port is not None if seven.IS_WINDOWS else True,
            'You must pass a valid `port` on Windows: `socket` not supported.',
        )
        check.invariant(
            (port or socket) and not (port and socket),
            'You must pass one and only one of `port` or `socket`.',
        )
        check.invariant(
            host is not None if port else True, 'Must provide a hostname',
        )

        if port:
            self._server_address = host + ':' + str(port)
        else:
            self._server_address = 'unix:' + os.path.abspath(socket)

        self._server_process = check.opt_inst_param(
            server_process, 'server_process', subprocess.Popen
        )

    def _query(self, method, request_type, **kwargs):
        with grpc.insecure_channel(self._server_address) as channel:
            stub = DagsterApiStub(channel)
            response = getattr(stub, method)(request_type(**kwargs))
        # TODO need error handling here
        return response

    def _streaming_query(self, method, request_type, **kwargs):
        with grpc.insecure_channel(self._server_address) as channel:
            stub = DagsterApiStub(channel)
            response_stream = getattr(stub, method)(request_type(**kwargs))
            for response in response_stream:
                yield response

    def terminate_server_process(self):
        if self._server_process is not None:
            # We hard terminate here because the interrupt machinery doesn't work with the grpc
            # server machinery. We will eventually implement both terminate_run and shutdown_server
            # calls over the GRPC API.
            self._server_process.terminate()
            self._server_process.wait()
            self._server_process = None

    def ping(self, echo):
        check.str_param(echo, 'echo')
        res = self._query('Ping', api_pb2.PingRequest, echo=echo)
        return res.echo

    def streaming_ping(self, sequence_length, echo):
        check.int_param(sequence_length, 'sequence_length')
        check.str_param(echo, 'echo')

        for res in self._streaming_query(
            'StreamingPing',
            api_pb2.StreamingPingRequest,
            sequence_length=sequence_length,
            echo=echo,
        ):
            yield {
                'sequence_number': res.sequence_number,
                'echo': res.echo,
            }

    def execution_plan_snapshot(self, execution_plan_snapshot_args):
        check.inst_param(
            execution_plan_snapshot_args, 'execution_plan_snapshot_args', ExecutionPlanSnapshotArgs
        )
        res = self._query(
            'ExecutionPlanSnapshot',
            api_pb2.ExecutionPlanSnapshotRequest,
            serialized_execution_plan_snapshot_args=serialize_dagster_namedtuple(
                execution_plan_snapshot_args
            ),
        )
        return deserialize_json_to_dagster_namedtuple(res.serialized_execution_plan_snapshot)

    def list_repositories(self, list_repositories_args):
        check.inst_param(list_repositories_args, 'list_repositories_args', ListRepositoriesArgs)

        res = self._query(
            'ListRepositories',
            api_pb2.ListRepositoriesRequest,
            serialized_list_repositories_args=serialize_dagster_namedtuple(list_repositories_args),
        )

        return deserialize_json_to_dagster_namedtuple(res.serialized_list_repositories_response)

    def external_partition_names(self, partition_names_args):
        check.inst_param(partition_names_args, 'partition_names_args', PartitionNamesArgs)

        res = self._query(
            'ExternalPartitionNames',
            api_pb2.ExternalPartitionNamesRequest,
            serialized_partition_names_args=serialize_dagster_namedtuple(partition_names_args),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_partition_names_or_external_partition_execution_error
        )

    def external_partition_config(self, partition_args):
        check.inst_param(partition_args, 'partition_args', PartitionArgs)

        res = self._query(
            'ExternalPartitionConfig',
            api_pb2.ExternalPartitionConfigRequest,
            serialized_partition_args=serialize_dagster_namedtuple(partition_args),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_partition_config_or_external_partition_execution_error
        )

    def external_partition_tags(self, partition_args):
        check.inst_param(partition_args, 'partition_args', PartitionArgs)

        res = self._query(
            'ExternalPartitionTags',
            api_pb2.ExternalPartitionTagsRequest,
            serialized_partition_args=serialize_dagster_namedtuple(partition_args),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_partition_tags_or_external_partition_execution_error
        )

    def external_pipeline_subset(self, pipeline_subset_snapshot_args):
        check.inst_param(
            pipeline_subset_snapshot_args,
            'pipeline_subset_snapshot_args',
            PipelineSubsetSnapshotArgs,
        )

        res = self._query(
            'ExternalPipelineSubsetSnapshot',
            api_pb2.ExternalPipelineSubsetSnapshotRequest,
            serialized_pipeline_subset_snapshot_args=serialize_dagster_namedtuple(
                pipeline_subset_snapshot_args
            ),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_pipeline_subset_result
        )

    def external_repository(self, repository_python_origin):
        check.inst_param(
            repository_python_origin, 'repository_python_origin', RepositoryPythonOrigin
        )

        res = self._query(
            'ExternalRepository',
            api_pb2.ExternalRepositoryRequest,
            serialized_repository_python_origin=serialize_dagster_namedtuple(
                repository_python_origin
            ),
        )

        return deserialize_json_to_dagster_namedtuple(res.serialized_external_repository_data)

    def external_schedule_execution(self, external_schedule_execution_args):
        check.inst_param(
            external_schedule_execution_args,
            'external_schedule_execution_args',
            ExternalScheduleExecutionArgs,
        )

        res = self._query(
            'ExternalScheduleExecution',
            api_pb2.ExternalScheduleExecutionRequest,
            serialized_external_schedule_execution_args=serialize_dagster_namedtuple(
                external_schedule_execution_args
            ),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_schedule_execution_data_or_external_schedule_execution_error
        )

    def execute_run(self, execute_run_args):
        check.inst_param(execute_run_args, 'execute_run_args', ExecuteRunArgs)

        try:
            instance = DagsterInstance.from_ref(execute_run_args.instance_ref)
            pipeline_run = instance.get_run_by_id(execute_run_args.pipeline_run_id)

            for event in self._streaming_query(
                'ExecuteRun',
                api_pb2.ExecuteRunRequest,
                serialized_execute_run_args=serialize_dagster_namedtuple(execute_run_args),
            ):
                yield deserialize_json_to_dagster_namedtuple(
                    event.serialized_dagster_event_or_ipc_error_message
                )
        except KeyboardInterrupt:
            self.terminate_server_process()
            yield instance.report_engine_event(
                message='Pipeline execution terminated by interrupt', pipeline_run=pipeline_run,
            )
            yield instance.report_run_failed(pipeline_run)
            return
        except grpc.RpcError as rpc_error:
            if (
                # posix
                'Socket closed' in rpc_error.debug_error_string()  # pylint: disable=no-member
                # windows
                or 'Stream removed' in rpc_error.debug_error_string()  # pylint: disable=no-member
            ):
                yield instance.report_engine_event(
                    message='User process: GRPC server for {run_id} terminated unexpectedly'.format(
                        run_id=pipeline_run.run_id
                    ),
                    pipeline_run=pipeline_run,
                    engine_event_data=EngineEventData.engine_error(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    ),
                )
                yield instance.report_run_failed(pipeline_run)
            else:
                yield instance.report_engine_event(
                    message='Unexpected error in IPC client',
                    pipeline_run=pipeline_run,
                    engine_event_data=EngineEventData.engine_error(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    ),
                )
            raise rpc_error
        except Exception as exc:  # pylint: disable=bare-except
            yield instance.report_engine_event(
                message='Unexpected error in IPC client',
                pipeline_run=pipeline_run,
                engine_event_data=EngineEventData.engine_error(
                    serializable_error_info_from_exc_info(sys.exc_info())
                ),
            )
            raise exc


def _wait_for_grpc_server(server_process, timeout=3):
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


def open_server_process(port, socket, python_executable_path=None):
    check.invariant((port or socket) and not (port and socket), 'Set only port or socket')
    python_executable_path = check.opt_str_param(
        python_executable_path, 'python_executable_path', default=sys.executable
    )

    server_process = open_ipc_subprocess(
        [python_executable_path, '-m', 'dagster.grpc']
        + (['-p', str(port)] if port else [])
        + (['-s', socket] if socket else []),
        stdout=subprocess.PIPE,
    )
    ready = _wait_for_grpc_server(server_process)

    if ready:
        return server_process
    else:
        if server_process.poll() is None:
            server_process.terminate()
        return None


def open_server_process_on_dynamic_port(max_retries=10, python_executable_path=None):
    server_process = None
    retries = 0
    while server_process is None and retries < max_retries:
        port = find_free_port()
        try:
            server_process = open_server_process(
                port=port, socket=None, python_executable_path=python_executable_path
            )
        except CouldNotBindGrpcServerToAddress:
            pass

        retries += 1

    return server_process, port


@contextmanager
def ephemeral_grpc_api_client(python_executable_path=None, force_port=False, max_retries=10):
    if seven.IS_WINDOWS or force_port:
        server_process, port = open_server_process_on_dynamic_port(
            max_retries=max_retries, python_executable_path=python_executable_path
        )

        if server_process is None:
            raise CouldNotStartServerProcess(port=port, socket=None)

        client = DagsterGrpcClient(port=port, server_process=server_process)

        try:
            yield client
        finally:
            client.terminate_server_process()

    else:
        with safe_tempfile_path() as socket:
            server_process = open_server_process(
                port=None, socket=socket, python_executable_path=python_executable_path
            )

            if server_process is None:
                raise CouldNotStartServerProcess(port=None, socket=socket)

            client = DagsterGrpcClient(socket=socket, server_process=server_process)

            try:
                yield client
            finally:
                client.terminate_server_process()
