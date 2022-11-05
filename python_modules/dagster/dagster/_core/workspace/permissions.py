from enum import Enum, unique
from typing import TYPE_CHECKING, Dict, NamedTuple, Optional

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


class PermissionResult(
    NamedTuple("_PermissionResult", [("enabled", bool), ("disabled_reason", Optional[str])])
):
    def __bool__(self):
        raise Exception(
            "Don't check a PermissionResult for truthiness - check the `enabled` property instead"
        )


def _get_disabled_reason(enabled: bool):
    return None if enabled else "Disabled by your administrator"


def get_user_permissions(read_only: bool) -> Dict[str, PermissionResult]:
    if read_only:
        perm_map = VIEWER_PERMISSIONS
    else:
        perm_map = EDITOR_PERMISSIONS

    return {
        perm: PermissionResult(enabled=enabled, disabled_reason=_get_disabled_reason(enabled))
        for perm, enabled in perm_map.items()
    }
