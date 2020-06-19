from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.host_representation.handle import RepositoryHandle

from .utils import execute_unary_api_cli_command


def sync_get_external_schedule_execution_data(instance, repository_handle, schedule_name):
    from dagster.cli.api import ScheduleExecutionDataCommandArgs

    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(schedule_name, 'schedule_name')

    origin = repository_handle.get_origin()

    return check.inst(
        execute_unary_api_cli_command(
            origin.executable_path,
            'schedule_config',
            ScheduleExecutionDataCommandArgs(
                repository_origin=origin,
                instance_ref=instance.get_ref(),
                schedule_name=schedule_name,
            ),
        ),
        (ExternalScheduleExecutionData, ExternalScheduleExecutionErrorData),
    )
