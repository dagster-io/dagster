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

export type PermissionsFromJSON = {
  launch_pipeline_execution?: boolean;
  launch_pipeline_reexecution?: boolean;
  start_schedule?: boolean;
  stop_running_schedule?: boolean;
  edit_sensor?: boolean;
  terminate_pipeline_execution?: boolean;
  delete_pipeline_run?: boolean;
  reload_repository_location?: boolean;
  reload_workspace?: boolean;
  wipe_assets?: boolean;
  launch_partition_backfill?: boolean;
  cancel_partition_backfill?: boolean;
};

const extractPermissions = (permissions: PermissionFragment[]) => {
  const permsMap: PermissionsFromJSON = {};
  for (const item of permissions) {
    permsMap[item.permission] = item.value;
  }

  return {
    canLaunchPipelineExecution: !!permsMap.launch_pipeline_execution,
    canLaunchPipelineReexecution: !!permsMap.launch_pipeline_reexecution,
    canStartSchedule: !!permsMap.start_schedule,
    canStopRunningSchedule: !!permsMap.stop_running_schedule,
    canStartSensor: !!permsMap.edit_sensor,
    canStopSensor: !!permsMap.edit_sensor,
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
  }
`;
