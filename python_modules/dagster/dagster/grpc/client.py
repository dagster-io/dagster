import os
import subprocess
import sys
import time
from contextlib import contextmanager

import grpc

from dagster import check, seven
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryGrpcServerOrigin
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info

from .__generated__ import DagsterApiStub, api_pb2
from .server import GrpcServerProcess
from .types import (
    CanCancelExecutionRequest,
    CancelExecutionRequest,
    ExecuteRunArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    LoadableTargetOrigin,
    PartitionArgs,
    PartitionNamesArgs,
    PipelineSubsetSnapshotArgs,
)

CLIENT_HEARTBEAT_INTERVAL = 1


def client_heartbeat_thread(client):
    while True:
        time.sleep(CLIENT_HEARTBEAT_INTERVAL)
        try:
            client.heartbeat('ping')
        except grpc._channel._InactiveRpcError:  # pylint: disable=protected-access
            continue


class DagsterGrpcClient(object):
    def __init__(self, port=None, socket=None, host='localhost'):
        self.port = check.opt_int_param(port, 'port')
        self.socket = check.opt_str_param(socket, 'socket')
        self.host = check.opt_str_param(host, 'host')
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

    def ping(self, echo):
        check.str_param(echo, 'echo')
        res = self._query('Ping', api_pb2.PingRequest, echo=echo)
        return res.echo

    def heartbeat(self, echo=''):
        check.str_param(echo, 'echo')
        res = self._query('Heartbeat', api_pb2.PingRequest, echo=echo)
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

    def list_repositories(self):

        res = self._query('ListRepositories', api_pb2.ListRepositoriesRequest)

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_list_repositories_response_or_error
        )

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

    def external_repository(self, repository_grpc_server_origin):
        check.inst_param(
            repository_grpc_server_origin,
            'repository_grpc_server_origin',
            RepositoryGrpcServerOrigin,
        )

        res = self._query(
            'ExternalRepository',
            api_pb2.ExternalRepositoryRequest,
            serialized_repository_python_origin=serialize_dagster_namedtuple(
                repository_grpc_server_origin
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
            event_iterator = self._streaming_query(
                'ExecuteRun',
                api_pb2.ExecuteRunRequest,
                serialized_execute_run_args=serialize_dagster_namedtuple(execute_run_args),
            )
        except Exception as exc:  # pylint: disable=bare-except
            yield instance.report_engine_event(
                message='Unexpected error in IPC client',
                pipeline_run=pipeline_run,
                engine_event_data=EngineEventData.engine_error(
                    serializable_error_info_from_exc_info(sys.exc_info())
                ),
            )
            raise exc

        try:
            for event in event_iterator:
                yield deserialize_json_to_dagster_namedtuple(
                    event.serialized_dagster_event_or_ipc_error_message
                )
        except KeyboardInterrupt:
            self.cancel_execution(CancelExecutionRequest(run_id=execute_run_args.pipeline_run_id))
            raise
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

    def shutdown_server(self):
        res = self._query('ShutdownServer', api_pb2.Empty)
        return deserialize_json_to_dagster_namedtuple(res.serialized_shutdown_server_result)

    def cancel_execution(self, cancel_execution_request):
        check.inst_param(
            cancel_execution_request, 'cancel_execution_request', CancelExecutionRequest,
        )

        res = self._query(
            'CancelExecution',
            api_pb2.CancelExecutionRequest,
            serialized_cancel_execution_request=serialize_dagster_namedtuple(
                cancel_execution_request
            ),
        )

        return deserialize_json_to_dagster_namedtuple(res.serialized_cancel_execution_result)

    def can_cancel_execution(self, can_cancel_execution_request):
        check.inst_param(
            can_cancel_execution_request, 'can_cancel_execution_request', CanCancelExecutionRequest,
        )

        res = self._query(
            'CanCancelExecution',
            api_pb2.CanCancelExecutionRequest,
            serialized_can_cancel_execution_request=serialize_dagster_namedtuple(
                can_cancel_execution_request
            ),
        )

        return deserialize_json_to_dagster_namedtuple(res.serialized_can_cancel_execution_result)

    def start_run(self, execute_run_args):
        check.inst_param(execute_run_args, 'execute_run_args', ExecuteRunArgs)

        try:
            instance = DagsterInstance.from_ref(execute_run_args.instance_ref)
            pipeline_run = instance.get_run_by_id(execute_run_args.pipeline_run_id)
            res = self._query(
                'StartRun',
                api_pb2.StartRunRequest,
                serialized_execute_run_args=serialize_dagster_namedtuple(execute_run_args),
            )
            return deserialize_json_to_dagster_namedtuple(res.serialized_start_run_result)

        except Exception:  # pylint: disable=bare-except
            instance.report_engine_event(
                message='Unexpected error in IPC client',
                pipeline_run=pipeline_run,
                engine_event_data=EngineEventData.engine_error(
                    serializable_error_info_from_exc_info(sys.exc_info())
                ),
            )
            raise

    def get_current_image(self):
        res = self._query('GetCurrentImage', api_pb2.Empty)
        return deserialize_json_to_dagster_namedtuple(res.serialized_current_image)


class EphemeralDagsterGrpcClient(DagsterGrpcClient):
    '''A client that tells the server process that created it to shut down once it is destroyed or leaves a context manager.'''

    def __init__(
        self, server_process=None, *args, **kwargs
    ):  # pylint: disable=keyword-arg-before-vararg
        self._server_process = check.inst_param(server_process, 'server_process', subprocess.Popen)
        super(EphemeralDagsterGrpcClient, self).__init__(*args, **kwargs)

    def cleanup_server(self):
        if self._server_process and self._server_process.poll() is None:
            self.shutdown_server()
            self._server_process = None

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.cleanup_server()

    def __del__(self):
        self.cleanup_server()


@contextmanager
def ephemeral_grpc_api_client(
    loadable_target_origin=None, force_port=False, max_retries=10, max_workers=1
):
    check.opt_inst_param(loadable_target_origin, 'loadable_target_origin', LoadableTargetOrigin)
    check.bool_param(force_port, 'force_port')
    check.int_param(max_retries, 'max_retries')

    with GrpcServerProcess(
        loadable_target_origin=loadable_target_origin,
        force_port=force_port,
        max_retries=max_retries,
        max_workers=max_workers,
    ).create_ephemeral_client() as client:
        yield client
