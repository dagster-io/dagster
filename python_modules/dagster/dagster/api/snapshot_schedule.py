import pendulum
from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.host_representation.handle import RepositoryHandle
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.types import ExternalScheduleExecutionArgs, ScheduleExecutionDataMode


def sync_get_external_schedule_execution_data_ephemeral_grpc(
    instance,
    repository_handle,
    schedule_name,
    schedule_execution_data_mode,
    scheduled_execution_time,
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
            scheduled_execution_time,
        )


def sync_get_external_schedule_execution_data_grpc(
    api_client,
    instance,
    repository_handle,
    schedule_name,
    schedule_execution_data_mode,
    scheduled_execution_time,
):
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(schedule_name, "schedule_name")
    check.inst_param(
        schedule_execution_data_mode, "schedule_execution_data_mode", ScheduleExecutionDataMode
    )
    check.opt_inst_param(scheduled_execution_time, "scheduled_execution_time", pendulum.Pendulum)

    origin = repository_handle.get_origin()

    return check.inst(
        api_client.external_schedule_execution(
            external_schedule_execution_args=ExternalScheduleExecutionArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                schedule_name=schedule_name,
                schedule_execution_data_mode=schedule_execution_data_mode,
                scheduled_execution_timestamp=scheduled_execution_time.timestamp()
                if scheduled_execution_time
                else None,
                scheduled_execution_timezone=scheduled_execution_time.timezone.name
                if scheduled_execution_time
                else None,
            )
        ),
        (ExternalScheduleExecutionData, ExternalScheduleExecutionErrorData),
    )
