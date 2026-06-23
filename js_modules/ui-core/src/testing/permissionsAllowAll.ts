import {PermissionsFromJSON} from '../app/Permissions';

const DEFAULT_PERMISSIONS = {
  enabled: true,
  disabledReason: '',
};

export const PERMISSIONS_ALLOW_ALL: PermissionsFromJSON = {
  launch_pipeline_execution: DEFAULT_PERMISSIONS,
  launch_pipeline_reexecution: DEFAULT_PERMISSIONS,
  start_schedule: DEFAULT_PERMISSIONS,
  stop_running_schedule: DEFAULT_PERMISSIONS,
  edit_sensor: DEFAULT_PERMISSIONS,
  update_sensor_cursor: DEFAULT_PERMISSIONS,
  terminate_pipeline_execution: DEFAULT_PERMISSIONS,
  delete_pipeline_run: DEFAULT_PERMISSIONS,
  reload_repository_location: DEFAULT_PERMISSIONS,
  reload_workspace: DEFAULT_PERMISSIONS,
  wipe_assets: DEFAULT_PERMISSIONS,
  launch_partition_backfill: DEFAULT_PERMISSIONS,
  cancel_partition_backfill: DEFAULT_PERMISSIONS,
};
