import memoize from 'lodash/memoize';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {DAGSTER_FLAGS_KEY} from './Flags';
import {getJSONForKey} from '../hooks/useStateWithStorage';

export const getFeatureFlags: () => FeatureFlag[] = memoize(
  () => getJSONForKey(DAGSTER_FLAGS_KEY) || [],
);
