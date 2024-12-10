import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

/**
 * Default values for feature flags when they are unset.
 */
export const DEFAULT_FEATURE_FLAG_VALUES: Partial<Record<FeatureFlag, boolean>> = {
  [FeatureFlag.flagAssetSelectionWorker]: true,
  [FeatureFlag.flagAssetSelectionSyntax]: (() => {
    // This code ends up in worker bundles so first check typeof window.
    if (typeof window === 'undefined') {
      return false;
    }
    return new URLSearchParams(window.location.search).has('new-asset-selection-syntax');
  })(),

  // Flags for tests
  [FeatureFlag.__TestFlagDefaultTrue]: true,
  [FeatureFlag.__TestFlagDefaultFalse]: false,
};
