import {Checkbox} from '@dagster-io/ui';
import * as React from 'react';

import {FeatureFlagType} from './Flags';
import {getVisibleFeatureFlagRows} from './getVisibleFeatureFlagRows';

/**
 * todo dish: Delete me!
 *
 * Temporary function to keep Cloud build happy.
 */
export const getFeatureFlagRows = (
  flags: FeatureFlagType[],
  toggleFlag: (flag: FeatureFlagType) => void,
) => {
  return getVisibleFeatureFlagRows().map(({key, flagType}) => ({
    key,
    value: (
      <Checkbox
        format="switch"
        checked={flags.includes(flagType)}
        onChange={() => toggleFlag(flagType)}
      />
    ),
  }));
};
