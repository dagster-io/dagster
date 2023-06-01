import React from 'react';

import {PermissionsContext, PermissionsMap, extractPermissions} from '../app/Permissions';

type PermissionOverrides = Partial<PermissionsMap>;

interface Props {
  unscopedOverrides?: PermissionOverrides;
  locationOverrides?: Record<string, PermissionOverrides>;
  children: React.ReactNode;
}

export const TestPermissionsProvider = (props: Props) => {
  const {unscopedOverrides = {}, locationOverrides = {}, children} = props;
  const value = React.useMemo(() => {
    const unscopedPermissions = {...extractPermissions([]), ...unscopedOverrides};

    const locationPermissions: Record<string, PermissionsMap> = {};
    for (const locationName in locationOverrides) {
      const overridesForLocation = locationOverrides[locationName];
      locationPermissions[locationName] = {...extractPermissions([]), ...overridesForLocation};
    }

    return {
      unscopedPermissions,
      locationPermissions,
      loading: false,
      rawUnscopedData: [], // Not used
    };
  }, [locationOverrides, unscopedOverrides]);

  return <PermissionsContext.Provider value={value}>{children}</PermissionsContext.Provider>;
};
