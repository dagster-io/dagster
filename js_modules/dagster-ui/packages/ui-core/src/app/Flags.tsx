import {DEFAULT_FEATURE_FLAG_VALUES} from 'shared/app/DefaultFeatureFlags.oss';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {getJSONForKey} from '../util/getJSONForKey';

export const DAGSTER_FLAGS_KEY = 'DAGSTER_FLAGS';

export const WEB_WORKER_FEATURE_FLAGS_KEY = '__featureFlags';

/**
 * Type representing the mapping of feature flags to their boolean states.
 */
type FeatureFlagMap = Partial<Record<FeatureFlag, boolean>>;

/**
 * In-memory cache for feature flags, excludes default values.
 */
let currentFeatureFlags: FeatureFlagMap = {};

export const getCurrentFeatureFlags = (): FeatureFlagMap => {
  return currentFeatureFlags;
};

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
export const featureFlagsChannel = new BroadcastChannel('feature-flags');

// Initialize feature flags on module load
initializeFeatureFlags();

export const getFeatureFlagsWithoutDefaultValues = (): FeatureFlagMap => {
  return currentFeatureFlags;
};

export const getFeatureFlagDefaults = (): FeatureFlagMap => {
  return DEFAULT_FEATURE_FLAG_VALUES;
};

export const getFeatureFlagsWithDefaults = (): FeatureFlagMap => {
  return {...DEFAULT_FEATURE_FLAG_VALUES, ...currentFeatureFlags};
};

/**
 * Function to check if a specific feature flag is enabled.
 * Falls back to default values if the flag is unset.
 */
export const featureEnabled = (flag: FeatureFlag): boolean => {
  if (flag in currentFeatureFlags) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return currentFeatureFlags[flag]!;
  }

  // Return default value if flag is unset
  return DEFAULT_FEATURE_FLAG_VALUES[flag] ?? false;
};

/**
 * Function to update feature flags.
 * Updates the in-memory cache, persists to localStorage, and broadcasts the change.
 */
export const setFeatureFlags = (flags: FeatureFlagMap, broadcast: boolean = true) => {
  setFeatureFlagsInternal(flags);
  if (broadcast) {
    featureFlagsChannel.postMessage('updated');
  }
};

export const toggleFeatureFlag = (flag: FeatureFlag) => {
  const flags = getFeatureFlagsWithDefaults();
  flags[flag] = !flags[flag];
  setFeatureFlags(flags);
  featureFlagsChannel.postMessage('updated');
};
