import memoize from 'lodash/memoize';
import * as React from 'react';

import {getJSONForKey} from '../hooks/useStateWithStorage';

export const DAGIT_FLAGS_KEY = 'DAGIT_FLAGS';

export enum FeatureFlag {
  flagDebugConsoleLogging = 'flagDebugConsoleLogging',
  flagDisableWebsockets = 'flagDisableWebsockets',
  flagNewPartitionsView = 'flagNewPartitionsView',
  flagFlatLeftNav = 'flagFlatLeftNav',
}

export const getFeatureFlags: () => FeatureFlag[] = memoize(
  () => getJSONForKey(DAGIT_FLAGS_KEY) || [],
);

export const featureEnabled = memoize((flag: FeatureFlag) => getFeatureFlags().includes(flag));

type FlagMap = {
  readonly [F in FeatureFlag]: boolean;
};

export const useFeatureFlags = () => {
  return React.useMemo(() => {
    const flagSet = new Set(getFeatureFlags());
    const all = {};
    for (const flag in FeatureFlag) {
      all[flag] = flagSet.has(flag as FeatureFlag);
    }
    return all as FlagMap;
  }, []);
};

export const setFeatureFlags = (flags: FeatureFlag[]) => {
  if (!(flags instanceof Array)) {
    throw new Error('flags must be an array');
  }
  localStorage.setItem(DAGIT_FLAGS_KEY, JSON.stringify(flags));
};
