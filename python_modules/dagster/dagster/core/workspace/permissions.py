from enum import Enum, unique
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .context import WorkspaceProcessContext


@unique
class Permissions(str, Enum):
    LAUNCH_PIPELINE_EXECUTION = "launch_pipeline_execution"
    LAUNCH_PIPELINE_REEXECUTION = "launch_pipeline_reexecution"
    START_SCHEDULE = "start_schedule"
    STOP_RUNNING_SCHEDULE = "stop_running_schedule"
    EDIT_SENSOR = "edit_sensor"
    TERMINATE_PIPELINE_EXECUTION = "terminate_pipeline_execution"
    DELETE_PIPELINE_RUN = "delete_pipeline_run"
    RELOAD_REPOSITORY_LOCATION = "reload_repository_location"
    RELOAD_WORKSPACE = "reload_workspace"
    WIPE_ASSETS = "wipe_assets"
    LAUNCH_PARTITION_BACKFILL = "launch_partition_backfill"
    CANCEL_PARTITION_BACKFILL = "cancel_partition_backfill"

    def __str__(self) -> str:
        return str.__str__(self)


VIEWER_PERMISSIONS: Dict[str, bool] = {
    Permissions.LAUNCH_PIPELINE_EXECUTION: False,
    Permissions.LAUNCH_PIPELINE_REEXECUTION: False,
    Permissions.START_SCHEDULE: False,
    Permissions.STOP_RUNNING_SCHEDULE: False,
    Permissions.EDIT_SENSOR: False,
    Permissions.TERMINATE_PIPELINE_EXECUTION: False,
    Permissions.DELETE_PIPELINE_RUN: False,
    Permissions.RELOAD_REPOSITORY_LOCATION: False,
    Permissions.RELOAD_WORKSPACE: False,
    Permissions.WIPE_ASSETS: False,
    Permissions.LAUNCH_PARTITION_BACKFILL: False,
    Permissions.CANCEL_PARTITION_BACKFILL: False,
}

EDITOR_PERMISSIONS: Dict[str, bool] = {
    Permissions.LAUNCH_PIPELINE_EXECUTION: True,
    Permissions.LAUNCH_PIPELINE_REEXECUTION: True,
    Permissions.START_SCHEDULE: True,
    Permissions.STOP_RUNNING_SCHEDULE: True,
    Permissions.EDIT_SENSOR: True,
    Permissions.TERMINATE_PIPELINE_EXECUTION: True,
    Permissions.DELETE_PIPELINE_RUN: True,
    Permissions.RELOAD_REPOSITORY_LOCATION: True,
    Permissions.RELOAD_WORKSPACE: True,
    Permissions.WIPE_ASSETS: True,
    Permissions.LAUNCH_PARTITION_BACKFILL: True,
    Permissions.CANCEL_PARTITION_BACKFILL: True,
}


def get_user_permissions(context: "WorkspaceProcessContext") -> Dict[str, bool]:
    if context.read_only:
        return VIEWER_PERMISSIONS
    else:
        return EDITOR_PERMISSIONS
