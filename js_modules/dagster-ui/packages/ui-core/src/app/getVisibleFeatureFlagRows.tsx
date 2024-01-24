import {FeatureFlag} from './Flags';

/**
 * Open-source feature flags to be displayed in Dagster UI "User settings"
 */
export const getVisibleFeatureFlagRows = () => [
  {
    key: 'Experimental DAG layout algorithm',
    flagType: FeatureFlag.flagGraphvizRendering,
  },
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
  {
    key: 'Debug console logging',
    flagType: FeatureFlag.flagDebugConsoleLogging,
  },
];
