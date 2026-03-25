import {FeatureFlag} from '@shared/FeatureFlags';
import React from 'react';

type FeatureFlagRow = {key: string; flagType: FeatureFlag; label?: React.ReactNode};

/**
 * Open-source feature flags to be displayed in Dagster UI "User settings"
 */
export const useVisibleFeatureFlagRows = (): FeatureFlagRow[] => [
  {
    key: 'Disable WebSockets',
    flagType: FeatureFlag.flagDisableWebsockets,
  },
  {
    key: 'Disable automatically loading default config in launchpad',
    flagType: FeatureFlag.flagDisableAutoLoadDefaults,
  },
  {
    key: 'Show separate asset graph groups per code location',
    flagType: FeatureFlag.flagAssetGraphGroupsPerCodeLocation,
  },
  {
    key: 'Skip optional resource defaults in run config',
    flagType: FeatureFlag.flagSkipOptionalResourceDefaultsInRunConfig,
  },
];
