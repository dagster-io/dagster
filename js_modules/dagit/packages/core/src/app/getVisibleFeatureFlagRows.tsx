import {FeatureFlag} from './Flags';

/**
 * Open-source feature flags to be displayed in Dagit "User settings"
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
    key: 'Experimental schedule/sensor logging view',
    flagType: FeatureFlag.flagSensorScheduleLogging,
  },
  {
    key: 'Experimental resource view',
    flagType: FeatureFlag.flagSidebarResources,
  },
];
