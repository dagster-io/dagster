from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .context import WorkspaceProcessContext

VIEWER_PERMISSIONS = {
    "launch_pipeline_execution": False,
    "launch_pipeline_reexecution": False,
    "reconcile_scheduler_state": False,
    "start_schedule": False,
    "stop_running_schedule": False,
    "start_sensor": False,
    "stop_sensor": False,
    "terminate_pipeline_execution": False,
    "delete_pipeline_run": False,
    "reload_repository_location": False,
    "reload_workspace": False,
    "wipe_assets": False,
    "launch_partition_backfill": False,
    "cancel_partition_backfill": False,
}

EDITOR_PERMISSIONS = {
    "launch_pipeline_execution": True,
    "launch_pipeline_reexecution": True,
    "reconcile_scheduler_state": True,
    "start_schedule": True,
    "stop_running_schedule": True,
    "start_sensor": True,
    "stop_sensor": True,
    "terminate_pipeline_execution": True,
    "delete_pipeline_run": True,
    "reload_repository_location": True,
    "reload_workspace": True,
    "wipe_assets": True,
    "launch_partition_backfill": True,
    "cancel_partition_backfill": True,
}


def get_user_permissions(context: "WorkspaceProcessContext") -> Dict[str, bool]:
    if context.read_only:
        return VIEWER_PERMISSIONS
    else:
        return EDITOR_PERMISSIONS
