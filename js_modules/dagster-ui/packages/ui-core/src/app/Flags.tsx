import memoize from 'lodash/memoize';
import {useMemo} from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {getFeatureFlags} from 'shared/app/getFeatureFlags.oss';

export const DAGSTER_FLAGS_KEY = 'DAGSTER_FLAGS';

export const featureEnabled = memoize((flag: FeatureFlag) => getFeatureFlags().includes(flag));

type FlagMap = {
  readonly [_ in FeatureFlag]: boolean;
};

export const useFeatureFlags = () => {
  return useMemo(() => {
    const flagSet = new Set(getFeatureFlags());
    const all: Record<string, boolean> = {};
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
  localStorage.setItem(DAGSTER_FLAGS_KEY, JSON.stringify(flags));
};
