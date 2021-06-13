import * as React from 'react';

import {AppContext} from '../app/AppContext';

export type PermissionsFromJSON = {
  launch_pipeline_execution?: boolean;
  launch_pipeline_reexecution?: boolean;
  reconcile_scheduler_state?: boolean;
  start_schedule?: boolean;
  stop_running_schedule?: boolean;
  start_sensor?: boolean;
  stop_sensor?: boolean;
  terminate_pipeline_execution?: boolean;
  delete_pipeline_run?: boolean;
  reload_repository_location?: boolean;
  reload_workspace?: boolean;
  wipe_assets?: boolean;
  launch_partition_backfill?: boolean;
  cancel_partition_backfill?: boolean;
};

export const PERMISSIONS_ALLOW_ALL: PermissionsFromJSON = {
  launch_pipeline_execution: true,
  launch_pipeline_reexecution: true,
  reconcile_scheduler_state: true,
  start_schedule: true,
  stop_running_schedule: true,
  start_sensor: true,
  stop_sensor: true,
  terminate_pipeline_execution: true,
  delete_pipeline_run: true,
  reload_repository_location: true,
  reload_workspace: true,
  wipe_assets: true,
  launch_partition_backfill: true,
  cancel_partition_backfill: true,
};

export const DISABLED_MESSAGE = 'Disabled by your administrator';

export const usePermissions = () => {
  const appContext = React.useContext(AppContext);
  const {permissions} = appContext;

  return React.useMemo(
    () => ({
      canLaunchPipelineExecution: !!permissions.launch_pipeline_execution,
      canLaunchPipelineReexecution: !!permissions.launch_pipeline_reexecution,
      canReconcileSchedulerState: !!permissions.reconcile_scheduler_state,
      canStartSchedule: !!permissions.start_schedule,
      canStopRunningSchedule: !!permissions.stop_running_schedule,
      canStartSensor: !!permissions.start_sensor,
      canStopSensor: !!permissions.stop_sensor,
      canTerminatePipelineExecution: !!permissions.terminate_pipeline_execution,
      canDeletePipelineRun: !!permissions.delete_pipeline_run,
      canReloadRepositoryLocation: !!permissions.reload_repository_location,
      canReloadWorkspace: !!permissions.reload_workspace,
      canWipeAssets: !!permissions.wipe_assets,
      canLaunchPartitionBackfill: !!permissions.launch_partition_backfill,
      canCancelPartitionBackfill: !!permissions.cancel_partition_backfill,
    }),
    [permissions],
  );
};

export type PermissionSet = ReturnType<typeof usePermissions>;
