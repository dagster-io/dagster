import memoize from 'lodash/memoize';
import * as React from 'react';

import {getJSONForKey} from '../hooks/useStateWithStorage';

export const DAGSTER_FLAGS_KEY = 'DAGSTER_FLAGS';

// Use const because we need to extend this in cloud. https://blog.logrocket.com/extend-enums-typescript/
export const FeatureFlag = {
  flagDebugConsoleLogging: 'flagDebugConsoleLogging' as const,
  flagDisableWebsockets: 'flagDisableWebsockets' as const,
  flagSidebarResources: 'flagSidebarResources' as const,
  flagDisableAutoLoadDefaults: 'flagDisableAutoLoadDefaults' as const,
  flagGraphvizRendering: 'flagGraphvizRendering' as const,
};
export type FeatureFlagType = keyof typeof FeatureFlag;

export const getFeatureFlags: () => FeatureFlagType[] = memoize(
  () => getJSONForKey(DAGSTER_FLAGS_KEY) || [],
);

export const featureEnabled = memoize((flag: FeatureFlagType) => getFeatureFlags().includes(flag));

type FlagMap = {
  readonly [F in FeatureFlagType]: boolean;
};

export const useFeatureFlags = () => {
  return React.useMemo(() => {
    const flagSet = new Set(getFeatureFlags());
    const all: Record<string, boolean> = {};
    for (const flag in FeatureFlag) {
      all[flag] = flagSet.has(flag as FeatureFlagType);
    }
    return all as FlagMap;
  }, []);
};

export const setFeatureFlags = (flags: FeatureFlagType[]) => {
  if (!(flags instanceof Array)) {
    throw new Error('flags must be an array');
  }
  localStorage.setItem(DAGSTER_FLAGS_KEY, JSON.stringify(flags));
};
