import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

/**
 * Default values for feature flags when they are unset.
 */
export const DEFAULT_FEATURE_FLAG_VALUES: Partial<Record<FeatureFlag, boolean>> = {
  [FeatureFlag.flagAssetSelectionWorker]: true,
  [FeatureFlag.flagAssetSelectionSyntax]: new URLSearchParams(global?.location?.search ?? '').has(
    'new-asset-selection-syntax',
  ),
  [FeatureFlag.flagRunSelectionSyntax]: new URLSearchParams(global?.location?.search ?? '').has(
    'new-run-selection-syntax',
  ),

  // Flags for tests
  [FeatureFlag.__TestFlagDefaultTrue]: true,
  [FeatureFlag.__TestFlagDefaultFalse]: false,
};
