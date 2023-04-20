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
    key: 'Display resources in navigation sidebar',
    flagType: FeatureFlag.flagSidebarResources,
  },
  {
    key: 'Experimental schedule/sensor logging view',
    flagType: FeatureFlag.flagSensorScheduleLogging,
  },
  {
    key: 'Experimental Runs table view with filtering',
    flagType: FeatureFlag.flagRunsTableFiltering,
  },
];
