import {useQuery} from '@apollo/client';
import * as React from 'react';

import {graphql} from '../graphql';
import {PermissionFragmentFragment} from '../graphql/graphql';

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

export const extractPermissions = (
  permissions: PermissionFragmentFragment[],
  fallback: PermissionFragmentFragment[] = [],
) => {
  const permsMap: PermissionsFromJSON = {};
  for (const item of permissions) {
    permsMap[item.permission] = {
      enabled: item.value,
      disabledReason: item.disabledReason || '',
    };
  }

  const fallbackMap: PermissionsFromJSON = {};
  for (const item of fallback) {
    fallbackMap[item.permission] = {
      enabled: item.value,
      disabledReason: item.disabledReason || '',
    };
  }

  const permissionOrFallback = (key: keyof PermissionsFromJSON) => {
    return permsMap[key] || fallbackMap[key] || DEFAULT_PERMISSIONS;
  };

  return {
    canLaunchPipelineExecution: permissionOrFallback('launch_pipeline_execution'),
    canLaunchPipelineReexecution: permissionOrFallback('launch_pipeline_reexecution'),
    canStartSchedule: permissionOrFallback('start_schedule'),
    canStopRunningSchedule: permissionOrFallback('stop_running_schedule'),
    canStartSensor: permissionOrFallback('edit_sensor'),
    canStopSensor: permissionOrFallback('edit_sensor'),
    canTerminatePipelineExecution: permissionOrFallback('terminate_pipeline_execution'),
    canDeletePipelineRun: permissionOrFallback('delete_pipeline_run'),
    canReloadRepositoryLocation: permissionOrFallback('reload_repository_location'),
    canReloadWorkspace: permissionOrFallback('reload_workspace'),
    canWipeAssets: permissionOrFallback('wipe_assets'),
    canLaunchPartitionBackfill: permissionOrFallback('launch_partition_backfill'),
    canCancelPartitionBackfill: permissionOrFallback('cancel_partition_backfill'),
  };
};

export type PermissionsMap = ReturnType<typeof extractPermissions>;

type PermissionsContext = {
  // todo dish: Optional for Cloud compatibility. Make them non-optional.
  unscopedPermissions?: PermissionsMap;
  locationPermissions?: Record<string, PermissionsMap>;
  loading: boolean;

  // todo dish: For Cloud compatibility, delete.
  data: PermissionFragmentFragment[];
};

export const PermissionsContext = React.createContext<PermissionsContext>({
  unscopedPermissions: extractPermissions([]),
  locationPermissions: {},
  loading: true,

  // todo dish: For Cloud compatibility, delete.
  data: [],
});

export const PermissionsProvider: React.FC = (props) => {
  const {data, loading} = useQuery(PERMISSIONS_QUERY, {
    fetchPolicy: 'cache-first', // Not expected to change after initial load.
  });

  const value = React.useMemo(() => {
    const unscopedPermissionsRaw = data?.unscopedPermissions || [];
    const unscopedPermissions = extractPermissions(unscopedPermissionsRaw);

    const locationEntries =
      data?.workspaceOrError.__typename === 'Workspace'
        ? data.workspaceOrError.locationEntries
        : [];

    const locationPermissions: Record<string, PermissionsMap> = {};
    locationEntries.forEach((locationEntry) => {
      const {name, permissions} = locationEntry;
      locationPermissions[name] = extractPermissions(permissions, unscopedPermissionsRaw);
    });

    return {
      unscopedPermissions,
      locationPermissions,
      loading,

      // todo dish: For Cloud compatibility, delete.
      data: unscopedPermissionsRaw,
    };
  }, [data, loading]);

  return <PermissionsContext.Provider value={value}>{props.children}</PermissionsContext.Provider>;
};

/**
 * Retrieve a permission that is intentionally unscoped.
 */
export const useUnscopedPermissions = () => {
  const {unscopedPermissions: unscoped, loading} = React.useContext(PermissionsContext);
  // todo dish: Clean up once `unscopedPermissions` is non-optional.
  const unscopedPermissions = unscoped!;
  return {...unscopedPermissions, loading};
};

/**
 * Retrieve a permission that is scoped to a specific code location. The unscoped permission set
 * will be used as a fallback, so that if the permission is not defined for that location, we still
 * have a valid value.
 */
export const usePermissionsForLocation = (locationName: string | null | undefined) => {
  const {unscopedPermissions, locationPermissions, loading} = React.useContext(PermissionsContext);
  // todo dish: Clean up once `unscopedPermissions` is non-optional.
  let permissionsForLocation = unscopedPermissions!;
  if (locationName && locationPermissions && locationPermissions.hasOwnProperty(locationName)) {
    permissionsForLocation = locationPermissions[locationName];
  }
  return {...permissionsForLocation, loading};
};

// todo dish: Update callsites to either location-based perms or intentionally unscoped perms.
export const usePermissionsDEPRECATED = useUnscopedPermissions;

// todo dish: Temporary to pass Cloud build. Delete after Cloud callsites are updated.
export const usePermissions = useUnscopedPermissions;

const PERMISSIONS_QUERY = graphql(`
  query PermissionsQuery {
    unscopedPermissions: permissions {
      ...PermissionFragment
    }
    workspaceOrError {
      ... on Workspace {
        locationEntries {
          id
          name
          permissions {
            ...PermissionFragment
          }
        }
      }
    }
  }

  fragment PermissionFragment on Permission {
    permission
    value
    disabledReason
  }
`);
