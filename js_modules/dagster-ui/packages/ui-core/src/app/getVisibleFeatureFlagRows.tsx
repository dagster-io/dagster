import {Box} from '@dagster-io/ui-components';
import React from 'react';

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
  {
    key: 'New asset lineage sidebar',
    label: (
      <Box flex={{direction: 'column'}}>
        New asset lineage sidebar,
        <div>
          <a
            href="https://github.com/dagster-io/dagster/discussions/16657"
            target="_blank"
            rel="noreferrer"
          >
            Learn more
          </a>
        </div>
      </Box>
    ),
    flagType: FeatureFlag.flagDAGSidebar,
  },
  {
    key: 'Disable Asset Graph caching',
    flagType: FeatureFlag.flagDisableDAGCache,
  },
  {
    key: 'Experimental longest path DAG algorithm (Faster)',
    flagType: FeatureFlag.flagLongestPathDag,
    label: (
      <Box flex={{direction: 'column'}}>
        Experimental longest path asset graph algorithm (Faster).
        <div>
          <a
            href="https://github.com/dagster-io/dagster/discussions/17240"
            target="_blank"
            rel="noreferrer"
          >
            Learn more
          </a>
        </div>
      </Box>
    ),
  },
];
