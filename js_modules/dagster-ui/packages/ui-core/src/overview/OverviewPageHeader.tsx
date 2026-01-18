import {Box, PageHeader} from '@dagster-io/ui-components';
import React from 'react';
import {observeEnabled} from 'shared/app/observeEnabled.oss';
import {ObserveRolloutBanner} from 'shared/overview/ObserveRolloutBanner.oss';

import {OverviewTabs} from './OverviewTabs';

export const OverviewPageHeader = ({
  tab,
  queryData,
  refreshState,
  ...rest
}: React.ComponentProps<typeof OverviewTabs> &
  Omit<React.ComponentProps<typeof PageHeader>, 'title'>) => {
  const observeUIEnabled = observeEnabled();
  if (observeUIEnabled) {
    return null;
  }

  return (
    <div>
      <ObserveRolloutBanner />
      <PageHeader
        tabs={
          <Box flex={{direction: 'column', gap: 8}}>
            <OverviewTabs tab={tab} queryData={queryData} refreshState={refreshState} />
          </Box>
        }
        {...rest}
      />
    </div>
  );
};
