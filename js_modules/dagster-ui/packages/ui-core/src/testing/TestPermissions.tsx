import * as React from 'react';

import {PermissionsContext, PermissionsMap, extractPermissions} from '../app/Permissions';
import {wrapPromise} from '../utils/wrapPromise';

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

  const wrapped = React.useMemo(() => {
    const p = Promise.resolve(value);
    return wrapPromise(p);
  }, [value]);

  return <PermissionsContext.Provider value={wrapped}>{children}</PermissionsContext.Provider>;
};
