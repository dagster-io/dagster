import {Box, PageHeader} from '@dagster-io/ui-components';
import React from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {OverviewTabs} from './OverviewTabs';
import {featureEnabled} from '../app/Flags';

export const OverviewPageHeader = ({
  tab,
  queryData,
  refreshState,
  ...rest
}: React.ComponentProps<typeof OverviewTabs> &
  Omit<React.ComponentProps<typeof PageHeader>, 'title'>) => {
  const observeUIEnabled = featureEnabled(FeatureFlag.flagUseNewObserveUIs);
  if (observeUIEnabled) {
    return null;
  }

  return (
    <PageHeader
      tabs={
        <Box flex={{direction: 'column', gap: 8}}>
          <OverviewTabs tab={tab} queryData={queryData} refreshState={refreshState} />
        </Box>
      }
      {...rest}
    />
  );
};
