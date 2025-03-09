import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

/**
 * Default values for feature flags when they are unset.
 */
export const DEFAULT_FEATURE_FLAG_VALUES: Partial<Record<FeatureFlag, boolean>> = {
  [FeatureFlag.flagAssetSelectionWorker]: true,
  [FeatureFlag.flagSelectionSyntax]: true,

  // Flags for tests
  [FeatureFlag.__TestFlagDefaultTrue]: true,
  [FeatureFlag.__TestFlagDefaultFalse]: false,
};
