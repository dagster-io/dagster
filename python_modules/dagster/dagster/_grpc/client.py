import os
import sys
from collections.abc import AsyncIterable, AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager, contextmanager
from threading import Event
from typing import Any, NoReturn, Optional, cast

import dagster_shared.seven as seven
import google.protobuf.message
import grpc
from grpc_health.v1 import health_pb2
from grpc_health.v1.health_pb2_grpc import HealthStub

import dagster._check as check
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.events import EngineEventData
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.origin import RemoteRepositoryOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.__generated__ import DagsterApiStub, dagster_api_pb2
from dagster._grpc.server import GrpcServerProcess
from dagster._grpc.types import (
    CanCancelExecutionRequest,
    CancelExecutionRequest,
    ExecuteExternalJobArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    JobSubsetSnapshotArgs,
    PartitionArgs,
    PartitionNamesArgs,
    PartitionSetExecutionParamArgs,
    SensorExecutionArgs,
)
from dagster._grpc.utils import (
    default_grpc_timeout,
    default_repository_grpc_timeout,
    default_schedule_grpc_timeout,
    default_sensor_grpc_timeout,
    max_rx_bytes,
    max_send_bytes,
)
from dagster._serdes import serialize_value
from dagster._utils.error import serializable_error_info_from_exc_info

CLIENT_HEARTBEAT_INTERVAL = 1

DEFAULT_GRPC_TIMEOUT = default_grpc_timeout()
DEFAULT_SCHEDULE_GRPC_TIMEOUT = default_schedule_grpc_timeout()
DEFAULT_SENSOR_GRPC_TIMEOUT = default_sensor_grpc_timeout()
DEFAULT_REPOSITORY_GRPC_TIMEOUT = default_repository_grpc_timeout()


def client_heartbeat_thread(client: "DagsterGrpcClient", shutdown_event: Event) -> None:
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
        port: Optional[int] = None,
        socket: Optional[str] = None,
        host: str = "localhost",
        use_ssl: bool = False,
        metadata: Optional[Sequence[tuple[str, str]]] = None,
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
            socket = check.not_none(socket)
            self._server_address = "unix:" + os.path.abspath(socket)

    @property
    def metadata(self) -> Sequence[tuple[str, str]]:
        return self._metadata

    @property
    def use_ssl(self) -> bool:
        return self._use_ssl

    @contextmanager
    def _channel(self) -> Iterator[grpc.Channel]:
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

    @asynccontextmanager
    async def _async_channel(self) -> AsyncIterator[grpc.Channel]:
        options = [
            ("grpc.max_receive_message_length", max_rx_bytes()),
            ("grpc.max_send_message_length", max_send_bytes()),
        ]
        async with (
            grpc.aio.secure_channel(
                self._server_address,
                self._ssl_creds,
                options=options,
                compression=grpc.Compression.Gzip,
            )
            if self._use_ssl
            else grpc.aio.insecure_channel(
                self._server_address,
                options=options,
                compression=grpc.Compression.Gzip,
            )
        ) as channel:
            yield channel

    def _get_response(
        self,
        method: str,
        request: google.protobuf.message.Message,
        timeout: int = DEFAULT_GRPC_TIMEOUT,
    ):
        with self._channel() as channel:
            stub = DagsterApiStub(channel)
            return getattr(stub, method)(request, metadata=self._metadata, timeout=timeout)

    async def _gen_response(
        self,
        method: str,
        request: google.protobuf.message.Message,
        timeout: int = DEFAULT_GRPC_TIMEOUT,
    ):
        async with self._async_channel() as channel:
            stub = DagsterApiStub(channel)
            return await getattr(stub, method)(request, metadata=self._metadata, timeout=timeout)

    def _raise_grpc_exception(
        self,
        e: Exception,
        timeout: int,
        custom_timeout_message: Optional[str] = None,
    ) -> NoReturn:
        if isinstance(e, grpc.RpcError):
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:  # type: ignore  # (bad stubs)
                raise DagsterUserCodeUnreachableError(
                    custom_timeout_message
                    or f"User code server request timed out due to taking longer than {timeout} seconds to complete."
                ) from e
            else:
                raise DagsterUserCodeUnreachableError(
                    f"Could not reach user code server. gRPC Error code: {e.code().name}"  # type: ignore  # (bad stubs)
                ) from e
        else:
            raise DagsterUserCodeUnreachableError("Could not reach user code server") from e

    def _query(
        self,
        method: str,
        request_type: type[google.protobuf.message.Message],
        timeout: int = DEFAULT_GRPC_TIMEOUT,
        custom_timeout_message: Optional[str] = None,
        **kwargs,
    ):
        try:
            return self._get_response(method, request=request_type(**kwargs), timeout=timeout)
        except Exception as e:
            self._raise_grpc_exception(
                e, timeout=timeout, custom_timeout_message=custom_timeout_message
            )

    async def _gen_query(
        self,
        method: str,
        request_type: type[google.protobuf.message.Message],
        timeout: int = DEFAULT_GRPC_TIMEOUT,
        custom_timeout_message: Optional[str] = None,
        **kwargs,
    ):
        try:
            return await self._gen_response(method, request=request_type(**kwargs), timeout=timeout)
        except Exception as e:
            self._raise_grpc_exception(
                e, timeout=timeout, custom_timeout_message=custom_timeout_message
            )

    def _get_streaming_response(
        self,
        method: str,
        request: google.protobuf.message.Message,
        timeout: int = DEFAULT_GRPC_TIMEOUT,
    ) -> Iterator[Any]:
        with self._channel() as channel:
            stub = DagsterApiStub(channel)
            yield from getattr(stub, method)(request, metadata=self._metadata, timeout=timeout)

    async def _gen_streaming_response(
        self,
        method: str,
        request: google.protobuf.message.Message,
        timeout: int = DEFAULT_GRPC_TIMEOUT,
    ) -> AsyncIterator[Any]:
        async with self._async_channel() as channel:
            stub = DagsterApiStub(channel)
            async for response in getattr(stub, method)(
                request, metadata=self._metadata, timeout=timeout
            ):
                yield response

    def _streaming_query(
        self,
        method: str,
        request_type: type[google.protobuf.message.Message],
        timeout=DEFAULT_GRPC_TIMEOUT,
        custom_timeout_message=None,
        **kwargs,
    ) -> Iterator[Any]:
        try:
            yield from self._get_streaming_response(
                method, request=request_type(**kwargs), timeout=timeout
            )
        except Exception as e:
            self._raise_grpc_exception(
                e, timeout=timeout, custom_timeout_message=custom_timeout_message
            )

    async def _gen_streaming_query(
        self,
        method: str,
        request_type: type[google.protobuf.message.Message],
        timeout=DEFAULT_GRPC_TIMEOUT,
        custom_timeout_message=None,
        **kwargs,
    ) -> AsyncIterable[Any]:
        try:
            async for response in self._gen_streaming_response(
                method, request=request_type(**kwargs), timeout=timeout
            ):
                yield response
        except Exception as e:
            self._raise_grpc_exception(
                e, timeout=timeout, custom_timeout_message=custom_timeout_message
            )

    def ping(self, echo: str) -> dict[str, Any]:
        check.str_param(echo, "echo")
        res = self._query("Ping", dagster_api_pb2.PingRequest, echo=echo)
        return {
            "echo": res.echo,
            "serialized_server_utilization_metrics": res.serialized_server_utilization_metrics,
        }

    def heartbeat(self, echo: str = "") -> str:
        check.str_param(echo, "echo")
        res = self._query("Heartbeat", dagster_api_pb2.PingRequest, echo=echo)
        return res.echo

    def streaming_ping(self, sequence_length: int, echo: str) -> Iterator[dict]:
        check.int_param(sequence_length, "sequence_length")
        check.str_param(echo, "echo")

        for res in self._streaming_query(
            "StreamingPing",
            dagster_api_pb2.StreamingPingRequest,
            sequence_length=sequence_length,
            echo=echo,
        ):
            yield {
                "sequence_number": res.sequence_number,
                "echo": res.echo,
            }

    def get_server_id(self, timeout: int = DEFAULT_GRPC_TIMEOUT) -> str:
        res = self._query("GetServerId", dagster_api_pb2.Empty, timeout=timeout)
        return res.server_id

    def execution_plan_snapshot(
        self, execution_plan_snapshot_args: ExecutionPlanSnapshotArgs
    ) -> str:
        check.inst_param(
            execution_plan_snapshot_args, "execution_plan_snapshot_args", ExecutionPlanSnapshotArgs
        )
        res = self._query(
            "ExecutionPlanSnapshot",
            dagster_api_pb2.ExecutionPlanSnapshotRequest,
            serialized_execution_plan_snapshot_args=serialize_value(execution_plan_snapshot_args),
        )
        return res.serialized_execution_plan_snapshot

    def list_repositories(self) -> str:
        res = self._query("ListRepositories", dagster_api_pb2.ListRepositoriesRequest)
        return res.serialized_list_repositories_response_or_error

    async def gen_list_repositories(self, **kwargs) -> str:
        res = await self._gen_query(
            "ListRepositories", dagster_api_pb2.ListRepositoriesRequest, **kwargs
        )
        return res.serialized_list_repositories_response_or_error

    def external_partition_names(self, partition_names_args: PartitionNamesArgs) -> str:
        check.inst_param(partition_names_args, "partition_names_args", PartitionNamesArgs)

        res = self._query(
            "ExternalPartitionNames",
            dagster_api_pb2.ExternalPartitionNamesRequest,
            serialized_partition_names_args=serialize_value(partition_names_args),
        )

        return res.serialized_external_partition_names_or_external_partition_execution_error

    def external_partition_config(self, partition_args: PartitionArgs) -> str:
        check.inst_param(partition_args, "partition_args", PartitionArgs)

        res = self._query(
            "ExternalPartitionConfig",
            dagster_api_pb2.ExternalPartitionConfigRequest,
            serialized_partition_args=serialize_value(partition_args),
        )

        return res.serialized_external_partition_config_or_external_partition_execution_error

    def external_partition_tags(self, partition_args: PartitionArgs) -> str:
        check.inst_param(partition_args, "partition_args", PartitionArgs)

        res = self._query(
            "ExternalPartitionTags",
            dagster_api_pb2.ExternalPartitionTagsRequest,
            serialized_partition_args=serialize_value(partition_args),
        )

        return res.serialized_external_partition_tags_or_external_partition_execution_error

    def external_partition_set_execution_params(
        self, partition_set_execution_param_args: PartitionSetExecutionParamArgs
    ) -> str:
        check.inst_param(
            partition_set_execution_param_args,
            "partition_set_execution_param_args",
            PartitionSetExecutionParamArgs,
        )

        chunks = list(
            self._streaming_query(
                "ExternalPartitionSetExecutionParams",
                dagster_api_pb2.ExternalPartitionSetExecutionParamsRequest,
                serialized_partition_set_execution_param_args=serialize_value(
                    partition_set_execution_param_args
                ),
            )
        )

        return "".join([chunk.serialized_chunk for chunk in chunks])

    def external_pipeline_subset(self, pipeline_subset_snapshot_args: JobSubsetSnapshotArgs) -> str:
        check.inst_param(
            pipeline_subset_snapshot_args,
            "pipeline_subset_snapshot_args",
            JobSubsetSnapshotArgs,
        )

        res = self._query(
            "ExternalPipelineSubsetSnapshot",
            dagster_api_pb2.ExternalPipelineSubsetSnapshotRequest,
            serialized_pipeline_subset_snapshot_args=serialize_value(pipeline_subset_snapshot_args),
        )

        return res.serialized_external_pipeline_subset_result

    def reload_code(self, timeout: int) -> dagster_api_pb2.ReloadCodeReply:
        return self._query("ReloadCode", dagster_api_pb2.ReloadCodeRequest, timeout=timeout)

    def external_repository(
        self,
        remote_repository_origin: RemoteRepositoryOrigin,
        defer_snapshots: bool = False,
    ) -> str:
        check.inst_param(
            remote_repository_origin,
            "remote_repository_origin",
            RemoteRepositoryOrigin,
        )

        res = self._query(
            "ExternalRepository",
            dagster_api_pb2.ExternalRepositoryRequest,
            # rename this param name
            serialized_repository_python_origin=serialize_value(remote_repository_origin),
            defer_snapshots=defer_snapshots,
        )

        return res.serialized_external_repository_data

    def external_job(
        self,
        remote_repository_origin: RemoteRepositoryOrigin,
        job_name: str,
        timeout=DEFAULT_GRPC_TIMEOUT,
    ) -> dagster_api_pb2.ExternalJobReply:
        check.inst_param(
            remote_repository_origin,
            "remote_repository_origin",
            RemoteRepositoryOrigin,
        )

        return self._query(
            "ExternalJob",
            dagster_api_pb2.ExternalJobRequest,
            serialized_repository_origin=serialize_value(remote_repository_origin),
            job_name=job_name,
            timeout=timeout,
        )

    def streaming_external_repository(
        self,
        remote_repository_origin: RemoteRepositoryOrigin,
        defer_snapshots: bool = False,
        timeout=DEFAULT_REPOSITORY_GRPC_TIMEOUT,
    ) -> Iterator[dict]:
        for res in self._streaming_query(
            "StreamingExternalRepository",
            dagster_api_pb2.ExternalRepositoryRequest,
            # Rename parameter
            serialized_repository_python_origin=serialize_value(remote_repository_origin),
            defer_snapshots=defer_snapshots,
            timeout=timeout,
        ):
            yield {
                "sequence_number": res.sequence_number,
                "serialized_external_repository_chunk": res.serialized_external_repository_chunk,
            }

    async def gen_streaming_external_repository(
        self,
        remote_repository_origin: RemoteRepositoryOrigin,
        defer_snapshots: bool = False,
        timeout=DEFAULT_REPOSITORY_GRPC_TIMEOUT,
    ) -> AsyncIterable[dict]:
        async for res in self._gen_streaming_query(
            "StreamingExternalRepository",
            dagster_api_pb2.ExternalRepositoryRequest,
            # Rename parameter
            serialized_repository_python_origin=serialize_value(remote_repository_origin),
            defer_snapshots=defer_snapshots,
            timeout=timeout,
        ):
            yield {
                "sequence_number": res.sequence_number,
                "serialized_external_repository_chunk": res.serialized_external_repository_chunk,
            }

    def _is_unimplemented_error(self, e: Exception) -> bool:
        return (
            isinstance(e.__cause__, grpc.RpcError)
            and cast(grpc.RpcError, e.__cause__).code() == grpc.StatusCode.UNIMPLEMENTED
        )

    def external_schedule_execution(
        self, external_schedule_execution_args: ExternalScheduleExecutionArgs
    ) -> str:
        check.inst_param(
            external_schedule_execution_args,
            "external_schedule_execution_args",
            ExternalScheduleExecutionArgs,
        )

        # The timeout for the schedule can be defined in one of three ways.
        #   1. By the default grpc timeout
        #   2. By the DEFAULT_SCHEDULE_GRPC_TIMEOUT environment variable
        #   3. By the client.
        # The DEFAULT_SCHEDULE_GRPC_TIMEOUT constant takes the maximum of (1) and
        # (2), while
        # the client may pass a timeout argument via the
        # `sensor_execution_args` object. If the timeout is passed from the client, we use that value irrespective of what the other timeout values may be set to.
        timeout = (
            external_schedule_execution_args.timeout
            if external_schedule_execution_args.timeout is not None
            else DEFAULT_SCHEDULE_GRPC_TIMEOUT
        )

        try:
            return self._query(
                "SyncExternalScheduleExecution",
                dagster_api_pb2.ExternalScheduleExecutionRequest,
                serialized_external_schedule_execution_args=serialize_value(
                    external_schedule_execution_args
                ),
                timeout=timeout,
            ).serialized_schedule_result
        except Exception as e:
            # On older servers that only have the streaming API call implemented, fall back to that API
            if self._is_unimplemented_error(e):
                chunks = list(
                    self._streaming_query(
                        "ExternalScheduleExecution",
                        dagster_api_pb2.ExternalScheduleExecutionRequest,
                        serialized_external_schedule_execution_args=serialize_value(
                            external_schedule_execution_args
                        ),
                        timeout=timeout,
                    )
                )
                return "".join([chunk.serialized_chunk for chunk in chunks])
            else:
                raise

    def external_sensor_execution(self, sensor_execution_args: SensorExecutionArgs) -> str:
        check.inst_param(
            sensor_execution_args,
            "sensor_execution_args",
            SensorExecutionArgs,
        )
        # The timeout for the sensor can be defined in one of three ways.
        #   1. By the default grpc timeout
        #   2. By the DEFAULT_SENSOR_GRPC_TIMEOUT environment variable
        #   3. By the client.
        # The DEFAULT_SENSOR_GRPC_TIMEOUT constant takes the maximum of (1) and
        # (2), while
        # the client may pass a timeout argument via the
        # `sensor_execution_args` object. If the timeout is passed from the client, we use that value irrespective of what the other timeout values may be set to.
        timeout = (
            sensor_execution_args.timeout
            if sensor_execution_args.timeout is not None
            else DEFAULT_SENSOR_GRPC_TIMEOUT
        )

        custom_timeout_message = (
            f"The sensor tick timed out due to taking longer than {timeout} seconds to execute the"
            " sensor function. One way to avoid this error is to break up the sensor work into"
            " chunks, using cursors to let subsequent sensor calls pick up where the previous call"
            " left off."
        )

        try:
            return self._query(
                "SyncExternalSensorExecution",
                dagster_api_pb2.ExternalSensorExecutionRequest,
                timeout=timeout,
                serialized_external_sensor_execution_args=serialize_value(sensor_execution_args),
                custom_timeout_message=custom_timeout_message,
            ).serialized_sensor_result
        except Exception as e:
            # On older servers that only have the streaming API call implemented, fall back to that API
            if self._is_unimplemented_error(e):
                chunks = list(
                    self._streaming_query(
                        "ExternalSensorExecution",
                        dagster_api_pb2.ExternalSensorExecutionRequest,
                        timeout=timeout,
                        serialized_external_sensor_execution_args=serialize_value(
                            sensor_execution_args
                        ),
                        custom_timeout_message=custom_timeout_message,
                    )
                )

                return "".join([chunk.serialized_chunk for chunk in chunks])
            else:
                raise

    def external_notebook_data(self, notebook_path: str) -> bytes:
        check.str_param(notebook_path, "notebook_path")
        res = self._query(
            "ExternalNotebookData",
            dagster_api_pb2.ExternalNotebookDataRequest,
            notebook_path=notebook_path,
        )
        return res.content

    def shutdown_server(self, timeout: int = 15) -> str:
        res = self._query("ShutdownServer", dagster_api_pb2.Empty, timeout=timeout)
        return res.serialized_shutdown_server_result

    def cancel_execution(self, cancel_execution_request: CancelExecutionRequest) -> str:
        check.inst_param(
            cancel_execution_request,
            "cancel_execution_request",
            CancelExecutionRequest,
        )

        res = self._query(
            "CancelExecution",
            dagster_api_pb2.CancelExecutionRequest,
            serialized_cancel_execution_request=serialize_value(cancel_execution_request),
        )

        return res.serialized_cancel_execution_result

    def can_cancel_execution(
        self,
        can_cancel_execution_request: CanCancelExecutionRequest,
        timeout: int = DEFAULT_GRPC_TIMEOUT,
    ) -> str:
        check.inst_param(
            can_cancel_execution_request,
            "can_cancel_execution_request",
            CanCancelExecutionRequest,
        )

        res = self._query(
            "CanCancelExecution",
            dagster_api_pb2.CanCancelExecutionRequest,
            timeout=timeout,
            serialized_can_cancel_execution_request=serialize_value(can_cancel_execution_request),
        )

        return res.serialized_can_cancel_execution_result

    def start_run(self, execute_run_args: ExecuteExternalJobArgs) -> str:
        check.inst_param(execute_run_args, "execute_run_args", ExecuteExternalJobArgs)

        with DagsterInstance.from_ref(execute_run_args.instance_ref) as instance:  # type: ignore # (possible none)
            try:
                res = self._query(
                    "StartRun",
                    dagster_api_pb2.StartRunRequest,
                    serialized_execute_run_args=serialize_value(execute_run_args),
                )
                return res.serialized_start_run_result

            except Exception:
                dagster_run = instance.get_run_by_id(execute_run_args.run_id)
                instance.report_engine_event(
                    message="Unexpected error in IPC client",
                    dagster_run=dagster_run,
                    engine_event_data=EngineEventData.engine_error(
                        serializable_error_info_from_exc_info(sys.exc_info())
                    ),
                )
                raise

    def get_current_image(self) -> str:
        res = self._query("GetCurrentImage", dagster_api_pb2.Empty)
        return res.serialized_current_image

    def get_current_runs(self) -> str:
        res = self._query("GetCurrentRuns", dagster_api_pb2.Empty)
        return res.serialized_current_runs

    def health_check_query(self):
        try:
            with self._channel() as channel:
                response = HealthStub(channel).Check(
                    health_pb2.HealthCheckRequest(service="DagsterApi")
                )
        except grpc.RpcError as e:
            print(e)  # noqa: T201
            return health_pb2.HealthCheckResponse.UNKNOWN

        status_number = response.status

        return health_pb2.HealthCheckResponse.ServingStatus.Name(status_number)


@contextmanager
def ephemeral_grpc_api_client(
    loadable_target_origin: Optional[LoadableTargetOrigin] = None,
    force_port: bool = False,
    max_retries: int = 10,
    max_workers: Optional[int] = None,
) -> Iterator[DagsterGrpcClient]:
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
            wait_on_exit=True,
        ) as server_process:
            yield server_process.create_client()
