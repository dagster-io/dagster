import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

/**
 * Open-source feature flags to be displayed in Dagster UI "User settings"
 */
export const useVisibleFeatureFlagRows = () => [
  {
    key: 'Display resources in navigation sidebar',
    flagType: FeatureFlag.flagSidebarResources,
  },
  {
    key: 'Disable WebSockets',
    flagType: FeatureFlag.flagDisableWebsockets,
  },
  {
    key: 'Disable automatically loading default config in launchpad',
    flagType: FeatureFlag.flagDisableAutoLoadDefaults,
  },
];
