import {useEffect, useState} from 'react';
import {DEFAULT_FEATURE_FLAG_VALUES} from 'shared/app/DefaultFeatureFlags.oss';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {getJSONForKey} from '../hooks/useStateWithStorage';

export const DAGSTER_FLAGS_KEY = 'DAGSTER_FLAGS';

/**
 * Type representing the mapping of feature flags to their boolean states.
 */
type FeatureFlagMap = Partial<Record<FeatureFlag, boolean>>;

/**
 * In-memory cache for feature flags, excludes default values.
 */
let currentFeatureFlags: FeatureFlagMap = {};

/**
 * Initialize the in-memory cache by loading from localStorage and handling migration.
 */
const initializeFeatureFlags = () => {
  let flags = getJSONForKey(DAGSTER_FLAGS_KEY);

  // Handle backward compatibility by migrating array to object
  if (Array.isArray(flags)) {
    const migratedFlags: FeatureFlagMap = {};
    flags.forEach((flag: FeatureFlag) => {
      migratedFlags[flag] = true;
    });
    setFeatureFlagsInternal(migratedFlags);
    flags = migratedFlags;
  }

  currentFeatureFlags = flags || {};
};

/**
 * Internal function to set feature flags without broadcasting.
 * Used during initialization and migration and by web-workers.
 */
export const setFeatureFlagsInternal = (flags: FeatureFlagMap) => {
  if (typeof flags !== 'object' || Array.isArray(flags)) {
    throw new Error('flags must be an object mapping FeatureFlag to boolean values');
  }
  currentFeatureFlags = flags;
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(DAGSTER_FLAGS_KEY, JSON.stringify(flags));
  }
};

// Initialize the BroadcastChannel
const featureFlagsChannel = new BroadcastChannel('feature-flags');

// Initialize feature flags on module load
initializeFeatureFlags();

export const getFeatureFlagsWithoutDefaultValues = (): FeatureFlagMap => {
  return currentFeatureFlags;
};

export const getFeatureFlagDefaults = (): FeatureFlagMap => {
  return DEFAULT_FEATURE_FLAG_VALUES;
};

/**
 * Function to check if a specific feature flag is enabled.
 * Falls back to default values if the flag is unset.
 */
export const featureEnabled = (flag: FeatureFlag): boolean => {
  if (flag in currentFeatureFlags) {
    return currentFeatureFlags[flag]!;
  }

  // Return default value if flag is unset
  return DEFAULT_FEATURE_FLAG_VALUES[flag] ?? false;
};

/**
 * Hook to access feature flags within React components.
 * Returns a flag map with resolved values (considering defaults).
 */
export const useFeatureFlags = (): Readonly<Record<FeatureFlag, boolean>> => {
  const [flags, setFlags] = useState<Record<FeatureFlag, boolean>>(() => {
    const allFlags: Partial<Record<FeatureFlag, boolean>> = {};

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

/**
 * Function to update feature flags.
 * Updates the in-memory cache, persists to localStorage, and broadcasts the change.
 */
export const setFeatureFlags = (flags: FeatureFlagMap) => {
  setFeatureFlagsInternal(flags);
  featureFlagsChannel.postMessage('updated');
};
