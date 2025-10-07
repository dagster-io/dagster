import React from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

type FeatureFlagRow = {key: string; flagType: FeatureFlag; label?: React.ReactNode};

/**
 * Open-source feature flags to be displayed in Dagster UI "User settings"
 */
export const useVisibleFeatureFlagRows = (): FeatureFlagRow[] => [
  {
    key: 'Display resources in navigation sidebar',
    flagType: FeatureFlag.flagSidebarResources,
  },
  {
    key: 'Display faceted asset graph nodes',
    flagType: FeatureFlag.flagAssetNodeFacets,
  },
  {
    key: 'Display integrations marketplace',
    flagType: FeatureFlag.flagMarketplace,
  },
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
];
