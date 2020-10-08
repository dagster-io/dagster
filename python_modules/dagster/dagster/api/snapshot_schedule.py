from datetime import datetime

from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.types import ExternalScheduleExecutionArgs, ScheduleExecutionDataMode
from dagster.seven import get_timestamp_from_utc_datetime

from .utils import execute_unary_api_cli_command


def sync_get_external_schedule_execution_data(
    instance,
    repository_handle,
    schedule_name,
    schedule_execution_data_mode,
    scheduled_execution_datetime_utc,
):

    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(schedule_name, "schedule_name")
    check.opt_inst_param(
        scheduled_execution_datetime_utc, "scheduled_execution_datetime_utc", datetime
    )
    check.inst_param(
        schedule_execution_data_mode, "schedule_execution_data_mode", ScheduleExecutionDataMode
    )

    origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            origin.executable_path,
            "schedule_config",
            ExternalScheduleExecutionArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                schedule_name=schedule_name,
                scheduled_execution_timestamp_utc=(
                    get_timestamp_from_utc_datetime(scheduled_execution_datetime_utc)
                    if scheduled_execution_datetime_utc
                    else None
                ),
                schedule_execution_data_mode=schedule_execution_data_mode,
            ),
        ),
        (ExternalScheduleExecutionData, ExternalScheduleExecutionErrorData),
    )


def sync_get_external_schedule_execution_data_ephemeral_grpc(
    instance,
    repository_handle,
    schedule_name,
    schedule_execution_data_mode,
    scheduled_execution_datetime_utc,
):
    from dagster.grpc.client import ephemeral_grpc_api_client

    origin = repository_handle.get_origin()
    with ephemeral_grpc_api_client(
        LoadableTargetOrigin(executable_path=origin.executable_path)
    ) as api_client:
        return sync_get_external_schedule_execution_data_grpc(
            api_client,
            instance,
            repository_handle,
            schedule_name,
            schedule_execution_data_mode,
            scheduled_execution_datetime_utc,
        )


def sync_get_external_schedule_execution_data_grpc(
    api_client,
    instance,
    repository_handle,
    schedule_name,
    schedule_execution_data_mode,
    scheduled_execution_datetime_utc,
):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(schedule_name, "schedule_name")
    check.opt_inst_param(
        scheduled_execution_datetime_utc, "scheduled_execution_datetime_utc", datetime
    )
    check.inst_param(
        schedule_execution_data_mode, "schedule_execution_data_mode", ScheduleExecutionDataMode
    )

    origin = repository_handle.get_origin()

    return check.inst(
        api_client.external_schedule_execution(
            external_schedule_execution_args=ExternalScheduleExecutionArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                schedule_name=schedule_name,
                scheduled_execution_timestamp_utc=(
                    get_timestamp_from_utc_datetime(scheduled_execution_datetime_utc)
                    if scheduled_execution_datetime_utc
                    else None
                ),
                schedule_execution_data_mode=schedule_execution_data_mode,
            )
        ),
        (ExternalScheduleExecutionData, ExternalScheduleExecutionErrorData),
    )
