import {useEffect, useState} from 'react';
import {DEFAULT_FEATURE_FLAG_VALUES} from 'shared/app/DefaultFeatureFlags.oss';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {featureFlagsChannel, getCurrentFeatureFlags} from './Flags';

/**
 * Hook to access feature flags within React components.
 * Returns a flag map with resolved values (considering defaults).
 */
export const useFeatureFlags = (): Readonly<Record<FeatureFlag, boolean>> => {
  const [flags, setFlags] = useState<Record<FeatureFlag, boolean>>(() => {
    const allFlags: Partial<Record<FeatureFlag, boolean>> = {};
    const currentFeatureFlags = getCurrentFeatureFlags();

    for (const flag in FeatureFlag) {
      const key = flag as FeatureFlag;
      if (key in currentFeatureFlags) {
        allFlags[key] = currentFeatureFlags[key];
      } else {
        allFlags[key] = DEFAULT_FEATURE_FLAG_VALUES[key] ?? false;
      }
    }
    return allFlags as Record<FeatureFlag, boolean>;
  });

  useEffect(() => {
    const handleFlagsChange = () => {
      const allFlags: Partial<Record<FeatureFlag, boolean>> = {};
      const currentFeatureFlags = getCurrentFeatureFlags();

      for (const flag in FeatureFlag) {
        const key = flag as FeatureFlag;
        if (key in currentFeatureFlags) {
          allFlags[key] = currentFeatureFlags[key];
        } else {
          allFlags[key] = DEFAULT_FEATURE_FLAG_VALUES[key] ?? false;
        }
      }
      setFlags(allFlags as Record<FeatureFlag, boolean>);
    };

    // Listen for messages from the BroadcastChannel
    featureFlagsChannel.addEventListener('message', handleFlagsChange);

    return () => {
      featureFlagsChannel.removeEventListener('message', handleFlagsChange);
    };
  }, []);

  return flags;
};
