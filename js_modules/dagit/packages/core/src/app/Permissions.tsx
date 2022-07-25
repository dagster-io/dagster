import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PermissionFragment} from './types/PermissionFragment';
import {PermissionsQuery} from './types/PermissionsQuery';

// used in tests, to ensure against permission renames.  Should make sure that the mapping in
// extractPermissions is handled correctly
export const EXPECTED_PERMISSIONS = {
  launch_pipeline_execution: true,
  launch_pipeline_reexecution: true,
  start_schedule: true,
  stop_running_schedule: true,
  edit_sensor: true,
  terminate_pipeline_execution: true,
  delete_pipeline_run: true,
  reload_repository_location: true,
  reload_workspace: true,
  wipe_assets: true,
  launch_partition_backfill: true,
  cancel_partition_backfill: true,
};

export type PermissionResult = {
  enabled: boolean;
  disabledReason: string;
};

export type PermissionsFromJSON = {
  launch_pipeline_execution?: PermissionResult;
  launch_pipeline_reexecution?: PermissionResult;
  start_schedule?: PermissionResult;
  stop_running_schedule?: PermissionResult;
  edit_sensor?: PermissionResult;
  terminate_pipeline_execution?: PermissionResult;
  delete_pipeline_run?: PermissionResult;
  reload_repository_location?: PermissionResult;
  reload_workspace?: PermissionResult;
  wipe_assets?: PermissionResult;
  launch_partition_backfill?: PermissionResult;
  cancel_partition_backfill?: PermissionResult;
};

const DEFAULT_PERMISSIONS = {
  enabled: false,
  disabledReason: 'Disabled by your administrator',
};

const extractPermissions = (permissions: PermissionFragment[]) => {
  const permsMap: PermissionsFromJSON = {};
  for (const item of permissions) {
    permsMap[item.permission] = {
      enabled: item.value,
      disabledReason: item.disabledReason || '',
    };
  }

  return {
    canLaunchPipelineExecution: permsMap.launch_pipeline_execution || DEFAULT_PERMISSIONS,
    canLaunchPipelineReexecution: permsMap.launch_pipeline_reexecution || DEFAULT_PERMISSIONS,
    canStartSchedule: permsMap.start_schedule || DEFAULT_PERMISSIONS,
    canStopRunningSchedule: permsMap.stop_running_schedule || DEFAULT_PERMISSIONS,
    canStartSensor: permsMap.edit_sensor || DEFAULT_PERMISSIONS,
    canStopSensor: permsMap.edit_sensor || DEFAULT_PERMISSIONS,
    canTerminatePipelineExecution: permsMap.terminate_pipeline_execution || DEFAULT_PERMISSIONS,
    canDeletePipelineRun: permsMap.delete_pipeline_run || DEFAULT_PERMISSIONS,
    canReloadRepositoryLocation: permsMap.reload_repository_location || DEFAULT_PERMISSIONS,
    canReloadWorkspace: permsMap.reload_workspace || DEFAULT_PERMISSIONS,
    canWipeAssets: permsMap.wipe_assets || DEFAULT_PERMISSIONS,
    canLaunchPartitionBackfill: permsMap.launch_partition_backfill || DEFAULT_PERMISSIONS,
    canCancelPartitionBackfill: permsMap.cancel_partition_backfill || DEFAULT_PERMISSIONS,
  };
};

export type PermissionsMap = ReturnType<typeof extractPermissions>;

export const PermissionsContext = React.createContext<PermissionFragment[]>([]);

export const PermissionsProvider: React.FC = (props) => {
  const {data} = useQuery<PermissionsQuery>(PERMISSIONS_QUERY);
  const value = React.useMemo(() => data?.permissions || [], [data]);
  return <PermissionsContext.Provider value={value}>{props.children}</PermissionsContext.Provider>;
};

export const usePermissions = () => {
  const rawPermissions = React.useContext(PermissionsContext);
  return React.useMemo(() => extractPermissions(rawPermissions), [rawPermissions]);
};

const PERMISSIONS_QUERY = gql`
  query PermissionsQuery {
    permissions {
      ...PermissionFragment
    }
  }

  fragment PermissionFragment on Permission {
    permission
    value
    disabledReason
  }
`;
