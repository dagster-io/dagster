import os
import subprocess
import sys
import warnings
from contextlib import contextmanager

import grpc
from dagster import check, seven
from dagster.core.events import EngineEventData
from dagster.core.host_representation import ExternalRepositoryOrigin
from dagster.core.instance import DagsterInstance
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info
from grpc_health.v1 import health_pb2
from grpc_health.v1.health_pb2_grpc import HealthStub

from .__generated__ import DagsterApiStub, api_pb2
from .server import GrpcServerProcess
from .types import (
    CanCancelExecutionRequest,
    CancelExecutionRequest,
    ExecuteExternalPipelineArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    PartitionArgs,
    PartitionNamesArgs,
    PartitionSetExecutionParamArgs,
    PipelineSubsetSnapshotArgs,
    SensorExecutionArgs,
)

CLIENT_HEARTBEAT_INTERVAL = 1


def client_heartbeat_thread(client, shutdown_event):
    while True:
        shutdown_event.wait(CLIENT_HEARTBEAT_INTERVAL)
        if shutdown_event.is_set():
            break

        try:
            client.heartbeat("ping")
        except grpc._channel._InactiveRpcError:  # pylint: disable=protected-access
            continue


class DagsterGrpcClient:
    def __init__(self, port=None, socket=None, host="localhost"):
        self.port = check.opt_int_param(port, "port")
        self.socket = check.opt_str_param(socket, "socket")
        self.host = check.opt_str_param(host, "host")
        check.invariant(
            port is not None if seven.IS_WINDOWS else True,
            "You must pass a valid `port` on Windows: `socket` not supported.",
        )
        check.invariant(
            (port or socket) and not (port and socket),
            "You must pass one and only one of `port` or `socket`.",
        )
        check.invariant(
            host is not None if port else True, "Must provide a hostname",
        )

        if port:
            self._server_address = host + ":" + str(port)
        else:
            self._server_address = "unix:" + os.path.abspath(socket)

    def _query(self, method, request_type, timeout=None, **kwargs):
        with grpc.insecure_channel(self._server_address) as channel:
            stub = DagsterApiStub(channel)
            response = getattr(stub, method)(request_type(**kwargs), timeout=timeout)
        # TODO need error handling here
        return response

    def _streaming_query(self, method, request_type, **kwargs):
        with grpc.insecure_channel(self._server_address) as channel:
            stub = DagsterApiStub(channel)
            response_stream = getattr(stub, method)(request_type(**kwargs))
            yield from response_stream

    def ping(self, echo):
        check.str_param(echo, "echo")
        res = self._query("Ping", api_pb2.PingRequest, echo=echo)
        return res.echo

    def heartbeat(self, echo=""):
        check.str_param(echo, "echo")
        res = self._query("Heartbeat", api_pb2.PingRequest, echo=echo)
        return res.echo

    def streaming_ping(self, sequence_length, echo):
        check.int_param(sequence_length, "sequence_length")
        check.str_param(echo, "echo")

        for res in self._streaming_query(
            "StreamingPing",
            api_pb2.StreamingPingRequest,
            sequence_length=sequence_length,
            echo=echo,
        ):
            yield {
                "sequence_number": res.sequence_number,
                "echo": res.echo,
            }

    def get_server_id(self):
        res = self._query("GetServerId", api_pb2.Empty)
        return res.server_id

    def execution_plan_snapshot(self, execution_plan_snapshot_args):
        check.inst_param(
            execution_plan_snapshot_args, "execution_plan_snapshot_args", ExecutionPlanSnapshotArgs
        )
        res = self._query(
            "ExecutionPlanSnapshot",
            api_pb2.ExecutionPlanSnapshotRequest,
            serialized_execution_plan_snapshot_args=serialize_dagster_namedtuple(
                execution_plan_snapshot_args
            ),
        )
        return deserialize_json_to_dagster_namedtuple(res.serialized_execution_plan_snapshot)

    def list_repositories(self):

        res = self._query("ListRepositories", api_pb2.ListRepositoriesRequest)

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_list_repositories_response_or_error
        )

    def external_partition_names(self, partition_names_args):
        check.inst_param(partition_names_args, "partition_names_args", PartitionNamesArgs)

        res = self._query(
            "ExternalPartitionNames",
            api_pb2.ExternalPartitionNamesRequest,
            serialized_partition_names_args=serialize_dagster_namedtuple(partition_names_args),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_partition_names_or_external_partition_execution_error
        )

    def external_partition_config(self, partition_args):
        check.inst_param(partition_args, "partition_args", PartitionArgs)

        res = self._query(
            "ExternalPartitionConfig",
            api_pb2.ExternalPartitionConfigRequest,
            serialized_partition_args=serialize_dagster_namedtuple(partition_args),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_partition_config_or_external_partition_execution_error
        )

    def external_partition_tags(self, partition_args):
        check.inst_param(partition_args, "partition_args", PartitionArgs)

        res = self._query(
            "ExternalPartitionTags",
            api_pb2.ExternalPartitionTagsRequest,
            serialized_partition_args=serialize_dagster_namedtuple(partition_args),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_partition_tags_or_external_partition_execution_error
        )

    def external_partition_set_execution_params(self, partition_set_execution_param_args):
        check.inst_param(
            partition_set_execution_param_args,
            "partition_set_execution_param_args",
            PartitionSetExecutionParamArgs,
        )

        res = self._query(
            "ExternalPartitionSetExecutionParams",
            api_pb2.ExternalPartitionSetExecutionParamsRequest,
            serialized_partition_set_execution_param_args=serialize_dagster_namedtuple(
                partition_set_execution_param_args
            ),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_partition_set_execution_param_data_or_external_partition_execution_error
        )

    def external_pipeline_subset(self, pipeline_subset_snapshot_args):
        check.inst_param(
            pipeline_subset_snapshot_args,
            "pipeline_subset_snapshot_args",
            PipelineSubsetSnapshotArgs,
        )

        res = self._query(
            "ExternalPipelineSubsetSnapshot",
            api_pb2.ExternalPipelineSubsetSnapshotRequest,
            serialized_pipeline_subset_snapshot_args=serialize_dagster_namedtuple(
                pipeline_subset_snapshot_args
            ),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_pipeline_subset_result
        )

    def external_repository(self, external_repository_origin):
        check.inst_param(
            external_repository_origin, "external_repository_origin", ExternalRepositoryOrigin,
        )

        res = self._query(
            "ExternalRepository",
            api_pb2.ExternalRepositoryRequest,
            # rename this param name
            serialized_repository_python_origin=serialize_dagster_namedtuple(
                external_repository_origin
            ),
        )

        return deserialize_json_to_dagster_namedtuple(res.serialized_external_repository_data)

    def streaming_external_repository(self, external_repository_origin):
        for res in self._streaming_query(
            "StreamingExternalRepository",
            api_pb2.ExternalRepositoryRequest,
            # Rename parameter
            serialized_repository_python_origin=serialize_dagster_namedtuple(
                external_repository_origin
            ),
        ):
            yield {
                "sequence_number": res.sequence_number,
                "serialized_external_repository_chunk": res.serialized_external_repository_chunk,
            }

    def external_schedule_execution(self, external_schedule_execution_args):
        check.inst_param(
            external_schedule_execution_args,
            "external_schedule_execution_args",
            ExternalScheduleExecutionArgs,
        )

        res = self._query(
            "ExternalScheduleExecution",
            api_pb2.ExternalScheduleExecutionRequest,
            serialized_external_schedule_execution_args=serialize_dagster_namedtuple(
                external_schedule_execution_args
            ),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_schedule_execution_data_or_external_schedule_execution_error
        )

    def external_sensor_execution(self, sensor_execution_args):
        check.inst_param(
            sensor_execution_args, "sensor_execution_args", SensorExecutionArgs,
        )

        res = self._query(
            "ExternalSensorExecution",
            api_pb2.ExternalSensorExecutionRequest,
            serialized_external_sensor_execution_args=serialize_dagster_namedtuple(
                sensor_execution_args
            ),
        )

        return deserialize_json_to_dagster_namedtuple(
            res.serialized_external_sensor_execution_data_or_external_sensor_execution_error
        )

    def shutdown_server(self, timeout=15):
        res = self._query("ShutdownServer", api_pb2.Empty, timeout=timeout)
        return deserialize_json_to_dagster_namedtuple(res.serialized_shutdown_server_result)

    def cancel_execution(self, cancel_execution_request):
        check.inst_param(
            cancel_execution_request, "cancel_execution_request", CancelExecutionRequest,
        )

        res = self._query(
            "CancelExecution",
            api_pb2.CancelExecutionRequest,
            serialized_cancel_execution_request=serialize_dagster_namedtuple(
                cancel_execution_request
            ),
        )

        return deserialize_json_to_dagster_namedtuple(res.serialized_cancel_execution_result)

    def can_cancel_execution(self, can_cancel_execution_request, timeout=None):
        check.inst_param(
            can_cancel_execution_request, "can_cancel_execution_request", CanCancelExecutionRequest,
        )

        res = self._query(
            "CanCancelExecution",
            api_pb2.CanCancelExecutionRequest,
            timeout=timeout,
            serialized_can_cancel_execution_request=serialize_dagster_namedtuple(
                can_cancel_execution_request
            ),
        )

        return deserialize_json_to_dagster_namedtuple(res.serialized_can_cancel_execution_result)

    def start_run(self, execute_run_args):
        check.inst_param(execute_run_args, "execute_run_args", ExecuteExternalPipelineArgs)

        with DagsterInstance.from_ref(execute_run_args.instance_ref) as instance:
            try:
                res = self._query(
                    "StartRun",
                    api_pb2.StartRunRequest,
                    serialized_execute_run_args=serialize_dagster_namedtuple(execute_run_args),
                )
                return deserialize_json_to_dagster_namedtuple(res.serialized_start_run_result)

            except Exception:  # pylint: disable=bare-except
                pipeline_run = instance.get_run_by_id(execute_run_args.pipeline_run_id)
                instance.report_engine_event(
                    message="Unexpected error in IPC client",
                    pipeline_run=pipeline_run,
                    engine_event_data=EngineEventData.engine_error(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    ),
                )
                raise

    def get_current_image(self):
        res = self._query("GetCurrentImage", api_pb2.Empty)
        return deserialize_json_to_dagster_namedtuple(res.serialized_current_image)

    def health_check_query(self):
        try:
            with grpc.insecure_channel(self._server_address) as channel:
                response = HealthStub(channel).Check(
                    health_pb2.HealthCheckRequest(service="DagsterApi")
                )
        except grpc.RpcError as e:
            print(e)  # pylint: disable=print-call
            return health_pb2.HealthCheckResponse.UNKNOWN  # pylint: disable=no-member

        status_number = response.status
        # pylint: disable=no-member
        return health_pb2.HealthCheckResponse.ServingStatus.Name(status_number)


class EphemeralDagsterGrpcClient(DagsterGrpcClient):
    """A client that tells the server process that created it to shut down once it leaves a
    context manager."""

    def __init__(
        self, server_process=None, *args, **kwargs
    ):  # pylint: disable=keyword-arg-before-vararg
        self._server_process = check.inst_param(server_process, "server_process", subprocess.Popen)
        super(EphemeralDagsterGrpcClient, self).__init__(*args, **kwargs)

    def cleanup_server(self):
        if self._server_process:
            if self._server_process.poll() is None:
                try:
                    self.shutdown_server()
                except grpc._channel._InactiveRpcError:  # pylint: disable=protected-access
                    pass
            self._server_process = None

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.cleanup_server()

    def __del__(self):
        if self._server_process:
            warnings.warn(
                "Managed gRPC client is being destroyed without signalling to server that "
                "it should shutdown. This may result in server processes living longer than "
                "they need to. To fix this, wrap the client in a contextmanager."
            )


@contextmanager
def ephemeral_grpc_api_client(
    loadable_target_origin=None, force_port=False, max_retries=10, max_workers=None
):
    check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
    check.bool_param(force_port, "force_port")
    check.int_param(max_retries, "max_retries")

    with GrpcServerProcess(
        loadable_target_origin=loadable_target_origin,
        force_port=force_port,
        max_retries=max_retries,
        max_workers=max_workers,
        lazy_load_user_code=True,
    ).create_ephemeral_client() as client:
        yield client
