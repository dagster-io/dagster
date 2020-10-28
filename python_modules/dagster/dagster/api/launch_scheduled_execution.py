import subprocess
import sys

from dagster import check
from dagster.core.errors import DagsterSubprocessError
from dagster.core.host_representation import ExternalScheduleOrigin
from dagster.core.scheduler import ScheduledExecutionResult
from dagster.serdes.ipc import IPCErrorMessage, read_unary_response
from dagster.seven import xplat_shlex_split
from dagster.utils.temp_file import get_temp_file_name


def sync_launch_scheduled_execution(schedule_origin):
    check.inst_param(schedule_origin, "schedule_origin", ExternalScheduleOrigin)

    with get_temp_file_name() as output_file:
        parts = (
            [sys.executable, "-m", "dagster", "api", "launch_scheduled_execution", output_file,]
            + xplat_shlex_split(schedule_origin.get_repo_cli_args())
            + ["--schedule_name={}".format(schedule_origin.schedule_name)]
        )
        subprocess.check_call(parts)
        result = read_unary_response(output_file)
        if isinstance(result, ScheduledExecutionResult):
            return result
        elif isinstance(result, IPCErrorMessage):
            error = result.serializable_error_info
            raise DagsterSubprocessError(
                "Error in API subprocess: {message}\n\n{err}".format(
                    message=result.message, err=error.to_string()
                ),
                subprocess_error_infos=[error],
            )
        else:
            check.failed("Unexpected result {}".format(result))
