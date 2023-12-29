import {Box} from '@dagster-io/ui-components';
import React from 'react';

import {FeatureFlag} from './Flags';

/**
 * Open-source feature flags to be displayed in Dagster UI "User settings"
 */
export const getVisibleFeatureFlagRows = () => [
  {
    key: 'Experimental asset graph experience',
    label: (
      <Box flex={{direction: 'column'}}>
        Experimental asset graph experience
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
    key: 'Display resources in navigation sidebar',
    flagType: FeatureFlag.flagSidebarResources,
  },
  {
    key: 'Disable Asset Graph caching',
    flagType: FeatureFlag.flagDisableDAGCache,
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
