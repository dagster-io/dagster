from collections.abc import Mapping
from enum import Enum, unique
from typing import NamedTuple, Optional


@unique
class Permissions(str, Enum):
    LAUNCH_PIPELINE_EXECUTION = "launch_pipeline_execution"
    LAUNCH_PIPELINE_REEXECUTION = "launch_pipeline_reexecution"
    START_SCHEDULE = "start_schedule"
    STOP_RUNNING_SCHEDULE = "stop_running_schedule"
    EDIT_SENSOR = "edit_sensor"
    UPDATE_SENSOR_CURSOR = "update_sensor_cursor"
    TERMINATE_PIPELINE_EXECUTION = "terminate_pipeline_execution"
    DELETE_PIPELINE_RUN = "delete_pipeline_run"
    RELOAD_REPOSITORY_LOCATION = "reload_repository_location"
    RELOAD_WORKSPACE = "reload_workspace"
    WIPE_ASSETS = "wipe_assets"
    REPORT_RUNLESS_ASSET_EVENTS = "report_runless_asset_events"
    LAUNCH_PARTITION_BACKFILL = "launch_partition_backfill"
    CANCEL_PARTITION_BACKFILL = "cancel_partition_backfill"
    EDIT_DYNAMIC_PARTITIONS = "edit_dynamic_partitions"
    TOGGLE_AUTO_MATERIALIZE = "toggle_auto_materialize"
    EDIT_CONCURRENCY_LIMIT = "edit_concurrency_limit"

    def __str__(self) -> str:
        return str.__str__(self)


VIEWER_PERMISSIONS: dict[str, bool] = {
    Permissions.LAUNCH_PIPELINE_EXECUTION: False,
    Permissions.LAUNCH_PIPELINE_REEXECUTION: False,
    Permissions.START_SCHEDULE: False,
    Permissions.STOP_RUNNING_SCHEDULE: False,
    Permissions.EDIT_SENSOR: False,
    Permissions.UPDATE_SENSOR_CURSOR: False,
    Permissions.TERMINATE_PIPELINE_EXECUTION: False,
    Permissions.DELETE_PIPELINE_RUN: False,
    Permissions.RELOAD_REPOSITORY_LOCATION: False,
    Permissions.RELOAD_WORKSPACE: False,
    Permissions.WIPE_ASSETS: False,
    Permissions.REPORT_RUNLESS_ASSET_EVENTS: False,
    Permissions.LAUNCH_PARTITION_BACKFILL: False,
    Permissions.CANCEL_PARTITION_BACKFILL: False,
    Permissions.EDIT_DYNAMIC_PARTITIONS: False,
    Permissions.TOGGLE_AUTO_MATERIALIZE: False,
    Permissions.EDIT_CONCURRENCY_LIMIT: False,
}

EDITOR_PERMISSIONS: dict[str, bool] = {
    Permissions.LAUNCH_PIPELINE_EXECUTION: True,
    Permissions.LAUNCH_PIPELINE_REEXECUTION: True,
    Permissions.START_SCHEDULE: True,
    Permissions.STOP_RUNNING_SCHEDULE: True,
    Permissions.EDIT_SENSOR: True,
    Permissions.UPDATE_SENSOR_CURSOR: True,
    Permissions.TERMINATE_PIPELINE_EXECUTION: True,
    Permissions.DELETE_PIPELINE_RUN: True,
    Permissions.RELOAD_REPOSITORY_LOCATION: True,
    Permissions.RELOAD_WORKSPACE: True,
    Permissions.WIPE_ASSETS: True,
    Permissions.REPORT_RUNLESS_ASSET_EVENTS: True,
    Permissions.LAUNCH_PARTITION_BACKFILL: True,
    Permissions.CANCEL_PARTITION_BACKFILL: True,
    Permissions.EDIT_DYNAMIC_PARTITIONS: True,
    Permissions.TOGGLE_AUTO_MATERIALIZE: True,
    Permissions.EDIT_CONCURRENCY_LIMIT: True,
}

LOCATION_SCOPED_PERMISSIONS = {
    Permissions.LAUNCH_PIPELINE_EXECUTION,
    Permissions.LAUNCH_PIPELINE_REEXECUTION,
    Permissions.START_SCHEDULE,
    Permissions.STOP_RUNNING_SCHEDULE,
    Permissions.EDIT_SENSOR,
    Permissions.UPDATE_SENSOR_CURSOR,
    Permissions.TERMINATE_PIPELINE_EXECUTION,
    Permissions.DELETE_PIPELINE_RUN,
    Permissions.RELOAD_REPOSITORY_LOCATION,
    Permissions.LAUNCH_PARTITION_BACKFILL,
    Permissions.CANCEL_PARTITION_BACKFILL,
    Permissions.EDIT_DYNAMIC_PARTITIONS,
    Permissions.REPORT_RUNLESS_ASSET_EVENTS,
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


def get_user_permissions(read_only: bool) -> Mapping[str, PermissionResult]:
    if read_only:
        perm_map = VIEWER_PERMISSIONS
    else:
        perm_map = EDITOR_PERMISSIONS

    return {
        perm: PermissionResult(enabled=enabled, disabled_reason=_get_disabled_reason(enabled))
        for perm, enabled in perm_map.items()
    }


def get_location_scoped_user_permissions(read_only: bool) -> Mapping[str, PermissionResult]:
    all_permissions = get_user_permissions(read_only)
    return {
        perm: result
        for perm, result in all_permissions.items()
        if perm in LOCATION_SCOPED_PERMISSIONS
    }
