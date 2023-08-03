import {FeatureFlag} from './Flags';

/**
 * Open-source feature flags to be displayed in Dagster UI "User settings"
 */
export const getVisibleFeatureFlagRows = () => [
  {
    key: 'Debug console logging',
    flagType: FeatureFlag.flagDebugConsoleLogging,
  },
  {
    key: 'Disable WebSockets',
    flagType: FeatureFlag.flagDisableWebsockets,
  },
  {
    key: 'Display resources in navigation sidebar',
    flagType: FeatureFlag.flagSidebarResources,
  },
  {
    key: 'Disable automatically loading default config in launchpad',
    flagType: FeatureFlag.flagDisableAutoLoadDefaults,
  },
  {
    key: 'Experimental schedule/sensor logging view',
    flagType: FeatureFlag.flagSensorScheduleLogging,
  },
  {
    key: 'Experimental instance-level concurrency limits',
    flagType: FeatureFlag.flagInstanceConcurrencyLimits,
  },
  {
    key: 'Experimental horizontal asset DAGs',
    flagType: FeatureFlag.flagHorizontalDAGs,
  },
];
