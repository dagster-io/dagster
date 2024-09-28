import * as React from 'react';

import {
  PermissionFragment,
  PermissionsQuery,
  PermissionsQueryVariables,
} from './types/Permissions.types';
import {gql, useQuery} from '../apollo-client';

// used in tests, to ensure against permission renames.  Should make sure that the mapping in
// extractPermissions is handled correctly
export const EXPECTED_PERMISSIONS = {
  launch_pipeline_execution: true,
  launch_pipeline_reexecution: true,
  start_schedule: true,
  stop_running_schedule: true,
  edit_sensor: true,
  update_sensor_cursor: true,
  terminate_pipeline_execution: true,
  delete_pipeline_run: true,
  reload_repository_location: true,
  reload_workspace: true,
  wipe_assets: true,
  report_runless_asset_events: true,
  launch_partition_backfill: true,
  cancel_partition_backfill: true,
  edit_dynamic_partitions: true,
  toggle_auto_materialize: true,
  edit_concurrency_limit: true,
  edit_workspace: true,
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
  update_sensor_cursor?: PermissionResult;
  terminate_pipeline_execution?: PermissionResult;
  delete_pipeline_run?: PermissionResult;
  reload_repository_location?: PermissionResult;
  reload_workspace?: PermissionResult;
  wipe_assets?: PermissionResult;
  report_runless_asset_events?: PermissionResult;
  launch_partition_backfill?: PermissionResult;
  cancel_partition_backfill?: PermissionResult;
  toggle_auto_materialize?: PermissionResult;
  edit_concurrency_limit?: PermissionResult;
  edit_workspace?: PermissionResult;
};

export const DEFAULT_DISABLED_REASON = 'Disabled by your administrator';

const DEFAULT_PERMISSIONS = {
  enabled: false,
  disabledReason: DEFAULT_DISABLED_REASON,
};

export const extractPermissions = (
  permissions: PermissionFragment[],
  fallback: PermissionFragment[] = [],
) => {
  const permsMap: PermissionsFromJSON = {};
  for (const item of permissions) {
    (permsMap as any)[item.permission] = {
      enabled: item.value,
      disabledReason: item.disabledReason || '',
    };
  }

  const fallbackMap: PermissionsFromJSON = {};
  for (const item of fallback) {
    (fallbackMap as any)[item.permission] = {
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
    canReportRunlessAssetEvents: permissionOrFallback('report_runless_asset_events'),
    canLaunchPartitionBackfill: permissionOrFallback('launch_partition_backfill'),
    canCancelPartitionBackfill: permissionOrFallback('cancel_partition_backfill'),
    canToggleAutoMaterialize: permissionOrFallback('toggle_auto_materialize'),
    canEditConcurrencyLimit: permissionOrFallback('edit_concurrency_limit'),
    canEditWorkspace: permissionOrFallback('edit_workspace'),
    canUpdateSensorCursor: permissionOrFallback('update_sensor_cursor'),
  };
};

export type PermissionsMap = ReturnType<typeof extractPermissions>;

type PermissionBooleans = Record<keyof PermissionsMap, boolean>;
type PermissionDisabledReasons = Record<keyof PermissionsMap, string>;
export type PermissionsState = {
  permissions: PermissionBooleans;
  disabledReasons: PermissionDisabledReasons;
  loading: boolean;
};

type PermissionsContextType = {
  unscopedPermissions: PermissionsMap;
  locationPermissions: Record<string, PermissionsMap>;
  loading: boolean;
  // Raw unscoped permission data, for Cloud extraction
  rawUnscopedData: PermissionFragment[];
};

export const PermissionsContext = React.createContext<PermissionsContextType>({
  unscopedPermissions: extractPermissions([]),
  locationPermissions: {},
  loading: true,
  rawUnscopedData: [],
});

export const PermissionsProvider = (props: {children: React.ReactNode}) => {
  const queryResult = useQuery<PermissionsQuery, PermissionsQueryVariables>(PERMISSIONS_QUERY, {
    fetchPolicy: 'cache-first', // Not expected to change after initial load.
  });

  const {data, loading} = queryResult;

  const value = React.useMemo(() => {
    const unscopedPermissionsRaw = data?.unscopedPermissions || [];
    const unscopedPermissions = extractPermissions(unscopedPermissionsRaw);

    const locationEntries =
      data?.locationStatusesOrError.__typename === 'WorkspaceLocationStatusEntries'
        ? data.locationStatusesOrError.entries
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
      rawUnscopedData: unscopedPermissionsRaw,
    };
  }, [data, loading]);

  return <PermissionsContext.Provider value={value}>{props.children}</PermissionsContext.Provider>;
};

export const permissionResultForKey = (
  permissionsState: PermissionsState,
  key: keyof PermissionsMap,
): PermissionResult => {
  const {permissions, disabledReasons} = permissionsState;
  return {
    enabled: permissions[key],
    disabledReason: disabledReasons[key],
  };
};

const unpackPermissions = (
  permissions: PermissionsMap,
): {booleans: PermissionBooleans; disabledReasons: PermissionDisabledReasons} => {
  const booleans = {};
  const disabledReasons = {};
  Object.keys(permissions).forEach((key) => {
    const {enabled, disabledReason} = (permissions as any)[key] as PermissionResult;
    (booleans as any)[key] = enabled;
    (disabledReasons as any)[key] = disabledReason;
  });
  return {
    booleans: booleans as PermissionBooleans,
    disabledReasons: disabledReasons as PermissionDisabledReasons,
  };
};

/**
 * Retrieve a permission that is intentionally unscoped.
 */
export const useUnscopedPermissions = (): PermissionsState => {
  const {unscopedPermissions, loading} = React.useContext(PermissionsContext);
  const unpacked = React.useMemo(
    () => unpackPermissions(unscopedPermissions),
    [unscopedPermissions],
  );

  return React.useMemo(() => {
    return {
      permissions: unpacked.booleans,
      disabledReasons: unpacked.disabledReasons,
      loading,
    };
  }, [unpacked, loading]);
};

/**
 * Retrieve a permission that is scoped to a specific code location. The unscoped permission set
 * will be used as a fallback, so that if the permission is not defined for that location, we still
 * have a valid value.
 */
export const usePermissionsForLocation = (
  locationName: string | null | undefined,
): PermissionsState => {
  const {unscopedPermissions, locationPermissions, loading} = React.useContext(PermissionsContext);
  let permissionsForLocation = unscopedPermissions;
  if (locationName && locationPermissions.hasOwnProperty(locationName)) {
    permissionsForLocation = locationPermissions[locationName]!;
  }

  const unpacked = unpackPermissions(permissionsForLocation);
  return React.useMemo(() => {
    return {
      permissions: unpacked.booleans,
      disabledReasons: unpacked.disabledReasons,
      loading,
    };
  }, [unpacked, loading]);
};

export const PERMISSIONS_QUERY = gql`
  query PermissionsQuery {
    unscopedPermissions: permissions {
      ...PermissionFragment
    }
    locationStatusesOrError {
      __typename
      ... on WorkspaceLocationStatusEntries {
        entries {
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
`;
