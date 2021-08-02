import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PermissionFragment} from './types/PermissionFragment';
import {PermissionsQuery} from './types/PermissionsQuery';

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

// todo dish: Delete this, we don't want it anymore.
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

export const extractPermissions = (permissions: PermissionFragment[]) => {
  const permsMap: PermissionsFromJSON = {};
  for (const item of permissions) {
    permsMap[item.permission] = item.value;
  }

  return {
    canLaunchPipelineExecution: !!permsMap.launch_pipeline_execution,
    canLaunchPipelineReexecution: !!permsMap.launch_pipeline_reexecution,
    canReconcileSchedulerState: !!permsMap.reconcile_scheduler_state,
    canStartSchedule: !!permsMap.start_schedule,
    canStopRunningSchedule: !!permsMap.stop_running_schedule,
    canStartSensor: !!permsMap.start_sensor,
    canStopSensor: !!permsMap.stop_sensor,
    canTerminatePipelineExecution: !!permsMap.terminate_pipeline_execution,
    canDeletePipelineRun: !!permsMap.delete_pipeline_run,
    canReloadRepositoryLocation: !!permsMap.reload_repository_location,
    canReloadWorkspace: !!permsMap.reload_workspace,
    canWipeAssets: !!permsMap.wipe_assets,
    canLaunchPartitionBackfill: !!permsMap.launch_partition_backfill,
    canCancelPartitionBackfill: !!permsMap.cancel_partition_backfill,
  };
};

export type PermissionsMap = ReturnType<typeof extractPermissions>;

export const DISABLED_MESSAGE = 'Disabled by your administrator';

type PermissionsContextValue = {
  rawPermissions: PermissionFragment[];
  permissionsMap: PermissionsMap;
};

export const PermissionsContext = React.createContext<PermissionsContextValue>({
  rawPermissions: [],
  permissionsMap: {} as PermissionsMap,
});

export const PermissionsProvider: React.FC = (props) => {
  const {data} = useQuery<PermissionsQuery>(PERMISSIONS_QUERY);
  const value = React.useMemo(() => {
    const rawPermissions = data?.permissions || [];
    const permissionsMap = extractPermissions(rawPermissions);
    return {
      rawPermissions,
      permissionsMap,
    };
  }, [data]);
  return <PermissionsContext.Provider value={value}>{props.children}</PermissionsContext.Provider>;
};

export const usePermissions = () => {
  const {permissionsMap} = React.useContext(PermissionsContext);
  return permissionsMap;
};

const PERMISSIONS_QUERY = gql`
  query PermissionsQuery {
    permissions {
      ...PermissionFragment
    }
  }

  fragment PermissionFragment on GraphenePermission {
    permission
    value
  }
`;
