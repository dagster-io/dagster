from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster.core.definitions.sensor_definition import SensorExecutionData
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.external_data import ExternalSensorExecutionErrorData
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.grpc.types import SensorExecutionArgs
from dagster.serdes import deserialize_as

if TYPE_CHECKING:
    from dagster.core.instance import DagsterInstance
    from dagster.grpc.client import DagsterGrpcClient


def sync_get_external_sensor_execution_data_ephemeral_grpc(
    instance, repository_handle, sensor_name, last_completion_time, last_run_key, cursor
):
    from dagster.grpc.client import ephemeral_grpc_api_client

    origin = repository_handle.get_external_origin()
    with ephemeral_grpc_api_client(
        origin.repository_location_origin.loadable_target_origin
    ) as api_client:
        return sync_get_external_sensor_execution_data_grpc(
            api_client,
            instance,
            repository_handle,
            sensor_name,
            last_completion_time,
            last_run_key,
            cursor,
        )


def sync_get_external_sensor_execution_data_grpc(
    api_client: "DagsterGrpcClient",
    instance: "DagsterInstance",
    repository_handle: RepositoryHandle,
    sensor_name: str,
    last_completion_time: Optional[float],
    last_run_key: Optional[str],
    cursor: Optional[str],
) -> SensorExecutionData:
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(sensor_name, "sensor_name")
    check.opt_float_param(last_completion_time, "last_completion_time")
    check.opt_str_param(last_run_key, "last_run_key")
    check.opt_str_param(cursor, "cursor")

    origin = repository_handle.get_external_origin()

    result = deserialize_as(
        api_client.external_sensor_execution(
            sensor_execution_args=SensorExecutionArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                sensor_name=sensor_name,
                last_completion_time=last_completion_time,
                last_run_key=last_run_key,
                cursor=cursor,
            )
        ),
        (SensorExecutionData, ExternalSensorExecutionErrorData),
    )

    if isinstance(result, ExternalSensorExecutionErrorData):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result
