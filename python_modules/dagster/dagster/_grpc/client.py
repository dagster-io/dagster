import os
import subprocess
import sys
import warnings
from contextlib import contextmanager
from typing import Iterator, Optional, Sequence, Tuple

import grpc
from grpc_health.v1 import health_pb2
from grpc_health.v1.health_pb2_grpc import HealthStub

import dagster._check as check
import dagster._seven as seven
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.events import EngineEventData
from dagster._core.host_representation.origin import ExternalRepositoryOrigin
from dagster._core.instance import DagsterInstance
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._serdes import serialize_dagster_namedtuple
from dagster._utils.error import serializable_error_info_from_exc_info

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
from .utils import default_grpc_timeout, max_rx_bytes, max_send_bytes

CLIENT_HEARTBEAT_INTERVAL = 1

DEFAULT_GRPC_TIMEOUT = default_grpc_timeout()


def client_heartbeat_thread(client, shutdown_event):
    while True:
        shutdown_event.wait(CLIENT_HEARTBEAT_INTERVAL)
        if shutdown_event.is_set():
            break

        try:
            client.heartbeat("ping")
        except DagsterUserCodeUnreachableError:
            continue


class DagsterGrpcClient:
    def __init__(
        self,
        port=None,
        socket=None,
        host="localhost",
        use_ssl=False,
        metadata: Optional[Sequence[Tuple[str, str]]] = None,
    ):
        self.port = check.opt_int_param(port, "port")
        self.socket = check.opt_str_param(socket, "socket")
        self.host = check.opt_str_param(host, "host")
        self._use_ssl = check.bool_param(use_ssl, "use_ssl")

        self._ssl_creds = grpc.ssl_channel_credentials() if use_ssl else None

        self._metadata = check.opt_sequence_param(metadata, "metadata")

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
            "Must provide a hostname",
        )

        if port:
            self._server_address = host + ":" + str(port)
        else:
            self._server_address = "unix:" + os.path.abspath(socket)

    @property
    def metadata(self) -> Sequence[Tuple[str, str]]:
        return self._metadata

    @property
    def use_ssl(self) -> bool:
        return self._use_ssl

    @contextmanager
    def _channel(self):
        options = [
            ("grpc.max_receive_message_length", max_rx_bytes()),
            ("grpc.max_send_message_length", max_send_bytes()),
        ]
        with (
            grpc.secure_channel(
                self._server_address,
                self._ssl_creds,
                options=options,
                compression=grpc.Compression.Gzip,
            )
            if self._use_ssl
            else grpc.insecure_channel(
                self._server_address,
                options=options,
                compression=grpc.Compression.Gzip,
            )
        ) as channel:
            yield channel

    def _get_response(
        self,
        method,
        request,
        timeout=DEFAULT_GRPC_TIMEOUT,
    ):
        with self._channel() as channel:
            stub = DagsterApiStub(channel)
            return getattr(stub, method)(request, metadata=self._metadata, timeout=timeout)

    def _query(
        self,
        method,
        request_type,
        timeout=DEFAULT_GRPC_TIMEOUT,
        **kwargs,
    ):
        try:
            return self._get_response(method, request=request_type(**kwargs), timeout=timeout)
        except Exception as e:
            raise DagsterUserCodeUnreachableError("Could not reach user code server") from e

    def _get_streaming_response(
        self,
        method,
        request,
        timeout=DEFAULT_GRPC_TIMEOUT,
    ):

        with self._channel() as channel:
            stub = DagsterApiStub(channel)
            yield from getattr(stub, method)(request, metadata=self._metadata, timeout=timeout)

    def _streaming_query(
        self,
        method,
        request_type,
        timeout=DEFAULT_GRPC_TIMEOUT,
        **kwargs,
    ):
        try:
            yield from self._get_streaming_response(
                method, request=request_type(**kwargs), timeout=timeout
            )
        except Exception as e:
            raise DagsterUserCodeUnreachableError("Could not reach user code server") from e

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

    def get_server_id(self, timeout=None):
        res = self._query("GetServerId", api_pb2.Empty, timeout=timeout)
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
        return res.serialized_execution_plan_snapshot

    def list_repositories(self):
        res = self._query("ListRepositories", api_pb2.ListRepositoriesRequest)
        return res.serialized_list_repositories_response_or_error

    def external_partition_names(self, partition_names_args):
        check.inst_param(partition_names_args, "partition_names_args", PartitionNamesArgs)

        res = self._query(
            "ExternalPartitionNames",
            api_pb2.ExternalPartitionNamesRequest,
            serialized_partition_names_args=serialize_dagster_namedtuple(partition_names_args),
        )

        return res.serialized_external_partition_names_or_external_partition_execution_error

    def external_partition_config(self, partition_args):
        check.inst_param(partition_args, "partition_args", PartitionArgs)

        res = self._query(
            "ExternalPartitionConfig",
            api_pb2.ExternalPartitionConfigRequest,
            serialized_partition_args=serialize_dagster_namedtuple(partition_args),
        )

        return res.serialized_external_partition_config_or_external_partition_execution_error

    def external_partition_tags(self, partition_args):
        check.inst_param(partition_args, "partition_args", PartitionArgs)

        res = self._query(
            "ExternalPartitionTags",
            api_pb2.ExternalPartitionTagsRequest,
            serialized_partition_args=serialize_dagster_namedtuple(partition_args),
        )

        return res.serialized_external_partition_tags_or_external_partition_execution_error

    def external_partition_set_execution_params(self, partition_set_execution_param_args):
        check.inst_param(
            partition_set_execution_param_args,
            "partition_set_execution_param_args",
            PartitionSetExecutionParamArgs,
        )

        chunks = list(
            self._streaming_query(
                "ExternalPartitionSetExecutionParams",
                api_pb2.ExternalPartitionSetExecutionParamsRequest,
                serialized_partition_set_execution_param_args=serialize_dagster_namedtuple(
                    partition_set_execution_param_args
                ),
            )
        )

        return "".join([chunk.serialized_chunk for chunk in chunks])

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

        return res.serialized_external_pipeline_subset_result

    def external_repository(
        self,
        external_repository_origin: ExternalRepositoryOrigin,
        defer_snapshots: bool = False,
    ):
        check.inst_param(
            external_repository_origin,
            "external_repository_origin",
            ExternalRepositoryOrigin,
        )

        res = self._query(
            "ExternalRepository",
            api_pb2.ExternalRepositoryRequest,
            # rename this param name
            serialized_repository_python_origin=serialize_dagster_namedtuple(
                external_repository_origin
            ),
            defer_snapshots=defer_snapshots,
        )

        return res.serialized_external_repository_data

    def external_job(
        self,
        external_repository_origin: ExternalRepositoryOrigin,
        job_name: str,
    ):
        check.inst_param(
            external_repository_origin,
            "external_repository_origin",
            ExternalRepositoryOrigin,
        )

        return self._query(
            "ExternalJob",
            api_pb2.ExternalJobRequest,
            serialized_repository_origin=serialize_dagster_namedtuple(external_repository_origin),
            job_name=job_name,
        )

    def streaming_external_repository(
        self,
        external_repository_origin: ExternalRepositoryOrigin,
        defer_snapshots: bool = False,
    ):
        for res in self._streaming_query(
            "StreamingExternalRepository",
            api_pb2.ExternalRepositoryRequest,
            # Rename parameter
            serialized_repository_python_origin=serialize_dagster_namedtuple(
                external_repository_origin
            ),
            defer_snapshots=defer_snapshots,
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

        chunks = list(
            self._streaming_query(
                "ExternalScheduleExecution",
                api_pb2.ExternalScheduleExecutionRequest,
                serialized_external_schedule_execution_args=serialize_dagster_namedtuple(
                    external_schedule_execution_args
                ),
            )
        )

        return "".join([chunk.serialized_chunk for chunk in chunks])

    def external_sensor_execution(self, sensor_execution_args, timeout=DEFAULT_GRPC_TIMEOUT):
        check.inst_param(
            sensor_execution_args,
            "sensor_execution_args",
            SensorExecutionArgs,
        )

        chunks = list(
            self._streaming_query(
                "ExternalSensorExecution",
                api_pb2.ExternalSensorExecutionRequest,
                timeout=timeout,
                serialized_external_sensor_execution_args=serialize_dagster_namedtuple(
                    sensor_execution_args
                ),
            )
        )

        return "".join([chunk.serialized_chunk for chunk in chunks])

    def external_notebook_data(self, notebook_path: str):
        check.str_param(notebook_path, "notebook_path")
        res = self._query(
            "ExternalNotebookData",
            api_pb2.ExternalNotebookDataRequest,
            notebook_path=notebook_path,
        )
        return res.content

    def shutdown_server(self, timeout=15):
        res = self._query("ShutdownServer", api_pb2.Empty, timeout=timeout)
        return res.serialized_shutdown_server_result

    def cancel_execution(self, cancel_execution_request):
        check.inst_param(
            cancel_execution_request,
            "cancel_execution_request",
            CancelExecutionRequest,
        )

        res = self._query(
            "CancelExecution",
            api_pb2.CancelExecutionRequest,
            serialized_cancel_execution_request=serialize_dagster_namedtuple(
                cancel_execution_request
            ),
        )

        return res.serialized_cancel_execution_result

    def can_cancel_execution(self, can_cancel_execution_request, timeout=None):
        check.inst_param(
            can_cancel_execution_request,
            "can_cancel_execution_request",
            CanCancelExecutionRequest,
        )

        res = self._query(
            "CanCancelExecution",
            api_pb2.CanCancelExecutionRequest,
            timeout=timeout,
            serialized_can_cancel_execution_request=serialize_dagster_namedtuple(
                can_cancel_execution_request
            ),
        )

        return res.serialized_can_cancel_execution_result

    def start_run(self, execute_run_args):
        check.inst_param(execute_run_args, "execute_run_args", ExecuteExternalPipelineArgs)

        with DagsterInstance.from_ref(execute_run_args.instance_ref) as instance:
            try:
                res = self._query(
                    "StartRun",
                    api_pb2.StartRunRequest,
                    serialized_execute_run_args=serialize_dagster_namedtuple(execute_run_args),
                )
                return res.serialized_start_run_result

            except Exception:
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
        return res.serialized_current_image

    def get_current_runs(self):
        res = self._query("GetCurrentRuns", api_pb2.Empty)
        return res.serialized_current_runs

    def health_check_query(self):
        try:
            with self._channel() as channel:
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
                except DagsterUserCodeUnreachableError:
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
    loadable_target_origin: Optional[LoadableTargetOrigin] = None,
    force_port: bool = False,
    max_retries: int = 10,
    max_workers: Optional[int] = None,
) -> Iterator[EphemeralDagsterGrpcClient]:
    check.opt_inst_param(loadable_target_origin, "loadable_target_origin", LoadableTargetOrigin)
    check.bool_param(force_port, "force_port")
    check.int_param(max_retries, "max_retries")

    from dagster._core.test_utils import instance_for_test

    with instance_for_test() as instance:
        with GrpcServerProcess(
            instance_ref=instance.get_ref(),
            loadable_target_origin=loadable_target_origin,
            force_port=force_port,
            max_retries=max_retries,
            max_workers=max_workers,
        ).create_ephemeral_client() as client:
            yield client
